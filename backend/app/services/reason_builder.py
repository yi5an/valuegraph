"""
推荐理由生成器 - 多维度丰富理由

生成包含基本面、动态信号、相关新闻、投资逻辑的推荐理由
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def build_rich_reason(
    stock_code: str,
    name: str,
    industry: str,
    grade: str,
    score_detail: Dict,
    financial_metrics: Dict,
    spot_info: Optional[Dict] = None,
    recent_news: Optional[List] = None,
) -> Dict:
    """
    构建丰富的推荐理由

    Args:
        stock_code: 股票代码
        name: 股票名称
        industry: 行业
        grade: 评级
        score_detail: 五维度评分明细
        financial_metrics: {roe, gross_margin, debt_ratio, revenue_yoy, net_profit_yoy, operating_cash_flow, eps}
        spot_info: 实时行情数据（来自 dynamic_scoring）
        recent_news: 近期新闻列表 [{title, source, published_at, sentiment, event_type}]

    Returns:
        {"recommendation_reason": str, "reason_sections": {...}}
    """
    sections = {}

    # 1. 标题行
    header = f"[{grade}] {name}({stock_code})"
    if industry:
        header += f" · {industry}"

    # 2. 基本面
    fundamentals = _build_fundamentals(financial_metrics)
    sections["fundamentals"] = fundamentals

    # 3. 动态信号
    market_signals = _build_market_signals(spot_info)
    sections["market_signals"] = market_signals

    # 4. 相关新闻
    news_section = _build_news_section(recent_news)
    if news_section:
        sections["related_news"] = news_section

    # 5. 投资逻辑
    investment_logic = _build_investment_logic(
        score_detail, financial_metrics, spot_info, recent_news
    )
    sections["investment_logic"] = investment_logic

    # 组装完整文本
    lines = [header]
    if fundamentals:
        lines.append(f"📊 基本面: {fundamentals}")
    if market_signals:
        lines.append(f"📈 动态信号: {market_signals}")
    if news_section:
        lines.append(f"📰 相关新闻: {news_section}")
    lines.append(f"💡 投资逻辑: {investment_logic}")

    full_text = "\n".join(lines)
    return {
        "recommendation_reason": full_text,
        "reason_sections": sections,
    }


def _build_fundamentals(m: Dict) -> str:
    """基本面摘要：top 2-3 指标"""
    parts = []

    roe = m.get("roe")
    if roe is not None and roe > 0:
        if roe >= 25:
            parts.append(f"ROE {roe:.1f}% 行业领先")
        elif roe >= 15:
            parts.append(f"ROE {roe:.1f}%")

    gm = m.get("gross_margin")
    if gm is not None and gm > 0:
        if gm >= 60:
            parts.append(f"毛利率 {gm:.1f}%")
        else:
            parts.append(f"毛利率 {gm:.1f}%")

    dr = m.get("debt_ratio")
    if dr is not None:
        if dr <= 30:
            parts.append(f"负债率仅 {dr:.1f}%")
        elif dr <= 50:
            parts.append(f"负债率 {dr:.1f}%")

    rev = m.get("revenue_yoy")
    if rev is not None and rev > 10:
        parts.append(f"营收增 {rev:.1f}%")

    np = m.get("net_profit_yoy")
    if np is not None and np > 10:
        parts.append(f"净利增 {np:.1f}%")

    ocf = m.get("operating_cash_flow")
    if ocf is not None and ocf > 0 and m.get("net_profit") and m["net_profit"] > 0:
        ratio = ocf / m["net_profit"]
        if ratio >= 1.2:
            parts.append("现金流充沛")

    return "，".join(parts[:3]) if parts else "财务数据良好"


def _build_market_signals(spot: Optional[Dict]) -> str:
    """动态信号：行情数据亮点"""
    if not spot:
        return ""

    parts = []
    change_pct = spot.get("change_pct")
    if change_pct is not None:
        if change_pct > 3:
            parts.append(f"今日涨 {change_pct:.1f}%")
        elif change_pct > 0:
            parts.append(f"今日涨 {change_pct:.1f}%")
        elif change_pct < -3:
            parts.append(f"今日跌 {abs(change_pct):.1f}%")

    # 量价信号用振幅近似
    amplitude = spot.get("amplitude")
    if amplitude is not None and amplitude > 5:
        parts.append("波动较大")

    price = spot.get("price")
    prev_close = spot.get("prev_close")
    if price and prev_close and prev_close > 0:
        # 判断是否在近期高位
        if price > prev_close * 1.05:
            parts.append("价格走强")

    return "，".join(parts[:2]) if parts else ""


def _build_news_section(news_list: Optional[List]) -> str:
    """相关新闻摘要"""
    if not news_list:
        return ""

    parts = []
    for news in news_list[:2]:
        sentiment_tag = news.get("sentiment") or "中性"
        title = news.get("title", "")
        if len(title) > 30:
            title = title[:30] + "..."
        source = news.get("source", "")

        # 计算时间差
        pub = news.get("published_at") or news.get("created_at")
        time_ago = _time_ago(pub)

        parts.append(f"[{sentiment_tag}] {title} ({source}, {time_ago})")

    return "\n               ".join(parts) if parts else ""


def _build_investment_logic(
    score_detail: Dict,
    metrics: Dict,
    spot: Optional[Dict],
    news: Optional[List],
) -> str:
    """一句话投资逻辑"""
    parts = []

    # 盈利能力
    prof = score_detail.get("profitability", 0)
    if prof >= 25:
        parts.append("盈利能力突出")
    elif prof >= 18:
        parts.append("盈利能力良好")

    # 估值
    val = score_detail.get("valuation", 0)
    if val >= 22:
        parts.append("估值处于历史低位")
    elif val >= 15:
        parts.append("估值合理")

    # 成长性
    growth = score_detail.get("growth", 0)
    if growth >= 12:
        parts.append("成长性优异")
    elif growth >= 8:
        parts.append("成长性良好")

    # 财务健康
    health = score_detail.get("financial_health", 0)
    if health >= 16:
        parts.append("财务稳健")

    # 新闻信号
    if news:
        positive_count = sum(1 for n in news[:3] if n.get("sentiment") == "正面")
        if positive_count >= 2:
            parts.append("近期利好频出")
        elif positive_count == 1:
            parts.append("近期有正面催化剂")

    if not parts:
        parts.append("综合基本面优秀")

    return " + ".join(parts) + "，安全边际充足"


def _time_ago(date_str: Optional[str]) -> str:
    """将日期字符串转为相对时间"""
    if not date_str:
        return "未知"
    try:
        # 尝试多种格式
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                delta = datetime.now() - dt
                days = delta.days
                if days <= 0:
                    return "今天"
                elif days == 1:
                    return "昨天"
                elif days <= 7:
                    return f"{days}天前"
                elif days <= 30:
                    return f"{days // 7}周前"
                else:
                    return f"{days // 30}月前"
            except ValueError:
                continue
        return date_str[:10]
    except Exception:
        return date_str[:10] if len(date_str) >= 10 else date_str


def fetch_recent_news(db: Session, stock_code: str, days: int = 7) -> List[Dict]:
    """获取某股票近 N 天的新闻"""
    from app.models.news import News

    threshold = datetime.now() - timedelta(days=days)
    news_list = (
        db.query(News)
        .filter(News.stock_code == stock_code, News.created_at >= threshold)
        .order_by(News.created_at.desc())
        .limit(3)
        .all()
    )

    return [
        {
            "title": n.title,
            "source": n.source,
            "published_at": n.published_at,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "sentiment": n.sentiment,
            "event_type": n.event_type,
        }
        for n in news_list
    ]
