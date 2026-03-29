"""
财报异常检测服务
"""
from typing import List, Dict
from sqlalchemy.orm import Session
from app.models.financial import Financial
import logging

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """财报异常检测器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def detect(self, stock_code: str) -> Dict:
        """
        检测财务数据异常
        
        检查项：
        - ROE 突然大幅下降（>30%）
        - 负债率突然飙升（>20%）
        - 营收增长但利润下降
        - 经营现金流连续为负
        
        Args:
            stock_code: 股票代码
        
        Returns:
            {
                has_anomaly: bool,
                items: [{type, description, severity}]
            }
        """
        items = []
        
        # 查询最近 4 期财报
        financials = self.db.query(Financial).filter(
            Financial.stock_code == stock_code
        ).order_by(Financial.report_date.desc()).limit(4).all()
        
        if len(financials) < 2:
            return {
                'has_anomaly': False,
                'items': [],
                'message': '数据不足，至少需要 2 期财报'
            }
        
        latest = financials[0]
        previous = financials[1]
        
        # 1. 检测 ROE 大幅下降
        if latest.roe and previous.roe and previous.roe > 0:
            roe_decline_pct = (previous.roe - latest.roe) / previous.roe * 100
            if roe_decline_pct > 30:
                severity = 'high' if roe_decline_pct > 50 else 'medium'
                items.append({
                    'type': 'roe_decline',
                    'description': f'ROE 从 {previous.roe:.2f}% 下降至 {latest.roe:.2f}%，降幅 {roe_decline_pct:.1f}%',
                    'severity': severity,
                    'details': {
                        'previous': previous.roe,
                        'current': latest.roe,
                        'change_pct': round(roe_decline_pct, 2)
                    }
                })
        
        # 2. 检测负债率飙升
        if latest.debt_ratio and previous.debt_ratio and previous.debt_ratio > 0:
            debt_increase_pct = (latest.debt_ratio - previous.debt_ratio) / previous.debt_ratio * 100
            if debt_increase_pct > 20:
                severity = 'high' if debt_increase_pct > 40 else 'medium'
                items.append({
                    'type': 'debt_surge',
                    'description': f'负债率从 {previous.debt_ratio:.2f}% 飙升至 {latest.debt_ratio:.2f}%，涨幅 {debt_increase_pct:.1f}%',
                    'severity': severity,
                    'details': {
                        'previous': previous.debt_ratio,
                        'current': latest.debt_ratio,
                        'change_pct': round(debt_increase_pct, 2)
                    }
                })
        
        # 3. 检测营收增长但利润下降
        if (latest.revenue_yoy and latest.revenue_yoy > 0 and 
            latest.net_profit_yoy and latest.net_profit_yoy < 0):
            severity = 'high' if abs(latest.net_profit_yoy) > 30 else 'medium'
            items.append({
                'type': 'profit_decline_with_revenue_growth',
                'description': f'营收同比增长 {latest.revenue_yoy:.1f}%，但净利润同比下降 {abs(latest.net_profit_yoy):.1f}%',
                'severity': severity,
                'details': {
                    'revenue_yoy': latest.revenue_yoy,
                    'net_profit_yoy': latest.net_profit_yoy
                }
            })
        
        # 4. 检测经营现金流连续为负
        negative_cash_flow_count = sum(
            1 for fin in financials 
            if fin.operating_cash_flow and fin.operating_cash_flow < 0
        )
        
        if negative_cash_flow_count >= 2:
            severity = 'high' if negative_cash_flow_count >= 3 else 'medium'
            items.append({
                'type': 'negative_cash_flow',
                'description': f'连续 {negative_cash_flow_count} 期经营现金流为负',
                'severity': severity,
                'details': {
                    'consecutive_periods': negative_cash_flow_count,
                    'latest_cash_flow': latest.operating_cash_flow
                }
            })
        
        return {
            'has_anomaly': len(items) > 0,
            'items': items,
            'total_issues': len(items),
            'high_severity_count': sum(1 for item in items if item['severity'] == 'high'),
            'stock_code': stock_code,
            'latest_report_date': str(latest.report_date)
        }
