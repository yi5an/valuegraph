# data_source.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class DataSourceAdapter(ABC):
    """数据源适配器抽象基类"""
    
    @abstractmethod
    async def get_stock_list(self, market: str) -> List[Dict[str, Any]]:
        """获取股票列表
        
        Args:
            market: 市场类型 (a-share, us-market 等)
        
        Returns:
            股票列表，每个股票包含代码、名称等信息
        """
        pass
    
    @abstractmethod
    async def get_financial_data(self, stock_code: str) -> Dict[str, Any]:
        """获取财务数据
        
        Args:
            stock_code: 股票代码
        
        Returns:
            财务数据字典，包含 ROE、ROA、毛利率、负债率等
        """
        pass
    
    @abstractmethod
    async def get_shareholders(self, stock_code: str) -> List[Dict[str, Any]]:
        """获取股东信息
        
        Args:
            stock_code: 股票代码
        
        Returns:
            股东列表，包含股东名称、持股比例等
        """
        pass
