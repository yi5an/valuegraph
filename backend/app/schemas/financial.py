"""
财报相关 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class FinancialTimeline(BaseModel):
    """财报时间线"""
    report_date: date = Field(..., description="报告期")
    report_type: str = Field(..., description="报告类型")
    revenue: Optional[float] = Field(None, description="营业收入（元）")
    revenue_yoy: Optional[float] = Field(None, description="营收同比增长率")
    net_profit: Optional[float] = Field(None, description="净利润（元）")
    net_profit_yoy: Optional[float] = Field(None, description="净利润同比增长率")
    roe: Optional[float] = Field(None, description="ROE")
    gross_margin: Optional[float] = Field(None, description="毛利率")
    debt_ratio: Optional[float] = Field(None, description="负债率")
    operating_cash_flow: Optional[float] = Field(None, description="经营现金流")
    investing_cash_flow: Optional[float] = Field(None, description="投资现金流")
    financing_cash_flow: Optional[float] = Field(None, description="筹资现金流")
    free_cash_flow: Optional[float] = Field(None, description="自由现金流")
    current_assets: Optional[float] = Field(None, description="流动资产")
    current_liabilities: Optional[float] = Field(None, description="流动负债")
    inventory: Optional[float] = Field(None, description="存货")
    accounts_receivable: Optional[float] = Field(None, description="应收账款")
    monetary_fund: Optional[float] = Field(None, description="货币资金")
    current_ratio: Optional[float] = Field(None, description="流动比率")
    quick_ratio: Optional[float] = Field(None, description="速动比率")
    roa: Optional[float] = Field(None, description="总资产收益率")
    eps: Optional[float] = Field(None, description="每股收益")
    bvps: Optional[float] = Field(None, description="每股净资产")
    
    class Config:
        from_attributes = True


class ChartData(BaseModel):
    """图表数据"""
    dates: List[str] = Field(..., description="日期列表")
    revenues: List[float] = Field(..., description="营收列表")
    net_profits: List[float] = Field(..., description="净利润列表")
    roes: List[float] = Field(..., description="ROE列表")


class HealthScore(BaseModel):
    """财务健康度评分"""
    overall: int = Field(..., description="综合评分")
    profitability: int = Field(..., description="盈利能力")
    solvency: int = Field(..., description="偿债能力")
    growth: int = Field(..., description="成长能力")
    operation: int = Field(..., description="运营能力")


class FinancialDetail(BaseModel):
    """财报详情"""
    stock_code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    timeline: List[FinancialTimeline] = Field(..., description="时间线")
    chart_data: Optional[ChartData] = Field(None, description="图表数据")
    health_score: Optional[HealthScore] = Field(None, description="健康度评分")


class FinancialResponse(BaseModel):
    """财报响应"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[FinancialDetail] = Field(None, description="财报数据")
