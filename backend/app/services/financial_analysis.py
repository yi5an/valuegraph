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
        
        # 如果数据库无数据，尝试从 AkShare 获取（非阻塞）
        if not financials:
            try:
                logger.info(f"📊 从 AkShare 获取 {stock_code} 财报数据")
                financials_raw = AkShareCollector.get_financial_data(stock_code)
                if financials_raw:
                    self._save_financial_data(stock_code, financials_raw)
                    financials = self.db.query(Financial).filter(
                        Financial.stock_code == stock_code
                    ).order_by(Financial.report_date.desc()).limit(years).all()
            except Exception as e:
                logger.warning(f"⚠️ 获取 {stock_code} 财报数据失败: {e}")
        
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
                'investing_cash_flow': fin.investing_cash_flow,
                'financing_cash_flow': fin.financing_cash_flow,
                'free_cash_flow': fin.free_cash_flow,
                'current_assets': fin.current_assets,
                'current_liabilities': fin.current_liabilities,
                'inventory': fin.inventory,
                'accounts_receivable': fin.accounts_receivable,
                'monetary_fund': fin.monetary_fund,
                'current_ratio': fin.current_ratio,
                'quick_ratio': fin.quick_ratio,
                'roa': fin.roa,
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
        
        # 偿债能力 (流动比率 + 负债率)
        solvency = 0
        if latest.current_ratio:
            # 流比率 2.0 = 100分，< 1.0 = 0分
            solvency += min(max((latest.current_ratio - 1.0) / 1.0 * 60, 0), 60)
        if latest.debt_ratio:
            # 负债率 < 50% = 40分，> 80% = 0分
            solvency += max(40 - (latest.debt_ratio - 50) * 1.33, 0) if latest.debt_ratio > 50 else 40
        solvency = min(int(solvency), 100)
        
        # 成长能力 (营收增长)
        growth = 0
        if latest.revenue_yoy:
            growth = min(max(latest.revenue_yoy, 0), 100)
        
        # 运营能力 (现金流三维度)
        operation = 0
        ocf = latest.operating_cash_flow
        icf = latest.investing_cash_flow
        fcf = latest.free_cash_flow
        if ocf and ocf > 0:
            operation += 40  # 经营现金流转正40分
        if fcf and fcf > 0:
            operation += 30  # 自由现金流转正30分
        if icf and icf < 0:
            operation += 30  # 投资支出（扩张）30分
        elif ocf and ocf > 0:
            operation += 15  # 经营正向但无投资 = 保守
        
        # 综合评分
        overall = int((profitability + solvency + growth + operation) / 4)
        
        return {
            'overall': overall,
            'profitability': int(profitability),
            'solvency': int(solvency),
            'growth': int(growth),
            'operation': int(operation),
        }
    
    def _save_financial_data(self, stock_code: str, financials_raw: list):
        """保存财报数据到数据库"""
        try:
            for fin_data in financials_raw:
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
                    bvps=fin_data.get('bvps'),
                    operating_cash_flow=fin_data.get('operating_cash_flow'),
                    revenue_yoy=fin_data.get('revenue_yoy'),
                    net_profit_yoy=fin_data.get('net_profit_yoy'),
                )
                self.db.add(fin)
            
            self.db.commit()
            logger.info(f"✅ 同步 {stock_code} 财报数据成功")
        
        except Exception as e:
            logger.error(f"❌ 同步 {stock_code} 财报数据失败: {e}")
            self.db.rollback()
