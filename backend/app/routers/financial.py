# routers/financial.py
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging

from ..config import settings
from ..services.financial_statement import FinancialStatementService
from ..services.data_storage import FinancialDataStorage
from ..services.financial_calculator import FinancialCalculator
from ..services.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/financial", tags=["financial"])

# 依赖注入
def get_financial_service():
    return FinancialStatementService(settings.tushare_token)

def get_storage():
    return FinancialDataStorage(settings.database_url)


@router.get("/balance-sheet/{stock_code}")
async def get_balance_sheet(
    stock_code: str,
    start_date: str = None,
    end_date: str = None,
    service: FinancialStatementService = Depends(get_financial_service)
):
    """获取资产负债表"""
    try:
        data = await service.get_balance_sheet(stock_code, start_date, end_date)
        return {"success": True, "data": data, "count": len(data)}
    except Exception as e:
        logger.error(f"获取资产负债表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/income-statement/{stock_code}")
async def get_income_statement(
    stock_code: str,
    start_date: str = None,
    end_date: str = None,
    service: FinancialStatementService = Depends(get_financial_service)
):
    """获取利润表"""
    try:
        data = await service.get_income_statement(stock_code, start_date, end_date)
        return {"success": True, "data": data, "count": len(data)}
    except Exception as e:
        logger.error(f"获取利润表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cash-flow/{stock_code}")
async def get_cash_flow(
    stock_code: str,
    start_date: str = None,
    end_date: str = None,
    service: FinancialStatementService = Depends(get_financial_service)
):
    """获取现金流量表"""
    try:
        data = await service.get_cash_flow_statement(stock_code, start_date, end_date)
        return {"success": True, "data": data, "count": len(data)}
    except Exception as e:
        logger.error(f"获取现金流量表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/{stock_code}")
async def sync_financial_data(
    stock_code: str,
    service: FinancialStatementService = Depends(get_financial_service),
    storage: FinancialDataStorage = Depends(get_storage)
):
    """同步股票财务数据到数据库"""
    try:
        # 获取数据
        balance_data = await service.get_balance_sheet(stock_code)
        income_data = await service.get_income_statement(stock_code)
        cashflow_data = await service.get_cash_flow_statement(stock_code)
        
        # 存储数据
        balance_count = await storage.store_balance_sheet(balance_data)
        income_count = await storage.store_income_statement(income_data)
        cashflow_count = await storage.store_cash_flow_statement(cashflow_data)
        
        return {
            "success": True,
            "message": f"成功同步 {stock_code} 的财务数据",
            "balance_count": balance_count,
            "income_count": income_count,
            "cashflow_count": cashflow_count
        }
    except Exception as e:
        logger.error(f"同步财务数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/{stock_code}")
async def calculate_financial_metrics(
    stock_code: str,
    service: FinancialStatementService = Depends(get_financial_service)
):
    """计算财务指标"""
    try:
        # 获取最新数据
        balance_data = await service.get_balance_sheet(stock_code)
        income_data = await service.get_income_statement(stock_code)
        cashflow_data = await service.get_cash_flow_statement(stock_code)
        
        if not balance_data or not income_data or not cashflow_data:
            raise HTTPException(status_code=404, detail="财务数据不完整")
        
        # 计算指标
        metrics = FinancialCalculator.calculate_all_metrics(
            balance_data[0],
            income_data[0],
            cashflow_data[0]
        )
        
        return {
            "success": True,
            "stock_code": stock_code,
            "metrics": metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"计算财务指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/anomalies/{stock_code}")
async def detect_anomalies(
    stock_code: str,
    service: FinancialStatementService = Depends(get_financial_service)
):
    """检测财务数据异常"""
    try:
        # 获取历史数据
        balance_data = await service.get_balance_sheet(stock_code)
        income_data = await service.get_income_statement(stock_code)
        cashflow_data = await service.get_cash_flow_statement(stock_code)
        
        # 检测异常
        anomalies = AnomalyDetector.detect_all_anomalies(
            balance_data,
            income_data,
            cashflow_data
        )
        
        # 验证数据质量
        quality = AnomalyDetector.validate_data_quality(
            balance_data,
            ['ts_code', 'end_date', 'total_assets', 'total_equity']
        )
        
        return {
            "success": True,
            "stock_code": stock_code,
            "anomalies": anomalies,
            "quality": quality
        }
    except Exception as e:
        logger.error(f"检测异常失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{stock_code}")
async def get_historical_data(
    stock_code: str,
    years: int = 10,
    storage: FinancialDataStorage = Depends(get_storage)
):
    """获取历史财务数据"""
    try:
        balance = await storage.get_historical_balance_sheets(stock_code, years)
        income = await storage.get_historical_income_statements(stock_code, years)
        cashflow = await storage.get_historical_cash_flow_statements(stock_code, years)
        
        return {
            "success": True,
            "stock_code": stock_code,
            "years": years,
            "balance_sheets": balance,
            "income_statements": income,
            "cash_flow_statements": cashflow
        }
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
