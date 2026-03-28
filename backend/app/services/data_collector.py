"""
数据采集服务
使用 AkShare 获取股票数据
"""
import akshare as ak
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AkShareCollector:
    """AkShare 数据采集器"""
    
    @staticmethod
    def get_a_stock_list() -> List[Dict]:
        """
        获取 A 股股票列表
        
        Returns:
            股票列表，格式：[{'code': '600519', 'name': '贵州茅台', ...}]
        """
        try:
            # 获取 A 股实时行情数据
            df = ak.stock_zh_a_spot_em()
            
            # 转换为字典列表
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'stock_code': row['代码'],
                    'name': row['名称'],
                    'market': 'A',
                    'market_cap': row.get('总市值', None),
                    'latest_pe': row.get('市盈率-动态', None),
                })
            
            logger.info(f"✅ 获取 A 股列表成功，共 {len(stocks)} 只股票")
            return stocks
        
        except Exception as e:
            logger.error(f"❌ 获取 A 股列表失败: {e}")
            return []
    
    @staticmethod
    def get_financial_data(stock_code: str) -> List[Dict]:
        """
        获取股票财务数据
        
        Args:
            stock_code: 股票代码（如 600519）
        
        Returns:
            财务数据列表
        """
        try:
            # 获取财务分析指标
            df = ak.stock_financial_analysis_indicator(symbol=stock_code)
            
            # 转换为字典列表
            financials = []
            for _, row in df.iterrows():
                financials.append({
                    'stock_code': stock_code,
                    'report_date': row.get('日期', None),
                    'report_type': 'annual',  # 默认年报
                    'roe': row.get('净资产收益率', None),
                    'gross_margin': row.get('销售毛利率', None),
                    'debt_ratio': row.get('资产负债率', None),
                    'revenue': row.get('营业收入', None),
                    'net_profit': row.get('净利润', None),
                    'eps': row.get('每股收益', None),
                })
            
            logger.info(f"✅ 获取 {stock_code} 财务数据成功，共 {len(financials)} 条")
            return financials
        
        except Exception as e:
            logger.error(f"❌ 获取 {stock_code} 财务数据失败: {e}")
            return []
    
    @staticmethod
    def get_shareholders(stock_code: str) -> Dict:
        """
        获取股东信息
        
        Args:
            stock_code: 股票代码（如 600519）
        
        Returns:
            股东信息字典
        """
        try:
            # 获取十大股东
            df_holders = ak.stock_gdfx_holding_teamwork_em(symbol=stock_code)
            
            # 解析十大股东
            top_holders = []
            for idx, row in df_holders.head(10).iterrows():
                top_holders.append({
                    'rank': idx + 1,
                    'holder_name': row.get('股东名称', ''),
                    'hold_amount': row.get('持股数', None),
                    'hold_ratio': row.get('持股比例', None),
                    'holder_type': row.get('股东性质', ''),
                    'change': row.get('增减', ''),
                })
            
            logger.info(f"✅ 获取 {stock_code} 股东信息成功")
            
            return {
                'stock_code': stock_code,
                'report_date': datetime.now().strftime('%Y-%m-%d'),
                'top_10_shareholders': top_holders,
                'institutional_holders': [],  # 需要额外接口
                'holder_distribution': None,
            }
        
        except Exception as e:
            logger.error(f"❌ 获取 {stock_code} 股东信息失败: {e}")
            return {
                'stock_code': stock_code,
                'report_date': datetime.now().strftime('%Y-%m-%d'),
                'top_10_shareholders': [],
                'institutional_holders': [],
                'holder_distribution': None,
            }
    
    @staticmethod
    def get_financial_indicator(stock_code: str) -> Optional[Dict]:
        """
        获取最新财务指标（用于推荐）
        
        Args:
            stock_code: 股票代码
        
        Returns:
            最新财务指标
        """
        try:
            financials = AkShareCollector.get_financial_data(stock_code)
            if financials:
                # 返回最新一条
                return financials[0]
            return None
        except Exception as e:
            logger.error(f"❌ 获取 {stock_code} 财务指标失败: {e}")
            return None
