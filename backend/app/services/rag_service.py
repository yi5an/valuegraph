"""
RAG 智能问答服务
基于 SQLite 财务数据和 Neo4j 知识图谱的检索增强生成
"""
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
import httpx
import logging
import re

from app.models.stock import Stock
from app.models.financial import Financial
from app.models.shareholder import Shareholder, InstitutionalHolder
from app.models.news import News
from app.services.recommendation import RecommendationService
from app.services.knowledge_graph import KnowledgeGraphService

logger = logging.getLogger(__name__)


class RAGService:
    """RAG 智能问答服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.recommendation_service = RecommendationService(db)
        self.kg_service = KnowledgeGraphService(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="valuegraph2026"
        )
    
    def extract_stocks(self, question: str) -> List[Dict]:
        """
        从问题中提取股票名称/代码
        
        Args:
            question: 用户问题
        
        Returns:
            匹配的股票列表 [{"stock_code": "600519", "name": "贵州茅台"}]
        """
        stocks = []
        
        # 尝试匹配股票代码（6位数字）
        code_pattern = r'\b(\d{6})\b'
        codes = re.findall(code_pattern, question)
        
        if codes:
            # 查询数据库中匹配的股票
            for code in codes:
                stock = self.db.query(Stock).filter(
                    Stock.stock_code == code
                ).first()
                if stock:
                    stocks.append({
                        "stock_code": stock.stock_code,
                        "name": stock.name
                    })
        
        # 尝试匹配股票名称
        # 获取所有股票，检查问题中是否包含股票名称
        all_stocks = self.db.query(Stock).all()
        for stock in all_stocks:
            if stock.name in question:
                # 避免重复添加
                if not any(s["stock_code"] == stock.stock_code for s in stocks):
                    stocks.append({
                        "stock_code": stock.stock_code,
                        "name": stock.name
                    })
        
        return stocks
    
    def classify_question(self, question: str) -> str:
        """
        分类问题类型
        
        Args:
            question: 用户问题
        
        Returns:
            问题类型: recommendation/financials/shareholders/supply_chain/risk/news
        """
        question_lower = question.lower()
        
        # 推荐类问题
        if any(keyword in question for keyword in ["推荐", "价值", "好股票", "值得投资"]):
            return "recommendation"
        
        # 财报类问题
        if any(keyword in question for keyword in ["财报", "利润", "收入", "ROE", "PE", "负债", "毛利率", "净利率", "现金流"]):
            return "financials"
        
        # 股东类问题
        if any(keyword in question for keyword in ["股东", "持仓", "机构", "持股"]):
            return "shareholders"
        
        # 产业链类问题
        if any(keyword in question for keyword in ["产业链", "供应商", "客户", "上游", "下游", "合作"]):
            return "supply_chain"
        
        # 风险类问题
        if any(keyword in question for keyword in ["风险", "影响", "传导", "关联"]):
            return "risk"
        
        # 新闻类问题
        if any(keyword in question for keyword in ["新闻", "消息", "公告", "动态", "最近"]):
            return "news"
        
        # 默认返回财务类
        return "financials"
    
    def query_recommendation(self, question: str, stocks: List[Dict]) -> Dict:
        """查询推荐数据"""
        try:
            # 从问题中提取筛选条件
            min_roe = 15.0
            max_debt = 50.0
            
            if "高ROE" in question or "高 ROE" in question:
                min_roe = 20.0
            if "低负债" in question or "低负债率" in question:
                max_debt = 40.0
            
            recommendations = self.recommendation_service.recommend_stocks(
                market="A",
                limit=10,
                min_roe=min_roe,
                max_debt_ratio=max_debt
            )
            
            return {
                "success": True,
                "data": recommendations,
                "count": len(recommendations),
                "query_params": {
                    "min_roe": min_roe,
                    "max_debt_ratio": max_debt
                }
            }
        except Exception as e:
            logger.error(f"查询推荐数据失败: {e}")
            return {"success": False, "error": str(e), "data": []}
    
    def query_financials(self, question: str, stocks: List[Dict]) -> Dict:
        """查询财报数据"""
        try:
            if not stocks:
                return {
                    "success": False,
                    "error": "未找到相关股票",
                    "data": []
                }
            
            stock_code = stocks[0]["stock_code"]
            stock_name = stocks[0]["name"]
            
            # 获取最新财报数据
            financial = self.db.query(Financial).filter(
                Financial.stock_code == stock_code
            ).order_by(Financial.report_date.desc()).first()
            
            if not financial:
                return {
                    "success": False,
                    "error": f"未找到 {stock_name} 的财报数据",
                    "data": []
                }
            
            # 构建财报数据
            data = {
                "stock_code": stock_code,
                "name": stock_name,
                "report_date": str(financial.report_date),
                "revenue": financial.revenue,
                "net_profit": financial.net_profit,
                "roe": financial.roe,
                "debt_ratio": financial.debt_ratio,
                "gross_margin": financial.gross_margin,
                "eps": financial.eps,
                "revenue_yoy": financial.revenue_yoy,
                "net_profit_yoy": financial.net_profit_yoy
            }
            
            return {
                "success": True,
                "data": data
            }
        except Exception as e:
            logger.error(f"查询财报数据失败: {e}")
            return {"success": False, "error": str(e), "data": {}}
    
    def query_shareholders(self, question: str, stocks: List[Dict]) -> Dict:
        """查询股东数据"""
        try:
            if not stocks:
                return {
                    "success": False,
                    "error": "未找到相关股票",
                    "data": []
                }
            
            stock_code = stocks[0]["stock_code"]
            stock_name = stocks[0]["name"]
            
            # 获取十大股东
            shareholders = self.db.query(Shareholder).filter(
                Shareholder.stock_code == stock_code
            ).order_by(Shareholder.report_date.desc(), Shareholder.rank).limit(10).all()
            
            # 获取机构持仓
            institutions = self.db.query(InstitutionalHolder).filter(
                InstitutionalHolder.stock_code == stock_code
            ).order_by(InstitutionalHolder.report_date.desc()).limit(10).all()
            
            data = {
                "stock_code": stock_code,
                "name": stock_name,
                "shareholders": [
                    {
                        "rank": s.rank,
                        "holder_name": s.holder_name,
                        "hold_amount": s.hold_amount,
                        "hold_ratio": s.hold_ratio,
                        "holder_type": s.holder_type,
                        "change": s.change
                    }
                    for s in shareholders
                ],
                "institutions": [
                    {
                        "institution_name": i.institution_name,
                        "institution_type": i.institution_type,
                        "hold_amount": i.hold_amount,
                        "hold_ratio": i.hold_ratio,
                        "change_ratio": i.change_ratio
                    }
                    for i in institutions
                ]
            }
            
            return {
                "success": True,
                "data": data
            }
        except Exception as e:
            logger.error(f"查询股东数据失败: {e}")
            return {"success": False, "error": str(e), "data": {}}
    
    def query_supply_chain(self, question: str, stocks: List[Dict]) -> Dict:
        """查询产业链数据（Neo4j）"""
        try:
            if not stocks:
                return {
                    "success": False,
                    "error": "未找到相关股票",
                    "data": []
                }
            
            stock_name = stocks[0]["name"]
            
            # 判断上游还是下游
            direction = "upstream"
            if "下游" in question or "客户" in question:
                direction = "downstream"
            
            supply_chain_data = self.kg_service.get_supply_chain(
                company_name=stock_name,
                direction=direction
            )
            
            return {
                "success": True,
                "data": supply_chain_data
            }
        except Exception as e:
            logger.error(f"查询产业链数据失败: {e}")
            return {"success": False, "error": str(e), "data": {}}
    
    def query_risk(self, question: str, stocks: List[Dict]) -> Dict:
        """查询风险传导数据（Neo4j）"""
        try:
            if not stocks:
                return {
                    "success": False,
                    "error": "未找到相关股票",
                    "data": []
                }
            
            stock_name = stocks[0]["name"]
            
            risk_data = self.kg_service.get_risk_propagation(
                company_name=stock_name,
                depth=3
            )
            
            return {
                "success": True,
                "data": risk_data
            }
        except Exception as e:
            logger.error(f"查询风险传导数据失败: {e}")
            return {"success": False, "error": str(e), "data": {}}
    
    def query_news(self, question: str, stocks: List[Dict]) -> Dict:
        """查询新闻数据"""
        try:
            query = self.db.query(News)
            
            # 如果有股票代码，筛选相关新闻
            if stocks:
                stock_code = stocks[0]["stock_code"]
                query = query.filter(
                    or_(
                        News.stock_code == stock_code,
                        News.title.contains(stocks[0]["name"])
                    )
                )
            
            news_list = query.order_by(News.created_at.desc()).limit(10).all()
            
            data = [
                {
                    "title": news.title,
                    "content": news.content,
                    "source": news.source,
                    "published_at": news.published_at,
                    "url": news.url
                }
                for news in news_list
            ]
            
            return {
                "success": True,
                "data": data,
                "count": len(data)
            }
        except Exception as e:
            logger.error(f"查询新闻数据失败: {e}")
            return {"success": False, "error": str(e), "data": []}
    
    def call_ollama(self, prompt: str) -> Optional[str]:
        """
        调用 Ollama LLM 生成回答
        
        Args:
            prompt: 提示词
        
        Returns:
            生成的回答，失败返回 None
        """
        try:
            response = httpx.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:0.5b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama 调用失败: {response.status_code}")
                return None
        except httpx.TimeoutException:
            logger.warning("Ollama 调用超时")
            return None
        except Exception as e:
            logger.error(f"Ollama 调用异常: {e}")
            return None
    
    def answer(self, question: str) -> Dict:
        """
        回答投资相关问题
        
        Args:
            question: 用户问题
        
        Returns:
            {
                "success": bool,
                "answer": str,
                "data_source": str,
                "related_stocks": List[str],
                "data": Any (结构化数据)
            }
        """
        # 1. 提取股票
        stocks = self.extract_stocks(question)
        related_stock_codes = [s["stock_code"] for s in stocks]
        
        # 2. 分类问题
        question_type = self.classify_question(question)
        
        # 3. 路由到不同数据源
        data_source = question_type
        query_result = {"success": False, "data": None}
        
        if question_type == "recommendation":
            query_result = self.query_recommendation(question, stocks)
        elif question_type == "financials":
            query_result = self.query_financials(question, stocks)
        elif question_type == "shareholders":
            query_result = self.query_shareholders(question, stocks)
        elif question_type == "supply_chain":
            query_result = self.query_supply_chain(question, stocks)
        elif question_type == "risk":
            query_result = self.query_risk(question, stocks)
        elif question_type == "news":
            query_result = self.query_news(question, stocks)
        
        if not query_result["success"]:
            return {
                "success": False,
                "answer": f"抱歉，查询数据失败：{query_result.get('error', '未知错误')}",
                "data_source": data_source,
                "related_stocks": related_stock_codes,
                "data": None
            }
        
        # 4. 尝试用 Ollama 生成自然语言回答
        data = query_result["data"]
        
        # 构建提示词
        prompt = f"基于以下数据回答问题：\n数据：{data}\n问题：{question}\n回答："
        
        llm_answer = self.call_ollama(prompt)
        
        if llm_answer:
            # LLM 调用成功
            return {
                "success": True,
                "answer": llm_answer,
                "data_source": data_source,
                "related_stocks": related_stock_codes,
                "data": data
            }
        else:
            # LLM 调用失败，返回结构化数据
            # 生成简单的回答
            simple_answer = self._generate_simple_answer(question, data_source, data, stocks)
            
            return {
                "success": True,
                "answer": simple_answer,
                "data_source": data_source,
                "related_stocks": related_stock_codes,
                "data": data,
                "llm_failed": True
            }
    
    def _generate_simple_answer(self, question: str, data_source: str, data: Any, stocks: List[Dict]) -> str:
        """
        生成简单回答（当 LLM 不可用时）
        
        Args:
            question: 用户问题
            data_source: 数据源类型
            data: 查询到的数据
            stocks: 相关股票
        
        Returns:
            简单回答
        """
        if data_source == "recommendation":
            if isinstance(data, list) and len(data) > 0:
                stock_names = [s["name"] for s in data[:5]]
                return f"根据筛选条件，推荐以下股票：{', '.join(stock_names)}。共找到 {len(data)} 只符合条件的股票。"
            return "未找到符合推荐条件的股票。"
        
        elif data_source == "financials":
            if isinstance(data, dict) and data:
                stock_name = data.get("name", "该股票")
                roe = data.get("roe")
                debt_ratio = data.get("debt_ratio")
                
                parts = [f"{stock_name}的最新财务数据："]
                if roe:
                    parts.append(f"ROE为{roe:.2f}%")
                if debt_ratio:
                    parts.append(f"负债率为{debt_ratio:.2f}%")
                
                return "，".join(parts) + "。"
            return "未找到相关财务数据。"
        
        elif data_source == "shareholders":
            if isinstance(data, dict) and data:
                stock_name = data.get("name", "该股票")
                shareholders = data.get("shareholders", [])
                if shareholders:
                    top3 = [s["holder_name"] for s in shareholders[:3]]
                    return f"{stock_name}的前三大股东：{', '.join(top3)}。"
            return "未找到股东数据。"
        
        elif data_source == "supply_chain":
            if isinstance(data, dict):
                company = data.get("company", "")
                direction = data.get("direction", "")
                entities = data.get("entities", [])
                
                if entities:
                    entity_names = [e.get("name", "") for e in entities[:5]]
                    direction_text = "上游供应商" if direction == "upstream" else "下游客户"
                    return f"{company}的{direction_text}包括：{', '.join(entity_names)}。"
            return "未找到产业链数据。"
        
        elif data_source == "risk":
            if isinstance(data, dict):
                source = data.get("source", "")
                affected = data.get("affected_companies", [])
                if affected:
                    affected_names = [c["name"] for c in affected[:5]]
                    return f"{source}的风险可能影响以下公司：{', '.join(affected_names)}。"
            return "未找到风险传导数据。"
        
        elif data_source == "news":
            if isinstance(data, list) and len(data) > 0:
                return f"找到 {len(data)} 条相关新闻。"
            return "未找到相关新闻。"
        
        return "查询完成，但无法生成回答。"
    
    def close(self):
        """关闭服务连接"""
        if self.kg_service:
            self.kg_service.close()
