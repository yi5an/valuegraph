"""
股东信息模型
"""
from sqlalchemy import Column, String, Float, Date, DateTime, BigInteger, Integer
from sqlalchemy.sql import func
from sqlalchemy import ForeignKey
from app.database import Base


class Shareholder(Base):
    """十大股东表"""
    __tablename__ = "shareholders"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(20), ForeignKey('stocks.stock_code'), nullable=False, comment="股票代码")
    report_date = Column(Date, nullable=False, comment="报告期")
    
    rank = Column(Integer, nullable=False, comment="排名")
    holder_name = Column(String(200), nullable=False, comment="股东名称")
    hold_amount = Column(BigInteger, comment="持股数量（股）")
    hold_ratio = Column(Float, comment="持股比例（%）")
    holder_type = Column(String(50), comment="股东类型")
    change = Column(String(20), comment="变化情况（新增/不变/减持）")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<Shareholder {self.stock_code} - {self.holder_name}>"


class InstitutionalHolder(Base):
    """机构持仓表"""
    __tablename__ = "institutional_holders"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(20), ForeignKey('stocks.stock_code'), nullable=False, comment="股票代码")
    report_date = Column(Date, nullable=False, comment="报告期")
    
    institution_name = Column(String(200), nullable=False, comment="机构名称")
    institution_type = Column(String(50), comment="机构类型（基金/券商/外资等）")
    hold_amount = Column(BigInteger, comment="持股数量（股）")
    hold_ratio = Column(Float, comment="持股比例（%）")
    change_ratio = Column(Float, comment="变化比例（%）")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<InstitutionalHolder {self.stock_code} - {self.institution_name}>"
