"""
事件分析流水线 - 新闻入库后自动执行：实体抽取 → 关系构建 → 情感分析 → 投资建议 → 推送
"""
import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.news import News
from app.models.stock import Stock
from app.models.financial import Financial

logger = logging.getLogger(__name__)


class EventAnalyzer:
    """
    事件分析器 - 将新闻转化为可操作的投资洞察

    流水线:
    1. 实体抽取 → 识别涉及的股票/公司/政府机构
    2. 关系构建 → 建立实体间关系并写入 Neo4j
    3. 情感分析 → 判断正面/负面/中性
    4. 影响评估 → 结合财务数据评估影响程度
    5. 投资建议 → 生成具体建议
    6. 推送通知 → 发送到 Telegram
    """

    def __init__(self, db: Session):
        self.db = db
        self._extractor = None
        self._kg = None
        self._sentiment = None

    def _get_extractor(self):
        if self._extractor is None:
            from app.services.entity_extractor import EntityExtractor
            self._extractor = EntityExtractor(db=self.db)
        return self._extractor

    def _get_kg(self):
        if self._kg is None:
            from app.services.knowledge_graph import KnowledgeGraphService
            self._kg = KnowledgeGraphService()
        return self._kg

    def _get_sentiment(self):
        if self._sentiment is None:
            from app.services.sentiment_analyzer import SentimentAnalyzer
            self._sentiment = SentimentAnalyzer()
        return self._sentiment

    async def analyze_news(self, news: News) -> Dict[str, Any]:
        """
        分析单条新闻，返回完整的分析报告

        Returns:
            {
                news_id, title,
                entities: [{name, type, stock_code}],
                relations: [{from, to, type}],
                sentiment: {label, score, confidence},
                impact: {level, affected_stocks: [{code, name, direction, reason}]},
                advice: {summary, details}
            }
        """
        report = {
            "news_id": news.id,
            "title": news.title,
            "analyzed_at": datetime.now().isoformat(),
        }

        # Step 1 & 2: 实体抽取 + 关系构建
        try:
            extractor = self._get_extractor()
            extract_result = await extractor.extract_from_news(
                title=news.title,
                content=news.content or "",
                stock_code=news.stock_code
            )
            report["entities"] = extract_result.get("entities", [])
            report["relations"] = extract_result.get("relations", [])
        except Exception as e:
            logger.warning(f"实体抽取失败: {e}")
            report["entities"] = []
            report["relations"] = []

        # Step 3: 情感分析（LLM + 规则兜底）
        try:
            raw = await self._get_sentiment().analyze(news.title + (news.content or ""))
            sentiment = {
                "label": raw.get("sentiment", "neutral"),
                "score": raw.get("score", 0.5),
                "confidence": raw.get("score", 0.5),
                "keywords": raw.get("keywords", []),
            }
            # 规则兜底：LLM 判断中性但标题有明确信号时覆盖
            text = news.title + (news.content or "")
            rule_label = self._rule_based_sentiment(text)
            if rule_label and sentiment["label"] == "neutral":
                sentiment["label"] = rule_label
                sentiment["confidence"] = 0.8
            report["sentiment"] = sentiment
            label_map = {"positive": "正面", "negative": "负面", "neutral": "中性"}
            news.sentiment = label_map.get(sentiment["label"], sentiment["label"])
        except Exception as e:
            logger.warning(f"情感分析失败: {e}")
            report["sentiment"] = {"label": "neutral", "score": 0.5, "confidence": 0, "keywords": []}

        # Step 4: 影响评估
        report["impact"] = self._assess_impact(report)

        # Step 5: 投资建议
        report["advice"] = self._generate_advice(report)

        # Step 6: 更新 DB
        try:
            event_type = self._classify_event(report)
            if event_type:
                news.event_type = event_type
            self.db.commit()
        except Exception:
            pass

        return report

    @staticmethod
    def _rule_based_sentiment(text: str) -> Optional[str]:
        """基于关键词规则判断情感，仅用于 LLM 返回中性时的兜底"""
        positive_kw = [
            "涨价", "涨价至", "上调", "提高", "增长", "盈利", "盈利预告",
            "超预期", "超预期", "突破", "新高", "历史新高", "翻倍",
            "涨停", "大涨", "暴涨", "回购", "增持", "举牌",
            "中标", "签约", "获批", "上市", "首发", "营收增长",
            "利润增长", "分红", "派息", "降税", "减税", "补贴",
            "产能扩张", "订单增长", "市场份额提升", "评级上调",
        ]
        negative_kw = [
            "暴跌", "跌停", "大跌", "暴跌", "崩盘", "熔断",
            "亏损", "亏损扩大", "业绩暴雷", "财务造假",
            "减持", "清仓", "质押", "爆仓", "退市", "ST",
            "处罚", "立案", "调查", "违规", "造假",
            "降级", "下调评级", "召回", "停产", "裁员",
            "债务违约", "资金链断裂", "商誉减值", "计提",
            "监管", "约谈", "整改", "封杀", "制裁", "禁令",
            "关税", "贸易战", "出口管制",
        ]
        for kw in positive_kw:
            if kw in text:
                return "positive"
        for kw in negative_kw:
            if kw in text:
                return "negative"
        return None

    def _assess_impact(self, report: Dict) -> Dict:
        """评估事件影响"""
        sentiment = report.get("sentiment", {})
        entities = report.get("entities", [])
        relations = report.get("relations", [])

        sentiment_label = sentiment.get("label", "neutral")
        confidence = sentiment.get("confidence", 0) or sentiment.get("score", 0)

        # 确定影响等级
        if sentiment_label in ("正面", "positive") and confidence >= 0.7:
            level = "high_positive"
        elif sentiment_label in ("负面", "negative") and confidence >= 0.7:
            level = "high_negative"
        elif sentiment_label in ("正面", "positive"):
            level = "positive"
        elif sentiment_label in ("负面", "negative"):
            level = "negative"
        else:
            level = "neutral"

        # 找出受影响的股票
        affected = []
        for ent in entities:
            code = ent.get("stock_code")
            if not code:
                continue
            stock = self.db.query(Stock).filter(Stock.stock_code == code).first()
            if not stock:
                continue

            # 获取最新财务数据
            fin = self.db.query(Financial).filter(
                Financial.stock_code == code
            ).order_by(Financial.report_date.desc()).first()

            direction = "利好" if "positive" in level else ("利空" if "negative" in level else "中性")

            reason_parts = []
            if fin:
                if fin.roe and fin.roe >= 20:
                    reason_parts.append(f"ROE {fin.roe:.1f}%优秀")
                if fin.debt_ratio and fin.debt_ratio <= 40:
                    reason_parts.append("负债率低")
                if fin.net_profit_yoy and fin.net_profit_yoy > 20:
                    reason_parts.append("利润高增长{:.0f}%".format(fin.net_profit_yoy))

            # 检查是否有监管关系
            for rel in relations:
                if rel.get("type") == "REGULATED_BY" and (
                    rel.get("from") == stock.name or rel.get("to") == stock.name
                ):
                    direction = "谨慎" if "negative" in level else direction
                    reason_parts.append("涉及监管关系")

            affected.append({
                "code": code,
                "name": stock.name,
                "industry": stock.industry,
                "direction": direction,
                "confidence": confidence,
                "reason": "，".join(reason_parts) if reason_parts else "基本面信息不足",
                "financials": {
                    "roe": round(fin.roe, 1) if fin and fin.roe else None,
                    "pe": stock.latest_pe,
                    "debt_ratio": round(fin.debt_ratio, 1) if fin and fin.debt_ratio else None,
                    "revenue_yoy": round(fin.revenue_yoy, 1) if fin and fin.revenue_yoy else None,
                } if fin else None
            })

        return {
            "level": level,
            "affected_stocks": affected,
            "entity_count": len(entities),
            "relation_count": len(relations),
        }

    def _generate_advice(self, report: Dict) -> Dict:
        """生成投资建议"""
        impact = report.get("impact", {})
        sentiment = report.get("sentiment", {})
        level = impact.get("level", "neutral")
        affected = impact.get("affected_stocks", [])

        if not affected:
            return {"summary": "该事件未涉及已知股票，暂无投资建议", "action": "watch", "details": []}

        # 基于影响等级和建议生成
        advices = []
        for stock in affected:
            code = stock["code"]
            name = stock["name"]
            direction = stock["direction"]
            reason = stock["reason"]
            fin = stock.get("financials")
            confidence = stock.get("confidence", 0)

            if direction == "利好":
                if fin and fin.get("roe") and fin["roe"] >= 20:
                    action = "关注"
                    detail = f"{name}({code}) 受此事件利好影响，ROE {fin['roe']}% 表现优秀。{reason}。"
                    if fin.get("debt_ratio") and fin["debt_ratio"] <= 40:
                        detail += "财务稳健，可适当关注。"
                else:
                    action = "观望"
                    detail = f"{name}({code}) 受事件利好，但基本面数据有限，建议观望。{reason}。"
            elif direction == "利空":
                action = "规避"
                detail = f"{name}({code}) 受此事件利空影响。{reason}。建议控制仓位。"
                if confidence >= 0.8:
                    detail = f"⚠️ {name}({code}) 高置信度利空信号！{reason}。建议暂时规避。"
                    action = "规避"
            elif direction == "谨慎":
                action = "谨慎"
                detail = f"{name}({code}) 涉及监管/政策因素，需密切关注后续进展。{reason}。"
            else:
                action = "中性"
                detail = f"{name}({code}) 事件影响中性。{reason}。"

            advices.append({
                "stock_code": code,
                "stock_name": name,
                "action": action,
                "detail": detail,
                "confidence": round(confidence, 2),
            })

        summary_parts = []
        if "positive" in level:
            summary_parts.append(f"📰 整体偏利好，涉及 {len(affected)} 只股票")
        elif "negative" in level:
            summary_parts.append(f"⚠️ 整体偏利空，涉及 {len(affected)} 只股票")
        else:
            summary_parts.append(f"ℹ️ 事件影响中性，涉及 {len(affected)} 只股票")

        # 实体关系摘要
        entities = report.get("entities", [])
        relations = report.get("relations", [])
        if relations:
            rel_summary = "、".join([f"{r.get('from','')}→{r.get('to','')}({r.get('type','')})" for r in relations[:3]])
            summary_parts.append(f"🔗 关系链：{rel_summary}")

        return {
            "summary": "。".join(summary_parts),
            "details": advices,
            "action": "watch" if "positive" in level else ("caution" if "negative" in level else "neutral"),
        }

    def _classify_event(self, report: Dict) -> Optional[str]:
        """分类事件类型"""
        from app.services.entity_extractor import POLICY_KEYWORDS

        title = report.get("title", "")
        entities = report.get("entities", [])
        relations = report.get("relations", [])
        sentiment = report.get("sentiment", {}).get("label", "")

        # 政策事件
        has_government = any(e.get("type") == "government" for e in entities)
        has_policy_kw = any(kw in title for kw in POLICY_KEYWORDS)
        has_regulation = any(r.get("type") == "REGULATED_BY" for r in relations)

        if has_government or has_policy_kw or has_regulation:
            return "policy"

        # 投资者评论
        if "增持" in title or "减持" in title or "举牌" in title:
            return "investor_comment"

        # 货币政策
        if any(kw in title for kw in ["降息", "加息", "降准", "LPR", "MLF"]):
            return "monetary_policy"

        # 负面事件
        if sentiment in ("负面", "negative"):
            return "negative"

        return "general"

    def format_report_message(self, report: Dict) -> str:
        """格式化分析报告为 Telegram 消息"""
        lines = []
        lines.append(f"<b>📊 事件分析报告</b>")
        lines.append(f"<i>{report.get('title', '')}</i>")
        lines.append("")

        # 实体和关系
        entities = report.get("entities", [])
        relations = report.get("relations", [])
        if entities:
            ent_str = "、".join([f"{e['name']}({e['type']})" for e in entities[:5]])
            lines.append(f"🔑 <b>实体</b>：{ent_str}")
        if relations:
            for r in relations[:3]:
                lines.append(f"  ↗️ {r.get('from','')} —{r.get('type','')}→ {r.get('to','')}")

        # 情感
        sentiment = report.get("sentiment", {})
        s_label = sentiment.get("label", "neutral")
        s_score = sentiment.get("confidence", 0) or sentiment.get("score", 0)
        emoji = {"正面": "🟢", "positive": "🟢", "负面": "🔴", "negative": "🔴"}.get(s_label, "⚪")
        lines.append(f"\n{emoji} <b>情感</b>：{s_label}（置信度 {s_score:.0%}）" if s_score else f"\n{emoji} <b>情感</b>：{s_label}")

        # 影响评估
        impact = report.get("impact", {})
        level = impact.get("level", "neutral")
        affected = impact.get("affected_stocks", [])
        if affected:
            lines.append(f"\n📈 <b>影响评估</b>：{len(affected)} 只股票受影响")
            for stock in affected[:5]:
                d = stock["direction"]
                icon = "🟢" if d == "利好" else ("🔴" if d == "利空" else "🟡")
                lines.append(f"  {icon} {stock['name']}({stock['code']}) — {d} | {stock['reason']}")

        # 投资建议
        advice = report.get("advice", {})
        if advice.get("summary"):
            lines.append(f"\n💡 <b>{advice['summary']}</b>")
        for det in advice.get("details", [])[:3]:
            action_icon = {"关注": "👀", "规避": "🚫", "谨慎": "⚠️"}.get(det["action"], "➡️")
            lines.append(f"  {action_icon} {det['detail']}")

        lines.append(f"\n⏰ {report.get('analyzed_at', '')[:19]}")
        return "\n".join(lines)

    async def analyze_and_push(self, news: News) -> Dict[str, Any]:
        """分析并推送（一步到位）"""
        report = await self.analyze_news(news)

        # 仅对有影响的事件推送
        impact = report.get("impact", {})
        should_push = (
            impact.get("level") in ("high_positive", "high_negative", "positive", "negative")
            and impact.get("affected_stocks")
        )

        if should_push:
            try:
                from app.services.notification import TelegramNotifier
                message = self.format_report_message(report)
                await TelegramNotifier.send_telegram_message(message)
                logger.info(f"📤 已推送事件分析：{news.title[:30]}...")
            except Exception as e:
                logger.warning(f"推送失败: {e}")

        return report

    def close(self):
        """清理资源"""
        if self._extractor:
            self._extractor.close()
        if self._kg:
            try:
                self._kg.close()
            except:
                pass
