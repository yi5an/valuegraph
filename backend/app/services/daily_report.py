"""
每日投资早报生成服务
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DailyReport:
    """每日投资早报"""

    def __init__(self, db: Session):
        self.db = db

    def generate(self) -> Dict[str, Any]:
        """生成结构化早报数据"""
        now = datetime.now()

        report = {
            "date": now.strftime("%Y-%m-%d"),
            "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "market_overview": self._market_overview(),
            "watchlist": self._watchlist(),
            "policy_news": self._policy_news(),
            "data_summary": self._data_summary(),
        }

        return report

    def _market_overview(self) -> Dict[str, Any]:
        """市场概览"""
        from app.models.stock import Stock

        # 统计涨跌数量（基于 latest_roe 等字段无法判断涨跌，用 market_cap 变化替代）
        # 由于 stocks 表没有涨跌字段，尝试用 AkShare
        indices = {}
        try:
            import akshare as ak
            # 上证指数
            sh = ak.stock_zh_index_spot_em()
            if sh is not None and not sh.empty:
                for _, row in sh.iterrows():
                    name = str(row.get("名称", ""))
                    if "上证" in name or "深证" in name or "创业板" in name or "科创" in name:
                        indices[name] = {
                            "price": float(row.get("最新价", 0)),
                            "change_pct": float(row.get("涨跌幅", 0)),
                        }
                        if len(indices) >= 4:
                            break
        except Exception as e:
            logger.warning(f"AkShare 指数数据获取失败: {e}")

        total_stocks = self.db.query(func.count(Stock.stock_code)).scalar() or 0

        return {
            "total_stocks": total_stocks,
            "indices": indices,
            "note": "涨跌统计需接入实时行情数据" if not indices else "",
        }

    def _watchlist(self) -> Dict[str, Any]:
        """持仓关注 - 负面新闻 + 增减持变动"""
        from app.models.news import News
        from app.models.financial import Financial
        from app.models.shareholder import Shareholder
        from app.models.stock import Stock

        twenty_four_h_ago = datetime.now() - timedelta(hours=24)

        # 有财务数据的股票代码
        tracked_codes = {
            code for (code,) in self.db.query(distinct(Financial.stock_code)).all()
        }

        # 负面新闻
        negative_news = []
        if tracked_codes:
            neg_items = (
                self.db.query(News)
                .filter(
                    News.sentiment == "负面",
                    News.stock_code.isnot(None),
                    News.stock_code.in_(tracked_codes),
                    News.created_at >= twenty_four_h_ago,
                )
                .order_by(News.created_at.desc())
                .limit(10)
                .all()
            )
            for n in neg_items:
                stock = self.db.query(Stock).filter(Stock.stock_code == n.stock_code).first()
                negative_news.append({
                    "title": n.title,
                    "stock_code": n.stock_code,
                    "stock_name": stock.name if stock else "",
                    "source": n.source,
                    "published_at": n.published_at,
                })

        # 近期增减持变动
        changes = (
            self.db.query(Shareholder, Stock.name)
            .join(Stock, Shareholder.stock_code == Stock.stock_code)
            .filter(
                Shareholder.change.isnot(None),
                Shareholder.change != "不变",
                Shareholder.created_at >= twenty_four_h_ago,
            )
            .order_by(Shareholder.created_at.desc())
            .limit(10)
            .all()
        )
        holder_changes = []
        for sh, name in changes:
            holder_changes.append({
                "stock_code": sh.stock_code,
                "stock_name": name or sh.stock_code,
                "holder_name": sh.holder_name,
                "change": sh.change,
                "hold_ratio": sh.hold_ratio,
            })

        return {
            "negative_news": negative_news,
            "holder_changes": holder_changes,
        }

    def _policy_news(self) -> list:
        """政策要闻 - 最近 24 小时的 policy 类型新闻"""
        from app.models.news import News
        from app.services.entity_extractor import POLICY_KEYWORDS

        twenty_four_h_ago = datetime.now() - timedelta(hours=24)

        all_news = (
            self.db.query(News)
            .filter(News.created_at >= twenty_four_h_ago)
            .order_by(News.created_at.desc())
            .limit(100)
            .all()
        )

        policy_items = []
        for n in all_news:
            title = n.title or ""
            content = n.content or ""
            text = title + content
            if any(kw in text for kw in POLICY_KEYWORDS):
                policy_items.append({
                    "title": n.title,
                    "source": n.source,
                    "published_at": n.published_at,
                    "stock_code": n.stock_code,
                })
            if len(policy_items) >= 10:
                break

        return policy_items

    def _data_summary(self) -> Dict[str, Any]:
        """数据摘要"""
        from app.models.stock import Stock
        from app.models.financial import Financial
        from app.models.news import News
        from app.models.shareholder import Shareholder

        return {
            "total_stocks": self.db.query(func.count(Stock.stock_code)).scalar() or 0,
            "stocks_with_financials": self.db.query(func.count(distinct(Financial.stock_code))).scalar() or 0,
            "total_news": self.db.query(func.count(News.id)).scalar() or 0,
            "total_shareholders": self.db.query(func.count(Shareholder.id)).scalar() or 0,
            "news_last_24h": self.db.query(func.count(News.id)).filter(
                News.created_at >= datetime.now() - timedelta(hours=24)
            ).scalar() or 0,
        }

    def format_text(self) -> str:
        """纯文本格式（适合 TG 推送）"""
        r = self.generate()
        lines = []
        lines.append(f"📊 每日投资早报 | {r['date']}")
        lines.append("=" * 30)

        # 市场概览
        lines.append(f"\n📈 市场概览")
        lines.append(f"  覆盖股票: {r['market_overview']['total_stocks']} 只")
        for name, info in r['market_overview'].get('indices', {}).items():
            sign = "+" if info['change_pct'] >= 0 else ""
            lines.append(f"  {name}: {info['price']:.2f} ({sign}{info['change_pct']:.2f}%)")

        # 持仓关注
        lines.append(f"\n⚠️ 持仓关注")
        neg = r['watchlist']['negative_news']
        if neg:
            lines.append(f"  负面新闻 ({len(neg)} 条):")
            for n in neg[:5]:
                lines.append(f"  • [{n['stock_name']}] {n['title']}")
        else:
            lines.append("  无负面新闻")

        changes = r['watchlist']['holder_changes']
        if changes:
            lines.append(f"\n  股东增减持 ({len(changes)} 条):")
            for c in changes[:5]:
                lines.append(f"  • [{c['stock_name']}] {c['holder_name']} {c['change']}")

        # 政策要闻
        lines.append(f"\n🏛 政策要闻")
        policies = r['policy_news']
        if policies:
            for p in policies[:5]:
                lines.append(f"  • {p['title']}")
        else:
            lines.append("  暂无重要政策新闻")

        # 数据摘要
        lines.append(f"\n📋 数据摘要")
        s = r['data_summary']
        lines.append(f"  股票: {s['total_stocks']} | 财务覆盖: {s['stocks_with_financials']}")
        lines.append(f"  新闻: {s['total_news']} | 近24h: {s['news_last_24h']}")
        lines.append(f"  股东记录: {s['total_shareholders']}")

        lines.append(f"\n⏰ 生成时间: {r['generated_at']}")
        return "\n".join(lines)

    def format_html(self) -> str:
        """HTML 格式"""
        r = self.generate()
        parts = []

        parts.append(f"<b>📊 每日投资早报</b> | {r['date']}")

        # 市场概览
        parts.append(f"\n<b>📈 市场概览</b>")
        parts.append(f"覆盖股票: {r['market_overview']['total_stocks']} 只")
        for name, info in r['market_overview'].get('indices', {}).items():
            sign = "+" if info['change_pct'] >= 0 else ""
            color = "🟢" if info['change_pct'] >= 0 else "🔴"
            parts.append(f"  {color} {name}: {info['price']:.2f} ({sign}{info['change_pct']:.2f}%)")

        # 持仓关注
        parts.append(f"\n<b>⚠️ 持仓关注</b>")
        neg = r['watchlist']['negative_news']
        if neg:
            parts.append(f"负面新闻 ({len(neg)} 条):")
            for n in neg[:5]:
                parts.append(f"  • <b>[{n['stock_name']}]</b> {n['title']}")
        else:
            parts.append("  无负面新闻")

        changes = r['watchlist']['holder_changes']
        if changes:
            parts.append(f"\n股东增减持 ({len(changes)} 条):")
            for c in changes[:5]:
                parts.append(f"  • <b>[{c['stock_name']}]</b> {c['holder_name']} {c['change']}")

        # 政策要闻
        parts.append(f"\n<b>🏛 政策要闻</b>")
        policies = r['policy_news']
        if policies:
            for p in policies[:5]:
                parts.append(f"  • {p['title']}")
        else:
            parts.append("  暂无重要政策新闻")

        # 数据摘要
        parts.append(f"\n<b>📋 数据摘要</b>")
        s = r['data_summary']
        parts.append(f"股票: {s['total_stocks']} | 财务覆盖: {s['stocks_with_financials']}")
        parts.append(f"新闻: {s['total_news']} | 近24h: {s['news_last_24h']}")
        parts.append(f"股东记录: {s['total_shareholders']}")

        parts.append(f"\n⏰ {r['generated_at']}")
        return "\n".join(parts)
