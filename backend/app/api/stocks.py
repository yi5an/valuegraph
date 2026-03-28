"""
股票推荐 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from app.database import SessionLocal, get_db
from app.schemas.stock import RecommendResponse, StockRecommend
from app.services.recommendation import RecommendationService
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
    db: Session = Depends(get_db)
):
    """
    价值投资推荐
    
    - **market**: 市场类型（A=A股，US=美股，HK=港股）
    - **limit**: 返回数量（1-100）
    - **min_roe**: 最低净资产收益率（%）
    - **max_debt_ratio**: 最高资产负债率（%）
    - **industry**: 行业筛选（可选）
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
            industry=industry
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
