"""
市场数据统一接口
整合 Ashare (A股) + Finnhub (美股/港股)
"""
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd
import requests

# 导入 Ashare
from app.services.Ashare import get_price as ashare_get_price

class MarketDataProvider:
    """统一市场数据接口"""
    
    def __init__(self):
        self.finnhub_token = os.getenv('FINNHUB_API_KEY', '')
    
    # ==================== A股 (Ashare) ====================
    
    def get_a_stock_quote(self, symbol: str, frequency: str = '1d', count: int = 1) -> pd.DataFrame:
        """
        获取A股实时/历史行情
        
        Args:
            symbol: 股票代码 (如 '000001', 'sh600519', '000001.XSHG')
            frequency: '1d'日, '1w'周, '1M'月, '1m','5m','15m','30m','60m'
            count: 获取条数
        
        Returns:
            DataFrame with columns: open, close, high, low, volume
        """
        # 统一股票代码格式
        if '.' in symbol:
            # 聚宽格式 000001.XSHG -> sh000001
            code, exchange = symbol.split('.')
            if exchange == 'XSHG':
                symbol = f'sh{code}'
            elif exchange == 'XSHE':
                symbol = f'sz{code}'
        
        return ashare_get_price(symbol, frequency=frequency, count=count)
    
    def get_a_stock_realtime(self, symbol: str) -> Dict[str, Any]:
        """
        获取A股实时报价 (快照)
        
        Returns:
            {
                'symbol': '000001',
                'name': '平安银行',
                'price': 10.88,
                'change': 0.43,
                'change_percent': 4.11,
                'volume': 1622251,
                'timestamp': '2026-03-25 10:88:00'
            }
        """
        df = self.get_a_stock_quote(symbol, frequency='1d', count=1)
        if df.empty:
            return {}
        
        row = df.iloc[-1]
        return {
            'symbol': symbol,
            'price': row['close'],
            'open': row['open'],
            'high': row['high'],
            'low': row['low'],
            'volume': row['volume'],
            'timestamp': datetime.now().isoformat()
        }
    
    # ==================== 美股/港股 (Finnhub) ====================
    
    def _finnhub_request(self, endpoint: str, params: dict = None) -> dict:
        """Finnhub API 请求"""
        url = f"https://finnhub.io/api/v1/{endpoint}"
        query = {'token': self.finnhub_token}
        if params:
            query.update(params)
        
        resp = requests.get(url, params=query, timeout=10)
        resp.raise_for_status()
        return resp.json()
    
    def get_us_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取美股实时报价
        
        Args:
            symbol: 股票代码 (如 'AAPL', 'TSLA', 'GOOGL')
        
        Returns:
            {
                'symbol': 'AAPL',
                'price': 251.64,
                'change': 0.15,
                'change_percent': 0.0596,
                'high': 254.825,
                'low': 249.55,
                'open': 250.35,
                'previous_close': 251.49,
                'timestamp': 1774382400
            }
        """
        data = self._finnhub_request('quote', {'symbol': symbol})
        
        return {
            'symbol': symbol,
            'price': data.get('c', 0),
            'change': data.get('d'),
            'change_percent': data.get('dp'),
            'high': data.get('h', 0),
            'low': data.get('l', 0),
            'open': data.get('o', 0),
            'previous_close': data.get('pc', 0),
            'timestamp': data.get('t', 0)
        }
    
    def get_hk_stock_quote(self, symbol: str) -> Dict[str, Any]:
        """
        获取港股实时报价
        
        Args:
            symbol: 股票代码 (如 '0700.HK', '9988.HK')
        
        Returns:
            同美股格式
        """
        return self.get_us_stock_quote(symbol)
    
    def get_company_profile(self, symbol: str) -> Dict[str, Any]:
        """
        获取公司简介 (Finnhub)
        
        Returns:
            {
                'symbol': 'AAPL',
                'name': 'Apple Inc',
                'ticker': 'AAPL',
                'exchange': 'NASDAQ',
                'industry': 'Consumer Electronics',
                'country': 'US',
                'market_cap': 3000000000000,
                'shares_outstanding': 15000000000,
                'logo': 'https://...',
                'website': 'https://apple.com'
            }
        """
        return self._finnhub_request('stock/profile2', {'symbol': symbol})
    
    def get_company_financials(self, symbol: str, metric: str = 'all') -> Dict[str, Any]:
        """
        获取公司基本面数据 (Finnhub)
        
        Args:
            symbol: 股票代码
            metric: 'all', 'valuation', 'margin', 'price', 'growth', 'perShare'
        
        Returns:
            包含 PE, PB, PS, ROE 等指标
        """
        return self._finnhub_request('stock/metric', {'symbol': symbol, 'metric': metric})
    
    def get_company_news(self, symbol: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取公司相关新闻 (Finnhub)
        
        Args:
            symbol: 股票代码
            days: 过去几天
        
        Returns:
            [
                {
                    'headline': '...',
                    'summary': '...',
                    'source': 'Yahoo',
                    'url': 'https://...',
                    'datetime': 1774409580
                },
                ...
            ]
        """
        from datetime import datetime, timedelta
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        data = self._finnhub_request('company-news', {
            'symbol': symbol,
            'from': start_date,
            'to': end_date
        })
        
        return data
    
    # ==================== 通用接口 ====================
    
    def get_quote(self, symbol: str, market: str = 'auto') -> Dict[str, Any]:
        """
        通用获取报价接口，        
        Args:
            symbol: 股票代码
            market: 'a' (A股), 'us' (美股), 'hk' (港股), 'auto' (自动识别)
        
        Returns:
            报价信息
        """
        if market == 'auto':
            # 自动识别市场
            if symbol.endswith('.HK') or '.HK' in symbol:
                market = 'hk'
            elif '.' in symbol and symbol.split('.')[1] in ['XSHG', 'XSHE']:
                market = 'a'
            elif symbol.startswith(('sh', 'sz', 'SH', 'SZ')) or symbol.isdigit() and len(symbol) == 6:
                market = 'a'
            else:
                market = 'us'
        
        if market == 'a':
            return self.get_a_stock_realtime(symbol)
        elif market == 'us':
            return self.get_us_stock_quote(symbol)
        elif market == 'hk':
            return self.get_hk_stock_quote(symbol)
        else:
            raise ValueError(f"Unknown market: {market}")
    
    def search_stock(self, keyword: str, market: str = 'a') -> List[Dict[str, Any]]:
        """
        搜索股票
        
        Args:
            keyword: 搜索关键词 (股票名称或代码)
            market: 'a', 'us', 'hk'
        
        Returns:
            [
                {'symbol': '000001', 'name': '平安银行', 'market': 'a'},
                ...
            ]
        """
        # TODO: 实现搜索功能
        return []


# 使用示例
if __name__ == '__main__':
    provider = MarketDataProvider()
    
    # 测试A股
    print("=== A股测试 ===")
    df = provider.get_a_stock_quote('sh600519', frequency='1d', count=5)
    print("贵州茅台日线:")
    print(df)
    
    # 测试美股
    print("\n=== 美股测试 ===")
    quote = provider.get_us_stock_quote('AAPL')
    print("苹果报价:", quote)
    
    # 测试自动识别
    print("\n=== 自动识别测试 ===")
    print("000001.XSHG:", provider.get_quote('000001.XSHG'))
    print("AAPL:", provider.get_quote('AAPL'))
