"""
股票推荐服务 - 多策略调度器
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.stock import Stock
from app.models.financial import Financial
from app.services.strategies import STRATEGY_REGISTRY
from app.services.strategies.base import StrategyBase
from app.utils.cache import cache
import logging

logger = logging.getLogger(__name__)


class RecommendationService:
    """推荐服务 - 支持多投资策略"""
    
    def __init__(self, db: Session):
        self.db = db
        self._dynamic_metadata = {}
    
    def recommend_stocks(
        self,
        market: str = "A",
        limit: int = 20,
        min_roe: float = 15.0,
        max_debt_ratio: float = 50.0,
        industry: Optional[str] = None,
        min_gross_margin: Optional[float] = None,
        min_net_profit_growth: Optional[float] = None,
        sort_by: str = "score",
        sector: Optional[str] = None,
        strategy: str = "value",
        min_safety_margin: float = 0.0,
        min_grade: str = "D",
    ) -> List[Dict]:
        """
        推荐股票（多策略）

        Args:
            market: 市场 (A, US, HK)
            limit: 返回数量
            min_roe: 最低 ROE
            max_debt_ratio: 最高负债率
            industry: 行业筛选
            min_gross_margin: 最低毛利率
            min_net_profit_growth: 最低净利润增长率
            sort_by: 排序字段 (score, roe, pe, market_cap, safety_margin)
            sector: 板块筛选（用于美股）
            strategy: 投资策略（value/growth/trend）
            min_safety_margin: 最低安全边际（%）
            min_grade: 最低评级（A+/A/B/C/D）

        Returns:
            推荐股票列表
        """
        # 美股走原有逻辑
        if market == "US":
            return self._recommend_us_stocks(limit=limit, sector=sector, sort_by=sort_by)

        # 使用策略引擎
        if strategy in STRATEGY_REGISTRY:
            strategy_cls = STRATEGY_REGISTRY[strategy]
            strategy_instance = strategy_cls(self.db)
            
            results = strategy_instance.filter_stocks(
                market=market,
                limit=limit,
                min_roe=min_roe,
                max_debt_ratio=max_debt_ratio,
                industry=industry,
                min_gross_margin=min_gross_margin,
                sort_by=sort_by,
                min_safety_margin=min_safety_margin,
                min_grade=min_grade,
            )
            
            # 计算安全边际（需要 PE）
            for item in results:
                if item.get('latest_pe') and item.get('eps'):
                    pe = item['latest_pe']
                    eps = item['eps']
                    if pe > 0 and eps > 0:
                        current_price = pe * eps
                        # 获取内在价值
                        stock_code = item['stock_code']
                        financial = self.db.query(Financial).filter(
                            Financial.stock_code == stock_code
                        ).order_by(Financial.report_date.desc()).first()
                        if financial and isinstance(strategy_instance, type):
                            pass
                        # 直接用策略方法
                        if hasattr(strategy_instance, 'calc_safety_margin_from_pe'):
                            sm = strategy_instance.calc_safety_margin_from_pe(financial, pe)
                            item['safety_margin'] = sm
            
            # 应用动态评分（A股）
            if market == "A" and results:
                from app.services.dynamic_scoring import fetch_spot_for_stocks, apply_dynamic_scores
                codes = [r.get("stock_code", "") for r in results]
                spot_data = fetch_spot_for_stocks(codes)
                results, dynamic_meta = apply_dynamic_scores(results, spot_data)
                self._dynamic_metadata = dynamic_meta

                # 生成丰富推荐理由
                self._enrich_reasons(results, spot_data)
            else:
                self._dynamic_metadata = {}
            
            logger.info(f"✅ [{strategy}策略] 推荐股票 {len(results)} 只")
            return results
        
        # 兜底：使用旧逻辑
        logger.warning(f"⚠️ 未知策略 '{strategy}'，使用默认推荐")
        return self._legacy_recommend(
            market=market, limit=limit, min_roe=min_roe,
            max_debt_ratio=max_debt_ratio, industry=industry,
            min_gross_margin=min_gross_margin,
            min_net_profit_growth=min_net_profit_growth,
            sort_by=sort_by,
        )
    
    def _legacy_recommend(
        self, market: str, limit: int, min_roe: float, max_debt_ratio: float,
        industry: Optional[str], min_gross_margin: Optional[float],
        min_net_profit_growth: Optional[float], sort_by: str,
    ) -> List[Dict]:
        """旧版推荐逻辑（向后兼容）"""
        query = self.db.query(Stock).filter(Stock.market == market)
        if industry:
            query = query.filter(Stock.industry == industry)
        stocks = query.all()

        recommendations = []
        for stock in stocks:
            financial = self.db.query(Financial).filter(
                Financial.stock_code == stock.stock_code
            ).order_by(Financial.report_date.desc()).first()
            if not financial:
                continue

            if financial.roe and financial.roe < min_roe:
                continue
            if financial.debt_ratio and financial.debt_ratio > max_debt_ratio:
                continue
            if min_gross_margin and financial.gross_margin and financial.gross_margin < min_gross_margin:
                continue
            if min_net_profit_growth and financial.net_profit_yoy and financial.net_profit_yoy < min_net_profit_growth:
                continue

            score = self.calculate_score(
                roe=financial.roe or 0,
                debt_ratio=financial.debt_ratio or 0,
                pe=stock.latest_pe
            )
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
                'gross_margin': financial.gross_margin,
                'net_profit_growth': financial.net_profit_yoy,
                'recommendation_score': score,
                'recommendation_reason': reason,
            })

        sort_field_map = {
            'score': 'recommendation_score',
            'roe': 'latest_roe',
            'pe': 'latest_pe',
            'market_cap': 'market_cap'
        }
        sort_field = sort_field_map.get(sort_by, 'recommendation_score')
        reverse_sort = sort_by != 'pe'
        recommendations.sort(key=lambda x: x.get(sort_field) or 0, reverse=reverse_sort)
        return recommendations[:limit]
    
    def calculate_score(self, roe: float, debt_ratio: float, pe: Optional[float] = None) -> float:
        """旧版评分（向后兼容）"""
        score = 0
        if roe >= 25: score += 40
        elif roe >= 20: score += 35
        elif roe >= 15: score += 30
        elif roe >= 10: score += 20
        else: score += 10

        if debt_ratio <= 30: score += 30
        elif debt_ratio <= 40: score += 25
        elif debt_ratio <= 50: score += 20
        else: score += 10

        if pe:
            if pe <= 15: score += 30
            elif pe <= 25: score += 25
            elif pe <= 35: score += 20
            else: score += 10
        else:
            score += 20
        return min(score, 100)
    
    def generate_reason(self, roe: float, debt_ratio: float, pe: Optional[float] = None) -> str:
        """旧版理由生成（向后兼容）"""
        reasons = []
        if roe >= 20: reasons.append("高ROE")
        elif roe >= 15: reasons.append("ROE良好")
        if debt_ratio <= 40: reasons.append("低负债")
        elif debt_ratio <= 50: reasons.append("负债适中")
        if pe and pe <= 20: reasons.append("估值合理")
        elif pe and pe <= 30: reasons.append("估值可接受")
        return "、".join(reasons) if reasons else "符合基本标准"
    
    def _recommend_us_stocks(self, limit: int = 20, sector: Optional[str] = None, sort_by: str = "score") -> List[Dict]:
        """美股推荐（保持不变）"""
        try:
            from app.services.data_collector import AkShareCollector
            us_stocks = AkShareCollector.get_us_stock_list()
            recommendations = []
            for stock in us_stocks:
                if sector and stock.get('category') != sector:
                    continue
                pe = stock.get('latest_pe')
                if pe and pe > 0:
                    if pe < 20: score = 80
                    elif pe < 30: score = 70
                    elif pe < 50: score = 60
                    else: score = 50
                else:
                    score = 50
                recommendations.append({
                    'stock_code': stock['stock_code'], 'name': stock['name'],
                    'market': 'US', 'industry': stock.get('category', ''),
                    'market_cap': stock.get('market_cap'),
                    'latest_roe': None, 'latest_pe': pe,
                    'debt_ratio': None, 'gross_margin': None,
                    'net_profit_growth': None,
                    'recommendation_score': score,
                    'recommendation_reason': f"美股知名企业，PE={pe}" if pe else "美股知名企业",
                })
            sort_field_map = {'score': 'recommendation_score', 'roe': 'latest_roe', 'pe': 'latest_pe', 'market_cap': 'market_cap'}
            sort_field = sort_field_map.get(sort_by, 'recommendation_score')
            reverse_sort = sort_by != 'pe'
            recommendations.sort(key=lambda x: x.get(sort_field) or 0, reverse=reverse_sort)
            return recommendations[:limit]
        except Exception as e:
            logger.error(f"❌ 推荐美股失败: {e}")
            return []
    
    def sync_stock_list(self, market: str = "A") -> int:
        """同步股票列表到数据库"""
        if market != "A":
            logger.warning("⚠️ MVP 阶段仅支持 A 股")
            return 0
        from app.services.data_collector import AkShareCollector
        stocks = AkShareCollector.get_a_stock_list()
        count = 0
        for stock_data in stocks:
            try:
                existing = self.db.query(Stock).filter(Stock.stock_code == stock_data['stock_code']).first()
                if existing:
                    existing.name = stock_data['name']
                    existing.market_cap = stock_data.get('market_cap')
                    existing.latest_pe = stock_data.get('latest_pe')
                else:
                    stock = Stock(**stock_data)
                    self.db.add(stock)
                    count += 1
            except Exception as e:
                logger.error(f"❌ 保存股票 {stock_data['stock_code']} 失败: {e}")
        self.db.commit()
        logger.info(f"✅ 同步股票列表成功，新增 {count} 只")
        return count
    
    def _enrich_reasons(self, results: List[Dict], spot_data: Dict) -> None:
        """用丰富理由替换简单理由"""
        from app.services.reason_builder import build_rich_reason, fetch_recent_news

        for item in results:
            try:
                code = item.get("stock_code", "")
                recent_news = fetch_recent_news(self.db, code)
                spot_info = spot_data.get(code) if spot_data else None

                financial_metrics = {
                    "roe": item.get("latest_roe"),
                    "gross_margin": item.get("gross_margin"),
                    "debt_ratio": item.get("debt_ratio"),
                    "revenue_yoy": item.get("revenue_yoy"),
                    "net_profit_yoy": item.get("net_profit_growth"),
                    "operating_cash_flow": item.get("operating_cash_flow"),
                    "eps": item.get("eps"),
                    "net_profit": None,
                }

                score_detail = item.get("score_detail") or {}

                rich = build_rich_reason(
                    stock_code=code,
                    name=item.get("name", ""),
                    industry=item.get("industry", ""),
                    grade=item.get("grade", ""),
                    score_detail=score_detail,
                    financial_metrics=financial_metrics,
                    spot_info=spot_info,
                    recent_news=recent_news,
                )

                item["recommendation_reason"] = rich["recommendation_reason"]
                item["reason_sections"] = rich["reason_sections"]
            except Exception as e:
                logger.warning(f"丰富理由生成失败 {code}: {e}")

    def get_available_strategies(self) -> List[Dict]:
        """获取所有可用策略的信息"""
        strategies = []
        for name, cls in STRATEGY_REGISTRY.items():
            instance = cls(self.db)
            strategies.append(instance.get_info())
        return strategies
