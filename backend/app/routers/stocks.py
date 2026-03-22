# stocks.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from ..services.stock_service import StockService

router = APIRouter(prefix="/api/stocks", tags=["stocks"])
stock_service = StockService()


@router.get("/recommend")
async def get_recommended_stocks(
    market: str = Query("a-share", description="市场类型：a-share 或 us-market"),
    top_n: int = Query(10, ge=1, le=50, description="返回数量 (1-50)"),
    min_roe: Optional[float] = Query(15.0, ge=0, le=100, description="最低 ROE (%)"),
    max_debt_ratio: Optional[float] = Query(50.0, ge=0, le=100, description="最高负债率 (%)")
):
    """获取价值投资推荐股票
    
    筛选标准：
    - ROE > min_roe (默认 15%)
    - 负债率 < max_debt_ratio (默认 50%)
    
    返回按评分排序的 Top N 股票
    """
    try:
        stocks = await stock_service.get_value_stocks(
            market, 
            top_n, 
            min_roe=min_roe, 
            max_debt_ratio=max_debt_ratio
        )
        
        return {
            "success": True,
            "market": market,
            "count": len(stocks),
            "filters": {
                "min_roe": min_roe,
                "max_debt_ratio": max_debt_ratio
            },
            "data": stocks
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取推荐股票失败: {str(e)}")


@router.get("/{stock_code}")
async def get_stock_detail(stock_code: str):
    """获取股票详情
    
    包含：
    - 财务数据（ROE、ROA、毛利率、负债率等）
    - 十大股东信息
    """
    try:
        detail = await stock_service.get_stock_detail(stock_code)
        
        return {
            "success": True,
            "data": detail
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取股票详情失败: {str(e)}")


@router.get("/health/check")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "stock-service"
    }
