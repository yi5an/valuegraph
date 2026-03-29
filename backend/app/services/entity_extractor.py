"""
实体抽取服务 - 从新闻中提取实体和关系
优先使用 LLM（Ollama），失败则 fallback 到规则匹配
"""
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.stock import Stock
from app.services.knowledge_graph import KnowledgeGraphService
from app.services.llm_extractor import LLMExtractor
import logging
import re

logger = logging.getLogger(__name__)


# 政府机构实体列表
GOVERNMENT_ENTITIES = [
    "央行", "中国人民银行", "国务院", "发改委", "国家发改委",
    "财政部", "证监会", "银保监会", "国家金融监督管理总局",
    "工信部", "商务部", "住建部", "自然资源部", "生态环境部",
    "科技部", "教育部", "卫健委", "人社部", "交通运输部",
    "最高法", "最高检", "全国人大", "政协",
    "美联储", "欧洲央行", "日本央行", "英央行",
]

# 政策关键词列表
POLICY_KEYWORDS = [
    "政策", "监管", "法规", "条例", "意见", "通知", "办法", "规定",
    "改革", "开放", "审批", "许可", "处罚", "整改", "约谈",
    "降准", "降息", "加息", "LPR", "MLF", "逆回购",
    "IPO", "注册制", "退市", "减持", "增持",
    "关税", "贸易战", "制裁", "出口管制",
    "碳中和", "双碳", "新能源补贴",
]


class EntityExtractor:
    """从新闻中抽取实体和关系"""

    def __init__(self, db: Session, kg_service: Optional[KnowledgeGraphService] = None):
        """
        初始化

        Args:
            db: 数据库会话
            kg_service: 知识图谱服务（可选）
        """
        self.db = db
        self.kg_service = kg_service or KnowledgeGraphService()
        self.llm_extractor = LLMExtractor()
        self._stock_names = None
        self._stock_map = None

        # 关系关键词映射
        self.relation_keywords = {
            'invests_in': ['投资', '入股', '参股', '注资', '融资', '领投', '跟投'],
            'competes_with': ['竞争', '对手', '竞品', '对标', 'PK', '抗衡'],
            'supplies_to': ['供应', '采购', '供应商', '采购商', '供货', '订单'],
            'partner_of': ['合作', '签约', '战略协议', '联合', '携手', '共建'],
            'REGULATED_BY': ['监管', '处罚', '约谈', '整改', '审批', '许可', '批准'],
            'RELATED_TO': []  # 默认共现关系
        }

        # 事件类型关键词映射（按优先级排序）
        self.event_keywords = {
            'policy': POLICY_KEYWORDS,  # policy 优先级最高
            'M&A': ['收购', '并购', '合并', '重组', '并购重组', '兼并', '收购案', '并购案', '私有化', '要约收购'],
            'earnings': ['财报', '业绩', '年报', '季报', '营收', '净利润', '盈利', '亏损', '业绩预告', '业绩快报', '业绩发布', '财报披露', '业绩大增', '业绩下滑'],
            'personnel': ['人事变动', '人事调整', '高管离职', '高管变动', 'CEO', '董事长', '总经理', '辞职', '任命', '聘任', '换届', '离职'],
            'regulation': ['监管', '处罚', '罚款', '监管函', '问询函', '证监会', '银保监会', '法规', '新规', '监管层', '监管政策', '监管要求'],
            'monetary_policy': ['央行', '利率', '货币', '流动性', '存款准备金', '公开市场操作'],
            'litigation': ['诉讼', '起诉', '仲裁', '纠纷', '官司', '索赔', '侵权', '反垄断', '集体诉讼', '法律诉讼', '涉诉']
        }
    
    def _load_stocks(self) -> Tuple[List[str], Dict[str, str]]:
        """
        从数据库加载股票名称列表
        
        Returns:
            (股票名称列表, 股票名称->代码映射)
        """
        if self._stock_names is None:
            stocks = self.db.query(Stock.stock_code, Stock.name).all()
            self._stock_names = [stock.name for stock in stocks]
            self._stock_map = {stock.name: stock.stock_code for stock in stocks}
            logger.info(f"已加载 {len(self._stock_names)} 只股票名称")
        
        return self._stock_names, self._stock_map
    
    def extract_companies(self, text: str) -> List[str]:
        """
        从文本中提取公司名称

        Args:
            text: 新闻文本

        Returns:
            匹配到的公司名称列表
        """
        stock_names, _ = self._load_stocks()
        found_companies = []

        # 按长度降序排序，优先匹配长名称（避免部分匹配）
        for name in sorted(stock_names, key=len, reverse=True):
            if name in text and name not in found_companies:
                found_companies.append(name)

        return found_companies

    def extract_government_entities(self, text: str) -> List[str]:
        """
        从文本中提取政府机构名称

        Args:
            text: 新闻文本

        Returns:
            匹配到的政府机构名称列表
        """
        found_entities = []

        # 按长度降序排序，优先匹配长名称（避免部分匹配）
        for entity in sorted(GOVERNMENT_ENTITIES, key=len, reverse=True):
            if entity in text and entity not in found_entities:
                found_entities.append(entity)

        return found_entities
    
    def detect_relation_type(self, text: str, company1: str, company2: str) -> str:
        """
        检测两个公司之间的关系类型
        
        Args:
            text: 新闻文本
            company1: 公司1
            company2: 公司2
        
        Returns:
            关系类型
        """
        # 提取两个公司之间的文本片段
        idx1 = text.find(company1)
        idx2 = text.find(company2)
        
        if idx1 == -1 or idx2 == -1:
            return 'RELATED_TO'
        
        # 获取两个公司之间的上下文
        start = min(idx1, idx2)
        end = max(idx1, idx2) + len(text[max(idx1, idx2) == idx1 and company1 or company2])
        context = text[start:end]
        
        # 匹配关系关键词
        for relation_type, keywords in self.relation_keywords.items():
            for keyword in keywords:
                if keyword in context:
                    return relation_type
        
        # 默认返回共现关系
        return 'RELATED_TO'
    
    def classify_event_type(self, text: str) -> str:
        """
        分类新闻事件类型（policy 优先级最高）

        Args:
            text: 新闻文本

        Returns:
            事件类型：policy, M&A, earnings, personnel, regulation, monetary_policy, litigation, 或 general
        """
        # 优先检测 policy（最高优先级）
        for keyword in POLICY_KEYWORDS:
            if keyword in text:
                return 'policy'

        # 然后按优先级顺序检测其他类型（从具体到一般）
        for event_type, keywords in self.event_keywords.items():
            if event_type == 'policy':  # 已经检测过，跳过
                continue
            for keyword in keywords:
                if keyword in text:
                    return event_type

        # 默认返回普通事件
        return 'general'
    
    async def extract_from_news(self, title: str, content: str, stock_code: Optional[str] = None) -> Dict[str, Any]:
        """
        从新闻中抽取实体和关系（优先 LLM，失败则用规则）
        
        Args:
            title: 新闻标题
            content: 新闻内容
            stock_code: 关联股票代码（可选）
        
        Returns:
            {
                'entities': [{'name': '...', 'type': 'company', ...}],
                'relations': [{'from': '...', 'to': '...', 'type': '...', ...}],
                'event_type': 'M&A|earnings|personnel|regulation|litigation|general'
            }
        """
        # 合并标题和内容
        full_text = f"{title} {content or ''}"
        
        # 分类事件类型
        event_type = self.classify_event_type(full_text)
        
        # 尝试使用 LLM 抽取
        try:
            llm_result = await self.llm_extractor.extract(full_text)
            
            if llm_result['entities'] or llm_result['relations']:
                # LLM 抽取成功
                logger.info(f"[LLM] 从新闻中提取 {len(llm_result['entities'])} 个实体, {len(llm_result['relations'])} 个关系: {title[:50]}")
                llm_result['event_type'] = event_type
                return llm_result
        except Exception as e:
            logger.warning(f"LLM 抽取失败，fallback 到规则: {e}")
        
        # Fallback: 使用规则抽取
        logger.info(f"[规则] 使用规则抽取: {title[:50]}")
        result = await self._extract_with_rules(full_text, title, content, stock_code)
        result['event_type'] = event_type
        return result
    
    async def _extract_with_rules(self, full_text: str, title: str, content: str, stock_code: Optional[str] = None) -> Dict[str, Any]:
        """
        使用规则抽取实体和关系（fallback 方案）

        Args:
            full_text: 完整文本（标题+内容）
            title: 新闻标题
            content: 新闻内容
            stock_code: 关联股票代码（可选）

        Returns:
            {
                'entities': [{'name': '...', 'type': 'company', ...}],
                'relations': [{'from': '...', 'to': '...', 'type': '...', ...}]
            }
        """

        # 提取公司名称
        companies = self.extract_companies(full_text)

        # 提取政府机构实体
        government_entities = self.extract_government_entities(full_text)

        if not companies and not government_entities:
            logger.debug(f"未找到实体: {title}")
            return {'entities': [], 'relations': []}

        # 创建实体列表
        entities = []
        _, stock_map = self._load_stocks()

        # 添加公司实体
        for company in companies:
            entity = {
                'name': company,
                'type': 'company',
                'stock_code': stock_map.get(company)
            }
            entities.append(entity)

            # 添加到 Neo4j
            if self.kg_service:
                self.kg_service.create_entity(
                    name=company,
                    entity_type='company',
                    properties={'stock_code': entity['stock_code']}
                )

        # 添加政府机构实体
        for gov_entity in government_entities:
            entity = {
                'name': gov_entity,
                'type': 'government'
            }
            entities.append(entity)

            # 添加到 Neo4j（类型为 government）
            if self.kg_service:
                self.kg_service.create_entity(
                    name=gov_entity,
                    entity_type='government',
                    properties={}
                )

        # 创建关系
        relations = []

        # 如果新闻关联了特定股票，优先创建该股票与其他公司的关系
        if stock_code:
            stock = self.db.query(Stock).filter(Stock.stock_code == stock_code).first()
            if stock and stock.name not in companies:
                companies.insert(0, stock.name)
                entities.insert(0, {
                    'name': stock.name,
                    'type': 'stock',
                    'stock_code': stock_code
                })
                if self.kg_service:
                    self.kg_service.create_entity(
                        name=stock.name,
                        entity_type='stock',
                        properties={'stock_code': stock_code}
                    )

        # 对每对公司创建关系
        for i, company1 in enumerate(companies):
            for company2 in companies[i+1:]:
                relation_type = self.detect_relation_type(full_text, company1, company2)

                relation = {
                    'from': company1,
                    'to': company2,
                    'type': relation_type,
                    'source': 'news'
                }
                relations.append(relation)

                # 添加到 Neo4j
                if self.kg_service:
                    self.kg_service.create_relation(
                        from_name=company1,
                        to_name=company2,
                        relation_type=relation_type
                    )

        # 对公司和政府机构创建 REGULATED_BY 关系
        if companies and government_entities:
            for company in companies:
                for gov_entity in government_entities:
                    # 检测是否包含监管类关键词
                    if any(kw in full_text for kw in ['监管', '处罚', '约谈', '整改', '审批', '许可', '批准']):
                        relation = {
                            'from': company,
                            'to': gov_entity,
                            'type': 'REGULATED_BY',
                            'source': 'news'
                        }
                        relations.append(relation)

                        # 添加到 Neo4j
                        if self.kg_service:
                            self.kg_service.create_relation(
                                from_name=company,
                                to_name=gov_entity,
                                relation_type='REGULATED_BY'
                            )

        logger.info(f"从新闻中提取 {len(entities)} 个实体, {len(relations)} 个关系: {title[:50]}")

        return {
            'entities': entities,
            'relations': relations
        }
    
    async def extract_from_news_list(self, news_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量从新闻列表中抽取实体和关系
        
        Args:
            news_list: 新闻列表 [{'title': '...', 'content': '...', 'stock_code': '...'}, ...]
        
        Returns:
            统计信息
        """
        total_entities = 0
        total_relations = 0
        processed = 0
        errors = 0
        
        for news in news_list:
            try:
                result = await self.extract_from_news(
                    title=news.get('title', ''),
                    content=news.get('content', ''),
                    stock_code=news.get('stock_code')
                )
                
                total_entities += len(result['entities'])
                total_relations += len(result['relations'])
                processed += 1
                
            except Exception as e:
                logger.error(f"处理新闻失败: {e}")
                errors += 1
        
        return {
            'processed': processed,
            'total_entities': total_entities,
            'total_relations': total_relations,
            'errors': errors
        }
    
    async def close(self):
        """关闭知识图谱连接和 LLM 客户端"""
        if self.kg_service:
            self.kg_service.close()
        if self.llm_extractor:
            await self.llm_extractor.close()
