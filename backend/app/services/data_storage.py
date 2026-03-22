# services/data_storage.py
import logging
from typing import List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from contextlib import contextmanager

from ..config import settings
from ..models.financial import Base, BalanceSheet, IncomeStatement, CashFlowStatement

logger = logging.getLogger(__name__)


class FinancialDataStorage:
    """财务数据存储服务"""
    
    def __init__(self, database_url: str = None):
        self.database_url = database_url or settings.database_url
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # 创建表（如果不存在）
        self._create_tables()
    
    def _create_tables(self):
        """创建数据库表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据库表创建成功")
        except Exception as e:
            logger.error(f"创建数据库表失败: {e}", exc_info=True)
    
    @contextmanager
    def get_session(self) -> Session:
        """获取数据库会话"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    async def store_balance_sheet(self, data: List[Dict[str, Any]]) -> int:
        """存储资产负债表数据
        
        Args:
            data: 资产负债表数据列表
        
        Returns:
            成功存储的记录数
        """
        if not data:
            logger.warning("无数据需要存储")
            return 0
        
        stored_count = 0
        
        with self.get_session() as session:
            for item in data:
                try:
                    # 检查是否已存在
                    existing = session.query(BalanceSheet).filter_by(
                        ts_code=item.get('ts_code'),
                        end_date=item.get('end_date')
                    ).first()
                    
                    if existing:
                        # 更新现有记录
                        for key, value in item.items():
                            if hasattr(existing, key) and value is not None:
                                setattr(existing, key, value)
                        logger.debug(f"更新资产负债表: {item.get('ts_code')} - {item.get('end_date')}")
                    else:
                        # 插入新记录
                        balance = BalanceSheet(**item)
                        session.add(balance)
                        logger.debug(f"插入资产负债表: {item.get('ts_code')} - {item.get('end_date')}")
                    
                    stored_count += 1
                    
                except IntegrityError as e:
                    logger.warning(f"数据已存在，跳过: {item.get('ts_code')} - {item.get('end_date')}")
                    session.rollback()
                    continue
                except Exception as e:
                    logger.error(f"存储资产负债表记录失败: {e}", exc_info=True)
                    continue
        
        logger.info(f"成功存储 {stored_count} 条资产负债表数据")
        return stored_count
    
    async def store_income_statement(self, data: List[Dict[str, Any]]) -> int:
        """存储利润表数据
        
        Args:
            data: 利润表数据列表
        
        Returns:
            成功存储的记录数
        """
        if not data:
            logger.warning("无数据需要存储")
            return 0
        
        stored_count = 0
        
        with self.get_session() as session:
            for item in data:
                try:
                    existing = session.query(IncomeStatement).filter_by(
                        ts_code=item.get('ts_code'),
                        end_date=item.get('end_date')
                    ).first()
                    
                    if existing:
                        for key, value in item.items():
                            if hasattr(existing, key) and value is not None:
                                setattr(existing, key, value)
                        logger.debug(f"更新利润表: {item.get('ts_code')} - {item.get('end_date')}")
                    else:
                        income = IncomeStatement(**item)
                        session.add(income)
                        logger.debug(f"插入利润表: {item.get('ts_code')} - {item.get('end_date')}")
                    
                    stored_count += 1
                    
                except IntegrityError as e:
                    logger.warning(f"数据已存在，跳过: {item.get('ts_code')} - {item.get('end_date')}")
                    session.rollback()
                    continue
                except Exception as e:
                    logger.error(f"存储利润表记录失败: {e}", exc_info=True)
                    continue
        
        logger.info(f"成功存储 {stored_count} 条利润表数据")
        return stored_count
    
    async def store_cash_flow_statement(self, data: List[Dict[str, Any]]) -> int:
        """存储现金流量表数据
        
        Args:
            data: 现金流量表数据列表
        
        Returns:
            成功存储的记录数
        """
        if not data:
            logger.warning("无数据需要存储")
            return 0
        
        stored_count = 0
        
        with self.get_session() as session:
            for item in data:
                try:
                    existing = session.query(CashFlowStatement).filter_by(
                        ts_code=item.get('ts_code'),
                        end_date=item.get('end_date')
                    ).first()
                    
                    if existing:
                        for key, value in item.items():
                            if hasattr(existing, key) and value is not None:
                                setattr(existing, key, value)
                        logger.debug(f"更新现金流量表: {item.get('ts_code')} - {item.get('end_date')}")
                    else:
                        cashflow = CashFlowStatement(**item)
                        session.add(cashflow)
                        logger.debug(f"插入现金流量表: {item.get('ts_code')} - {item.get('end_date')}")
                    
                    stored_count += 1
                    
                except IntegrityError as e:
                    logger.warning(f"数据已存在，跳过: {item.get('ts_code')} - {item.get('end_date')}")
                    session.rollback()
                    continue
                except Exception as e:
                    logger.error(f"存储现金流量表记录失败: {e}", exc_info=True)
                    continue
        
        logger.info(f"成功存储 {stored_count} 条现金流量表数据")
        return stored_count
    
    async def get_historical_balance_sheets(
        self, 
        ts_code: str, 
        years: int = 10
    ) -> List[Dict[str, Any]]:
        """获取历史资产负债表数据
        
        Args:
            ts_code: 股票代码
            years: 历史年数
        
        Returns:
            历史资产负债表数据列表
        """
        with self.get_session() as session:
            from datetime import datetime, timedelta
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            
            records = session.query(BalanceSheet).filter(
                BalanceSheet.ts_code == ts_code,
                BalanceSheet.end_date >= start_date
            ).order_by(BalanceSheet.end_date.desc()).all()
            
            return [
                {
                    'ts_code': r.ts_code,
                    'end_date': str(r.end_date),
                    'total_assets': float(r.total_assets) if r.total_assets else None,
                    'total_liabilities': float(r.total_liabilities) if r.total_liabilities else None,
                    'total_equity': float(r.total_equity) if r.total_equity else None,
                    'current_assets': float(r.current_assets) if r.current_assets else None,
                    'current_liabilities': float(r.current_liabilities) if r.current_liabilities else None,
                }
                for r in records
            ]
    
    async def get_historical_income_statements(
        self, 
        ts_code: str, 
        years: int = 10
    ) -> List[Dict[str, Any]]:
        """获取历史利润表数据"""
        with self.get_session() as session:
            from datetime import datetime, timedelta
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            
            records = session.query(IncomeStatement).filter(
                IncomeStatement.ts_code == ts_code,
                IncomeStatement.end_date >= start_date
            ).order_by(IncomeStatement.end_date.desc()).all()
            
            return [
                {
                    'ts_code': r.ts_code,
                    'end_date': str(r.end_date),
                    'revenue': float(r.revenue) if r.revenue else None,
                    'net_profit': float(r.net_profit) if r.net_profit else None,
                    'gross_profit': float(r.gross_profit) if r.gross_profit else None,
                    'operating_profit': float(r.operating_profit) if r.operating_profit else None,
                }
                for r in records
            ]
    
    async def get_historical_cash_flow_statements(
        self, 
        ts_code: str, 
        years: int = 10
    ) -> List[Dict[str, Any]]:
        """获取历史现金流量表数据"""
        with self.get_session() as session:
            from datetime import datetime, timedelta
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=years * 365)
            
            records = session.query(CashFlowStatement).filter(
                CashFlowStatement.ts_code == ts_code,
                CashFlowStatement.end_date >= start_date
            ).order_by(CashFlowStatement.end_date.desc()).all()
            
            return [
                {
                    'ts_code': r.ts_code,
                    'end_date': str(r.end_date),
                    'operating_cash_flow': float(r.operating_cash_flow) if r.operating_cash_flow else None,
                    'investing_cash_flow': float(r.investing_cash_flow) if r.investing_cash_flow else None,
                    'financing_cash_flow': float(r.financing_cash_flow) if r.financing_cash_flow else None,
                    'free_cash_flow': float(r.free_cash_flow) if r.free_cash_flow else None,
                }
                for r in records
            ]
