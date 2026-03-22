# services/financial_statement.py
import tushare as ts
import akshare as ak
import pandas as pd
import logging
from typing import List, Dict, Any, Optional
from functools import lru_cache
import json

logger = logging.getLogger(__name__)


class FinancialStatementService:
    """财务报表数据获取服务"""
    
    def __init__(self, tushare_token: str):
        self.tushare = ts.pro_api(tushare_token)
        self._cache = {}
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清理数据中的 NaN 值"""
        if df.empty:
            return df
        # 将 NaN 替换为 None，以便后续转换为 dict 时不会出现 NaN
        return df.where(pd.notnull(df), None)
    
    def _convert_to_records(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """将 DataFrame 转换为字典列表"""
        if df.empty:
            return []
        df_clean = self._clean_data(df)
        records = df_clean.to_dict('records')
        # 转换日期格式
        for record in records:
            if 'end_date' in record and record['end_date']:
                record['end_date'] = str(record['end_date'])
            if 'ann_date' in record and record['ann_date']:
                record['ann_date'] = str(record['ann_date'])
        return records
    
    async def get_balance_sheet(
        self, 
        stock_code: str, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取资产负债表
        
        Args:
            stock_code: 股票代码 (例如: 000001.SZ)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
        
        Returns:
            资产负债表数据列表
        """
        cache_key = f"balance_sheet_{stock_code}_{start_date}_{end_date}"
        if cache_key in self._cache:
            logger.info(f"从缓存获取资产负债表: {stock_code}")
            return self._cache[cache_key]
        
        try:
            # 尝试从 Tushare 获取
            logger.info(f"从 Tushare 获取资产负债表: {stock_code}")
            df = self.tushare.balancesheet(
                ts_code=stock_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if not df.empty:
                records = self._convert_to_records(df)
                self._cache[cache_key] = records
                logger.info(f"成功从 Tushare 获取 {len(records)} 条资产负债表数据")
                return records
            
            # 降级到 AkShare
            logger.info(f"Tushare 无数据，降级到 AkShare: {stock_code}")
            # AkShare 使用不带后缀的股票代码
            symbol = stock_code.split('.')[0]
            df = ak.stock_balance_sheet_by_report_em(symbol=symbol)
            
            if not df.empty:
                # 标准化 AkShare 的字段名
                df = self._standardize_akshare_balance_sheet(df, stock_code)
                records = self._convert_to_records(df)
                self._cache[cache_key] = records
                logger.info(f"成功从 AkShare 获取 {len(records)} 条资产负债表数据")
                return records
            
            logger.warning(f"未找到资产负债表数据: {stock_code}")
            return []
            
        except Exception as e:
            logger.error(f"获取资产负债表失败 {stock_code}: {e}", exc_info=True)
            return []
    
    async def get_income_statement(
        self, 
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取利润表
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
        
        Returns:
            利润表数据列表
        """
        cache_key = f"income_statement_{stock_code}_{start_date}_{end_date}"
        if cache_key in self._cache:
            logger.info(f"从缓存获取利润表: {stock_code}")
            return self._cache[cache_key]
        
        try:
            # 尝试从 Tushare 获取
            logger.info(f"从 Tushare 获取利润表: {stock_code}")
            df = self.tushare.income(
                ts_code=stock_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if not df.empty:
                records = self._convert_to_records(df)
                self._cache[cache_key] = records
                logger.info(f"成功从 Tushare 获取 {len(records)} 条利润表数据")
                return records
            
            # 降级到 AkShare
            logger.info(f"Tushare 无数据，降级到 AkShare: {stock_code}")
            symbol = stock_code.split('.')[0]
            df = ak.stock_profit_sheet_by_report_em(symbol=symbol)
            
            if not df.empty:
                df = self._standardize_akshare_income_statement(df, stock_code)
                records = self._convert_to_records(df)
                self._cache[cache_key] = records
                logger.info(f"成功从 AkShare 获取 {len(records)} 条利润表数据")
                return records
            
            logger.warning(f"未找到利润表数据: {stock_code}")
            return []
            
        except Exception as e:
            logger.error(f"获取利润表失败 {stock_code}: {e}", exc_info=True)
            return []
    
    async def get_cash_flow_statement(
        self, 
        stock_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取现金流量表
        
        Args:
            stock_code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
        
        Returns:
            现金流量表数据列表
        """
        cache_key = f"cash_flow_{stock_code}_{start_date}_{end_date}"
        if cache_key in self._cache:
            logger.info(f"从缓存获取现金流量表: {stock_code}")
            return self._cache[cache_key]
        
        try:
            # 尝试从 Tushare 获取
            logger.info(f"从 Tushare 获取现金流量表: {stock_code}")
            df = self.tushare.cashflow(
                ts_code=stock_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if not df.empty:
                records = self._convert_to_records(df)
                self._cache[cache_key] = records
                logger.info(f"成功从 Tushare 获取 {len(records)} 条现金流量表数据")
                return records
            
            # 降级到 AkShare
            logger.info(f"Tushare 无数据，降级到 AkShare: {stock_code}")
            symbol = stock_code.split('.')[0]
            df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)
            
            if not df.empty:
                df = self._standardize_akshare_cash_flow(df, stock_code)
                records = self._convert_to_records(df)
                self._cache[cache_key] = records
                logger.info(f"成功从 AkShare 获取 {len(records)} 条现金流量表数据")
                return records
            
            logger.warning(f"未找到现金流量表数据: {stock_code}")
            return []
            
        except Exception as e:
            logger.error(f"获取现金流量表失败 {stock_code}: {e}", exc_info=True)
            return []
    
    def _standardize_akshare_balance_sheet(self, df: pd.DataFrame, ts_code: str) -> pd.DataFrame:
        """标准化 AkShare 资产负债表字段"""
        # AkShare 字段映射到标准字段
        field_mapping = {
            '报告期': 'end_date',
            '总资产': 'total_assets',
            '总负债': 'total_liabilities',
            '所有者权益': 'total_equity',
            '流动资产': 'current_assets',
            '流动负债': 'current_liabilities'
        }
        
        df = df.rename(columns=field_mapping)
        df['ts_code'] = ts_code
        
        return df
    
    def _standardize_akshare_income_statement(self, df: pd.DataFrame, ts_code: str) -> pd.DataFrame:
        """标准化 AkShare 利润表字段"""
        field_mapping = {
            '报告期': 'end_date',
            '营业总收入': 'revenue',
            '净利润': 'net_profit',
            '毛利润': 'gross_profit',
            '营业利润': 'operating_profit'
        }
        
        df = df.rename(columns=field_mapping)
        df['ts_code'] = ts_code
        
        return df
    
    def _standardize_akshare_cash_flow(self, df: pd.DataFrame, ts_code: str) -> pd.DataFrame:
        """标准化 AkShare 现金流量表字段"""
        field_mapping = {
            '报告期': 'end_date',
            '经营活动产生的现金流量净额': 'operating_cash_flow',
            '投资活动产生的现金流量净额': 'investing_cash_flow',
            '筹资活动产生的现金流量净额': 'financing_cash_flow'
        }
        
        df = df.rename(columns=field_mapping)
        df['ts_code'] = ts_code
        
        # 计算自由现金流
        if 'operating_cash_flow' in df.columns and 'investing_cash_flow' in df.columns:
            df['free_cash_flow'] = df['operating_cash_flow'] + df['investing_cash_flow']
        
        return df
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        logger.info("缓存已清除")
