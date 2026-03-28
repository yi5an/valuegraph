"""
股票基础信息模型
"""
from sqlalchemy import Column, String, Float, Date, DateTime, Integer
from sqlalchemy.sql import func
from app.database import Base


class Stock(Base):
    """股票基础信息表"""
    __tablename__ = "stocks"
    
    stock_code = Column(String(20), primary_key=True, comment="股票代码（如 600519）")
    market = Column(String(10), nullable=False, comment="市场：A, US, HK")
    name = Column(String(100), nullable=False, comment="股票名称")
    industry = Column(String(50), comment="所属行业")
    sector = Column(String(50), comment="所属板块")
    market_cap = Column(Float, comment="总市值（元）")
    listed_date = Column(Date, comment="上市日期")
    
    # 价值投资指标
    latest_roe = Column(Float, comment="最新 ROE")
    latest_pe = Column(Float, comment="最新市盈率")
    debt_ratio = Column(Float, comment="负债率")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<Stock {self.stock_code} - {self.name}>"
