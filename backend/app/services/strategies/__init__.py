"""
投资策略模块

支持多种投资策略：
- value: 价值投资策略（Graham + 巴菲特理念）
- growth: 成长投资策略（预留）
- trend: 趋势投资策略（预留）
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


def get_strategy(strategy_name: str) -> StrategyBase:
    """
    获取策略实例

    Args:
        strategy_name: 策略名称（value/growth/trend）

    Returns:
        策略实例

    Raises:
        ValueError: 策略不存在
    """
    strategy_class = STRATEGY_REGISTRY.get(strategy_name)
    if not strategy_class:
        raise ValueError(f"未知策略: {strategy_name}，可用策略: {list(STRATEGY_REGISTRY.keys())}")

    return strategy_class()


def list_strategies() -> dict:
    """
    列出所有可用策略及其描述

    Returns:
        策略列表 {name: {description, params}}
    """
    strategies = {}
    for name, strategy_class in STRATEGY_REGISTRY.items():
        strategy = strategy_class()
        strategies[name] = {
            "name": strategy.name,
            "description": strategy.description,
            "params": strategy.get_params_info(),
        }
    return strategies


__all__ = [
    "StrategyBase",
    "ValueInvestingStrategy",
    "GrowthInvestingStrategy",
    "TrendInvestingStrategy",
    "get_strategy",
    "list_strategies",
    "STRATEGY_REGISTRY"
]
