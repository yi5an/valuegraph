"""
价值投资策略

基于 Graham 和巴菲特的价值投资理念，结合 A 股市场特点。

核心要素：
1. 定量筛选：ROE > 15%、负债率 < 60%、经营现金流 > 0、净利润 > 0
2. 评分体系：盈利能力(30) + 估值水平(25) + 财务健康(20) + 成长性(15) + 分红回报(10)
3. 安全边际：Graham 公式 V = EPS × (8.5 + 2g) × 4.4 / Y
4. 评级体系：A+(90+) / A(80-89) / B(70-79) / C(60-69) / D(<60)
"""

from typing import Dict, Any, Optional
from app.services.strategies.base import StrategyBase


class ValueInvestingStrategy(StrategyBase):
    """价值投资策略"""

    def __init__(
        self,
        min_roe: float = 15.0,
        max_debt_ratio: float = 60.0,
        min_gross_margin: float = 20.0,
        min_cash_flow: float = 0,
        min_net_profit: float = 0,
        bond_yield: float = 3.0,  # 10年期国债收益率（%）
    ):
        super().__init__()
        self.name = "value"
        self.description = "价值投资策略（Graham + 巴菲特理念）"

        # 筛选参数
        self.min_roe = min_roe
        self.max_debt_ratio = max_debt_ratio
        self.min_gross_margin = min_gross_margin
        self.min_cash_flow = min_cash_flow
        self.min_net_profit = min_net_profit
        self.bond_yield = bond_yield

    def screen(self, financial_data: Dict[str, Any]) -> tuple[bool, list]:
        """
        定量筛选（硬门槛）

        筛选条件：
        - ROE 最近一年 > 15%
        - 负债率 < 60%
        - 经营现金流 > 0
        - 净利润 > 0
        - 毛利率 > 20%（可选）
        """
        reasons = []

        # ROE 筛选
        roe = financial_data.get("roe")
        if roe is None:
            reasons.append("缺少ROE数据")
        elif roe < self.min_roe:
            reasons.append(f"ROE {roe:.1f}% 低于最低要求 {self.min_roe}%")

        # 负债率筛选
        debt_ratio = financial_data.get("debt_ratio")
        if debt_ratio is None:
            reasons.append("缺少负债率数据")
        elif debt_ratio > self.max_debt_ratio:
            reasons.append(f"负债率 {debt_ratio:.1f}% 超过上限 {self.max_debt_ratio}%")

        # 经营现金流筛选
        operating_cash_flow = financial_data.get("operating_cash_flow")
        if operating_cash_flow is None:
            pass  # 缺失数据不惩罚
        elif operating_cash_flow < self.min_cash_flow:
            reasons.append(f"经营现金流为负")

        # 净利润筛选
        net_profit = financial_data.get("net_profit")
        if net_profit is None:
            pass  # 缺失数据不惩罚
        elif net_profit < self.min_net_profit:
            reasons.append(f"净利润为负")

        # 毛利率筛选（可选）
        gross_margin = financial_data.get("gross_margin")
        if gross_margin is not None and gross_margin < self.min_gross_margin:
            reasons.append(f"毛利率 {gross_margin:.1f}% 低于最低要求 {self.min_gross_margin}%")

        passed = len(reasons) == 0
        return passed, reasons

    def calculate_score(self, financial_data: Dict[str, Any], stock_data: Dict[str, Any]) -> float:
        """
        计算综合得分（满分100分）

        评分维度：
        - 盈利能力 30分：ROE（连续3年平均）、净利润增长率
        - 估值水平 25分：PE、PB（与行业均值比较）
        - 财务健康 20分：负债率、经营现金流/净利润比
        - 成长性 15分：营收增长率、净利润增长率
        - 分红回报 10分：股息率（如有数据）
        """
        total_score = 0

        # 1. 盈利能力（30分）
        profitability_score = self._score_profitability(financial_data)
        total_score += profitability_score

        # 2. 估值水平（25分）
        valuation_score = self._score_valuation(financial_data, stock_data)
        total_score += valuation_score

        # 3. 财务健康（20分）
        financial_health_score = self._score_financial_health(financial_data)
        total_score += financial_health_score

        # 4. 成长性（15分）
        growth_score = self._score_growth(financial_data)
        total_score += growth_score

        # 5. 分红回报（10分）
        dividend_score = self._score_dividend(financial_data, stock_data)
        total_score += dividend_score

        return min(total_score, 100)

    def _score_profitability(self, financial_data: Dict[str, Any]) -> float:
        """
        盈利能力评分（30分）

        - ROE（20分）：>25%=20, >20%=16, >18%=14, >15%=12, >12%=8
        - 净利润增长率（10分）：>30%=10, >20%=8, >10%=6, >0%=4
        """
        score = 0

        # ROE 评分（20分）
        roe = financial_data.get("roe")
        if roe is not None:
            if roe >= 25:
                score += 20
            elif roe >= 20:
                score += 16
            elif roe >= 18:
                score += 14
            elif roe >= 15:
                score += 12
            elif roe >= 12:
                score += 8
            else:
                score += 4
        else:
            score += 10  # 缺失给中性分

        # 净利润增长率评分（10分）
        net_profit_yoy = financial_data.get("net_profit_yoy")
        if net_profit_yoy is not None:
            if net_profit_yoy >= 30:
                score += 10
            elif net_profit_yoy >= 20:
                score += 8
            elif net_profit_yoy >= 10:
                score += 6
            elif net_profit_yoy >= 0:
                score += 4
            else:
                score += 2
        else:
            score += 5  # 缺失给中性分

        return score

    def _score_valuation(self, financial_data: Dict[str, Any], stock_data: Dict[str, Any]) -> float:
        """
        估值水平评分（25分）

        - PE 评分（15分）：<10=15, <15=12, <20=10, <30=7, <50=5
        - PB 评分（10分）：<1=10, <1.5=8, <2=6, <3=4
        """
        score = 0

        # PE 评分（15分）
        pe = stock_data.get("latest_pe")
        if pe is not None and pe > 0:
            if pe < 10:
                score += 15
            elif pe < 15:
                score += 12
            elif pe < 20:
                score += 10
            elif pe < 30:
                score += 7
            elif pe < 50:
                score += 5
            else:
                score += 2
        else:
            score += 8  # 缺失给中性分

        # PB 评分（10分）- 通过 BVPS 计算
        bvps = financial_data.get("bvps")  # 每股净资产
        # 假设股价可以从 market_cap / 总股本估算，这里简化处理
        # PB = 股价 / BVPS，但没有股价数据，给中性分
        score += 5  # 缺失 PB 数据给中性分

        return score

    def _score_financial_health(self, financial_data: Dict[str, Any]) -> float:
        """
        财务健康评分（20分）

        - 负债率（10分）：<30%=10, <40%=8, <50%=6, <60%=4
        - 经营现金流/净利润比（10分）：>1.5=10, >1.2=8, >1.0=6, >0.8=4
        """
        score = 0

        # 负债率评分（10分）
        debt_ratio = financial_data.get("debt_ratio")
        if debt_ratio is not None:
            if debt_ratio < 30:
                score += 10
            elif debt_ratio < 40:
                score += 8
            elif debt_ratio < 50:
                score += 6
            elif debt_ratio < 60:
                score += 4
            else:
                score += 2
        else:
            score += 5  # 缺失给中性分

        # 经营现金流/净利润比（10分）
        operating_cash_flow = financial_data.get("operating_cash_flow")
        net_profit = financial_data.get("net_profit")

        if operating_cash_flow is not None and net_profit is not None and net_profit > 0:
            ratio = operating_cash_flow / net_profit
            if ratio >= 1.5:
                score += 10
            elif ratio >= 1.2:
                score += 8
            elif ratio >= 1.0:
                score += 6
            elif ratio >= 0.8:
                score += 4
            else:
                score += 2
        else:
            score += 5  # 缺失给中性分

        return score

    def _score_growth(self, financial_data: Dict[str, Any]) -> float:
        """
        成长性评分（15分）

        - 营收增长率（7.5分）：>30%=7.5, >20%=6, >10%=4.5, >0%=3
        - 净利润增长率（7.5分）：>30%=7.5, >20%=6, >10%=4.5, >0%=3
        """
        score = 0

        # 营收增长率评分（7.5分）
        revenue_yoy = financial_data.get("revenue_yoy")
        if revenue_yoy is not None:
            if revenue_yoy >= 30:
                score += 7.5
            elif revenue_yoy >= 20:
                score += 6
            elif revenue_yoy >= 10:
                score += 4.5
            elif revenue_yoy >= 0:
                score += 3
            else:
                score += 1
        else:
            score += 4  # 缺失给中性分

        # 净利润增长率评分（7.5分）
        net_profit_yoy = financial_data.get("net_profit_yoy")
        if net_profit_yoy is not None:
            if net_profit_yoy >= 30:
                score += 7.5
            elif net_profit_yoy >= 20:
                score += 6
            elif net_profit_yoy >= 10:
                score += 4.5
            elif net_profit_yoy >= 0:
                score += 3
            else:
                score += 1
        else:
            score += 4  # 缺失给中性分

        return score

    def _score_dividend(self, financial_data: Dict[str, Any], stock_data: Dict[str, Any]) -> float:
        """
        分红回报评分（10分）

        股息率评分：>5%=10, >3%=8, >2%=6, >1%=4, >0%=2

        注：当前数据库没有股息率字段，给中性分
        """
        # TODO: 如果有股息率数据，可以实现完整评分
        # dividend_yield = financial_data.get("dividend_yield")
        # 暂时给中性分
        return 5

    def calculate_safety_margin(self, financial_data: Dict[str, Any], stock_data: Dict[str, Any]) -> Optional[float]:
        """
        计算安全边际（Graham 公式）

        简化 Graham 公式:
        V = EPS × (8.5 + 2g) × 4.4 / Y

        其中：
        - V = 内在价值
        - EPS = 每股收益
        - g = 过去3年平均净利润增长率（%）
        - Y = 当前10年期国债收益率（默认3%）
        - 8.5 = 基准PE（零增长公司的合理PE）

        安全边际 = (V - 当前价格) / V × 100%

        Returns:
            安全边际（%），如无数据返回 None
        """
        eps = financial_data.get("eps")
        net_profit_yoy = financial_data.get("net_profit_yoy")
        pe = stock_data.get("latest_pe")

        # 缺少关键数据，返回 None
        if eps is None or eps <= 0 or pe is None or pe <= 0:
            return None

        # g = 净利润增长率（如有数据）
        g = net_profit_yoy if net_profit_yoy is not None else 0

        # 计算内在价值
        # V = EPS × (8.5 + 2g) × 4.4 / Y
        intrinsic_value = eps * (8.5 + 2 * g) * 4.4 / self.bond_yield

        # 计算当前价格（P = EPS × PE）
        current_price = eps * pe

        # 计算安全边际
        if intrinsic_value <= 0:
            return None

        safety_margin = (intrinsic_value - current_price) / intrinsic_value * 100

        return safety_margin

    def get_grade(self, score: float, safety_margin: Optional[float] = None) -> str:
        """
        根据得分和安全边际获取评级

        评级标准：
        - A+ (90+分，强烈推荐)：高ROE + 低估值 + 大安全边际
        - A (80-89分，推荐)：基本面优秀 + 估值合理
        - B (70-79分，关注)：基本面良好但估值偏高
        - C (60-69分，观望)：部分指标不达标
        - D (<60分，不推荐)：多项指标不达标
        """
        # 基础评级
        if score >= 90:
            base_grade = "A+"
        elif score >= 80:
            base_grade = "A"
        elif score >= 70:
            base_grade = "B"
        elif score >= 60:
            base_grade = "C"
        else:
            base_grade = "D"

        # 安全边际加成（仅对 A 类及以下评级）
        if safety_margin is not None and safety_margin > 30 and base_grade in ["A", "B"]:
            # 安全边际 > 30%，可以提升一个等级（但不超过 A+）
            if base_grade == "A" and score >= 85:
                return "A+"

        return base_grade

    def get_score_breakdown(self, financial_data: Dict[str, Any], stock_data: Dict[str, Any]) -> Dict[str, float]:
        """
        获取得分明细（按维度）
        """
        return {
            "盈利能力": self._score_profitability(financial_data),
            "估值水平": self._score_valuation(financial_data, stock_data),
            "财务健康": self._score_financial_health(financial_data),
            "成长性": self._score_growth(financial_data),
            "分红回报": self._score_dividend(financial_data, stock_data),
        }

    def generate_recommendation_reason(
        self,
        financial_data: Dict[str, Any],
        stock_data: Dict[str, Any],
        score: float,
        grade: str
    ) -> str:
        """
        生成推荐理由
        """
        reasons = []

        # ROE 分析
        roe = financial_data.get("roe")
        if roe is not None:
            if roe >= 25:
                reasons.append("ROE优秀")
            elif roe >= 20:
                reasons.append("ROE良好")

        # 负债率分析
        debt_ratio = financial_data.get("debt_ratio")
        if debt_ratio is not None:
            if debt_ratio < 40:
                reasons.append("低负债")
            elif debt_ratio < 50:
                reasons.append("负债适中")

        # 估值分析
        pe = stock_data.get("latest_pe")
        if pe is not None and pe > 0:
            if pe < 15:
                reasons.append("估值偏低")
            elif pe < 25:
                reasons.append("估值合理")

        # 成长性分析
        revenue_yoy = financial_data.get("revenue_yoy")
        net_profit_yoy = financial_data.get("net_profit_yoy")
        if revenue_yoy is not None and revenue_yoy > 20:
            reasons.append("营收高增长")
        if net_profit_yoy is not None and net_profit_yoy > 20:
            reasons.append("利润高增长")

        # 安全边际
        safety_margin = self.calculate_safety_margin(financial_data, stock_data)
        if safety_margin is not None and safety_margin > 30:
            reasons.append(f"安全边际{safety_margin:.0f}%")

        # 评级说明
        grade_desc = {
            "A+": "强烈推荐",
            "A": "推荐",
            "B": "关注",
            "C": "观望",
            "D": "不推荐"
        }

        reason_text = "、".join(reasons) if reasons else "符合基本标准"
        return f"[{grade_desc.get(grade, '')}] {reason_text}"

    def get_params_info(self) -> Dict[str, Any]:
        """
        获取策略参数说明
        """
        return {
            "description": self.description,
            "min_roe": {
                "type": "float",
                "default": self.min_roe,
                "description": "最低ROE（%）"
            },
            "max_debt_ratio": {
                "type": "float",
                "default": self.max_debt_ratio,
                "description": "最高负债率（%）"
            },
            "min_gross_margin": {
                "type": "float",
                "default": self.min_gross_margin,
                "description": "最低毛利率（%）"
            },
            "min_safety_margin": {
                "type": "float",
                "default": 0,
                "description": "最低安全边际（%）"
            },
            "grade": {
                "type": "string",
                "default": "C",
                "description": "最低评级（A+/A/B/C/D）"
            }
        }
