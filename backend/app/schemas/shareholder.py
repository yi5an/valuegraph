"""
股东相关 Pydantic 模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class TopShareholder(BaseModel):
    """十大股东"""
    rank: int = Field(..., description="排名")
    holder_name: str = Field(..., description="股东名称")
    hold_amount: Optional[int] = Field(None, description="持股数量（股）")
    hold_ratio: Optional[float] = Field(None, description="持股比例（%）")
    holder_type: Optional[str] = Field(None, description="股东类型")
    change: Optional[str] = Field(None, description="变化情况")
    
    class Config:
        from_attributes = True


class InstitutionalHolder(BaseModel):
    """机构持仓"""
    institution_name: str = Field(..., description="机构名称")
    hold_amount: Optional[int] = Field(None, description="持股数量（股）")
    hold_ratio: Optional[float] = Field(None, description="持股比例（%）")
    institution_type: Optional[str] = Field(None, description="机构类型")
    change_ratio: Optional[float] = Field(None, description="变化比例（%）")
    
    class Config:
        from_attributes = True


class HolderDistribution(BaseModel):
    """持股分布"""
    institutional: float = Field(..., description="机构持股比例")
    individual: float = Field(..., description="个人持股比例")
    foreign: float = Field(..., description="外资持股比例")


class ShareholderDetail(BaseModel):
    """股东详情"""
    stock_code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    report_date: date = Field(..., description="报告期")
    top_10_shareholders: List[TopShareholder] = Field(..., description="十大股东")
    institutional_holders: List[InstitutionalHolder] = Field(..., description="机构持仓")
    holder_distribution: Optional[HolderDistribution] = Field(None, description="持股分布")


class ShareholderResponse(BaseModel):
    """股东响应"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[ShareholderDetail] = Field(None, description="股东数据")
