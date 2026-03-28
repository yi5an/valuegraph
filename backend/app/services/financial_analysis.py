"""
财报分析服务
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.financial import Financial
from app.models.stock import Stock
from app.services.data_collector import AkShareCollector
from app.utils.cache import cache
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FinancialService:
    """财报服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_timeline(self, stock_code: str, years: int = 5) -> Dict:
        """
        获取财报时间线
        
        Args:
            stock_code: 股票代码
            years: 年数
        
        Returns:
            财报时间线数据
        """
        cache_key = f"financial:{stock_code}:{years}"
        
        # 尝试从缓存获取
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"✅ 从缓存获取 {stock_code} 财报数据")
            return cached
        
        # 获取股票信息
        stock = self.db.query(Stock).filter(Stock.stock_code == stock_code).first()
        if not stock:
            return {
                'stock_code': stock_code,
                'name': '',
                'timeline': [],
                'chart_data': None,
                'health_score': None,
            }
        
        # 从数据库查询财报
        financials = self.db.query(Financial).filter(
            Financial.stock_code == stock_code
        ).order_by(Financial.report_date.desc()).limit(years).all()
        
        # 如果数据库无数据，从 AkShare 获取
        if not financials:
            logger.info(f"📊 从 AkShare 获取 {stock_code} 财报数据")
            self._sync_financial_data(stock_code)
            financials = self.db.query(Financial).filter(
                Financial.stock_code == stock_code
            ).order_by(Financial.report_date.desc()).limit(years).all()
        
        # 构建时间线
        timeline = []
        for fin in financials:
            timeline.append({
                'report_date': fin.report_date,
                'report_type': fin.report_type,
                'revenue': fin.revenue,
                'revenue_yoy': fin.revenue_yoy,
                'net_profit': fin.net_profit,
                'net_profit_yoy': fin.net_profit_yoy,
                'roe': fin.roe,
                'gross_margin': fin.gross_margin,
                'debt_ratio': fin.debt_ratio,
                'operating_cash_flow': fin.operating_cash_flow,
                'eps': fin.eps,
                'bvps': fin.bvps,
            })
        
        # 构建图表数据
        chart_data = self._build_chart_data(financials)
        
        # 计算健康度评分
        health_score = self._calculate_health_score(financials)
        
        result = {
            'stock_code': stock_code,
            'name': stock.name,
            'timeline': timeline,
            'chart_data': chart_data,
            'health_score': health_score,
        }
        
        # 写入缓存
        cache.set(cache_key, result)
        
        return result
    
    def _build_chart_data(self, financials: List[Financial]) -> Dict:
        """构建图表数据"""
        dates = []
        revenues = []
        net_profits = []
        roes = []
        
        for fin in reversed(financials):  # 从旧到新
            dates.append(str(fin.report_date))
            revenues.append(fin.revenue or 0)
            net_profits.append(fin.net_profit or 0)
            roes.append(fin.roe or 0)
        
        return {
            'dates': dates,
            'revenues': revenues,
            'net_profits': net_profits,
            'roes': roes,
        }
    
    def _calculate_health_score(self, financials: List[Financial]) -> Dict:
        """计算财务健康度评分"""
        if not financials:
            return {
                'overall': 0,
                'profitability': 0,
                'solvency': 0,
                'growth': 0,
                'operation': 0,
            }
        
        # 取最新数据
        latest = financials[0]
        
        # 盈利能力 (ROE + 毛利率)
        profitability = 0
        if latest.roe:
            profitability += min(latest.roe / 30 * 50, 50)  # ROE 贡献50分
        if latest.gross_margin:
            profitability += min(latest.gross_margin / 50 * 50, 50)  # 毛利率贡献50分
        
        # 偿债能力 (负债率)
        solvency = 0
        if latest.debt_ratio:
            solvency = max(100 - latest.debt_ratio, 0)
        
        # 成长能力 (营收增长)
        growth = 0
        if latest.revenue_yoy:
            growth = min(max(latest.revenue_yoy, 0), 100)
        
        # 运营能力 (现金流)
        operation = 0
        if latest.operating_cash_flow and latest.operating_cash_flow > 0:
            operation = 100
        elif latest.operating_cash_flow and latest.operating_cash_flow < 0:
            operation = 30
        
        # 综合评分
        overall = int((profitability + solvency + growth + operation) / 4)
        
        return {
            'overall': overall,
            'profitability': int(profitability),
            'solvency': int(solvency),
            'growth': int(growth),
            'operation': int(operation),
        }
    
    def _sync_financial_data(self, stock_code: str):
        """同步财报数据到数据库"""
        try:
            financials = AkShareCollector.get_financial_data(stock_code)
            
            for fin_data in financials:
                # 解析日期
                report_date = fin_data.get('report_date')
                if isinstance(report_date, str):
                    report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
                
                # 检查是否已存在
                existing = self.db.query(Financial).filter(
                    Financial.stock_code == stock_code,
                    Financial.report_date == report_date,
                    Financial.report_type == fin_data['report_type']
                ).first()
                
                if existing:
                    continue
                
                # 新增
                fin = Financial(
                    stock_code=stock_code,
                    report_date=report_date,
                    report_type=fin_data['report_type'],
                    roe=fin_data.get('roe'),
                    gross_margin=fin_data.get('gross_margin'),
                    debt_ratio=fin_data.get('debt_ratio'),
                    revenue=fin_data.get('revenue'),
                    net_profit=fin_data.get('net_profit'),
                    eps=fin_data.get('eps'),
                )
                self.db.add(fin)
            
            self.db.commit()
            logger.info(f"✅ 同步 {stock_code} 财报数据成功")
        
        except Exception as e:
            logger.error(f"❌ 同步 {stock_code} 财报数据失败: {e}")
            self.db.rollback()
