"""
趋势投资策略（预留）
TODO: 待实现
"""
from app.services.strategies.base import StrategyBase
from typing import List, Dict, Any


class TrendInvestingStrategy(StrategyBase):
    """趋势投资策略（预留）"""
    
    def __init__(self, db):
        super().__init__(db)
    
    @property
    def name(self) -> str:
        return "trend"
    
    @property
    def display_name(self) -> str:
        return "📈 趋势投资"
    
    @property
    def description(self) -> str:
        return "趋势投资策略（预留，待实现）- 基于技术面和动量"
    
    def get_params_schema(self) -> List[Dict[str, Any]]:
        return []
    
    def filter_stocks(self, **kwargs) -> List[Dict]:
        raise NotImplementedError("趋势投资策略尚未实现")
