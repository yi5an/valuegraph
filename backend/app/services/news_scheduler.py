from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging

logger = logging.getLogger(__name__)

class NewsScheduler:
    """新闻自动采集调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """启动定时任务"""
        # 每 10 分钟采集热点新闻
        self.scheduler.add_job(
            self._sync_hot_news,
            trigger=IntervalTrigger(minutes=10),
            id='sync_hot_news',
            name='同步热点新闻',
            replace_existing=True
        )
        
        # 每 30 分钟采集自选股新闻（高ROE股票）
        self.scheduler.add_job(
            self._sync_stock_news,
            trigger=IntervalTrigger(minutes=30),
            id='sync_stock_news',
            name='同步个股新闻',
            replace_existing=True
        )
        
        # 每 30 分钟对最新新闻做实体抽取和关系录入
        self.scheduler.add_job(
            self._process_new_entities,
            trigger=IntervalTrigger(minutes=30),
            id='process_entities',
            name='实体抽取与关系录入',
            replace_existing=True
        )
        
        # 每 1 小时采集 36氪科技新闻
        self.scheduler.add_job(
            self._sync_36kr_news,
            trigger=IntervalTrigger(hours=1),
            id='sync_36kr',
            name='同步36氪新闻',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("📰 新闻采集调度器已启动")
    
    async def _sync_hot_news(self):
        """采集热点新闻（财联社）"""
        logger.info("📰 开始采集热点新闻...")
        try:
            from app.services.news_collector import NewsCollector
            from app.database import SessionLocal
            from app.models.news import News
            from sqlalchemy import or_
            
            collector = NewsCollector()
            db = SessionLocal()
            try:
                news_list = collector.fetch_hot_news()
                if not news_list:
                    logger.info("无新热点新闻")
                    return
                
                new_count = 0
                for item in news_list:
                    # 去重：用 url 检查是否已存在
                    existing = db.query(News).filter(News.url == item.get('url')).first()
                    if existing:
                        continue
                    
                    news = News(
                        title=item.get('title', ''),
                        content=item.get('content', '') or item.get('summary', ''),
                        source=item.get('source', '财联社') or '财联社',
                        keywords=item.get('keywords', '') or item.get('tag', ''),
                        published_at=item.get('published_at', ''),
                        url=item.get('url', ''),
                        stock_code=None
                    )
                    db.add(news)
                    new_count += 1
                
                db.commit()
                logger.info(f"📰 热点新闻采集完成：新增 {new_count} 条，共 {len(news_list)} 条")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"热点新闻采集失败: {e}")
    
    async def _sync_stock_news(self):
        """采集高ROE股票的新闻"""
        logger.info("📰 开始采集个股新闻...")
        try:
            from app.services.news_collector import NewsCollector
            from app.database import SessionLocal
            from app.models.news import News
            from app.models.stock import Stock
            from app.models.financial import Financial
            import akshare as ak
            
            collector = NewsCollector()
            db = SessionLocal()
            try:
                # 获取有财务数据且ROE>15的股票（前20只）
                top_stocks = db.query(Financial.stock_code).filter(
                    Financial.roe > 15
                ).distinct().limit(20).all()
                
                if not top_stocks:
                    logger.info("无符合条件的股票")
                    return
                
                total_new = 0
                for (stock_code,) in top_stocks:
                    try:
                        news_list = collector.fetch_stock_news(stock_code)
                        if not news_list:
                            continue
                        
                        stock = db.query(Stock).filter(Stock.stock_code == stock_code).first()
                        for item in news_list:
                            existing = db.query(News).filter(News.url == item.get('url')).first()
                            if existing:
                                continue
                            news = News(
                                title=item.get('title', ''),
                                content=item.get('content', ''),
                                source=item.get('source', '东方财富'),
                                keywords=item.get('keywords', ''),
                                published_at=item.get('published_at', ''),
                                url=item.get('url', ''),
                                stock_code=stock_code
                            )
                            db.add(news)
                            total_new += 1
                        
                        db.commit()
                        import time
                        time.sleep(0.5)  # 请求间隔
                    except Exception as e:
                        logger.warning(f"采集 {stock_code} 新闻失败: {e}")
                        continue
                
                logger.info(f"📰 个股新闻采集完成：新增 {total_new} 条")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"个股新闻采集失败: {e}")
    
    async def _process_new_entities(self):
        """对未处理的新闻做实体抽取和关系录入"""
        logger.info("🔍 开始实体抽取与关系录入...")
        try:
            from app.database import SessionLocal
            from app.models.news import News
            from app.services.entity_extractor import EntityExtractor
            from app.services.knowledge_graph import KnowledgeGraphService
            
            db = SessionLocal()
            extractor = None
            try:
                # 获取最近未抽取的新闻（最近24小时，按 id 降序，限制100条）
                # 用简单标记：新闻表如果没有 processed 字段，就按 id > last_processed_id
                # 为简单起见，每次处理最新 50 条
                recent_news = db.query(News).order_by(News.id.desc()).limit(50).all()
                
                if not recent_news:
                    logger.info("无待处理新闻")
                    return
                
                extractor = EntityExtractor(db=db)
                total_entities = 0
                total_relations = 0
                processed = 0
                
                for news in recent_news:
                    try:
                        result = await extractor.extract_from_news(
                            title=news.title,
                            content=news.content,
                            stock_code=news.stock_code
                        )
                        total_entities += len(result['entities'])
                        total_relations += len(result['relations'])
                        processed += 1
                    except Exception as e:
                        logger.warning(f"处理新闻失败: {e}")
                
                logger.info(f"🔍 实体抽取完成：处理 {processed} 条，新增 {total_entities} 实体，{total_relations} 关系")
            finally:
                if extractor:
                    extractor.close()
                db.close()
        except Exception as e:
            logger.error(f"实体抽取失败: {e}")
    
    async def _sync_36kr_news(self):
        """采集36氪科技新闻"""
        logger.info("📰 开始采集36氪新闻...")
        try:
            from app.services.news_collector import NewsCollector
            from app.database import SessionLocal
            from app.models.news import News
            
            collector = NewsCollector()
            db = SessionLocal()
            try:
                news_list = collector.fetch_36kr_news(limit=30)
                if not news_list:
                    logger.info("无新36氪新闻")
                    return
                
                new_count = 0
                for item in news_list:
                    existing = db.query(News).filter(News.url == item.get('url')).first()
                    if existing:
                        continue
                    news = News(
                        title=item.get('title', ''),
                        content=item.get('content', ''),
                        source='36氪',
                        keywords=item.get('keywords', ''),
                        published_at=item.get('published_at', ''),
                        url=item.get('url', ''),
                        stock_code=None
                    )
                    db.add(news)
                    new_count += 1
                
                db.commit()
                logger.info(f"📰 36氪新闻采集完成：新增 {new_count} 条")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"36氪新闻采集失败: {e}")
    
    def shutdown(self):
        self.scheduler.shutdown()
