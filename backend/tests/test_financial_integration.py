# tests/test_financial_integration.py
"""
集成测试：测试财务数据获取和存储的完整流程
注意：这些测试需要真实的 Tushare token 和数据库连接
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd

from app.services.financial_statement import FinancialStatementService
from app.services.data_storage import FinancialDataStorage
from app.services.financial_calculator import FinancialCalculator
from app.services.anomaly_detector import AnomalyDetector


class TestFinancialStatementServiceIntegration:
    """测试财务报表服务集成"""
    
    @pytest.fixture
    def mock_tushare(self):
        """模拟 Tushare API"""
        with patch('tushare.pro_api') as mock:
            mock_api = Mock()
            
            # 模拟资产负债表数据
            balance_df = pd.DataFrame({
                'ts_code': ['000001.SZ', '000001.SZ'],
                'end_date': ['20231231', '20230930'],
                'total_assets': [1000000.00, 980000.00],
                'total_liabilities': [600000.00, 590000.00],
                'total_equity': [400000.00, 390000.00],
                'current_assets': [300000.00, 290000.00],
                'current_liabilities': [200000.00, 195000.00],
            })
            mock_api.balancesheet.return_value = balance_df
            
            # 模拟利润表数据
            income_df = pd.DataFrame({
                'ts_code': ['000001.SZ', '000001.SZ'],
                'end_date': ['20231231', '20230930'],
                'revenue': [500000.00, 480000.00],
                'net_profit': [50000.00, 48000.00],
                'gross_profit': [200000.00, 190000.00],
                'operating_profit': [80000.00, 75000.00],
            })
            mock_api.income.return_value = income_df
            
            # 模拟现金流量表数据
            cashflow_df = pd.DataFrame({
                'ts_code': ['000001.SZ', '000001.SZ'],
                'end_date': ['20231231', '20230930'],
                'operating_cash_flow': [100000.00, 95000.00],
                'investing_cash_flow': [-50000.00, -48000.00],
                'financing_cash_flow': [-30000.00, -28000.00],
            })
            mock_api.cashflow.return_value = cashflow_df
            
            mock.return_value = mock_api
            yield mock_api
    
    @pytest.mark.asyncio
    async def test_get_balance_sheet(self, mock_tushare):
        """测试获取资产负债表"""
        service = FinancialStatementService('test_token')
        
        data = await service.get_balance_sheet('000001.SZ')
        
        assert len(data) == 2
        assert data[0]['ts_code'] == '000001.SZ'
        assert data[0]['total_assets'] == 1000000.00
        assert data[0]['total_equity'] == 400000.00
    
    @pytest.mark.asyncio
    async def test_get_income_statement(self, mock_tushare):
        """测试获取利润表"""
        service = FinancialStatementService('test_token')
        
        data = await service.get_income_statement('000001.SZ')
        
        assert len(data) == 2
        assert data[0]['ts_code'] == '000001.SZ'
        assert data[0]['revenue'] == 500000.00
        assert data[0]['net_profit'] == 50000.00
    
    @pytest.mark.asyncio
    async def test_get_cash_flow_statement(self, mock_tushare):
        """测试获取现金流量表"""
        service = FinancialStatementService('test_token')
        
        data = await service.get_cash_flow_statement('000001.SZ')
        
        assert len(data) == 2
        assert data[0]['ts_code'] == '000001.SZ'
        assert data[0]['operating_cash_flow'] == 100000.00
    
    @pytest.mark.asyncio
    async def test_caching(self, mock_tushare):
        """测试缓存功能"""
        service = FinancialStatementService('test_token')
        
        # 第一次调用
        data1 = await service.get_balance_sheet('000001.SZ')
        assert mock_tushare.balancesheet.call_count == 1
        
        # 第二次调用（应该从缓存获取）
        data2 = await service.get_balance_sheet('000001.SZ')
        assert mock_tushare.balancesheet.call_count == 1  # 没有增加
        assert data1 == data2
        
        # 清除缓存后再调用
        service.clear_cache()
        data3 = await service.get_balance_sheet('000001.SZ')
        assert mock_tushare.balancesheet.call_count == 2  # 增加了


class TestDataStorageIntegration:
    """测试数据存储集成"""
    
    @pytest.fixture
    def mock_session(self):
        """模拟数据库会话"""
        with patch('app.services.data_storage.sessionmaker') as mock:
            mock_session = Mock()
            mock.return_value = mock_session
            yield mock_session
    
    @pytest.mark.asyncio
    async def test_store_balance_sheet(self, mock_session):
        """测试存储资产负债表"""
        # 这个测试需要实际的数据库连接，这里只做基本测试
        storage = FinancialDataStorage('sqlite:///:memory:')
        
        data = [
            {
                'ts_code': '000001.SZ',
                'end_date': '2023-12-31',
                'total_assets': 1000000.00,
                'total_liabilities': 600000.00,
                'total_equity': 400000.00,
            }
        ]
        
        # 应该不会抛出异常
        count = await storage.store_balance_sheet(data)
        assert count >= 0


class TestEndToEnd:
    """端到端测试"""
    
    @pytest.mark.asyncio
    async def test_complete_financial_analysis_workflow(self):
        """测试完整的财务分析工作流"""
        # 1. 模拟获取数据
        balance_sheet = {
            'total_assets': 1000000,
            'total_liabilities': 600000,
            'total_equity': 400000,
            'current_assets': 300000,
            'current_liabilities': 200000
        }
        
        income_statement = {
            'revenue': 500000,
            'net_profit': 50000,
            'gross_profit': 200000,
            'operating_profit': 80000
        }
        
        cash_flow = {
            'operating_cash_flow': 100000,
            'investing_cash_flow': -50000
        }
        
        # 2. 计算财务指标
        metrics = FinancialCalculator.calculate_all_metrics(
            balance_sheet, income_statement, cash_flow
        )
        
        assert metrics['roe'] == 12.5  # 50000/400000 * 100
        assert metrics['roa'] == 5.0   # 50000/1000000 * 100
        assert metrics['debt_ratio'] == 60.0
        assert metrics['gross_margin'] == 40.0
        assert metrics['current_ratio'] == 1.5
        
        # 3. 检测异常
        balance_sheets_list = [
            {'ts_code': '000001.SZ', 'end_date': '20231231', 'total_assets': 1000000},
            {'ts_code': '000001.SZ', 'end_date': '20230930', 'total_assets': 980000},
        ]
        
        outliers = AnomalyDetector.detect_outliers(
            balance_sheets_list, 'total_assets'
        )
        
        # 正常数据应该没有异常
        assert len(outliers) == 0
        
        # 4. 验证数据质量
        quality_report = AnomalyDetector.validate_data_quality(
            balance_sheets_list,
            ['ts_code', 'end_date', 'total_assets']
        )
        
        assert quality_report['status'] == 'ok'
        assert quality_report['overall_completeness'] == 100.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
