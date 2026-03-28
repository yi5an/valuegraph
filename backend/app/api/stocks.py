"""
股票推荐 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.stock import RecommendResponse, StockRecommend
from app.services.recommendation import RecommendationService
from app.utils.rate_limiter import limiter

router = APIRouter()


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
    market: str = Query(default="A", description="市场"),
    db: Session = Depends(get_db)
):
    """
    同步股票列表（管理员接口）
    
    - **market**: 市场类型（A=A股）
    """
    try:
        service = RecommendationService(db)
        count = service.sync_stock_list(market=market)
        
        return {
            'success': True,
            'message': f'同步成功，新增 {count} 只股票',
            'count': count
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步失败: {str(e)}")
