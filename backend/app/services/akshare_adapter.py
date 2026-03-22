# akshare_adapter.py
import akshare as ak
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .data_source import DataSourceAdapter


class AkShareAdapter(DataSourceAdapter):
    """AkShare 数据源适配器"""
    
    def __init__(self):
        """初始化适配器，设置缓存"""
        self._financial_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 3600  # 缓存 1 小时
    
    async def get_stock_list(self, market: str) -> List[Dict[str, Any]]:
        """获取 A 股股票列表
        
        Args:
            market: 市场类型
        
        Returns:
            股票列表
        """
        try:
            # 在线程池中执行同步调用，避免阻塞
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, ak.stock_zh_a_spot_em)
            
            stocks = df.to_dict('records')
            
            # 限制返回数量（避免数据过多）
            return stocks[:100]
        except Exception as e:
            print(f"❌ 获取股票列表失败: {e}")
            return []
    
    async def get_financial_data(self, stock_code: str) -> Dict[str, Any]:
        """获取财务数据（ROE/ROA/毛利率等）
        
        优先级：
        1. 使用 stock_financial_analysis_indicator（直接返回指标）
        2. 降级到 stock_financial_report_sina（从财务报表计算）
        
        Args:
            stock_code: 股票代码
        
        Returns:
            财务数据字典
        """
        # 检查缓存
        cache_key = f"financial_{stock_code}"
        cached = self._get_from_cache(cache_key)
        if cached:
            print(f"✓ 使用缓存数据 [{stock_code}]")
            return cached
        
        # 尝试方法1: 直接获取财务指标
        result = await self._get_financial_from_indicator(stock_code)
        
        # 如果方法1失败，降级到方法2: 从财务报表计算
        if not result or result.get('roe', 0) == 0:
            print(f"⚠ 指标接口失败，降级到报表接口 [{stock_code}]")
            result = await self._get_financial_from_reports(stock_code)
        
        # 如果仍然失败，返回默认值
        if not result:
            result = {
                'stock_code': stock_code,
                'roe': 0,
                'roa': 0,
                'gross_margin': 0,
                'debt_ratio': 100,
                'net_profit_growth': 0,
                'revenue_growth': 0,
                'error': '无法获取财务数据'
            }
        else:
            result['stock_code'] = stock_code
        
        # 存入缓存
        self._save_to_cache(cache_key, result)
        
        return result
    
    async def _get_financial_from_indicator(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """从财务指标接口获取数据
        
        Args:
            stock_code: 股票代码
        
        Returns:
            财务数据字典或 None
        """
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_financial_analysis_indicator(symbol=stock_code)
            )
            
            if df.empty:
                return None
            
            # 获取最新一期数据
            latest = df.iloc[0]
            
            # 提取关键财务指标
            # 注意：不同版本的 AkShare 字段名可能不同
            result = {
                'roe': self._safe_float(latest.get('净资产收益率', 0)),
                'roa': self._safe_float(latest.get('总资产净利率', 0)),
                'gross_margin': self._safe_float(latest.get('销售毛利率', 0)),
                'debt_ratio': self._safe_float(latest.get('资产负债率', 100)),
                'net_profit_growth': self._safe_float(latest.get('净利润增长率', 0)),
                'revenue_growth': self._safe_float(latest.get('营业收入增长率', 0)),
            }
            
            # 如果关键字段为 0，尝试其他字段名
            if result['roe'] == 0:
                result['roe'] = self._safe_float(latest.get('roe', 0))
            if result['roa'] == 0:
                result['roa'] = self._safe_float(latest.get('roa', 0))
            if result['debt_ratio'] == 100:
                result['debt_ratio'] = self._safe_float(latest.get('资产负债率(%)', 100))
            
            print(f"✓ 指标接口成功 [{stock_code}]: ROE={result['roe']:.2f}%, 负债率={result['debt_ratio']:.2f}%")
            return result
            
        except Exception as e:
            print(f"⚠ 指标接口失败 [{stock_code}]: {e}")
            return None
    
    async def _get_financial_from_reports(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """从财务报表计算财务指标
        
        Args:
            stock_code: 股票代码
        
        Returns:
            财务数据字典或 None
        """
        try:
            loop = asyncio.get_event_loop()
            
            # 并发获取资产负债表和利润表
            balance_task = loop.run_in_executor(
                None,
                lambda: ak.stock_financial_report_sina(stock=stock_code, symbol='资产负债表')
            )
            profit_task = loop.run_in_executor(
                None,
                lambda: ak.stock_financial_report_sina(stock=stock_code, symbol='利润表')
            )
            
            df_balance, df_profit = await asyncio.gather(balance_task, profit_task)
            
            if df_balance.empty or df_profit.empty:
                return None
            
            # 获取最新一期数据
            latest_balance = df_balance.iloc[0]
            latest_profit = df_profit.iloc[0]
            
            # 提取关键财务数据
            total_assets = self._safe_float(latest_balance.get('资产总计', 0))
            total_liabilities = self._safe_float(latest_balance.get('负债合计', 0))
            equity = self._safe_float(latest_balance.get('所有者权益(或股东权益)合计', 0))
            
            net_profit = self._safe_float(latest_profit.get('归属于母公司所有者的净利润', 0))
            revenue = self._safe_float(latest_profit.get('营业收入', 0))
            operating_cost = self._safe_float(latest_profit.get('营业成本', 0))
            
            # 计算财务指标
            result = {
                'roe': 0.0,
                'roa': 0.0,
                'gross_margin': 0.0,
                'debt_ratio': 100.0,
                'net_profit_growth': 0.0,
                'revenue_growth': 0.0,
            }
            
            # 计算资产负债率
            if total_assets > 0:
                result['debt_ratio'] = (total_liabilities / total_assets) * 100
            
            # 计算 ROE（净资产收益率）
            if equity > 0:
                result['roe'] = (net_profit / equity) * 100
            
            # 计算 ROA（总资产收益率）
            if total_assets > 0:
                result['roa'] = (net_profit / total_assets) * 100
            
            # 计算毛利率
            if revenue > 0:
                result['gross_margin'] = ((revenue - operating_cost) / revenue) * 100
            
            print(f"✓ 报表接口成功 [{stock_code}]: ROE={result['roe']:.2f}%, 负债率={result['debt_ratio']:.2f}%, 毛利率={result['gross_margin']:.2f}%")
            return result
            
        except Exception as e:
            print(f"❌ 报表接口失败 [{stock_code}]: {e}")
            return None
    
    async def get_shareholders(self, stock_code: str) -> List[Dict[str, Any]]:
        """获取十大股东
        
        Args:
            stock_code: 股票代码
        
        Returns:
            股东列表
        """
        try:
            # 在线程池中执行同步调用
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_main_stock_holder(stock=stock_code)
            )
            
            shareholders = df.to_dict('records')
            
            # 返回前 10 个股东
            return shareholders[:10]
        except Exception as e:
            print(f"❌ 获取股东信息失败 [{stock_code}]: {e}")
            return []
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据
        
        Args:
            key: 缓存键
        
        Returns:
            缓存数据或 None
        """
        if key not in self._financial_cache:
            return None
        
        cached_item = self._financial_cache[key]
        if datetime.now() - cached_item['timestamp'] > timedelta(seconds=self._cache_ttl):
            # 缓存过期
            del self._financial_cache[key]
            return None
        
        return cached_item['data']
    
    def _save_to_cache(self, key: str, data: Dict[str, Any]):
        """保存数据到缓存
        
        Args:
            key: 缓存键
            data: 要缓存的数据
        """
        self._financial_cache[key] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    @staticmethod
    def _safe_float(value: Any) -> float:
        """安全转换为浮点数
        
        Args:
            value: 任意类型的值
        
        Returns:
            浮点数
        """
        try:
            if value is None or value == '' or value == '-':
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
