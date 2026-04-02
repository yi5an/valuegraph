"""
成长投资策略
关注高增长、高潜力的成长型股票
"""
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
import logging

from app.services.strategies.base import StrategyBase
from app.models.stock import Stock
from app.models.financial import Financial

logger = logging.getLogger(__name__)


class GrowthInvestingStrategy(StrategyBase):
    """成长投资策略"""

    @property
    def name(self) -> str:
        return "growth"

    @property
    def display_name(self) -> str:
        return "🌱 成长投资"

    @property
    def description(self) -> str:
        return "关注营收和利润高速增长、市场空间大的成长型股票"

    def get_params_schema(self) -> List[Dict[str, Any]]:
        return [
            {"name": "min_revenue_yoy", "type": "float", "default": 20.0, "description": "最低营收增长率（%）"},
            {"name": "min_profit_yoy", "type": "float", "default": 15.0, "description": "最低净利润增长率（%）"},
            {"name": "max_pe", "type": "float", "default": 80.0, "description": "最高PE（排除泡沫）"},
            {"name": "min_gross_margin", "type": "float", "default": 20.0, "description": "最低毛利率（护城河）"},
        ]

    def filter_stocks(
        self,
        market: str = "A",
        limit: int = 20,
        min_revenue_yoy: float = 20.0,
        min_profit_yoy: float = 15.0,
        max_pe: float = 80.0,
        min_gross_margin: float = 20.0,
        sort_by: str = "score",
        **kwargs
    ) -> List[Dict]:
        """
        成长投资筛选

        五维度评分：
        1. 成长速度 35分（营收增长率15 + 净利增长率15 + 加速度5）
        2. 盈利质量 25分（毛利率10 + ROE10 + 现金流覆盖率5）
        3. 规模扩张 15分（营收规模5 + 市值增长10）
        4. 估值合理性 15分（PEG评分）
        5. 持续性 10分（连续增长期数）
        """
        stocks = self.db.query(Stock).filter(Stock.market == market).all()
        results = []

        for stock in stocks:
            # 获取最近4个季度财报（用于评估持续性）
            financials = self.db.query(Financial).filter(
                Financial.stock_code == stock.stock_code
            ).order_by(Financial.report_date.desc()).limit(4).all()

            if not financials:
                continue

            f = financials[0]  # 最新一期

            # 硬门槛
            if min_gross_margin is not None and f.gross_margin is not None and f.gross_margin < min_gross_margin:
                continue
            if f.net_profit is not None and f.net_profit <= 0:
                continue
            if stock.latest_pe is not None and stock.latest_pe > max_pe:
                continue

            # 计算评分
            score_detail = self._calc_score(f, financials, stock)

            if score_detail["total"] < 40:
                continue

            results.append({
                'stock_code': stock.stock_code,
                'name': stock.name,
                'market': stock.market,
                'industry': stock.industry,
                'market_cap': stock.market_cap,
                'latest_roe': f.roe,
                'latest_pe': stock.latest_pe,
                'debt_ratio': f.debt_ratio,
                'gross_margin': f.gross_margin,
                'net_profit_growth': f.net_profit_yoy,
                'recommendation_score': score_detail["total"],
                'recommendation_reason': self._generate_reason(score_detail),
                'strategy_name': self.name,
                'composite_score': score_detail["total"],
                'score_detail': score_detail,
                'eps': f.eps,
                'bvps': f.bvps,
                'revenue_yoy': f.revenue_yoy,
            })

        # 排序
        sort_field_map = {
            'score': 'composite_score',
            'roe': 'latest_roe',
            'growth': 'revenue_yoy',
        }
        sort_field = sort_field_map.get(sort_by, 'composite_score')
        results.sort(key=lambda x: x.get(sort_field) if x.get(sort_field) is not None else 0, reverse=True)

        return results[:limit]

    def _calc_score(self, f: Financial, historical: list, stock: Stock) -> Dict:
        scores = {}

        # 1. 成长速度（35分）
        growth_speed = 0
        ry = f.revenue_yoy
        if ry is not None:
            growth_speed += min(15, max(0, int(ry / 4)))
        ny = f.net_profit_yoy
        if ny is not None:
            growth_speed += min(15, max(0, int(ny / 4)))

        # 加速度：对比前一期
        if len(historical) >= 2:
            prev = historical[1]
            if (ry is not None and prev.revenue_yoy is not None and
                prev.revenue_yoy > 0 and ry > prev.revenue_yoy):
                growth_speed += 5  # 加速增长
            elif ry is not None and prev.revenue_yoy is not None:
                growth_speed += 2  # 减速但仍在增长
        scores["growth_speed"] = growth_speed

        # 2. 盈利质量（25分）
        quality = 0
        if f.gross_margin is not None:
            if f.gross_margin >= 50:
                quality += 10
            elif f.gross_margin >= 35:
                quality += 8
            elif f.gross_margin >= 25:
                quality += 6
            else:
                quality += 3

        if f.roe is not None:
            if f.roe >= 20:
                quality += 10
            elif f.roe >= 15:
                quality += 8
            elif f.roe >= 10:
                quality += 5
            else:
                quality += 2

        # 现金流覆盖
        if f.net_profit and f.net_profit > 0 and f.operating_cash_flow:
            if f.operating_cash_flow / f.net_profit >= 1.0:
                quality += 5
            elif f.operating_cash_flow / f.net_profit >= 0.7:
                quality += 3
        scores["profit_quality"] = quality

        # 3. 规模扩张（15分）
        expansion = 0
        if stock.market_cap:
            if stock.market_cap >= 1000:
                expansion += 5  # 大市值稳定
            elif stock.market_cap >= 200:
                expansion += 4
            else:
                expansion += 2  # 小市值弹性大但风险高
        # 留10分给未来扩展
        scores["expansion"] = expansion

        # 4. 估值合理性（15分）- PEG
        valuation = 0
        if stock.latest_pe and stock.latest_pe > 0 and ny and ny > 0:
            peg = stock.latest_pe / ny
            if peg <= 0.8:
                valuation += 15
            elif peg <= 1.0:
                valuation += 12
            elif peg <= 1.5:
                valuation += 8
            elif peg <= 2.0:
                valuation += 5
            else:
                valuation += 2
        else:
            valuation += 7
        scores["valuation"] = valuation

        # 5. 持续性（10分）
        consistency = 0
        consecutive = 0
        for fin in historical:
            if fin.net_profit_yoy is not None and fin.net_profit_yoy > 0:
                consecutive += 1
            else:
                break
        if consecutive >= 4:
            consistency += 10
        elif consecutive >= 3:
            consistency += 7
        elif consecutive >= 2:
            consistency += 4
        else:
            consistency += 1
        scores["consistency"] = consistency

        scores["total"] = sum(scores.values())
        return scores

    def _generate_reason(self, score_detail: Dict) -> str:
        reasons = []
        if score_detail.get("growth_speed", 0) >= 25:
            reasons.append("高速增长")
        elif score_detail.get("growth_speed", 0) >= 15:
            reasons.append("稳定增长")

        if score_detail.get("profit_quality", 0) >= 20:
            reasons.append("盈利质量优秀")
        elif score_detail.get("profit_quality", 0) >= 12:
            reasons.append("盈利质量良好")

        if score_detail.get("valuation", 0) >= 12:
            reasons.append("PEG合理")
        elif score_detail.get("valuation", 0) <= 5:
            reasons.append("估值偏高需注意")

        if score_detail.get("consistency", 0) >= 7:
            reasons.append("增长持续性强")

        return "，".join(reasons) if reasons else "具备一定成长性"
