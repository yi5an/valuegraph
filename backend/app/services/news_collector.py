"""
新闻采集服务
使用 AkShare 采集东方财富和财联社的新闻
"""
import akshare as ak
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NewsCollector:
    """新闻采集器"""
    
    @staticmethod
    def fetch_stock_news(stock_code: str) -> List[Dict]:
        """
        获取东方财富个股新闻
        
        Args:
            stock_code: 股票代码（如 600519）
            
        Returns:
            新闻列表，每条新闻包含：
            - keywords: 关键词
            - title: 新闻标题
            - content: 新闻内容
            - published_at: 发布时间
            - source: 文章来源
            - url: 新闻链接
        """
        try:
            # 使用 akshare 获取个股新闻
            df = ak.stock_news_em(symbol=stock_code)
            
            if df.empty:
                logger.warning(f"未找到股票 {stock_code} 的新闻")
                return []
            
            # 转换为字典列表
            news_list = []
            for _, row in df.iterrows():
                news_item = {
                    'keywords': row.get('关键词', ''),
                    'title': row.get('新闻标题', ''),
                    'content': row.get('新闻内容', ''),
                    'published_at': row.get('发布时间', ''),
                    'source': row.get('文章来源', '东方财富'),
                    'url': row.get('新闻链接', ''),
                    'stock_code': stock_code
                }
                news_list.append(news_item)
            
            logger.info(f"成功获取 {stock_code} 的 {len(news_list)} 条新闻")
            return news_list
            
        except Exception as e:
            logger.error(f"获取股票 {stock_code} 新闻失败: {str(e)}")
            return []
    
    @staticmethod
    def fetch_hot_news() -> List[Dict]:
        """
        获取财联社热点新闻
        
        Returns:
            新闻列表，每条新闻包含：
            - keywords: 关键词（从 tag 提取）
            - title: 标题（从 summary 提取）
            - content: 内容
            - source: 来源
            - url: 新闻链接
        """
        try:
            # 使用 akshare 获取财联社热点新闻
            df = ak.stock_news_main_cx()
            
            if df.empty:
                logger.warning("未找到热点新闻")
                return []
            
            # 转换为字典列表
            news_list = []
            for _, row in df.iterrows():
                news_item = {
                    'keywords': row.get('tag', ''),
                    'title': row.get('summary', '')[:500] if row.get('summary', '') else '',  # 限制标题长度
                    'content': row.get('summary', ''),
                    'published_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # 财联社接口不返回时间，使用当前时间
                    'source': '财联社',
                    'url': row.get('url', ''),
                    'stock_code': None  # 热点新闻不关联特定股票
                }
                news_list.append(news_item)
            
            logger.info(f"成功获取 {len(news_list)} 条热点新闻")
            return news_list
            
        except Exception as e:
            logger.error(f"获取热点新闻失败: {str(e)}")
            return []
