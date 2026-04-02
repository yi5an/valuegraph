"""
新闻相关的 Pydantic 模型
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
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
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    sentiment: Optional[Dict[str, Any]] = None  # 情感分析结果
    event_type: Optional[str] = None  # 事件类型：M&A, earnings, personnel, regulation, litigation, general
    
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


class RelatedNewsItem(NewsItem):
    """关联新闻项（包含关联实体信息）"""
    related_entities: Optional[List[Dict[str, Any]]] = None  # 关联实体列表
    relation_types: Optional[List[str]] = None  # 关系类型列表


class RelatedNewsResponse(BaseModel):
    """关联新闻响应"""
    success: bool = True
    data: List[RelatedNewsItem]
    meta: Optional[Dict[str, Any]] = None
