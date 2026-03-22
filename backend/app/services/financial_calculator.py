# services/financial_calculator.py
import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal

logger = logging.getLogger(__name__)


class FinancialCalculator:
    """财务指标计算服务"""
    
    @staticmethod
    def _safe_divide(numerator: Optional[float], denominator: Optional[float]) -> float:
        """安全除法，避免除零错误"""
        if numerator is None or denominator is None or denominator == 0:
            return 0.0
        try:
            return float(numerator) / float(denominator)
        except (TypeError, ValueError) as e:
            logger.warning(f"除法计算失败: {e}")
            return 0.0
    
    @staticmethod
    def calculate_roe(net_profit: Optional[float], equity: Optional[float]) -> float:
        """计算 ROE (Return on Equity, 净资产收益率)
        
        ROE = 净利润 / 股东权益 * 100
        
        Args:
            net_profit: 净利润
            equity: 股东权益
        
        Returns:
            ROE 百分比值
        """
        roe = FinancialCalculator._safe_divide(net_profit, equity) * 100
        logger.debug(f"计算 ROE: 净利润={net_profit}, 权益={equity}, ROE={roe:.2f}%")
        return round(roe, 2)
    
    @staticmethod
    def calculate_roa(net_profit: Optional[float], total_assets: Optional[float]) -> float:
        """计算 ROA (Return on Assets, 总资产收益率)
        
        ROA = 净利润 / 总资产 * 100
        
        Args:
            net_profit: 净利润
            total_assets: 总资产
        
        Returns:
            ROA 百分比值
        """
        roa = FinancialCalculator._safe_divide(net_profit, total_assets) * 100
        logger.debug(f"计算 ROA: 净利润={net_profit}, 总资产={total_assets}, ROA={roa:.2f}%")
        return round(roa, 2)
    
    @staticmethod
    def calculate_debt_ratio(total_liabilities: Optional[float], total_assets: Optional[float]) -> float:
        """计算资产负债率 (Debt Ratio)
        
        资产负债率 = 总负债 / 总资产 * 100
        
        Args:
            total_liabilities: 总负债
            total_assets: 总资产
        
        Returns:
            资产负债率百分比
        """
        ratio = FinancialCalculator._safe_divide(total_liabilities, total_assets) * 100
        logger.debug(f"计算资产负债率: 总负债={total_liabilities}, 总资产={total_assets}, 比率={ratio:.2f}%")
        return round(ratio, 2)
    
    @staticmethod
    def calculate_gross_margin(gross_profit: Optional[float], revenue: Optional[float]) -> float:
        """计算毛利率 (Gross Margin)
        
        毛利率 = 毛利润 / 营业收入 * 100
        
        Args:
            gross_profit: 毛利润
            revenue: 营业收入
        
        Returns:
            毛利率百分比
        """
        margin = FinancialCalculator._safe_divide(gross_profit, revenue) * 100
        logger.debug(f"计算毛利率: 毛利润={gross_profit}, 营业收入={revenue}, 毛利率={margin:.2f}%")
        return round(margin, 2)
    
    @staticmethod
    def calculate_current_ratio(current_assets: Optional[float], current_liabilities: Optional[float]) -> float:
        """计算流动比率 (Current Ratio)
        
        流动比率 = 流动资产 / 流动负债
        
        Args:
            current_assets: 流动资产
            current_liabilities: 流动负债
        
        Returns:
            流动比率
        """
        ratio = FinancialCalculator._safe_divide(current_assets, current_liabilities)
        logger.debug(f"计算流动比率: 流动资产={current_assets}, 流动负债={current_liabilities}, 比率={ratio:.2f}")
        return round(ratio, 2)
    
    @staticmethod
    def calculate_quick_ratio(
        current_assets: Optional[float], 
        inventory: Optional[float], 
        current_liabilities: Optional[float]
    ) -> float:
        """计算速动比率 (Quick Ratio)
        
        速动比率 = (流动资产 - 存货) / 流动负债
        
        Args:
            current_assets: 流动资产
            inventory: 存货
            current_liabilities: 流动负债
        
        Returns:
            速动比率
        """
        if current_assets is None or current_liabilities is None or current_liabilities == 0:
            return 0.0
        
        quick_assets = current_assets - (inventory or 0)
        ratio = FinancialCalculator._safe_divide(quick_assets, current_liabilities)
        logger.debug(f"计算速动比率: 流动资产={current_assets}, 存货={inventory}, 流动负债={current_liabilities}, 比率={ratio:.2f}")
        return round(ratio, 2)
    
    @staticmethod
    def calculate_free_cash_flow(operating_cf: Optional[float], investing_cf: Optional[float]) -> float:
        """计算自由现金流 (Free Cash Flow)
        
        FCF = 经营现金流 + 投资现金流
        
        注意: 投资现金流通常为负值
        
        Args:
            operating_cf: 经营活动现金流
            investing_cf: 投资活动现金流
        
        Returns:
            自由现金流
        """
        if operating_cf is None or investing_cf is None:
            return 0.0
        
        fcf = operating_cf + investing_cf
        logger.debug(f"计算自由现金流: 经营现金流={operating_cf}, 投资现金流={investing_cf}, FCF={fcf:.2f}")
        return round(fcf, 2)
    
    @staticmethod
    def calculate_operating_margin(operating_profit: Optional[float], revenue: Optional[float]) -> float:
        """计算营业利润率 (Operating Margin)
        
        营业利润率 = 营业利润 / 营业收入 * 100
        
        Args:
            operating_profit: 营业利润
            revenue: 营业收入
        
        Returns:
            营业利润率百分比
        """
        margin = FinancialCalculator._safe_divide(operating_profit, revenue) * 100
        logger.debug(f"计算营业利润率: 营业利润={operating_profit}, 营业收入={revenue}, 利润率={margin:.2f}%")
        return round(margin, 2)
    
    @staticmethod
    def calculate_net_margin(net_profit: Optional[float], revenue: Optional[float]) -> float:
        """计算净利率 (Net Profit Margin)
        
        净利率 = 净利润 / 营业收入 * 100
        
        Args:
            net_profit: 净利润
            revenue: 营业收入
        
        Returns:
            净利率百分比
        """
        margin = FinancialCalculator._safe_divide(net_profit, revenue) * 100
        logger.debug(f"计算净利率: 净利润={net_profit}, 营业收入={revenue}, 净利率={margin:.2f}%")
        return round(margin, 2)
    
    @staticmethod
    def calculate_eps(net_profit: Optional[float], total_shares: Optional[float]) -> float:
        """计算每股收益 (EPS, Earnings Per Share)
        
        EPS = 净利润 / 总股本
        
        Args:
            net_profit: 净利润
            total_shares: 总股本
        
        Returns:
            每股收益
        """
        eps = FinancialCalculator._safe_divide(net_profit, total_shares)
        logger.debug(f"计算 EPS: 净利润={net_profit}, 总股本={total_shares}, EPS={eps:.2f}")
        return round(eps, 2)
    
    @staticmethod
    def calculate_book_value_per_share(equity: Optional[float], total_shares: Optional[float]) -> float:
        """计算每股净资产 (Book Value Per Share)
        
        每股净资产 = 股东权益 / 总股本
        
        Args:
            equity: 股东权益
            total_shares: 总股本
        
        Returns:
            每股净资产
        """
        bvps = FinancialCalculator._safe_divide(equity, total_shares)
        logger.debug(f"计算每股净资产: 权益={equity}, 总股本={total_shares}, BVPS={bvps:.2f}")
        return round(bvps, 2)
    
    @staticmethod
    def calculate_all_metrics(
        balance_sheet: Dict[str, Any],
        income_statement: Dict[str, Any],
        cash_flow: Dict[str, Any]
    ) -> Dict[str, float]:
        """计算所有财务指标
        
        Args:
            balance_sheet: 资产负债表数据
            income_statement: 利润表数据
            cash_flow: 现金流量表数据
        
        Returns:
            包含所有财务指标的字典
        """
        metrics = {
            # 盈利能力指标
            'roe': FinancialCalculator.calculate_roe(
                income_statement.get('net_profit'),
                balance_sheet.get('total_equity')
            ),
            'roa': FinancialCalculator.calculate_roa(
                income_statement.get('net_profit'),
                balance_sheet.get('total_assets')
            ),
            'gross_margin': FinancialCalculator.calculate_gross_margin(
                income_statement.get('gross_profit'),
                income_statement.get('revenue')
            ),
            'operating_margin': FinancialCalculator.calculate_operating_margin(
                income_statement.get('operating_profit'),
                income_statement.get('revenue')
            ),
            'net_margin': FinancialCalculator.calculate_net_margin(
                income_statement.get('net_profit'),
                income_statement.get('revenue')
            ),
            
            # 偿债能力指标
            'debt_ratio': FinancialCalculator.calculate_debt_ratio(
                balance_sheet.get('total_liabilities'),
                balance_sheet.get('total_assets')
            ),
            'current_ratio': FinancialCalculator.calculate_current_ratio(
                balance_sheet.get('current_assets'),
                balance_sheet.get('current_liabilities')
            ),
            
            # 现金流指标
            'free_cash_flow': FinancialCalculator.calculate_free_cash_flow(
                cash_flow.get('operating_cash_flow'),
                cash_flow.get('investing_cash_flow')
            ),
        }
        
        logger.info(f"计算财务指标完成: {metrics}")
        return metrics
    
    @staticmethod
    def calculate_growth_rate(current_value: Optional[float], previous_value: Optional[float]) -> float:
        """计算增长率
        
        增长率 = (当前值 - 上期值) / abs(上期值) * 100
        
        Args:
            current_value: 当前值
            previous_value: 上期值
        
        Returns:
            增长率百分比
        """
        if current_value is None or previous_value is None or previous_value == 0:
            return 0.0
        
        growth = ((current_value - previous_value) / abs(previous_value)) * 100
        logger.debug(f"计算增长率: 当前={current_value}, 上期={previous_value}, 增长率={growth:.2f}%")
        return round(growth, 2)
    
    @staticmethod
    def calculate_cagr(
        beginning_value: Optional[float], 
        ending_value: Optional[float], 
        years: int
    ) -> float:
        """计算复合年增长率 (CAGR)
        
        CAGR = (结束值 / 起始值)^(1/年数) - 1
        
        Args:
            beginning_value: 起始值
            ending_value: 结束值
            years: 年数
        
        Returns:
            CAGR 百分比
        """
        if beginning_value is None or ending_value is None or beginning_value == 0 or years == 0:
            return 0.0
        
        if ending_value <= 0 or beginning_value <= 0:
            logger.warning(f"无法计算 CAGR: 起始值={beginning_value}, 结束值={ending_value}")
            return 0.0
        
        cagr = ((ending_value / beginning_value) ** (1 / years) - 1) * 100
        logger.debug(f"计算 CAGR: 起始={beginning_value}, 结束={ending_value}, 年数={years}, CAGR={cagr:.2f}%")
        return round(cagr, 2)
