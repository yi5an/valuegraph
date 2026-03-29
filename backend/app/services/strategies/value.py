"""
价值投资策略
基于格雷厄姆/巴菲特/费雪的经典价值投资理论
"""
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
import logging

from app.services.strategies.base import StrategyBase
from app.models.stock import Stock
from app.models.financial import Financial

logger = logging.getLogger(__name__)


class ValueInvestingStrategy(StrategyBase):
    """价值投资策略"""
    
    # 10年期国债收益率（用于 Graham 公式）
    RISK_FREE_RATE = 0.03
    
    @property
    def name(self) -> str:
        return "value"
    
    @property
    def display_name(self) -> str:
        return "🏛️ 价值投资"
    
    @property
    def description(self) -> str:
        return "基于基本面分析的价值投资策略，关注ROE、安全边际和财务健康度"
    
    def get_params_schema(self) -> List[Dict[str, Any]]:
        return [
            {"name": "min_roe", "type": "float", "default": 15.0, "description": "最低ROE（%）"},
            {"name": "max_debt_ratio", "type": "float", "default": 60.0, "description": "最高负债率（%）"},
            {"name": "min_safety_margin", "type": "float", "default": 0.0, "description": "最低安全边际（%）"},
            {"name": "min_grade", "type": "str", "default": "D", "description": "最低评级（A+/A/B/C/D）"},
            {"name": "min_gross_margin", "type": "float", "default": None, "description": "最低毛利率（%）"},
            {"name": "industry", "type": "str", "default": None, "description": "行业筛选"},
        ]
    
    def filter_stocks(
        self,
        market: str = "A",
        limit: int = 20,
        min_roe: float = 15.0,
        max_debt_ratio: float = 60.0,
        min_safety_margin: float = 0.0,
        min_grade: str = "D",
        min_gross_margin: Optional[float] = None,
        industry: Optional[str] = None,
        sort_by: str = "score",
        **kwargs
    ) -> List[Dict]:
        """
        价值投资筛选
        
        流程：
        1. 定量硬门槛过滤
        2. 五维度评分（满分100）
        3. 安全边际计算
        4. 评级分配
        5. 排序返回
        """
        grade_threshold = self._grade_to_score(min_grade)
        
        # 查询股票
        query = self.db.query(Stock).filter(Stock.market == market)
        if industry:
            query = query.filter(Stock.industry == industry)
        stocks = query.all()
        
        # 获取行业均值（用于估值比较）
        industry_avg_pe = self._calc_industry_avg_pe(stocks)
        
        results = []
        for stock in stocks:
            financial = self.db.query(Financial).filter(
                Financial.stock_code == stock.stock_code
            ).order_by(Financial.report_date.desc()).first()
            
            if not financial:
                continue
            
            # ====== 第一步：硬门槛过滤 ======
            if not self._pass_hard_filters(financial, min_roe, max_debt_ratio, min_gross_margin):
                continue
            
            # ====== 第二步：五维度评分 ======
            score_detail = self._calc_composite_score(financial, stock, industry_avg_pe)
            
            # ====== 第三步：安全边际 ======
            safety_margin = self._calc_safety_margin(financial)
            
            # ====== 第四步：评级 ======
            grade = self._calc_grade(score_detail["total"], safety_margin)
            
            # ====== 第五步：筛选 ======
            if score_detail["total"] < grade_threshold:
                continue
            if safety_margin < min_safety_margin:
                continue
            
            results.append({
                'stock_code': stock.stock_code,
                'name': stock.name,
                'market': stock.market,
                'industry': stock.industry,
                'market_cap': stock.market_cap,
                # 原有字段（向后兼容）
                'latest_roe': financial.roe,
                'latest_pe': stock.latest_pe,
                'debt_ratio': financial.debt_ratio,
                'gross_margin': financial.gross_margin,
                'net_profit_growth': financial.net_profit_yoy,
                'recommendation_score': score_detail["total"],
                'recommendation_reason': self._generate_reason(score_detail, safety_margin, grade),
                # 新增字段
                'strategy_name': self.name,
                'grade': grade,
                'safety_margin': round(safety_margin, 2),
                'composite_score': score_detail["total"],
                'score_detail': score_detail,
                'eps': financial.eps,
                'bvps': financial.bvps,
                'operating_cash_flow': financial.operating_cash_flow,
                'revenue_yoy': financial.revenue_yoy,
            })
        
        # 排序
        sort_field_map = {
            'score': 'composite_score',
            'roe': 'latest_roe',
            'pe': 'latest_pe',
            'market_cap': 'market_cap',
            'safety_margin': 'safety_margin',
        }
        sort_field = sort_field_map.get(sort_by, 'composite_score')
        reverse_sort = sort_by not in ('pe',)
        results.sort(key=lambda x: x.get(sort_field) or 0, reverse=reverse_sort)
        
        return results[:limit]
    
    def _pass_hard_filters(
        self, f: Financial,
        min_roe: float, max_debt_ratio: float,
        min_gross_margin: Optional[float]
    ) -> bool:
        """硬门槛过滤"""
        if f.roe is not None and f.roe < min_roe:
            return False
        if f.debt_ratio is not None and f.debt_ratio > max_debt_ratio:
            return False
        if f.net_profit is not None and f.net_profit <= 0:
            return False
        if f.operating_cash_flow is not None and f.operating_cash_flow <= 0:
            return False
        if min_gross_margin is not None and f.gross_margin is not None and f.gross_margin < min_gross_margin:
            return False
        return True
    
    def _calc_composite_score(
        self, f: Financial, stock: Stock, industry_avg_pe: float
    ) -> Dict:
        """
        五维度评分（满分100分）
        
        盈利能力 30分 + 估值水平 25分 + 财务健康 20分 + 成长性 15分 + 分红回报 10分
        """
        scores = {}
        
        # ====== 1. 盈利能力（30分）======
        profit_score = 0
        # ROE 评分（20分）
        roe = f.roe or 0
        if roe >= 25:
            profit_score += 20
        elif roe >= 20:
            profit_score += 17
        elif roe >= 15:
            profit_score += 14
        elif roe >= 10:
            profit_score += 10
        else:
            profit_score += 5
        
        # 净利润增长率（10分）
        npg = f.net_profit_yoy
        if npg is not None and npg > 0:
            profit_score += min(10, int(npg / 5))
        else:
            profit_score += 2  # 无增长数据给低分
        
        scores["profitability"] = profit_score
        
        # ====== 2. 估值水平（25分）======
        valuation_score = 0
        pe = stock.latest_pe
        
        if pe is not None and pe > 0:
            if industry_avg_pe > 0:
                # 与行业均值比较
                pe_ratio = pe / industry_avg_pe
                if pe_ratio <= 0.7:
                    valuation_score += 25  # 显著低于行业均值
                elif pe_ratio <= 0.9:
                    valuation_score += 20
                elif pe_ratio <= 1.1:
                    valuation_score += 15
                elif pe_ratio <= 1.3:
                    valuation_score += 10
                else:
                    valuation_score += 5
            else:
                # 无行业均值，用绝对值
                if pe <= 15:
                    valuation_score += 22
                elif pe <= 25:
                    valuation_score += 18
                elif pe <= 35:
                    valuation_score += 12
                elif pe <= 50:
                    valuation_score += 7
                else:
                    valuation_score += 3
        else:
            valuation_score += 12  # 无数据给中性分
        
        scores["valuation"] = valuation_score
        
        # ====== 3. 财务健康（20分）======
        health_score = 0
        # 负债率（12分）
        dr = f.debt_ratio or 50
        if dr <= 30:
            health_score += 12
        elif dr <= 40:
            health_score += 10
        elif dr <= 50:
            health_score += 8
        elif dr <= 60:
            health_score += 5
        else:
            health_score += 2
        
        # 经营现金流/净利润比（8分）
        if f.net_profit and f.net_profit > 0 and f.operating_cash_flow:
            ocf_ratio = f.operating_cash_flow / f.net_profit
            if ocf_ratio >= 1.2:
                health_score += 8  # 现金流覆盖利润，质量很高
            elif ocf_ratio >= 1.0:
                health_score += 6
            elif ocf_ratio >= 0.7:
                health_score += 4
            else:
                health_score += 2
        else:
            health_score += 4  # 无数据给中性分
        
        scores["financial_health"] = health_score
        
        # ====== 4. 成长性（15分）======
        growth_score = 0
        # 营收增长率（8分）
        rg = f.revenue_yoy
        if rg is not None:
            if rg >= 30:
                growth_score += 8
            elif rg >= 20:
                growth_score += 7
            elif rg >= 10:
                growth_score += 5
            elif rg >= 5:
                growth_score += 3
            else:
                growth_score += 1
        else:
            growth_score += 3
        
        # 净利润增长率（7分）
        if npg is not None:
            if npg >= 30:
                growth_score += 7
            elif npg >= 20:
                growth_score += 6
            elif npg >= 10:
                growth_score += 4
            elif npg >= 5:
                growth_score += 2
            else:
                growth_score += 1
        else:
            growth_score += 2
        
        scores["growth"] = growth_score
        
        # ====== 5. 分红回报（10分）======
        # 当前数据库暂无股息率字段，给中性分
        dividend_score = 5
        scores["dividend"] = dividend_score
        
        total = sum(scores.values())
        scores["total"] = total
        
        return scores
    
    def _calc_safety_margin(self, f: Financial) -> float:
        """
        计算 Graham 安全边际
        
        V = EPS × (8.5 + 2g) × 4.4 / Y
        
        Returns:
            安全边际百分比（0-1），负数表示无安全边际
        """
        eps = f.eps
        if eps is None or eps <= 0:
            return 0.0
        
        g = f.net_profit_yoy  # 简化：用最近一年增长率
        if g is None:
            g = 5  # 默认5%增长
        
        Y = self.RISK_FREE_RATE * 100 if self.RISK_FREE_RATE < 1 else self.RISK_FREE_RATE
        
        intrinsic_value = eps * (8.5 + 2 * g) * 4.4 / Y
        
        # 当前价格近似 = PE × EPS
        # 如果没有 PE，无法计算安全边际
        # 这个会在上层用 stock.latest_pe 来算
        # 这里先返回 Graham 价值，让上层计算
        return intrinsic_value  # 返回内在价值，由上层计算安全边际
    
    def calc_safety_margin_from_pe(self, f: Financial, pe: float) -> float:
        """
        基于 PE 计算安全边际（供外部调用）
        """
        if pe is None or pe <= 0:
            return 0.0
        
        eps = f.eps
        if eps is None or eps <= 0:
            return 0.0
        
        intrinsic_value = self._calc_safety_margin(f)
        current_price = pe * eps
        
        if current_price <= 0:
            return 0.0
        
        margin = (intrinsic_value - current_price) / intrinsic_value
        return round(margin * 100, 2) if margin > 0 else 0.0
    
    def _calc_grade(self, score: float, safety_margin: float) -> str:
        """根据评分和安全边际计算评级"""
        # A+ 需要同时满足高分和较高安全边际
        if score >= 90 and safety_margin >= 20:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 60:
            return "C"
        else:
            return "D"
    
    def _grade_to_score(self, grade: str) -> float:
        """评级转最低分数阈值"""
        mapping = {"A+": 90, "A": 80, "B": 70, "C": 60, "D": 0}
        return mapping.get(grade.upper(), 0)
    
    def _calc_industry_avg_pe(self, stocks: list) -> float:
        """计算行业平均 PE"""
        pe_values = []
        for s in stocks:
            if s.latest_pe and s.latest_pe > 0 and s.latest_pe < 200:  # 排除异常值
                pe_values.append(s.latest_pe)
        if not pe_values:
            return 0
        return sum(pe_values) / len(pe_values)
    
    def _generate_reason(self, score_detail: Dict, safety_margin: float, grade: str) -> str:
        """生成推荐理由"""
        reasons = []
        
        # 盈利能力
        if score_detail.get("profitability", 0) >= 25:
            reasons.append("盈利能力优秀")
        elif score_detail.get("profitability", 0) >= 18:
            reasons.append("盈利能力良好")
        
        # 估值
        if score_detail.get("valuation", 0) >= 22:
            reasons.append("估值低估")
        elif score_detail.get("valuation", 0) >= 15:
            reasons.append("估值合理")
        elif score_detail.get("valuation", 0) <= 7:
            reasons.append("估值偏高")
        
        # 财务健康
        if score_detail.get("financial_health", 0) >= 16:
            reasons.append("财务稳健")
        
        # 成长性
        if score_detail.get("growth", 0) >= 12:
            reasons.append("成长性好")
        
        # 安全边际
        if safety_margin >= 30:
            reasons.append(f"安全边际{safety_margin:.0f}%充足")
        elif safety_margin >= 15:
            reasons.append(f"安全边际{safety_margin:.0f}%")
        
        if not reasons:
            reasons.append("符合价值投资基本标准")
        
        return f"[{grade}] " + "，".join(reasons)
