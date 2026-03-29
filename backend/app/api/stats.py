"""
数据统计 API
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.stock import Stock
from app.models.financial import Financial
from app.models.news import News
from app.services.knowledge_graph import KnowledgeGraphService
from app.utils.rate_limiter import limiter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/overview")
@limiter.limit("30/minute")
async def get_stats_overview(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    获取整体数据统计

    返回：
    - 股票总数
    - 有财务数据的股票数
    - 新闻总数
    - 图谱节点/关系数
    - 各市场分布
    """
    try:
        # 1. 股票总数
        total_stocks = db.query(func.count(Stock.stock_code)).scalar()

        # 2. 有财务数据的股票数
        stocks_with_financials = db.query(func.count(func.distinct(Financial.stock_code))).scalar()

        # 3. 新闻总数
        total_news = db.query(func.count(News.id)).scalar()

        # 4. 图谱节点/关系数
        kg = KnowledgeGraphService()
        try:
            # 获取节点数
            with kg.driver.session() as session:
                node_count_result = session.run("MATCH (n) RETURN count(n) as count")
                node_record = node_count_result.single()
                node_count = node_record['count'] if node_record else 0

                # 获取关系数
                relation_count_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                relation_record = relation_count_result.single()
                relation_count = relation_record['count'] if relation_record else 0
        except Exception as e:
            logger.warning(f"获取图谱统计失败: {e}")
            node_count = 0
            relation_count = 0
        finally:
            try:
                kg.close()
            except:
                pass

        # 5. 各市场分布
        market_distribution = db.query(
            Stock.market,
            func.count(Stock.stock_code).label('count')
        ).group_by(Stock.market).all()

        market_stats = {market: count for market, count in market_distribution}

        # 6. 行业分布（Top 10）
        industry_distribution = db.query(
            Stock.industry,
            func.count(Stock.stock_code).label('count')
        ).filter(
            Stock.industry.isnot(None)
        ).group_by(Stock.industry).order_by(
            func.count(Stock.stock_code).desc()
        ).limit(10).all()

        industry_stats = {industry: count for industry, count in industry_distribution}

        # 7. 最新财报日期
        latest_report = db.query(func.max(Financial.report_date)).scalar()

        return {
            "success": True,
            "data": {
                "total_stocks": total_stocks,
                "stocks_with_financials": stocks_with_financials,
                "total_news": total_news,
                "knowledge_graph": {
                    "nodes": node_count,
                    "relations": relation_count
                },
                "market_distribution": market_stats,
                "top_industries": industry_stats,
                "latest_report_date": str(latest_report) if latest_report else None
            }
        }

    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return {
            "success": False,
            "data": None,
            "error": f"获取统计信息失败: {str(e)}"
        }
