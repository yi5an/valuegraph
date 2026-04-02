"""
异常关联检测服务 - 检测潜在利益输送或异常关联
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """异常关联检测器"""

    def __init__(self, db: Session):
        self.db = db

    def detect_anomaly_relations(self, stock_code: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        检测潜在的利益输送或异常关联

        Args:
            stock_code: 可选，过滤特定股票的异常

        Returns:
            [{type, entities, risk_level, description}]
        """
        anomalies = []

        # 1. 持股比例异常高的个人股东（>30% 且非创始人）
        anomalies.extend(self._detect_high_concentration(stock_code))

        # 2. 多个公司共享同一大股东
        anomalies.extend(self._detect_shared_holders(stock_code))

        # 3. 近期新增的政府监管关系
        anomalies.extend(self._detect_regulatory_risk(stock_code))

        # 4. 竞争对手之间有合作关系
        anomalies.extend(self._detect_conflict_relations(stock_code))

        # 按 risk_level 排序
        risk_order = {"high": 0, "medium": 1, "low": 2}
        anomalies.sort(key=lambda x: risk_order.get(x["risk_level"], 9))

        return anomalies

    def _detect_high_concentration(self, stock_code: Optional[str]) -> List[Dict[str, Any]]:
        """查找持股比例 > 30% 的个人股东"""
        from app.models.shareholder import Shareholder
        from app.models.stock import Stock

        query = (
            self.db.query(Shareholder, Stock.name)
            .join(Stock, Shareholder.stock_code == Stock.stock_code)
            .filter(
                Shareholder.holder_type == "个人",
                Shareholder.hold_ratio > 30,
            )
        )
        if stock_code:
            query = query.filter(Shareholder.stock_code == stock_code)

        results = query.all()

        anomalies = []
        for sh, stock_name in results:
            anomalies.append({
                "type": "high_concentration",
                "entities": [
                    {"name": sh.holder_name, "type": "person"},
                    {"name": stock_name or sh.stock_code, "type": "company", "stock_code": sh.stock_code},
                ],
                "risk_level": "high" if sh.hold_ratio > 50 else "medium",
                "description": f"{sh.holder_name} 持有 {stock_name or sh.stock_code} {sh.hold_ratio}% 股份，持股比例异常偏高",
            })

        return anomalies

    def _detect_shared_holders(self, stock_code: Optional[str]) -> List[Dict[str, Any]]:
        """查找多个公司共享同一大股东"""
        from app.models.shareholder import Shareholder
        from app.models.stock import Stock

        # 找到出现在多只股票中的大股东（前5大且持股 > 5%）
        subq = (
            self.db.query(
                Shareholder.holder_name,
                func.count(func.distinct(Shareholder.stock_code)).label("company_count"),
            )
            .filter(Shareholder.rank <= 5, Shareholder.hold_ratio > 5)
            .group_by(Shareholder.holder_name)
            .having(func.count(func.distinct(Shareholder.stock_code)) >= 3)
        )

        if stock_code:
            subq = subq.filter(Shareholder.stock_code == stock_code)

        shared_holders = subq.all()

        anomalies = []
        for holder_name, company_count in shared_holders:
            # 获取相关公司
            companies_q = (
                self.db.query(Shareholder.stock_code, Stock.name)
                .join(Stock, Shareholder.stock_code == Stock.stock_code)
                .filter(Shareholder.holder_name == holder_name, Shareholder.rank <= 5)
                .distinct()
                .limit(10)
                .all()
            )

            entities = [{"name": holder_name, "type": "person"}]
            entities.extend(
                {"name": name or code, "type": "company", "stock_code": code}
                for code, name in companies_q
            )

            risk = "high" if company_count >= 5 else "medium"
            anomalies.append({
                "type": "shared_holder",
                "entities": entities,
                "risk_level": risk,
                "description": f"{holder_name} 同时是 {company_count} 家公司的大股东，存在潜在关联交易风险",
            })

        return anomalies

    def _detect_regulatory_risk(self, stock_code: Optional[str]) -> List[Dict[str, Any]]:
        """查找近期被证监会/央行等监管机构标记的公司"""
        from app.models.news import News
        from app.models.stock import Stock
        from datetime import datetime, timedelta

        regulatory_keywords = ["证监会", "银保监会", "央行", "处罚", "立案", "调查", "警示", "整改"]

        three_months_ago = datetime.now() - timedelta(days=90)
        query = (
            self.db.query(News)
            .filter(News.created_at >= three_months_ago)
        )

        # 通过标题关键词匹配监管新闻
        regulatory_news = []
        for news in query.all():
            if any(kw in (news.title or "") for kw in regulatory_keywords):
                if stock_code and news.stock_code != stock_code:
                    continue
                regulatory_news.append(news)

        # 按 stock_code 聚合
        from collections import defaultdict
        code_map = defaultdict(list)
        for n in regulatory_news:
            if n.stock_code:
                code_map[n.stock_code].append(n)

        anomalies = []
        for code, news_items in code_map.items():
            stock = self.db.query(Stock).filter(Stock.stock_code == code).first()
            name = stock.name if stock else code
            anomalies.append({
                "type": "regulatory_risk",
                "entities": [
                    {"name": name, "type": "company", "stock_code": code},
                ],
                "risk_level": "high" if len(news_items) >= 3 else "medium",
                "description": f"{name} 近3个月有 {len(news_items)} 条监管相关新闻，存在合规风险",
            })

        return anomalies

    def _detect_conflict_relations(self, stock_code: Optional[str]) -> List[Dict[str, Any]]:
        """查找竞争对手之间有合作关系"""
        try:
            from app.services.knowledge_graph import KnowledgeGraphService

            kg = KnowledgeGraphService()
            try:
                # 查找所有 competes_with 和 partner_of 关系
                with kg.driver.session() as session:
                    # 找竞争对手关系
                    compete_query = "MATCH (a)-[:competes_with]->(b) RETURN a.name as a_name, b.name as b_name"
                    compete_results = session.run(compete_query).data()

                    # 找合作关系
                    partner_query = "MATCH (a)-[:partner_of]->(b) RETURN a.name as a_name, b.name as b_name"
                    partner_results = session.run(partner_query).data()

                compete_pairs = {(r["a_name"], r["b_name"]) for r in compete_results}
                partner_pairs = {(r["a_name"], r["b_name"]) for r in partner_results}

                # 找交集：既是竞争对手又有合作关系
                conflicts = compete_pairs & partner_pairs

                anomalies = []
                for a_name, b_name in conflicts:
                    if stock_code:
                        # 简单匹配：检查名称或代码是否相关
                        if stock_code not in a_name and stock_code not in b_name:
                            continue

                    anomalies.append({
                        "type": "conflict_relation",
                        "entities": [
                            {"name": a_name, "type": "company"},
                            {"name": b_name, "type": "company"},
                        ],
                        "risk_level": "medium",
                        "description": f"{a_name} 与 {b_name} 既是竞争对手又有合作关系，可能存在信息泄露风险",
                    })

                return anomalies
            finally:
                kg.close()
        except Exception as e:
            logger.warning(f"Neo4j 冲突关系检测失败（Neo4j 可能未启动）: {e}")
            return []
