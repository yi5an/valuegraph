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

    @staticmethod
    def fetch_xueqiu_news(stock_code: str = None, limit: int = 20) -> List[Dict]:
        """
        获取雪球新闻
        
        Args:
            stock_code: 股票代码（可选），如 600519
            limit: 返回条数
        """
        try:
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Origin": "https://xueqiu.com",
                "Referer": "https://xueqiu.com/",
            }
            # 先获取 cookie
            session = requests.Session()
            session.get("https://xueqiu.com/", headers=headers, timeout=10)
            
            if stock_code:
                # 获取个股新闻
                symbol = f"SH{stock_code}" if stock_code.startswith("6") else f"SZ{stock_code}"
                api_url = f"https://xueqiu.com/query/v1/symbol/search/status.json?symbol={symbol}&count={limit}&comment=0&page=1"
            else:
                # 获取热点
                api_url = f"https://xueqiu.com/query/v1/symbol/search/status.json?count={limit}&comment=0&page=1&source=all"
            
            resp = session.get(api_url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            
            news_list = []
            for item in data.get("list", [])[:limit]:
                text = item.get("text", "") or item.get("title", "")
                # 清理 HTML 标签
                import re
                clean_text = re.sub(r'<[^>]+>', '', text)
                news_list.append({
                    "title": item.get("title", "") or clean_text[:200],
                    "content": clean_text[:2000],
                    "source": "雪球",
                    "keywords": item.get("topic", "") or "",
                    "published_at": datetime.fromtimestamp(item.get("created_at", 0) / 1000).strftime('%Y-%m-%d %H:%M:%S') if item.get("created_at") else datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "url": f"https://xueqiu.com{item.get('target', '')}" if item.get("target", "").startswith("/") else item.get("target", ""),
                    "stock_code": stock_code,
                })
            
            logger.info(f"雪球新闻采集完成：{len(news_list)} 条")
            return news_list
        except Exception as e:
            logger.error(f"雪球新闻采集失败: {e}")
            return []

    @staticmethod
    def fetch_sina_news(stock_code: str = None, limit: int = 20) -> List[Dict]:
        """
        获取新浪财经新闻
        
        Args:
            stock_code: 股票代码（可选），如 sh600519
            limit: 返回条数
        """
        try:
            if stock_code:
                # 如果没有前缀，自动补全
                if not stock_code.startswith(("sh", "sz")):
                    full_code = f"sh{stock_code}" if stock_code.startswith("6") else f"sz{stock_code}"
                else:
                    full_code = stock_code
                df = ak.stock_news_sina(symbol=full_code)
            else:
                # 无特定股票时获取全球财经热点
                df = ak.stock_info_global_em()
            
            if df.empty:
                logger.warning("未找到新浪财经新闻")
                return []
            
            news_list = []
            col_map = {
                'stock_news_sina': {
                    'title': 'title',
                    'content': 'content',
                    'published_at': 'datetime',
                    'url': 'url',
                },
                'stock_info_global_em': {
                    'title': '标题',
                    'content': '内容',
                    'published_at': '发布时间',
                    'url': '链接',
                }
            }
            
            # 判断是哪个接口返回的
            if 'title' in df.columns:
                mapping = col_map['stock_news_sina']
            else:
                mapping = col_map['stock_info_global_em']
            
            for _, row in df.head(limit).iterrows():
                news_list.append({
                    "title": str(row.get(mapping['title'], '')),
                    "content": str(row.get(mapping['content'], ''))[:2000],
                    "source": "新浪财经",
                    "keywords": "",
                    "published_at": str(row.get(mapping['published_at'], '')),
                    "url": str(row.get(mapping['url'], '')),
                    "stock_code": stock_code,
                })
            
            logger.info(f"新浪财经新闻采集完成：{len(news_list)} 条")
            return news_list
        except Exception as e:
            logger.error(f"新浪财经新闻采集失败: {e}")
            return []

    @staticmethod
    def fetch_36kr_news(limit=30):
        """36氪科技新闻（RSS）"""
        import feedparser
        try:
            feed = feedparser.parse("https://36kr.com/feed")
            results = []
            for entry in feed.entries[:limit]:
                image_url = ""
                # Try media:thumbnail
                if entry.get("media_thumbnail"):
                    image_url = entry["media_thumbnail"][0].get("url", "")
                # Try enclosure
                if not image_url and entry.get("enclosures"):
                    for enc in entry["enclosures"]:
                        if enc.get("type", "").startswith("image"):
                            image_url = enc.get("href", enc.get("url", ""))
                            break
                results.append({
                    "title": entry.get("title", ""),
                    "content": entry.get("summary", ""),
                    "source": "36氪",
                    "keywords": "",
                    "published_at": entry.get("published", ""),
                    "url": entry.get("link", ""),
                    "image_url": image_url or None,
                })
            return results
        except Exception as e:
            logging.getLogger(__name__).error(f"36氪采集失败: {e}")
            return []

    @staticmethod
    async def fetch_og_image(url: str) -> str:
        """从 URL 抓取 og:image，3秒超时"""
        if not url:
            return None
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"}, limit=10240)
                text = resp.text[:10240]
                import re
                match = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', text)
                if not match:
                    match = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', text)
                return match.group(1).strip() if match else None
        except Exception:
            return None
