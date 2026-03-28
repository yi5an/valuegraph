"""
财报数据模型
"""
from sqlalchemy import Column, String, Float, Date, DateTime, Integer, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from app.database import Base


class Financial(Base):
    """财报数据表"""
    __tablename__ = "financials"
    __table_args__ = (
        UniqueConstraint('stock_code', 'report_date', 'report_type', name='uix_financial_code_date_type'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(20), ForeignKey('stocks.stock_code'), nullable=False, comment="股票代码")
    report_date = Column(Date, nullable=False, comment="报告期")
    report_type = Column(String(20), nullable=False, comment="报告类型：annual, Q1, Q2, Q3")
    
    # 核心财务指标
    revenue = Column(Float, comment="营业收入（元）")
    net_profit = Column(Float, comment="净利润（元）")
    total_assets = Column(Float, comment="总资产（元）")
    total_liabilities = Column(Float, comment="总负债（元）")
    operating_cash_flow = Column(Float, comment="经营现金流（元）")
    
    # 计算指标
    roe = Column(Float, comment="ROE（净资产收益率）")
    gross_margin = Column(Float, comment="毛利率")
    debt_ratio = Column(Float, comment="负债率")
    eps = Column(Float, comment="每股收益")
    bvps = Column(Float, comment="每股净资产")
    
    # 增长率
    revenue_yoy = Column(Float, comment="营收同比增长率")
    net_profit_yoy = Column(Float, comment="净利润同比增长率")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<Financial {self.stock_code} - {self.report_date}>"
