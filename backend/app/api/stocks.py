"""
股票推荐 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import SessionLocal, get_db
from app.schemas.stock import RecommendResponse, StockRecommend
from app.services.recommendation import RecommendationService
from app.services.data_collector import AkShareCollector
from app.utils.rate_limiter import limiter
from app.models.stock import Stock

router = APIRouter()


@router.get("/search")
async def search_stocks(
    request: Request,
    keyword: str = Query(default="", description="搜索关键词（代码或名称）"),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """搜索股票"""
    if not keyword:
        return {"success": True, "data": []}
    
    query = db.query(Stock).filter(
        (Stock.stock_code.contains(keyword)) | (Stock.name.contains(keyword))
    ).limit(limit).all()
    
    data = [{"stock_code": s.stock_code, "name": s.name, "market": s.market} for s in query]
    return {"success": True, "data": data}


@router.get("/recommend", response_model=RecommendResponse)
async def recommend_stocks(
    request: Request,
    market: str = Query(default="A", description="市场：A, US, HK"),
    limit: int = Query(default=20, ge=1, le=100, description="返回数量"),
    min_roe: float = Query(default=15.0, ge=0, le=100, description="最低ROE（%）"),
    max_debt_ratio: float = Query(default=50.0, ge=0, le=100, description="最高负债率（%）"),
    industry: Optional[str] = Query(default=None, description="行业筛选"),
    min_gross_margin: Optional[float] = Query(default=None, ge=0, le=100, description="最低毛利率（%）"),
    min_net_profit_growth: Optional[float] = Query(default=None, ge=-100, le=500, description="最低净利润增长率（%）"),
    sort_by: str = Query(default="score", description="排序字段：score, roe, pe, market_cap"),
    sector: Optional[str] = Query(default=None, description="板块筛选（用于美股：科技类/金融类/医药类/消费类）"),
    db: Session = Depends(get_db)
):
    """
    价值投资推荐

    - **market**: 市场类型（A=A股，US=美股，HK=港股）
    - **limit**: 返回数量（1-100）
    - **min_roe**: 最低净资产收益率（%）
    - **max_debt_ratio**: 最高资产负债率（%）
    - **industry**: 行业筛选（可选）
    - **min_gross_margin**: 最低毛利率（%）
    - **min_net_profit_growth**: 最低净利润增长率（%）
    - **sort_by**: 排序字段（score/roe/pe/market_cap）
    - **sector**: 板块筛选（美股）
    """
    try:
        # 创建推荐服务
        service = RecommendationService(db)

        # 获取推荐
        recommendations = service.recommend_stocks(
            market=market,
            limit=limit,
            min_roe=min_roe,
            max_debt_ratio=max_debt_ratio,
            industry=industry,
            min_gross_margin=min_gross_margin,
            min_net_profit_growth=min_net_profit_growth,
            sort_by=sort_by,
            sector=sector
        )

        # 构建响应
        data = [StockRecommend(**rec) for rec in recommendations]

        return RecommendResponse(
            success=True,
            data=data,
            meta={
                'total': len(data),
                'page': 1,
                'limit': limit,
                'filters': {
                    'market': market,
                    'min_roe': min_roe,
                    'max_debt_ratio': max_debt_ratio,
                    'industry': industry,
                    'min_gross_margin': min_gross_margin,
                    'min_net_profit_growth': min_net_profit_growth,
                    'sort_by': sort_by,
                    'sector': sector,
                }
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")


@router.post("/sync")
async def sync_stock_list(
    request: Request,
    background_tasks: BackgroundTasks,
    market: str = Query(default="A", description="市场"),
    db: Session = Depends(get_db)
):
    """同步股票列表（后台任务）"""
    def do_sync():
        sync_db = SessionLocal()
        try:
            service = RecommendationService(sync_db)
            service.sync_stock_list(market=market)
        finally:
            sync_db.close()
    
    background_tasks.add_task(do_sync)
    return {'success': True, 'message': '同步任务已提交', 'count': 0}


@router.get("/compare")
async def compare_stocks(
    request: Request,
    codes: str = Query(..., description="股票代码列表（逗号分隔，如 600519,000858,601318）"),
    db: Session = Depends(get_db)
):
    """
    股票对比分析
    
    - **codes**: 股票代码列表（逗号分隔）
    
    返回多只股票的财务指标横向对比数据
    """
    try:
        # 解析股票代码
        stock_codes = [code.strip() for code in codes.split(',') if code.strip()]
        
        if not stock_codes:
            raise HTTPException(status_code=400, detail="请提供至少一个股票代码")
        
        if len(stock_codes) > 10:
            raise HTTPException(status_code=400, detail="一次最多对比 10 只股票")
        
        # 获取股票信息
        stocks_data = []
        
        for stock_code in stock_codes:
            # 查询股票基本信息
            stock = db.query(Stock).filter(Stock.stock_code == stock_code).first()
            
            if not stock:
                continue
            
            # 从数据库获取最新财务数据（不实时调 AkShare）
            from app.models.financial import Financial
            latest_financial = db.query(Financial).filter(
                Financial.stock_code == stock_code
            ).order_by(Financial.id.desc()).first()
            
            stock_info = {
                'code': stock_code,
                'name': stock.name,
                'market': stock.market,
            }
            
            # 添加财务指标
            if latest_financial:
                stock_info.update({
                    'roe': getattr(latest_financial, 'roe', None),
                    'debt_ratio': getattr(latest_financial, 'debt_ratio', None),
                    'gross_margin': getattr(latest_financial, 'gross_margin', None),
                    'revenue': getattr(latest_financial, 'revenue', None),
                    'net_profit': getattr(latest_financial, 'net_profit', None),
                    'revenue_yoy': getattr(latest_financial, 'revenue_yoy', None),
                    'net_profit_yoy': getattr(latest_financial, 'net_profit_yoy', None),
                    'eps': getattr(latest_financial, 'eps', None),
                    'bvps': getattr(latest_financial, 'bvps', None),
                    'operating_cash_flow': getattr(latest_financial, 'operating_cash_flow', None),
                    'report_date': str(getattr(latest_financial, 'report_date', ''))
                })
            
            stocks_data.append(stock_info)
        
        return {
            'success': True,
            'stocks': stocks_data,
            'total': len(stocks_data),
            'metrics': [
                'roe',
                'debt_ratio',
                'gross_margin',
                'revenue',
                'net_profit',
                'revenue_yoy',
                'net_profit_yoy',
                'eps',
                'bvps',
                'operating_cash_flow'
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"对比失败: {str(e)}")
