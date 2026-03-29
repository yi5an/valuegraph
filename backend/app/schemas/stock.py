"""
股票相关 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime


class StockBase(BaseModel):
    """股票基础模型"""
    stock_code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    market: str = Field(..., description="市场")
    industry: Optional[str] = Field(None, description="所属行业")
    sector: Optional[str] = Field(None, description="所属板块")
    market_cap: Optional[float] = Field(None, description="总市值")


class StockRecommend(StockBase):
    """股票推荐模型"""
    latest_roe: Optional[float] = Field(None, description="最新ROE")
    latest_pe: Optional[float] = Field(None, description="最新市盈率")
    debt_ratio: Optional[float] = Field(None, description="负债率")
    gross_margin: Optional[float] = Field(None, description="毛利率")
    net_profit_growth: Optional[float] = Field(None, description="净利润增长率")
    recommendation_score: Optional[float] = Field(None, description="推荐得分")
    recommendation_reason: Optional[str] = Field(None, description="推荐理由")

    class Config:
        from_attributes = True


class RecommendRequest(BaseModel):
    """推荐请求参数"""
    market: str = Field(default="A", description="市场：A, US, HK")
    limit: int = Field(default=20, ge=1, le=100, description="返回数量")
    min_roe: float = Field(default=15.0, ge=0, le=100, description="最低ROE（%）")
    max_debt_ratio: float = Field(default=50.0, ge=0, le=100, description="最高负债率（%）")
    industry: Optional[str] = Field(None, description="行业筛选")


class RecommendResponse(BaseModel):
    """推荐响应"""
    success: bool = Field(..., description="请求是否成功")
    data: List[StockRecommend] = Field(..., description="推荐股票列表")
    meta: dict = Field(..., description="元数据")
