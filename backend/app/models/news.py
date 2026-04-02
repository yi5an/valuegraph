"""
新闻数据模型
"""
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.sql import func
from app.database import Base


class News(Base):
    """新闻表"""
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="新闻ID")
    title = Column(String(500), nullable=False, comment="新闻标题")
    content = Column(String(5000), comment="新闻摘要")
    source = Column(String(100), comment="来源（东方财富/财联社）")
    stock_code = Column(String(20), comment="关联股票代码（可为空）")
    keywords = Column(String(200), comment="关键词")
    published_at = Column(String(50), comment="发布时间")
    url = Column(String(1000), comment="原文链接")
    image_url = Column(String(1000), comment="新闻图片URL")
    sentiment = Column(String(20), comment="情感标签（正面/负面/中性）")
    event_type = Column(String(50), comment="事件类型（general/policy/investor_comment等）")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    
    def __repr__(self):
        return f"<News {self.id} - {self.title}>"
