# models/financial.py
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass


class BalanceSheet(Base):
    """资产负债表"""
    __tablename__ = "balance_sheets"
    
    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String(20), nullable=False, index=True)
    end_date = Column(Date, nullable=False)
    total_assets = Column(Numeric(20, 2))
    total_liabilities = Column(Numeric(20, 2))
    total_equity = Column(Numeric(20, 2))
    current_assets = Column(Numeric(20, 2))
    current_liabilities = Column(Numeric(20, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('ts_code', 'end_date', name='balance_sheets_ts_code_end_date_unique'),
    )


class IncomeStatement(Base):
    """利润表"""
    __tablename__ = "income_statements"
    
    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String(20), nullable=False, index=True)
    end_date = Column(Date, nullable=False)
    revenue = Column(Numeric(20, 2))
    net_profit = Column(Numeric(20, 2))
    gross_profit = Column(Numeric(20, 2))
    operating_profit = Column(Numeric(20, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('ts_code', 'end_date', name='income_statements_ts_code_end_date_unique'),
    )


class CashFlowStatement(Base):
    """现金流量表"""
    __tablename__ = "cash_flow_statements"
    
    id = Column(Integer, primary_key=True, index=True)
    ts_code = Column(String(20), nullable=False, index=True)
    end_date = Column(Date, nullable=False)
    operating_cash_flow = Column(Numeric(20, 2))
    investing_cash_flow = Column(Numeric(20, 2))
    financing_cash_flow = Column(Numeric(20, 2))
    free_cash_flow = Column(Numeric(20, 2))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('ts_code', 'end_date', name='cash_flow_statements_ts_code_end_date_unique'),
    )
