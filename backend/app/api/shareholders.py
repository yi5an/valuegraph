"""
持股查询 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.shareholder import ShareholderResponse, ShareholderDetail
from app.services.data_collector import AkShareCollector
from app.utils.cache import cache
from app.utils.rate_limiter import limiter

router = APIRouter()


@router.get("/{stock_code}", response_model=ShareholderResponse)
async def get_shareholders(
    request: Request,
    stock_code: str,
    db: Session = Depends(get_db)
):
    """
    获取股东信息
    
    - **stock_code**: 股票代码（如 600519）
    """
    cache_key = f"shareholder:{stock_code}"
    
    # 尝试从缓存获取
    cached = cache.get(cache_key)
    if cached:
        return ShareholderResponse(success=True, data=ShareholderDetail(**cached))
    
    try:
        # 从 AkShare 获取股东信息
        data = AkShareCollector.get_shareholders(stock_code)
        
        if not data['top_10_shareholders']:
            return ShareholderResponse(
                success=False,
                data=None
            )
        
        # 写入缓存
        cache.set(cache_key, data)
        
        # 构建响应
        shareholder_detail = ShareholderDetail(**data)
        
        return ShareholderResponse(
            success=True,
            data=shareholder_detail
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
