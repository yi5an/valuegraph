"""
财报分析 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.financial import FinancialResponse, FinancialDetail
from app.services.financial_analysis import FinancialService
from app.utils.rate_limiter import limiter

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
