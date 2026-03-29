"""
财报分析 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.financial import FinancialResponse, FinancialDetail
from app.services.financial_analysis import FinancialService
from app.services.anomaly_detector import AnomalyDetector
from app.utils.rate_limiter import limiter
from app.models.stock import Stock
from app.models.financial import Financial

router = APIRouter()


@router.get("/{stock_code}", response_model=FinancialResponse)
async def get_financials(
    request: Request,
    stock_code: str,
    years: int = Query(default=5, ge=1, le=10, description="查询年数"),
    db: Session = Depends(get_db)
):
    """
    获取财报时间线
    
    - **stock_code**: 股票代码（如 600519）
    - **years**: 查询年数（1-10年）
    """
    try:
        # 创建财报服务
        service = FinancialService(db)
        
        # 获取财报数据
        data = service.get_timeline(stock_code=stock_code, years=years)
        
        if not data['timeline']:
            return FinancialResponse(
                success=False,
                data=None
            )
        
        # 构建响应
        financial_detail = FinancialDetail(**data)
        
        return FinancialResponse(
            success=True,
            data=financial_detail
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/{stock_code}/anomalies")
async def get_financial_anomalies(
    request: Request,
    stock_code: str,
    db: Session = Depends(get_db)
):
    """
    检测财务数据异常
    
    - **stock_code**: 股票代码（如 600519）
    
    返回异常检测结果，包括：
    - ROE 大幅下降（>30%）
    - 负债率飙升（>20%）
    - 营收增长但利润下降
    - 经营现金流连续为负
    """
    try:
        # 创建异常检测器
        detector = AnomalyDetector(db)
        
        # 执行检测
        result = detector.detect(stock_code=stock_code)
        
        return {
            'success': True,
            'data': result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


@router.get("/{stock_code}/peers")
async def get_peer_comparison(
    request: Request,
    stock_code: str,
    limit: int = Query(default=10, ge=1, le=50, description="返回同业数量"),
    db: Session = Depends(get_db)
):
    """
    同业对比分析

    - **stock_code**: 股票代码（如 600519）
    - **limit**: 返回同业数量（1-50）

    从 stocks 表找到同行业/同板块的股票，返回这些股票的最新财务指标对比
    """
    try:
        # 1. 查询目标股票
        target_stock = db.query(Stock).filter(Stock.stock_code == stock_code).first()

        if not target_stock:
            raise HTTPException(status_code=404, detail=f"股票 {stock_code} 不存在")

        # 2. 确定行业/板块（优先使用 sector，如果没有则用 industry）
        sector = target_stock.sector or target_stock.industry

        if not sector:
            return {
                "success": True,
                "data": {
                    "target": {
                        "stock_code": target_stock.stock_code,
                        "name": target_stock.name,
                        "market": target_stock.market,
                        "industry": target_stock.industry,
                        "sector": target_stock.sector
                    },
                    "peers": [],
                    "total": 0,
                    "message": "该股票未分类行业/板块，无法进行同业对比"
                }
            }

        # 3. 查询同行业/板块的股票（排除目标股票）
        peer_stocks = db.query(Stock).filter(
            (Stock.sector == sector) | (Stock.industry == sector),
            Stock.stock_code != stock_code
        ).limit(limit).all()

        # 4. 获取财务数据
        peers_data = []

        # 目标股票的财务数据
        target_financial = db.query(Financial).filter(
            Financial.stock_code == stock_code
        ).order_by(Financial.report_date.desc()).first()

        # 同业股票的财务数据
        for peer in peer_stocks:
            peer_financial = db.query(Financial).filter(
                Financial.stock_code == peer.stock_code
            ).order_by(Financial.report_date.desc()).first()

            peer_info = {
                "stock_code": peer.stock_code,
                "name": peer.name,
                "market": peer.market,
                "industry": peer.industry,
                "sector": peer.sector,
                "market_cap": peer.market_cap
            }

            if peer_financial:
                peer_info.update({
                    "roe": peer_financial.roe,
                    "debt_ratio": peer_financial.debt_ratio,
                    "gross_margin": peer_financial.gross_margin,
                    "revenue": peer_financial.revenue,
                    "net_profit": peer_financial.net_profit,
                    "revenue_yoy": peer_financial.revenue_yoy,
                    "net_profit_yoy": peer_financial.net_profit_yoy,
                    "eps": peer_financial.eps,
                    "bvps": peer_financial.bvps,
                    "operating_cash_flow": peer_financial.operating_cash_flow,
                    "report_date": str(peer_financial.report_date) if peer_financial.report_date else None
                })

            peers_data.append(peer_info)

        # 5. 构建目标股票信息
        target_info = {
            "stock_code": target_stock.stock_code,
            "name": target_stock.name,
            "market": target_stock.market,
            "industry": target_stock.industry,
            "sector": target_stock.sector,
            "market_cap": target_stock.market_cap
        }

        if target_financial:
            target_info.update({
                "roe": target_financial.roe,
                "debt_ratio": target_financial.debt_ratio,
                "gross_margin": target_financial.gross_margin,
                "revenue": target_financial.revenue,
                "net_profit": target_financial.net_profit,
                "revenue_yoy": target_financial.revenue_yoy,
                "net_profit_yoy": target_financial.net_profit_yoy,
                "eps": target_financial.eps,
                "bvps": target_financial.bvps,
                "operating_cash_flow": target_financial.operating_cash_flow,
                "report_date": str(target_financial.report_date) if target_financial.report_date else None
            })

        return {
            "success": True,
            "data": {
                "target": target_info,
                "peers": peers_data,
                "total": len(peers_data),
                "sector": sector
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同业对比失败: {str(e)}")
