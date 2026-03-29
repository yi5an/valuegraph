"""
新闻 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from app.database import SessionLocal, get_db
from app.schemas.news import NewsItem, NewsResponse, SyncResponse
from app.services.news_collector import NewsCollector
from app.services.sentiment_analyzer import SentimentAnalyzer
from app.models.news import News
from app.utils.rate_limiter import limiter
from datetime import datetime, timedelta
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)


def get_cached_news(db: Session, stock_code: Optional[str] = None, hours: int = 24) -> list:
    """
    获取缓存的新闻
    
    Args:
        db: 数据库会话
        stock_code: 股票代码（为空则获取热点新闻）
        hours: 缓存有效期（小时）
    
    Returns:
        新闻列表
    """
    # 计算缓存截止时间
    cache_threshold = datetime.now() - timedelta(hours=hours)
    
    # 查询缓存
    query = db.query(News)
    
    if stock_code:
        # 个股新闻
        query = query.filter(News.stock_code == stock_code)
    else:
        # 热点新闻（stock_code 为空）
        query = query.filter(News.stock_code.is_(None))
    
    # 只返回缓存有效期内的新闻
    query = query.filter(News.created_at >= cache_threshold)
    query = query.order_by(News.created_at.desc()).limit(50)
    
    return query.all()


def save_news_to_db(db: Session, news_list: list):
    """
    保存新闻到数据库
    
    Args:
        db: 数据库会话
        news_list: 新闻列表（字典格式）
    """
    for news_data in news_list:
        # 检查是否已存在（通过 URL 去重）
        existing = db.query(News).filter(News.url == news_data.get('url')).first()
        
        if not existing:
            news = News(
                title=news_data.get('title', ''),
                content=news_data.get('content', ''),
                source=news_data.get('source', ''),
                stock_code=news_data.get('stock_code'),
                keywords=news_data.get('keywords', ''),
                published_at=news_data.get('published_at', ''),
                url=news_data.get('url', '')
            )
            db.add(news)
    
    db.commit()


async def add_sentiment_to_news(news_items: list) -> list:
    """
    为新闻列表添加情感分析
    
    Args:
        news_items: 新闻项列表
        
    Returns:
        添加了 sentiment 字段的新闻列表
    """
    analyzer = SentimentAnalyzer()
    
    try:
        # 批量分析情感
        for item in news_items:
            try:
                # 合并标题和内容进行分析
                text = f"{item.title} {item.content or ''}"
                sentiment = await analyzer.analyze(text)
                
                # 将 sentiment 添加到 NewsItem
                # 由于 NewsItem 是 Pydantic 模型，需要转换为字典再添加
                if hasattr(item, '__dict__'):
                    item.__dict__['sentiment'] = sentiment
                else:
                    # 直接设置属性（Pydantic 模型）
                    item.sentiment = sentiment
                    
            except Exception as e:
                logger.warning(f"情感分析失败: {e}")
                # 设置默认值
                item.sentiment = {
                    'sentiment': 'neutral',
                    'score': 0.5,
                    'keywords': []
                }
    finally:
        await analyzer.close()
    
    return news_items


@router.get("/stock/{stock_code}", response_model=NewsResponse)
async def get_stock_news(
    request: Request,
    stock_code: str,
    db: Session = Depends(get_db)
):
    """
    获取个股新闻（带情感分析）
    
    - 先查询数据库缓存（24小时内）
    - 如果没有缓存，实时抓取东方财富新闻
    - 每条新闻包含情感分析结果
    """
    try:
        # 尝试从缓存获取
        cached_news = get_cached_news(db, stock_code=stock_code)
        
        if cached_news:
            # 有缓存，直接返回
            data = [NewsItem.from_orm(news) for news in cached_news]
            # 添加情感分析
            data = await add_sentiment_to_news(data)
            return NewsResponse(
                success=True,
                data=data,
                meta={'source': 'cache', 'count': len(data)}
            )
        
        # 无缓存，实时抓取
        logger.info(f"未找到 {stock_code} 的缓存新闻，开始实时抓取")
        news_list = NewsCollector.fetch_stock_news(stock_code)
        
        if not news_list:
            return NewsResponse(
                success=True,
                data=[],
                meta={'source': 'realtime', 'count': 0, 'message': '未找到相关新闻'}
            )
        
        # 保存到数据库
        save_news_to_db(db, news_list)
        
        # 返回结果
        data = [NewsItem(**news) for news in news_list]
        # 添加情感分析
        data = await add_sentiment_to_news(data)
        return NewsResponse(
            success=True,
            data=data,
            meta={'source': 'realtime', 'count': len(data)}
        )
        
    except Exception as e:
        logger.error(f"获取股票 {stock_code} 新闻失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取新闻失败: {str(e)}")


@router.get("/hot", response_model=NewsResponse)
async def get_hot_news(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    获取热点新闻（带情感分析）
    
    - 先查询数据库缓存（24小时内）
    - 如果没有缓存，实时抓取财联社新闻
    - 每条新闻包含情感分析结果
    """
    try:
        # 尝试从缓存获取
        cached_news = get_cached_news(db, stock_code=None)
        
        if cached_news:
            # 有缓存，直接返回
            data = [NewsItem.from_orm(news) for news in cached_news]
            # 添加情感分析
            data = await add_sentiment_to_news(data)
            return NewsResponse(
                success=True,
                data=data,
                meta={'source': 'cache', 'count': len(data)}
            )
        
        # 无缓存，实时抓取
        logger.info("未找到热点新闻缓存，开始实时抓取")
        news_list = NewsCollector.fetch_hot_news()
        
        if not news_list:
            return NewsResponse(
                success=True,
                data=[],
                meta={'source': 'realtime', 'count': 0, 'message': '未找到热点新闻'}
            )
        
        # 保存到数据库
        save_news_to_db(db, news_list)
        
        # 返回结果
        data = [NewsItem(**news) for news in news_list]
        # 添加情感分析
        data = await add_sentiment_to_news(data)
        return NewsResponse(
            success=True,
            data=data,
            meta={'source': 'realtime', 'count': len(data)}
        )
        
    except Exception as e:
        logger.error(f"获取热点新闻失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取热点新闻失败: {str(e)}")


@router.post("/sync", response_model=SyncResponse)
async def sync_news(
    request: Request,
    background_tasks: BackgroundTasks,
    stock_code: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    手动触发新闻同步
    
    - **stock_code**: 股票代码（为空则同步热点新闻）
    """
    def do_sync():
        sync_db = SessionLocal()
        try:
            if stock_code:
                # 同步个股新闻
                news_list = NewsCollector.fetch_stock_news(stock_code)
            else:
                # 同步热点新闻
                news_list = NewsCollector.fetch_hot_news()
            
            if news_list:
                save_news_to_db(sync_db, news_list)
                logger.info(f"同步完成：{len(news_list)} 条新闻")
        
        except Exception as e:
            logger.error(f"同步新闻失败: {str(e)}")
        
        finally:
            sync_db.close()
    
    # 添加后台任务
    background_tasks.add_task(do_sync)
    
    return SyncResponse(
        success=True,
        message='同步任务已提交',
        count=0
    )
