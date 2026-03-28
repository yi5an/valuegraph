# API package
from fastapi import APIRouter
from app.api import stocks, financials, shareholders

api_router = APIRouter()

# 注册路由
api_router.include_router(stocks.router, prefix="/stocks", tags=["股票推荐"])
api_router.include_router(financials.router, prefix="/financials", tags=["财报分析"])
api_router.include_router(shareholders.router, prefix="/shareholders", tags=["持股查询"])
