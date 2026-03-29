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
