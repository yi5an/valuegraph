"""
投资策略抽象基类

所有投资策略必须继承此类并实现以下方法：
- screen(): 定量筛选（硬门槛）
- calculate_score(): 计算综合得分
- calculate_safety_margin(): 计算安全边际
- get_grade(): 根据得分获取评级
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """分析结果数据类"""

    # 基础信息
    stock_code: str
    name: str
    market: str

    # 策略信息
    strategy_name: str
    composite_score: float  # 综合得分（0-100）
    grade: str  # 推荐等级（A+/A/B/C/D）
    safety_margin: Optional[float]  # 安全边际（%）

    # 筛选结果
    passed_screening: bool  # 是否通过定量筛选
    screening_reasons: list  # 筛选失败原因

    # 详细得分（按维度）
    score_breakdown: Dict[str, float]

    # 推荐理由
    recommendation_reason: str

    # 财务指标（原样返回）
    financial_metrics: Dict[str, Any]


class StrategyBase(ABC):
    """投资策略抽象基类"""

    def __init__(self):
        self.name: str = "base"
        self.description: str = "基础策略"

    @abstractmethod
    def screen(self, financial_data: Dict[str, Any]) -> tuple[bool, list]:
        """
        定量筛选（硬门槛）

        Args:
            financial_data: 财务数据字典

        Returns:
            (是否通过, [失败原因列表])
        """
        pass

    @abstractmethod
    def calculate_score(self, financial_data: Dict[str, Any], stock_data: Dict[str, Any]) -> float:
        """
        计算综合得分

        Args:
            financial_data: 财务数据
            stock_data: 股票数据

        Returns:
            综合得分（0-100）
        """
        pass

    @abstractmethod
    def calculate_safety_margin(self, financial_data: Dict[str, Any], stock_data: Dict[str, Any]) -> Optional[float]:
        """
        计算安全边际

        Args:
            financial_data: 财务数据
            stock_data: 股票数据

        Returns:
            安全边际（%），如无数据返回 None
        """
        pass

    @abstractmethod
    def get_grade(self, score: float, safety_margin: Optional[float] = None) -> str:
        """
        根据得分和安全边际获取评级

        Args:
            score: 综合得分
            safety_margin: 安全边际

        Returns:
            评级（A+/A/B/C/D）
        """
        pass

    @abstractmethod
    def get_score_breakdown(self, financial_data: Dict[str, Any], stock_data: Dict[str, Any]) -> Dict[str, float]:
        """
        获取得分明细（按维度）

        Args:
            financial_data: 财务数据
            stock_data: 股票数据

        Returns:
            {维度名称: 得分}
        """
        pass

    @abstractmethod
    def generate_recommendation_reason(
        self,
        financial_data: Dict[str, Any],
        stock_data: Dict[str, Any],
        score: float,
        grade: str
    ) -> str:
        """
        生成推荐理由

        Args:
            financial_data: 财务数据
            stock_data: 股票数据
            score: 综合得分
            grade: 评级

        Returns:
            推荐理由文本
        """
        pass

    def get_params_info(self) -> Dict[str, Any]:
        """
        获取策略参数说明

        Returns:
            参数说明字典
        """
        return {
            "description": self.description,
            "min_roe": {"type": "float", "default": 15.0, "description": "最低ROE（%）"},
            "max_debt_ratio": {"type": "float", "default": 60.0, "description": "最高负债率（%）"},
        }

    def get_info(self) -> Dict[str, Any]:
        """
        获取策略完整信息

        Returns:
            策略信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "params": self.get_params_info()
        }

    def analyze(
        self,
        stock_code: str,
        name: str,
        market: str,
        financial_data: Dict[str, Any],
        stock_data: Dict[str, Any]
    ) -> AnalysisResult:
        """
        完整分析一只股票

        Args:
            stock_code: 股票代码
            name: 股票名称
            market: 市场
            financial_data: 财务数据
            stock_data: 股票数据

        Returns:
            AnalysisResult
        """
        # 1. 定量筛选
        passed_screening, screening_reasons = self.screen(financial_data)

        # 2. 计算得分
        composite_score = self.calculate_score(financial_data, stock_data) if passed_screening else 0

        # 3. 计算安全边际
        safety_margin = self.calculate_safety_margin(financial_data, stock_data) if passed_screening else None

        # 4. 获取评级
        grade = self.get_grade(composite_score, safety_margin) if passed_screening else "D"

        # 5. 获取得分明细
        score_breakdown = self.get_score_breakdown(financial_data, stock_data) if passed_screening else {}

        # 6. 生成推荐理由
        recommendation_reason = self.generate_recommendation_reason(
            financial_data, stock_data, composite_score, grade
        ) if passed_screening else "未通过定量筛选：" + "、".join(screening_reasons)

        return AnalysisResult(
            stock_code=stock_code,
            name=name,
            market=market,
            strategy_name=self.name,
            composite_score=round(composite_score, 2),
            grade=grade,
            safety_margin=round(safety_margin, 2) if safety_margin is not None else None,
            passed_screening=passed_screening,
            screening_reasons=screening_reasons,
            score_breakdown=score_breakdown,
            recommendation_reason=recommendation_reason,
            financial_metrics=financial_data
        )
