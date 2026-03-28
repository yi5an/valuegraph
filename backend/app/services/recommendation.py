"""
股票推荐服务
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.stock import Stock
from app.models.financial import Financial
from app.services.data_collector import AkShareCollector
from app.utils.cache import cache
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class RecommendationService:
    """推荐服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_score(self, roe: float, debt_ratio: float, pe: Optional[float] = None) -> float:
        """
        计算推荐得分
        
        Args:
            roe: ROE (%)
            debt_ratio: 负债率 (%)
            pe: 市盈率
        
        Returns:
            推荐得分 (0-100)
        """
        score = 0
        
        # ROE 得分 (40分)
        if roe >= 25:
            score += 40
        elif roe >= 20:
            score += 35
        elif roe >= 15:
            score += 30
        elif roe >= 10:
            score += 20
        else:
            score += 10
        
        # 负债率得分 (30分)
        if debt_ratio <= 30:
            score += 30
        elif debt_ratio <= 40:
            score += 25
        elif debt_ratio <= 50:
            score += 20
        else:
            score += 10
        
        # PE 得分 (30分)
        if pe:
            if pe <= 15:
                score += 30
            elif pe <= 25:
                score += 25
            elif pe <= 35:
                score += 20
            else:
                score += 10
        else:
            score += 20  # 无 PE 数据，给平均分
        
        return min(score, 100)
    
    def generate_reason(self, roe: float, debt_ratio: float, pe: Optional[float] = None) -> str:
        """
        生成推荐理由
        
        Args:
            roe: ROE
            debt_ratio: 负债率
            pe: 市盈率
        
        Returns:
            推荐理由
        """
        reasons = []
        
        if roe >= 20:
            reasons.append("高ROE")
        elif roe >= 15:
            reasons.append("ROE良好")
        
        if debt_ratio <= 40:
            reasons.append("低负债")
        elif debt_ratio <= 50:
            reasons.append("负债适中")
        
        if pe and pe <= 20:
            reasons.append("估值合理")
        elif pe and pe <= 30:
            reasons.append("估值可接受")
        
        return "、".join(reasons) if reasons else "符合基本标准"
    
    def recommend_stocks(
        self,
        market: str = "A",
        limit: int = 20,
        min_roe: float = 15.0,
        max_debt_ratio: float = 50.0,
        industry: Optional[str] = None
    ) -> List[Dict]:
        """
        推荐股票
        
        Args:
            market: 市场
            limit: 返回数量
            min_roe: 最低 ROE
            max_debt_ratio: 最高负债率
            industry: 行业筛选
        
        Returns:
            推荐股票列表
        """
        cache_key = f"recommend:{market}:{min_roe}:{max_debt_ratio}:{limit}"
        
        # 尝试从缓存获取
        cached = cache.get(cache_key)
        if cached:
            logger.info("✅ 从缓存获取推荐结果")
            return cached
        
        # 从数据库查询股票
        query = self.db.query(Stock).filter(Stock.market == market)
        
        if industry:
            query = query.filter(Stock.industry == industry)
        
        stocks = query.all()
        
        # 筛选和评分
        recommendations = []
        for stock in stocks:
            # 获取最新财务数据
            financial = self.db.query(Financial).filter(
                Financial.stock_code == stock.stock_code
            ).order_by(Financial.report_date.desc()).first()
            
            if not financial:
                continue
            
            # 筛选条件
            if financial.roe and financial.roe < min_roe:
                continue
            
            if financial.debt_ratio and financial.debt_ratio > max_debt_ratio:
                continue
            
            # 计算得分
            score = self.calculate_score(
                roe=financial.roe or 0,
                debt_ratio=financial.debt_ratio or 0,
                pe=stock.latest_pe
            )
            
            # 生成理由
            reason = self.generate_reason(
                roe=financial.roe or 0,
                debt_ratio=financial.debt_ratio or 0,
                pe=stock.latest_pe
            )
            
            recommendations.append({
                'stock_code': stock.stock_code,
                'name': stock.name,
                'market': stock.market,
                'industry': stock.industry,
                'market_cap': stock.market_cap,
                'latest_roe': financial.roe,
                'latest_pe': stock.latest_pe,
                'debt_ratio': financial.debt_ratio,
                'recommendation_score': score,
                'recommendation_reason': reason,
            })
        
        # 按得分排序
        recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        # 限制数量
        recommendations = recommendations[:limit]
        
        # 写入缓存
        cache.set(cache_key, recommendations)
        
        logger.info(f"✅ 推荐股票 {len(recommendations)} 只")
        return recommendations
    
    def sync_stock_list(self, market: str = "A") -> int:
        """
        同步股票列表到数据库
        
        Args:
            market: 市场
        
        Returns:
            同步数量
        """
        if market != "A":
            logger.warning("⚠️ MVP 阶段仅支持 A 股")
            return 0
        
        # 获取股票列表
        stocks = AkShareCollector.get_a_stock_list()
        
        # 保存到数据库
        count = 0
        for stock_data in stocks:
            try:
                # 检查是否已存在
                existing = self.db.query(Stock).filter(
                    Stock.stock_code == stock_data['stock_code']
                ).first()
                
                if existing:
                    # 更新
                    existing.name = stock_data['name']
                    existing.market_cap = stock_data.get('market_cap')
                    existing.latest_pe = stock_data.get('latest_pe')
                else:
                    # 新增
                    stock = Stock(**stock_data)
                    self.db.add(stock)
                    count += 1
            except Exception as e:
                logger.error(f"❌ 保存股票 {stock_data['stock_code']} 失败: {e}")
        
        self.db.commit()
        logger.info(f"✅ 同步股票列表成功，新增 {count} 只")
        return count
