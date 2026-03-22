# tests/test_financial_services.py
import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from app.services.financial_calculator import FinancialCalculator
from app.services.anomaly_detector import AnomalyDetector


class TestFinancialCalculator:
    """测试财务指标计算"""
    
    def test_calculate_roe(self):
        """测试 ROE 计算"""
        # 正常情况
        roe = FinancialCalculator.calculate_roe(1000, 5000)
        assert roe == 20.0
        
        # 权益为 0
        roe = FinancialCalculator.calculate_roe(1000, 0)
        assert roe == 0.0
        
        # 权益为 None
        roe = FinancialCalculator.calculate_roe(1000, None)
        assert roe == 0.0
        
        # 净利润为负
        roe = FinancialCalculator.calculate_roe(-500, 5000)
        assert roe == -10.0
    
    def test_calculate_roa(self):
        """测试 ROA 计算"""
        # 正常情况
        roa = FinancialCalculator.calculate_roa(1000, 10000)
        assert roa == 10.0
        
        # 总资产为 0
        roa = FinancialCalculator.calculate_roa(1000, 0)
        assert roa == 0.0
    
    def test_calculate_debt_ratio(self):
        """测试资产负债率计算"""
        # 正常情况
        ratio = FinancialCalculator.calculate_debt_ratio(6000, 10000)
        assert ratio == 60.0
        
        # 总资产为 0
        ratio = FinancialCalculator.calculate_debt_ratio(6000, 0)
        assert ratio == 0.0
    
    def test_calculate_gross_margin(self):
        """测试毛利率计算"""
        # 正常情况
        margin = FinancialCalculator.calculate_gross_margin(4000, 10000)
        assert margin == 40.0
        
        # 营业收入为 0
        margin = FinancialCalculator.calculate_gross_margin(4000, 0)
        assert margin == 0.0
    
    def test_calculate_current_ratio(self):
        """测试流动比率计算"""
        # 正常情况
        ratio = FinancialCalculator.calculate_current_ratio(2000, 1000)
        assert ratio == 2.0
        
        # 流动负债为 0
        ratio = FinancialCalculator.calculate_current_ratio(2000, 0)
        assert ratio == 0.0
    
    def test_calculate_free_cash_flow(self):
        """测试自由现金流计算"""
        # 正常情况（投资现金流通常为负）
        fcf = FinancialCalculator.calculate_free_cash_flow(5000, -2000)
        assert fcf == 3000.0
        
        # 都为正值
        fcf = FinancialCalculator.calculate_free_cash_flow(5000, 2000)
        assert fcf == 7000.0
    
    def test_calculate_operating_margin(self):
        """测试营业利润率计算"""
        margin = FinancialCalculator.calculate_operating_margin(1500, 10000)
        assert margin == 15.0
    
    def test_calculate_net_margin(self):
        """测试净利率计算"""
        margin = FinancialCalculator.calculate_net_margin(800, 10000)
        assert margin == 8.0
    
    def test_calculate_growth_rate(self):
        """测试增长率计算"""
        # 正常增长
        growth = FinancialCalculator.calculate_growth_rate(1200, 1000)
        assert growth == 20.0
        
        # 下降
        growth = FinancialCalculator.calculate_growth_rate(800, 1000)
        assert growth == -20.0
        
        # 上期为 0
        growth = FinancialCalculator.calculate_growth_rate(1000, 0)
        assert growth == 0.0
    
    def test_calculate_cagr(self):
        """测试复合年增长率计算"""
        # 5 年从 100 增长到 200
        cagr = FinancialCalculator.calculate_cagr(100, 200, 5)
        assert round(cagr, 2) == 14.87  # (200/100)^(1/5) - 1 ≈ 14.87%
        
        # 年数为 0
        cagr = FinancialCalculator.calculate_cagr(100, 200, 0)
        assert cagr == 0.0
    
    def test_calculate_all_metrics(self):
        """测试计算所有指标"""
        balance_sheet = {
            'total_assets': 10000,
            'total_liabilities': 6000,
            'total_equity': 4000,
            'current_assets': 3000,
            'current_liabilities': 2000
        }
        income_statement = {
            'revenue': 10000,
            'net_profit': 1000,
            'gross_profit': 4000,
            'operating_profit': 1500
        }
        cash_flow = {
            'operating_cash_flow': 5000,
            'investing_cash_flow': -2000
        }
        
        metrics = FinancialCalculator.calculate_all_metrics(
            balance_sheet, income_statement, cash_flow
        )
        
        assert metrics['roe'] == 25.0
        assert metrics['roa'] == 10.0
        assert metrics['debt_ratio'] == 60.0
        assert metrics['gross_margin'] == 40.0
        assert metrics['current_ratio'] == 1.5
        assert metrics['free_cash_flow'] == 3000.0


class TestAnomalyDetector:
    """测试异常检测"""
    
    def test_detect_outliers(self):
        """测试异常值检测"""
        # 正常数据（无异常）
        normal_data = [
            {'ts_code': '000001.SZ', 'value': 100},
            {'ts_code': '000001.SZ', 'value': 102},
            {'ts_code': '000001.SZ', 'value': 98},
            {'ts_code': '000001.SZ', 'value': 101},
            {'ts_code': '000001.SZ', 'value': 99},
        ]
        outliers = AnomalyDetector.detect_outliers(normal_data, 'value')
        assert len(outliers) == 0
        
        # 包含异常值 - 使用更极端的异常值
        data_with_outlier = [
            {'ts_code': '000001.SZ', 'value': 100},
            {'ts_code': '000001.SZ', 'value': 102},
            {'ts_code': '000001.SZ', 'value': 98},
            {'ts_code': '000001.SZ', 'value': 1010},  # 极端异常值
            {'ts_code': '000001.SZ', 'value': 99},
            {'ts_code': '000001.SZ', 'value': 103},
            {'ts_code': '000001.SZ', 'value': 97},
        ]
        outliers = AnomalyDetector.detect_outliers(data_with_outlier, 'value', threshold=2.0)
        assert len(outliers) > 0
        # 验证异常值被识别
        outlier_values = [o['value'] for o in outliers]
        assert 1010 in outlier_values
        assert 'z_score' in outliers[0]
    
    def test_detect_outliers_insufficient_data(self):
        """测试数据量不足时的情况"""
        # 少于 3 个数据点
        small_data = [
            {'ts_code': '000001.SZ', 'value': 100},
            {'ts_code': '000001.SZ', 'value': 200},
        ]
        outliers = AnomalyDetector.detect_outliers(small_data, 'value')
        assert len(outliers) == 0
    
    def test_detect_missing_data(self):
        """测试缺失数据检测"""
        # 连续的季度数据（无缺失）
        continuous_data = [
            {'ts_code': '000001.SZ', 'end_date': '20231231'},
            {'ts_code': '000001.SZ', 'end_date': '20230930'},
            {'ts_code': '000001.SZ', 'end_date': '20230630'},
            {'ts_code': '000001.SZ', 'end_date': '20230331'},
        ]
        missing = AnomalyDetector.detect_missing_data(continuous_data)
        assert len(missing) == 0
        
        # 有缺失的数据（缺失 2023Q2）
        data_with_gap = [
            {'ts_code': '000001.SZ', 'end_date': '20231231'},
            {'ts_code': '000001.SZ', 'end_date': '20230930'},
            {'ts_code': '000001.SZ', 'end_date': '20230331'},  # 跳过了 Q2
        ]
        missing = AnomalyDetector.detect_missing_data(data_with_gap)
        assert len(missing) > 0
    
    def test_detect_negative_values(self):
        """测试异常负值检测"""
        # 应该为正的字段出现负值
        data = [
            {'ts_code': '000001.SZ', 'total_assets': 10000},
            {'ts_code': '000002.SZ', 'total_assets': -5000},  # 异常
            {'ts_code': '000003.SZ', 'total_assets': 8000},
        ]
        anomalies = AnomalyDetector.detect_negative_values(
            data, 
            ['total_assets'], 
            expected_positive=True
        )
        assert len(anomalies) == 1
        assert anomalies[0]['ts_code'] == '000002.SZ'
        assert anomalies[0]['anomaly_type'] == 'unexpected_negative'
    
    def test_detect_drastic_change(self):
        """测试剧烈变化检测"""
        # 正常变化
        normal_data = [
            {'ts_code': '000001.SZ', 'value': 100},
            {'ts_code': '000001.SZ', 'value': 110},
            {'ts_code': '000001.SZ', 'value': 105},
            {'ts_code': '000001.SZ', 'value': 115},
        ]
        changes = AnomalyDetector.detect_drastic_change(normal_data, 'value', threshold_pct=50.0)
        assert len(changes) == 0
        
        # 包含剧烈变化
        data_with_change = [
            {'ts_code': '000001.SZ', 'value': 100},
            {'ts_code': '000001.SZ', 'value': 200},  # 100% 增长
            {'ts_code': '000001.SZ', 'value': 50},   # -75% 下降
        ]
        changes = AnomalyDetector.detect_drastic_change(data_with_change, 'value', threshold_pct=50.0)
        assert len(changes) == 2
    
    def test_validate_data_quality(self):
        """测试数据质量验证"""
        # 完整的数据
        complete_data = [
            {'ts_code': '000001.SZ', 'end_date': '20231231', 'value': 100},
            {'ts_code': '000002.SZ', 'end_date': '20231231', 'value': 200},
            {'ts_code': '000003.SZ', 'end_date': '20231231', 'value': 300},
        ]
        report = AnomalyDetector.validate_data_quality(
            complete_data, 
            ['ts_code', 'end_date', 'value']
        )
        assert report['status'] == 'ok'
        assert report['overall_completeness'] == 100.0
        
        # 有缺失的数据
        incomplete_data = [
            {'ts_code': '000001.SZ', 'end_date': '20231231', 'value': 100},
            {'ts_code': '000002.SZ', 'end_date': '20231231'},  # 缺少 value
            {'ts_code': '000003.SZ', 'value': 300},  # 缺少 end_date
        ]
        report = AnomalyDetector.validate_data_quality(
            incomplete_data, 
            ['ts_code', 'end_date', 'value']
        )
        assert report['status'] == 'warning'
        assert report['overall_completeness'] < 100.0
    
    def test_detect_all_anomalies(self):
        """测试综合异常检测"""
        # 需要足够的数据点来检测异常
        balance_sheets = [
            {'ts_code': '000001.SZ', 'end_date': '20231231', 'total_assets': 10000},
            {'ts_code': '000001.SZ', 'end_date': '20230930', 'total_assets': 9800},
            {'ts_code': '000001.SZ', 'end_date': '20230630', 'total_assets': 50000},  # 异常值
            {'ts_code': '000001.SZ', 'end_date': '20230331', 'total_assets': 9700},
            {'ts_code': '000001.SZ', 'end_date': '20221231', 'total_assets': 9600},
        ]
        
        income_statements = [
            {'ts_code': '000001.SZ', 'end_date': '20231231', 'revenue': 1000},
            {'ts_code': '000001.SZ', 'end_date': '20230930', 'revenue': 2000},  # 50% 下降
            {'ts_code': '000001.SZ', 'end_date': '20230630', 'revenue': 900},
            {'ts_code': '000001.SZ', 'end_date': '20230331', 'revenue': 850},
        ]
        
        cash_flows = [
            {'ts_code': '000001.SZ', 'end_date': '20231231', 'operating_cash_flow': 500},
            {'ts_code': '000001.SZ', 'end_date': '20230930', 'operating_cash_flow': 450},
            {'ts_code': '000001.SZ', 'end_date': '20230630', 'operating_cash_flow': 400},
        ]
        
        anomalies = AnomalyDetector.detect_all_anomalies(
            balance_sheets, income_statements, cash_flows
        )
        
        assert 'outliers' in anomalies
        assert 'missing_periods' in anomalies
        assert 'negative_values' in anomalies
        assert 'drastic_changes' in anomalies
        # 验证检测到了异常（至少应该检测到剧烈变化）
        total_anomalies = sum(len(v) for v in anomalies.values())
        assert total_anomalies > 0


class TestFinancialCalculatorEdgeCases:
    """测试边界情况"""
    
    def test_zero_division(self):
        """测试除零保护"""
        assert FinancialCalculator.calculate_roe(1000, 0) == 0.0
        assert FinancialCalculator.calculate_current_ratio(1000, 0) == 0.0
        assert FinancialCalculator.calculate_gross_margin(1000, 0) == 0.0
    
    def test_none_values(self):
        """测试 None 值处理"""
        assert FinancialCalculator.calculate_roe(None, 1000) == 0.0
        assert FinancialCalculator.calculate_roe(1000, None) == 0.0
        assert FinancialCalculator.calculate_roe(None, None) == 0.0
    
    def test_negative_values(self):
        """测试负值处理"""
        # 负利润
        roe = FinancialCalculator.calculate_roe(-1000, 5000)
        assert roe == -20.0
        
        # 负资产（理论上不应该出现，但应该能处理）
        roa = FinancialCalculator.calculate_roa(1000, -10000)
        assert roa == -10.0


# 运行测试的说明
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
