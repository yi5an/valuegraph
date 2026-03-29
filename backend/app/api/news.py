"""
新闻 API
"""
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from app.database import SessionLocal, get_db
from app.schemas.news import NewsItem, NewsResponse, SyncResponse, RelatedNewsItem, RelatedNewsResponse
from app.services.news_collector import NewsCollector
from app.services.sentiment_analyzer import SentimentAnalyzer
from app.services.knowledge_graph import KnowledgeGraphService
from app.services.entity_extractor import EntityExtractor
from app.models.news import News
from app.models.stock import Stock
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
    为新闻列表添加情感分析和事件类型（不阻塞事件循环）
    情感分析在后台线程执行，先返回数据，sentiment 为 None
    """
    import asyncio
    
    analyzer = SentimentAnalyzer()
    
    # 先设置默认值，立即返回
    for item in news_items:
        item.sentiment = {'sentiment': 'neutral', 'score': 0.5, 'keywords': []}
        item.event_type = 'general'
    
    # 后台异步执行情感分析（不阻塞响应）
    async def _bg_analyze():
        try:
            for item in news_items[:3]:
                try:
                    text = f"{item.title} {item.content or ''}"
                    sentiment = await analyzer.analyze(text)
                    item.sentiment = sentiment
                except Exception as e:
                    logger.warning(f"情感分析失败: {e}")
        finally:
            await analyzer.close()
    
    asyncio.create_task(_bg_analyze())
    return news_items
    
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


@router.get("/related/{stock_code}", response_model=RelatedNewsResponse)
async def get_related_news(
    request: Request,
    stock_code: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    基于知识图谱的关联新闻分析

    1. 查询 Neo4j 获取与该股票相关的所有实体
    2. 在 news 表中搜索包含这些实体名称的新闻
    3. 返回结果并标注关联路径

    - **stock_code**: 股票代码（如 600519）
    - **limit**: 返回数量（默认 20）
    """
    try:
        # 1. 查询股票名称
        stock = db.query(Stock).filter(Stock.stock_code == stock_code).first()
        if not stock:
            raise HTTPException(status_code=404, detail=f"股票 {stock_code} 不存在")

        company_name = stock.name

        # 2. 查询 Neo4j 获取关联实体
        kg = KnowledgeGraphService()
        try:
            graph_data = kg.get_graph_data(company_name, depth=2)

            # 提取关联实体名称
            related_names = [n['label'] for n in graph_data.get('nodes', []) if n['label'] != company_name]

            logger.info(f"股票 {stock_code} ({company_name}) 关联实体: {related_names}")

        except Exception as e:
            logger.warning(f"Neo4j 查询失败: {e}，将仅返回该股票相关新闻")
            related_names = []
        finally:
            kg.close()

        # 3. 在 news 表中搜索相关新闻
        # 构建查询条件：新闻标题或内容包含股票名称或关联实体名称
        news_items = []

        # 先搜索股票名称相关的新闻
        stock_news = db.query(News).filter(
            (News.title.contains(company_name)) | (News.content.contains(company_name)) | (News.stock_code == stock_code)
        ).order_by(News.created_at.desc()).limit(limit).all()

        # 为每条新闻添加关联实体信息
        for news in stock_news:
            # 找出这条新闻中出现的关联实体
            related_entities = []
            relation_types = []

            for entity_name in related_names:
                if entity_name in news.title or entity_name in (news.content or ''):
                    # 查找该实体的关系类型
                    for edge in graph_data.get('edges', []):
                        if (edge.get('source') == entity_name or edge.get('target') == entity_name):
                            rel_type = edge.get('type')
                            if rel_type and rel_type not in relation_types:
                                relation_types.append(rel_type)

                    related_entities.append({
                        'name': entity_name,
                        'type': 'related_company'
                    })

            # 构建响应
            news_item = RelatedNewsItem.from_orm(news)
            news_item.related_entities = related_entities if related_entities else None
            news_item.relation_types = relation_types if relation_types else None
            news_items.append(news_item)

        # 如果新闻不够，再搜索关联实体的新闻
        if len(news_items) < limit and related_names:
            # 搜索包含关联实体但不是该股票的新闻
            for entity_name in related_names[:5]:  # 限制搜索前5个实体
                entity_news = db.query(News).filter(
                    (News.title.contains(entity_name)) | (News.content.contains(entity_name))
                ).filter(
                    ~News.id.in_([n.id for n in stock_news])  # 排除已添加的新闻
                ).order_by(News.created_at.desc()).limit(5).all()

                for news in entity_news:
                    if len(news_items) >= limit:
                        break

                    # 找出关系类型
                    relation_types = []
                    for edge in graph_data.get('edges', []):
                        if edge.get('source') == entity_name or edge.get('target') == entity_name:
                            rel_type = edge.get('type')
                            if rel_type and rel_type not in relation_types:
                                relation_types.append(rel_type)

                    news_item = RelatedNewsItem.from_orm(news)
                    news_item.related_entities = [{'name': entity_name, 'type': 'related_company'}]
                    news_item.relation_types = relation_types
                    news_items.append(news_item)

        # 4. 添加情感分析
        news_items = await add_sentiment_to_news(news_items)

        return RelatedNewsResponse(
            success=True,
            data=news_items[:limit],
            meta={
                'stock_code': stock_code,
                'company_name': company_name,
                'related_entities_count': len(related_names),
                'related_entities': related_names[:10],  # 返回前10个关联实体
                'total_news': len(news_items)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取关联新闻失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取关联新闻失败: {str(e)}")


@router.post("/collect")
async def trigger_collection(background_tasks: BackgroundTasks):
    """手动触发一次完整采集流水线"""
    from app.services.news_scheduler import NewsScheduler
    
    async def run_collection():
        scheduler = NewsScheduler()
        await scheduler._sync_hot_news()
        await scheduler._sync_stock_news()
        await scheduler._process_new_entities()
    
    background_tasks.add_task(run_collection)
    return {"success": True, "message": "采集任务已启动"}


@router.get("/collect/status")
async def get_collect_status():
    """获取采集调度器状态"""
    from app.services.news_scheduler import NewsScheduler
    from app.main import news_scheduler
    
    try:
        # 获取调度器状态
        jobs = news_scheduler.scheduler.get_jobs()
        
        job_info = []
        for job in jobs:
            next_run = job.next_run_time
            job_info.append({
                'id': job.id,
                'name': job.name,
                'next_run': next_run.isoformat() if next_run else None,
                'trigger': str(job.trigger)
            })
        
        return {
            "success": True,
            "running": news_scheduler.scheduler.running,
            "jobs": job_info
        }
    except Exception as e:
        logger.error(f"获取调度器状态失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }
