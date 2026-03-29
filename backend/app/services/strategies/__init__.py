"""
投资策略模块
"""
from app.services.strategies.base import StrategyBase
from app.services.strategies.value import ValueInvestingStrategy
from app.services.strategies.growth import GrowthInvestingStrategy
from app.services.strategies.trend import TrendInvestingStrategy

# 策略注册表
STRATEGY_REGISTRY = {
    "value": ValueInvestingStrategy,
    "growth": GrowthInvestingStrategy,
    "trend": TrendInvestingStrategy,
}

__all__ = ["StrategyBase", "ValueInvestingStrategy", "GrowthInvestingStrategy", "TrendInvestingStrategy", "STRATEGY_REGISTRY"]
