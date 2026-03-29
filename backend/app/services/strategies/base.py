"""
策略基类 - 所有投资策略的抽象基类
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session


class StrategyBase(ABC):
    """投资策略抽象基类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """策略显示名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """策略描述"""
        pass
    
    @abstractmethod
    def filter_stocks(
        self,
        market: str = "A",
        limit: int = 20,
        **kwargs
    ) -> List[Dict]:
        """
        筛选和评分股票
        
        Args:
            market: 市场
            limit: 返回数量
            **kwargs: 策略特定参数
            
        Returns:
            推荐股票列表
        """
        pass
    
    @abstractmethod
    def get_params_schema(self) -> List[Dict[str, Any]]:
        """
        获取策略参数说明
        
        Returns:
            参数列表，每个参数包含 name, type, default, description
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """获取策略完整信息"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "params": self.get_params_schema(),
        }
