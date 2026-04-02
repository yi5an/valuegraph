from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

class NewsScheduler:
    """新闻自动采集调度器"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """启动定时任务"""
        # 每 10 分钟采集热点新闻 + 紧急新闻检查
        self.scheduler.add_job(
            self._sync_hot_news,
            trigger=IntervalTrigger(minutes=10),
            id='sync_hot_news',
            name='同步热点新闻',
            replace_existing=True
        )
        
        # 每 10 分钟兜底检查紧急新闻（防漏）
        self.scheduler.add_job(
            self._push_urgent_news,
            trigger=IntervalTrigger(minutes=10),
            id='push_urgent_news',
            name='紧急新闻兜底检查',
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
        
        # 每 30 分钟对最新新闻做实体抽取、关系录入、情感分析、投资建议推送
        self.scheduler.add_job(
            self._process_and_analyze_events,
            trigger=IntervalTrigger(minutes=30),
            id='process_events',
            name='事件分析与推送',
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
        
        # 每 30 分钟采集雪球新闻
        self.scheduler.add_job(
            self._sync_xueqiu_news,
            trigger=IntervalTrigger(minutes=30),
            id='sync_xueqiu',
            name='同步雪球新闻',
            replace_existing=True
        )
        
        # 每 30 分钟采集 Twitter 监控
        self.scheduler.add_job(
            self._sync_twitter_news,
            trigger=IntervalTrigger(minutes=30),
            id='sync_twitter',
            name='同步Twitter监控',
            replace_existing=True
        )
        
        # 每 30 分钟采集新浪财经新闻
        self.scheduler.add_job(
            self._sync_sina_news,
            trigger=IntervalTrigger(minutes=30),
            id='sync_sina',
            name='同步新浪财经新闻',
            replace_existing=True
        )
        
        # 每天 02:00 增量同步财务数据（500只/次）
        self.scheduler.add_job(
            self._sync_financials,
            trigger=CronTrigger(hour=2, minute=0),
            id='sync_financials',
            name='增量同步财务数据',
            replace_existing=True
        )
        
        # 每周日 03:00 增量同步股东数据
        self.scheduler.add_job(
            self._sync_shareholders,
            trigger=CronTrigger(day_of_week='sun', hour=3, minute=0),
            id='sync_shareholders',
            name='增量同步股东数据',
            replace_existing=True
        )
        
        # 每 6 小时：关联新闻到股票 + 补全情感分析
        self.scheduler.add_job(
            self._associate_and_analyze,
            trigger=IntervalTrigger(hours=6),
            id='associate_sentiment',
            name='新闻关联与情感分析',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info("📰 新闻采集调度器已启动")

        # 启动时立即执行一次关联和情感分析
        self._associate_and_analyze()

    def _associate_and_analyze(self):
        """关联未关联的新闻到股票，并补全情感分析"""
        try:
            from app.database import SessionLocal
            from app.services.news_collector import associate_news_with_stocks, backfill_sentiment

            db = SessionLocal()
            try:
                associate_news_with_stocks(db)
                backfill_sentiment(db)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"新闻关联/情感分析失败: {e}")

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
                
                # 事件驱动：新采集的新闻立即检查是否紧急
                if new_count > 0:
                    await self._check_new_news_urgent(news_list)
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
    
    async def _process_and_analyze_events(self):
        """对最新新闻做实体抽取 + 关系构建 + 情感分析 + 投资建议 + 推送"""
        logger.info("🔍 开始事件分析流水线...")
        try:
            from app.database import SessionLocal
            from app.models.news import News
            from app.services.event_analyzer import EventAnalyzer

            db = SessionLocal()
            analyzer = None
            try:
                # 只处理最近30分钟内、尚未标记 event_type 的新闻
                from datetime import datetime, timedelta
                threshold = datetime.now() - timedelta(minutes=35)
                recent_news = db.query(News).filter(
                    News.event_type.is_(None)
                ).order_by(News.id.desc()).limit(30).all()

                if not recent_news:
                    logger.info("无待分析新闻")
                    return

                analyzer = EventAnalyzer(db)
                analyzed = 0
                pushed = 0

                for news in recent_news:
                    try:
                        report = await analyzer.analyze_and_push(news)
                        analyzed += 1
                        impact = report.get("impact", {})
                        if impact.get("level") in ("high_positive", "high_negative", "positive", "negative"):
                            pushed += 1
                    except Exception as e:
                        logger.warning(f"分析新闻失败(id={news.id}): {e}")

                logger.info(f"🔍 事件分析完成：分析 {analyzed} 条，推送 {pushed} 条")
            finally:
                if analyzer:
                    analyzer.close()
                db.close()
        except Exception as e:
            logger.error(f"事件分析流水线失败: {e}")
    
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
    
    async def _sync_xueqiu_news(self):
        """采集雪球新闻"""
        logger.info("📰 开始采集雪球新闻...")
        try:
            from app.services.news_collector import NewsCollector
            from app.database import SessionLocal
            from app.models.news import News
            
            collector = NewsCollector()
            db = SessionLocal()
            try:
                news_list = collector.fetch_xueqiu_news(limit=20)
                if not news_list:
                    logger.info("无新雪球新闻")
                    return
                
                new_count = 0
                for item in news_list:
                    existing = db.query(News).filter(News.url == item.get('url')).first()
                    if existing:
                        continue
                    news = News(
                        title=item.get('title', ''),
                        content=item.get('content', ''),
                        source='雪球',
                        keywords=item.get('keywords', ''),
                        published_at=item.get('published_at', ''),
                        url=item.get('url', ''),
                        stock_code=item.get('stock_code'),
                    )
                    db.add(news)
                    new_count += 1
                
                db.commit()
                logger.info(f"📰 雪球新闻采集完成：新增 {new_count} 条")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"雪球新闻采集失败: {e}")
    
    async def _sync_sina_news(self):
        """采集新浪财经新闻"""
        logger.info("📰 开始采集新浪财经新闻...")
        try:
            from app.services.news_collector import NewsCollector
            from app.database import SessionLocal
            from app.models.news import News
            
            collector = NewsCollector()
            db = SessionLocal()
            try:
                news_list = collector.fetch_sina_news(limit=20)
                if not news_list:
                    logger.info("无新新浪财经新闻")
                    return
                
                new_count = 0
                for item in news_list:
                    existing = db.query(News).filter(News.url == item.get('url')).first()
                    if existing:
                        continue
                    news = News(
                        title=item.get('title', ''),
                        content=item.get('content', ''),
                        source='新浪财经',
                        keywords=item.get('keywords', ''),
                        published_at=item.get('published_at', ''),
                        url=item.get('url', ''),
                        stock_code=item.get('stock_code'),
                    )
                    db.add(news)
                    new_count += 1
                
                db.commit()
                logger.info(f"📰 新浪财经新闻采集完成：新增 {new_count} 条")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"新浪财经新闻采集失败: {e}")
    
    async def _sync_twitter_news(self):
        """采集 Twitter 监控新闻"""
        logger.info("🐦 开始采集 Twitter 监控...")
        try:
            from app.services.twitter_monitor import run_twitter_monitor
            from app.database import SessionLocal
            
            db = SessionLocal()
            try:
                result = await run_twitter_monitor(db)
                logger.info(f"🐦 Twitter 监控完成：抓取 {result['total_fetched']}，新增 {result['total_new']}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Twitter 监控采集失败: {e}")

    async def _push_urgent_news(self):
        """事件驱动：检查并立即推送紧急新闻到 Telegram"""
        try:
            from app.services.notification import TelegramNotifier
            pushed = await TelegramNotifier.push_urgent_news()
            if pushed:
                logger.info("🚨 紧急新闻已推送")
        except Exception as e:
            logger.error(f"TG推送任务失败: {e}")

    async def _check_new_news_urgent(self, news_list: list):
        """事件驱动：对新采集的新闻立即检查紧急度并推送"""
        try:
            from app.services.notification import TelegramNotifier
            new_items = [{"title": n.get("title", ""), "content": n.get("content", ""), 
                         "source": n.get("source", ""), "stock_code": n.get("stock_code"),
                         "event_type": n.get("event_type")} for n in news_list]
            await TelegramNotifier.check_and_push(new_items)
        except Exception as e:
            logger.error(f"紧急新闻检查失败: {e}")

    async def _sync_financials(self):
        """每天增量同步财务数据"""
        logger.info("📊 开始增量同步财务数据...")
        try:
            from app.services.financial_crawler import FinancialCrawler
            crawler = FinancialCrawler()
            result = crawler.sync(limit=500, force=False, delay=0.2)
            logger.info(f"📊 财务数据同步完成: {result.get('status')}, new={result.get('new_rows', 0)}")
        except Exception as e:
            logger.error(f"财务数据同步失败: {e}")

    async def _sync_shareholders(self):
        """每周增量同步股东数据"""
        logger.info("👥 开始增量同步股东数据...")
        try:
            from app.services.shareholder_crawler import ShareholderCrawler
            crawler = ShareholderCrawler()
            result = crawler.sync(limit=200, force=False, delay=0.5)
            logger.info(f"👥 股东数据同步完成: {result.get('status')}, new={result.get('new_rows', 0)}")
        except Exception as e:
            logger.error(f"股东数据同步失败: {e}")



    def shutdown(self):
        self.scheduler.shutdown()
