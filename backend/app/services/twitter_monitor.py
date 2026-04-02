"""
Twitter/X 重要人物监控服务
通过 Nitter/RSSHub 抓取知名投资者和金融机构的推文，关联到持仓股票
"""
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field

import feedparser
import requests

logger = logging.getLogger(__name__)

PROXY = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
TIMEOUT = 15

NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.woodland.cafe",
]

RSSHUB_BASE = "https://rsshub.app/twitter/user"


@dataclass
class Influencer:
    handle: str
    name: str
    category: str
    keywords: List[str] = field(default_factory=list)
    # keywords 用于匹配 A 股，如 ["贵州茅台", "600519", "白酒", "腾讯", "00700"]
    last_fetch_status: str = "never"
    last_fetch_time: Optional[str] = None
    last_tweet_count: int = 0


INFLUENCER_LIST: List[Influencer] = [
    Influencer("WSJ", "Wall Street Journal", "财经媒体", [
        "美联储", "加息", "降息", "通胀", "利率", "recession",
        "美联储", "中国", "China", "trade",
    ]),
    Influencer("FT", "Financial Times", "财经媒体", [
        "央行", "美联储", "通胀", "China", "中国",
        "半导体", "芯片", "AI",
    ]),
    Influencer("federalreserve", "Federal Reserve", "央行/监管", [
        "利率", "加息", "降息", "通胀", "CPI", "employment",
        "monetary policy", "interest rate",
    ]),
    Influencer("ecb", "European Central Bank", "央行/监管", [
        "利率", "加息", "通胀", "欧元",
    ]),
    Influencer("elerianm", "Mohamed El-Erian", "财经大V", [
        "美联储", "通胀", "economy", "recession", "利率",
        "China", "emerging markets",
    ]),
    Influencer("jimcramer", "Jim Cramer", "财经大V", [
        "NVIDIA", "Apple", "Microsoft", "Google", "Amazon",
        "特斯拉", "AI", "chip",
    ]),
    Influencer("BlackRock", "BlackRock", "机构", [
        "ETF", "中国", "China", "emerging markets",
        "能源", "科技", "债券",
    ]),
    Influencer("Vanguard_Group", "Vanguard", "机构", [
        "ETF", "index fund", "退休", "养老金",
    ]),
    Influencer("GoldmanSachs", "Goldman Sachs", "机构", [
        "IPO", "中国", "China", "科技",
        "大宗商品", "commodity",
    ]),
    Influencer("JPMorgan", "JPMorgan", "机构", [
        "美联储", "利率", "China", "中国",
        "credit", "债券",
    ]),
]


def _fetch_rss(url: str) -> Optional[feedparser.FeedParserDict]:
    """通过代理获取 RSS feed"""
    try:
        resp = requests.get(url, proxies=PROXY, timeout=TIMEOUT, headers={
            "User-Agent": "Mozilla/5.0 (compatible; ValueGraph/1.0)"
        })
        if resp.status_code == 200:
            feed = feedparser.parse(resp.text)
            if feed.entries:
                return feed
    except Exception as e:
        logger.debug(f"RSS 获取失败 {url}: {e}")
    return None


def fetch_influencer_tweets(influencer: Influencer, limit: int = 10) -> List[Dict]:
    """抓取某个 influencer 的最新推文，自动 fallback"""
    handle = influencer.handle

    # 1. 尝试 Nitter 实例
    for instance in NITTER_INSTANCES:
        url = f"{instance}/{handle}/rss"
        feed = _fetch_rss(url)
        if feed:
            influencer.last_fetch_status = "nitter"
            return _parse_feed(feed, handle, influencer.name, limit)

    # 2. Fallback 到 RSSHub
    url = f"{RSSHUB_BASE}/{handle}"
    feed = _fetch_rss(url)
    if feed:
        influencer.last_fetch_status = "rsshub"
        return _parse_feed(feed, handle, influencer.name, limit)

    influencer.last_fetch_status = "failed"
    logger.warning(f"所有数据源均失败: @{handle}")
    return []


def _parse_feed(feed, handle: str, name: str, limit: int) -> List[Dict]:
    """解析 RSS feed entries 为统一格式"""
    results = []
    for entry in feed.entries[:limit]:
        # 清理 HTML
        content = entry.get("summary", "") or entry.get("description", "")
        clean = re.sub(r'<[^>]+>', '', content).strip()

        published = ""
        if entry.get("published_parsed"):
            try:
                published = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                published = entry.get("published", "")

        results.append({
            "title": entry.get("title", "")[:300],
            "content": clean[:2000],
            "url": entry.get("link", ""),
            "published_at": published,
            "author": f"@{handle} ({name})",
        })
    return results


def match_stocks(text: str, influencer: Influencer) -> Optional[Dict]:
    """
    用 influencer 的关键词匹配文本，返回关联信息。
    如果匹配到关键词，返回 {"matched_keywords": [...], "matched_text": "片段"}
    实际股票关联留给上层（数据库查询）处理。
    """
    text_lower = text.lower()
    matched = []
    for kw in influencer.keywords:
        if kw.lower() in text_lower:
            matched.append(kw)
    if matched:
        return {"matched_keywords": matched}
    return None


async def run_twitter_monitor(db_session) -> Dict:
    """
    执行一次完整的 Twitter 监控采集。

    Args:
        db_session: SQLAlchemy session

    Returns:
        {"total_fetched": int, "total_new": int, "details": [...]}
    """
    from app.models.news import News

    total_fetched = 0
    total_new = 0
    details = []

    for influencer in INFLUENCER_LIST:
        try:
            tweets = fetch_influencer_tweets(influencer, limit=10)
            influencer.last_fetch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            influencer.last_tweet_count = len(tweets)
            total_fetched += len(tweets)

            new_count = 0
            for tweet in tweets:
                # 去重
                existing = db_session.query(News).filter(
                    News.url == tweet["url"]
                ).first()
                if existing:
                    continue

                # 关键词匹配
                full_text = f"{tweet['title']} {tweet['content']}"
                match = match_stocks(full_text, influencer)

                # 简单情感判断（基于关键词数量和匹配）
                sentiment = "neutral"
                if match and match["matched_keywords"]:
                    sentiment = "positive"  # 有关联即标记，后续可调优

                news = News(
                    title=f"[{influencer.name}] {tweet['title']}",
                    content=tweet["content"],
                    source="twitter",
                    url=tweet["url"],
                    published_at=tweet["published_at"],
                    stock_code=None,  # 关键词匹配未直接映射到 stock_code
                    sentiment=sentiment,
                    event_type="investor_comment",
                    keywords=", ".join(match["matched_keywords"]) if match else "",
                )
                db_session.add(news)
                new_count += 1

            total_new += new_count
            details.append({
                "handle": influencer.handle,
                "name": influencer.name,
                "status": influencer.last_fetch_status,
                "fetched": len(tweets),
                "new": new_count,
            })

            import time
            time.sleep(1)  # 礼貌间隔

        except Exception as e:
            logger.error(f"监控 @{influencer.handle} 失败: {e}")
            details.append({
                "handle": influencer.handle,
                "name": influencer.name,
                "status": "error",
                "error": str(e),
            })

    db_session.commit()
    logger.info(f"🐦 Twitter 监控完成：抓取 {total_fetched}，新增 {total_new}")
    return {"total_fetched": total_fetched, "total_new": total_new, "details": details}


def get_influencer_status() -> List[Dict]:
    """获取所有监控目标的当前状态"""
    return [
        {
            "handle": inf.handle,
            "name": inf.name,
            "category": inf.category,
            "keywords": inf.keywords,
            "status": inf.last_fetch_status,
            "last_fetch_time": inf.last_fetch_time,
            "last_tweet_count": inf.last_tweet_count,
        }
        for inf in INFLUENCER_LIST
    ]
