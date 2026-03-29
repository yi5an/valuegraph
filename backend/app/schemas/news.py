"""
新闻相关的 Pydantic 模型
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class NewsItem(BaseModel):
    """新闻项"""
    id: Optional[int] = None
    title: str
    content: Optional[str] = None
    source: Optional[str] = None
    stock_code: Optional[str] = None
    keywords: Optional[str] = None
    published_at: Optional[str] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True  # Pydantic v2 语法（原 orm_mode）


class NewsResponse(BaseModel):
    """新闻响应"""
    success: bool = True
    data: List[NewsItem]
    meta: Optional[dict] = None


class SyncResponse(BaseModel):
    """同步响应"""
    success: bool
    message: str
    count: int
