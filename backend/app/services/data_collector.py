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
    def _detect_report_type(date_val) -> str:
        """根据报告期判断报告类型"""
        try:
            if hasattr(date_val, 'month'):
                month = date_val.month
            else:
                dt = pd.to_datetime(str(date_val))
                month = dt.month
            if month in (3, 4):
                return 'Q1'
            elif month in (6, 7, 8):
                return 'Q2'
            elif month in (9, 10):
                return 'Q3'
            else:
                return 'annual'
        except Exception:
            return 'annual'

    @staticmethod
    def _safe_float(val) -> Optional[float]:
        """安全转换为 float（支持百分比字符串如 '24.64%'）"""
        if val is None or val is False or (isinstance(val, float) and (pd.isna(val) or pd.isinf(val))):
            return None
        try:
            if isinstance(val, str):
                val = val.strip().replace('%', '').replace(',', '')
                if not val or val == '-':
                    return None
            return float(val)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def get_financial_data(stock_code: str) -> List[Dict]:
        """获取股票财务数据（同花顺数据源）"""
        sf = AkShareCollector._safe_float
        try:
            df = ak.stock_financial_abstract_ths(symbol=stock_code, indicator="按报告期")
            
            financials = []
            for _, row in df.iterrows():
                report_date = row.get('报告期', None)
                
                # 过滤异常日期
                if report_date is None:
                    continue
                try:
                    dt = pd.to_datetime(str(report_date))
                    if dt.year < 1990:
                        continue
                except Exception:
                    continue
                
                financials.append({
                    'stock_code': stock_code,
                    'report_date': report_date,
                    'report_type': AkShareCollector._detect_report_type(report_date),
                    'roe': sf(row.get('净资产收益率')),
                    'gross_margin': sf(row.get('销售毛利率')),
                    'debt_ratio': sf(row.get('资产负债率')),
                    'revenue': sf(row.get('营业总收入')),
                    'net_profit': sf(row.get('净利润')),
                    'eps': sf(row.get('基本每股收益')),
                    'bvps': sf(row.get('每股净资产')),
                    'operating_cash_flow': sf(row.get('每股经营现金流')),
                    'revenue_yoy': sf(row.get('营业总收入同比增长率')),
                    'net_profit_yoy': sf(row.get('净利润同比增长率')),
                })
            
            logger.info(f"✅ 获取 {stock_code} 财务数据成功（同花顺），共 {len(financials)} 条")
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
        sf = AkShareCollector._safe_float
        top_holders = []
        report_date = datetime.now().strftime('%Y-%m-%d')

        try:
            # 方案1: 使用 stock_main_stock_holder
            try:
                df = ak.stock_main_stock_holder(stock=stock_code)
                if df is not None and not df.empty:
                    for idx, row in df.head(10).iterrows():
                        top_holders.append({
                            'rank': idx + 1,
                            'holder_name': str(row.get('股东名称', '')),
                            'hold_amount': sf(row.get('持股数量')),
                            'hold_ratio': sf(row.get('持股比例')),
                            'holder_type': str(row.get('股本性质', '')),
                            'change': str(row.get('增减', '')),
                        })
                    # 获取报告日期
                    if '截至日期' in df.columns and len(df) > 0:
                        report_date = str(df.iloc[0].get('截至日期', report_date))
                    logger.info(f"✅ 获取 {stock_code} 股东信息成功 (main_stock_holder)")
            except Exception as e1:
                logger.warning(f"stock_main_stock_holder 失败: {e1}")

                # 方案2: 使用 stock_gdfx_top_10_em (需要 sh/sz 前缀)
                try:
                    # 添加前缀
                    prefix = 'sh' if stock_code.startswith('6') else 'sz'
                    symbol = f"{prefix}{stock_code}"

                    # 尝试最近几个季度的日期
                    dates_to_try = ['20241231', '20240930', '20240630', '20240331']
                    for date in dates_to_try:
                        try:
                            df = ak.stock_gdfx_top_10_em(symbol=symbol, date=date)
                            if df is not None and not df.empty:
                                for idx, row in df.iterrows():
                                    top_holders.append({
                                        'rank': int(row.get('名次', idx + 1)),
                                        'holder_name': str(row.get('股东名称', '')),
                                        'hold_amount': sf(row.get('持股数')),
                                        'hold_ratio': sf(row.get('占总股本持股比例')),
                                        'holder_type': str(row.get('股份类型', '')),
                                        'change': str(row.get('增减', '')),
                                    })
                                report_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
                                logger.info(f"✅ 获取 {stock_code} 股东信息成功 (top_10_em, date={date})")
                                break
                        except:
                            continue
                except Exception as e2:
                    logger.warning(f"stock_gdfx_top_10_em 失败: {e2}")

            return {
                'stock_code': stock_code,
                'report_date': report_date,
                'top_10_shareholders': top_holders,
                'institutional_holders': [],
                'holder_distribution': None,
            }

        except Exception as e:
            logger.error(f"❌ 获取 {stock_code} 股东信息失败: {e}")
            return {
                'stock_code': stock_code,
                'report_date': report_date,
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

    # ==================== 美股数据 ====================

    @staticmethod
    def get_us_stock_list() -> List[Dict]:
        """
        获取美股列表（使用知名美股数据，速度较快）

        Returns:
            股票列表，格式：[{'code': 'AAPL', 'name': '苹果', ...}]
        """
        try:
            stocks = []

            # 获取多类知名美股
            categories = ['科技类', '金融类', '医药类', '消费类']

            for category in categories:
                try:
                    df = ak.stock_us_famous_spot_em(symbol=category)
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            code_raw = str(row.get('代码', ''))
                            # 提取代码部分 (如 105.AAPL -> AAPL)
                            if '.' in code_raw:
                                code = code_raw.split('.')[-1]
                            else:
                                code = code_raw

                            stocks.append({
                                'stock_code': code,
                                'name': str(row.get('名称', '')),
                                'market': 'US',
                                'market_cap': row.get('总市值'),
                                'latest_pe': row.get('市盈率'),
                                'latest_price': row.get('最新价'),
                                'category': category,
                            })
                except Exception as e:
                    logger.warning(f"获取美股 {category} 失败: {e}")
                    continue

            # 去重
            seen = set()
            unique_stocks = []
            for s in stocks:
                if s['stock_code'] not in seen:
                    seen.add(s['stock_code'])
                    unique_stocks.append(s)

            logger.info(f"✅ 获取美股列表成功，共 {len(unique_stocks)} 只股票")
            return unique_stocks

        except Exception as e:
            logger.error(f"❌ 获取美股列表失败: {e}")
            return []

    @staticmethod
    def get_us_financial_data(symbol: str) -> Dict:
        """
        获取美股财务数据

        Args:
            symbol: 美股代码（如 AAPL, NVDA）

        Returns:
            财务数据字典
        """
        sf = AkShareCollector._safe_float
        try:
            result = {
                'symbol': symbol,
                'market': 'US',
                'valuation': None,
                'latest_data': None,
            }

            # 尝试获取估值数据
            try:
                df = ak.stock_us_valuation_baidu(symbol=symbol, indicator='总市值')
                if df is not None and not df.empty:
                    latest = df.iloc[-1]
                    result['valuation'] = {
                        'date': str(latest.get('date', '')),
                        'market_cap': sf(latest.get('value')),
                    }
            except Exception as e:
                logger.warning(f"获取美股 {symbol} 估值数据失败: {e}")

            # 尝试获取历史价格
            try:
                df_hist = ak.stock_us_hist(symbol=f"105.{symbol}", period="daily", adjust="qfq")
                if df_hist is not None and not df.empty:
                    latest = df_hist.iloc[-1]
                    result['latest_data'] = {
                        'date': str(latest.get('日期', '')),
                        'close': sf(latest.get('收盘')),
                        'volume': sf(latest.get('成交量')),
                    }
            except Exception as e:
                logger.warning(f"获取美股 {symbol} 历史数据失败: {e}")

            logger.info(f"✅ 获取美股 {symbol} 财务数据成功")
            return result

        except Exception as e:
            logger.error(f"❌ 获取美股 {symbol} 财务数据失败: {e}")
            return {'symbol': symbol, 'market': 'US', 'valuation': None, 'latest_data': None}

    @staticmethod
    def get_institutional_holders(stock_code: str) -> List[Dict]:
        """
        获取机构持仓数据（基金持仓）

        Args:
            stock_code: 股票代码（如 600519）

        Returns:
            机构持仓列表
        """
        sf = AkShareCollector._safe_float
        try:
            df = ak.stock_fund_stock_holder(symbol=stock_code)

            holders = []
            for _, row in df.head(20).iterrows():
                holders.append({
                    'fund_name': str(row.get('基金名称', '')),
                    'fund_code': str(row.get('基金代码', '')),
                    'hold_amount': sf(row.get('持仓数量')),
                    'hold_ratio': sf(row.get('占流通股比例')),
                    'hold_value': sf(row.get('持股市值')),
                    'net_value_ratio': sf(row.get('占净值比例')),
                    'report_date': str(row.get('截止日期', '')),
                })

            logger.info(f"✅ 获取 {stock_code} 机构持仓成功，共 {len(holders)} 条")
            return holders

        except Exception as e:
            logger.error(f"❌ 获取 {stock_code} 机构持仓失败: {e}")
            return []
