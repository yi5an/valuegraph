# stock_service.py
from typing import List, Dict, Any
import asyncio
from .akshare_adapter import AkShareAdapter


class StockService:
    """股票业务逻辑服务"""
    
    def __init__(self):
        self.data_source = AkShareAdapter()
    
    async def get_value_stocks(
        self, 
        market: str, 
        top_n: int = 10,
        min_roe: float = 15.0,
        max_debt_ratio: float = 50.0
    ) -> List[Dict[str, Any]]:
        """获取价值股票推荐
        
        筛选标准：
        - ROE > min_roe（默认 15%）
        - 负债率 < max_debt_ratio（默认 50%）
        
        Args:
            market: 市场类型
            top_n: 返回数量
            min_roe: 最低 ROE 要求
            max_debt_ratio: 最高负债率要求
        
        Returns:
            符合条件的价值股票列表
        """
        # 1. 获取股票列表
        stocks = await self.data_source.get_stock_list(market)
        
        if not stocks:
            print("⚠️  未获取到股票列表")
            return []
        
        print(f"📊 获取到 {len(stocks)} 只股票，开始筛选...")
        
        # 2. 获取每只股票的财务数据并筛选
        value_stocks = []
        
        # 限制并发数量（避免 API 频率限制）
        semaphore = asyncio.Semaphore(5)
        
        async def process_stock(stock: Dict[str, Any]) -> Dict[str, Any] | None:
            """处理单只股票"""
            async with semaphore:
                try:
                    # 获取股票代码（字段名可能是 '代码' 或 'code'）
                    stock_code = stock.get('代码') or stock.get('code')
                    
                    if not stock_code:
                        return None
                    
                    # 获取财务数据
                    financial_data = await self.data_source.get_financial_data(stock_code)
                    
                    # 应用价值筛选标准
                    roe = financial_data.get('roe', 0)
                    debt_ratio = financial_data.get('debt_ratio', 100)
                    
                    if roe >= min_roe and debt_ratio <= max_debt_ratio:
                        # 计算评分（简单加权）
                        score = roe * 0.5 + (100 - debt_ratio) * 0.5
                        
                        return {
                            **stock,
                            'roe': roe,
                            'debt_ratio': debt_ratio,
                            'net_profit_growth': financial_data.get('net_profit_growth', 0),
                            'gross_margin': financial_data.get('gross_margin', 0),
                            'score': score
                        }
                    
                    return None
                except Exception as e:
                    print(f"⚠️  处理股票 {stock.get('代码', 'unknown')} 失败: {e}")
                    return None
        
        # 批量处理（限制为前 50 只，避免 API 频率限制）
        tasks = [process_stock(stock) for stock in stocks[:50]]
        results = await asyncio.gather(*tasks)
        
        # 过滤掉 None 结果
        value_stocks = [r for r in results if r is not None]
        
        print(f"✅ 筛选完成，共 {len(value_stocks)} 只股票符合条件")
        
        # 3. 按评分排序，返回 Top N
        value_stocks.sort(key=lambda x: x['score'], reverse=True)
        return value_stocks[:top_n]
    
    async def get_stock_detail(self, stock_code: str) -> Dict[str, Any]:
        """获取股票详情
        
        Args:
            stock_code: 股票代码
        
        Returns:
            股票详情信息
        """
        # 并发获取财务数据和股东信息
        financial_task = self.data_source.get_financial_data(stock_code)
        shareholders_task = self.data_source.get_shareholders(stock_code)
        
        financial_data, shareholders = await asyncio.gather(
            financial_task,
            shareholders_task
        )
        
        return {
            'stock_code': stock_code,
            'financial_data': financial_data,
            'shareholders': shareholders
        }
