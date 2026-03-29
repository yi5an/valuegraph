"""
知识图谱服务 - Neo4j 操作
"""
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging
import networkx as nx
from collections import defaultdict

logger = logging.getLogger(__name__)


class KnowledgeGraphService:
    """Neo4j 知识图谱服务"""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", 
                 password: str = "valuegraph2026"):
        """初始化 Neo4j 连接"""
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info("Neo4j 连接已建立")
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j 连接已关闭")
    
    def create_entity(self, name: str, entity_type: str, properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        创建实体节点
        
        Args:
            name: 实体名称
            entity_type: 实体类型 (company/person/stock/industry/event)
            properties: 实体属性
        
        Returns:
            是否创建成功
        """
        if properties is None:
            properties = {}
        
        properties['name'] = name
        properties['type'] = entity_type
        
        query = f"""
        MERGE (n:{entity_type} {{name: $name}})
        SET n += $properties
        RETURN n
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, name=name, properties=properties)
                return result.single() is not None
        except Exception as e:
            logger.error(f"创建实体失败 {name}: {e}")
            return False
    
    def create_relation(self, from_name: str, to_name: str, relation_type: str, 
                       properties: Optional[Dict[str, Any]] = None) -> bool:
        """
        创建关系
        
        Args:
            from_name: 起始实体名称
            to_name: 目标实体名称
            relation_type: 关系类型 (invests_in/competes_with/supplies_to/partner_of/ceo_of/located_in/RELATED_TO)
            properties: 关系属性
        
        Returns:
            是否创建成功
        """
        if properties is None:
            properties = {}
        
        # 使用 MERGE 避免重复关系
        query = f"""
        MATCH (a {{name: $from_name}})
        MATCH (b {{name: $to_name}})
        MERGE (a)-[r:{relation_type}]->(b)
        SET r += $properties
        RETURN r
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, from_name=from_name, to_name=to_name, 
                                   properties=properties)
                return result.single() is not None
        except Exception as e:
            logger.error(f"创建关系失败 {from_name}-[{relation_type}]->{to_name}: {e}")
            return False
    
    def get_entity_relations(self, name: str, depth: int = 2) -> Dict[str, Any]:
        """
        获取实体的关联图谱
        
        Args:
            name: 实体名称
            depth: 查询深度
        
        Returns:
            包含节点和关系的字典
        """
        query = f"""
        MATCH path = (center {{name: $name}})-[*1..{depth}]-(related)
        RETURN center, related, relationships(path) as rels
        """
        
        nodes = {}
        relationships = []
        
        try:
            with self.driver.session() as session:
                result = session.run(query, name=name)
                
                for record in result:
                    center = dict(record['center'])
                    related = dict(record['related'])
                    rels = record['rels']
                    
                    # 收集节点
                    if center['name'] not in nodes:
                        nodes[center['name']] = center
                    if related['name'] not in nodes:
                        nodes[related['name']] = related
                    
                    # 收集关系
                    for rel in rels:
                        rel_data = {
                            'type': rel.type,
                            'properties': dict(rel)
                        }
                        if rel_data not in relationships:
                            relationships.append(rel_data)
                
                return {
                    'center': name,
                    'nodes': list(nodes.values()),
                    'relationships': relationships
                }
        except Exception as e:
            logger.error(f"查询实体关系失败 {name}: {e}")
            return {'center': name, 'nodes': [], 'relationships': []}
    
    def find_path(self, from_name: str, to_name: str) -> List[Dict[str, Any]]:
        """
        查找两个实体间最短路径
        
        Args:
            from_name: 起始实体
            to_name: 目标实体
        
        Returns:
            路径上的节点和关系列表
        """
        query = """
        MATCH path = shortestPath((a {name: $from_name})-[*]-(b {name: $to_name}))
        RETURN nodes(path) as nodes, relationships(path) as rels
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, from_name=from_name, to_name=to_name)
                record = result.single()
                
                if record:
                    nodes = [dict(n) for n in record['nodes']]
                    rels = [{'type': r.type, 'properties': dict(r)} for r in record['rels']]
                    return [{'nodes': nodes, 'relationships': rels}]
                return []
        except Exception as e:
            logger.error(f"查找路径失败 {from_name} -> {to_name}: {e}")
            return []
    
    def get_supply_chain(self, company_name: str, direction: str = "upstream") -> Dict[str, Any]:
        """
        产业链查询
        
        Args:
            company_name: 公司名称
            direction: upstream=上游供应商, downstream=下游客户
        
        Returns:
            产业链数据
        """
        if direction == "upstream":
            rel_type = "supplies_to"
            query = f"""
            MATCH (supplier)-[:supplies_to]->(company {{name: $name}})
            RETURN supplier
            """
        else:
            rel_type = "supplies_to"
            query = f"""
            MATCH (company {{name: $name}})-[:supplies_to]->(customer)
            RETURN customer
            """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, name=company_name)
                entities = [dict(record[0]) for record in result]
                
                return {
                    'company': company_name,
                    'direction': direction,
                    'entities': entities,
                    'count': len(entities)
                }
        except Exception as e:
            logger.error(f"查询产业链失败 {company_name}: {e}")
            return {'company': company_name, 'direction': direction, 'entities': [], 'count': 0}
    
    def get_risk_propagation(self, company_name: str, depth: int = 3) -> Dict[str, Any]:
        """
        风险传导分析 - 返回可能受影响的关联公司
        
        Args:
            company_name: 公司名称
            depth: 传导深度
        
        Returns:
            风险传导路径和受影响公司
        """
        # 查找所有关联公司（投资、合作、供应链关系）
        query = f"""
        MATCH path = (center {{name: $name}})-[*1..{depth}]-(related)
        WHERE related:company OR related:stock
        WITH related, path
        RETURN DISTINCT related, 
               min(length(path)) as distance,
               [r in relationships(path) | type(r)] as rel_types
        ORDER BY distance
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, name=company_name)
                
                affected_companies = []
                for record in result:
                    company = dict(record['related'])
                    affected_companies.append({
                        'name': company.get('name'),
                        'type': company.get('type'),
                        'distance': record['distance'],
                        'relationship_path': record['rel_types']
                    })
                
                return {
                    'source': company_name,
                    'depth': depth,
                    'affected_companies': affected_companies,
                    'total_affected': len(affected_companies)
                }
        except Exception as e:
            logger.error(f"风险传导分析失败 {company_name}: {e}")
            return {'source': company_name, 'depth': depth, 'affected_companies': [], 'total_affected': 0}
    
    def get_graph_data(self, center_name: str, depth: int = 2) -> Dict[str, Any]:
        """
        获取可视化数据（nodes + edges 格式，给前端用）
        
        Args:
            center_name: 中心实体名称
            depth: 查询深度
        
        Returns:
            可视化格式的图谱数据
        """
        query = f"""
        MATCH path = (center {{name: $name}})-[*1..{depth}]-(related)
        RETURN center, related, relationships(path) as rels
        """
        
        nodes = {}
        edges = []
        edge_set = set()
        
        try:
            with self.driver.session() as session:
                result = session.run(query, name=center_name)
                
                for record in result:
                    center = dict(record['center'])
                    related = dict(record['related'])
                    rels = record['rels']
                    
                    # 添加节点（确保唯一）
                    if center['name'] not in nodes:
                        nodes[center['name']] = {
                            'id': center['name'],
                            'label': center['name'],
                            'type': center.get('type', 'unknown'),
                            **center
                        }
                    
                    if related['name'] not in nodes:
                        nodes[related['name']] = {
                            'id': related['name'],
                            'label': related['name'],
                            'type': related.get('type', 'unknown'),
                            **related
                        }
                    
                    # 添加边（确保唯一）
                    for rel in rels:
                        edge_id = f"{rel.start_node.id}-{rel.type}-{rel.end_node.id}"
                        if edge_id not in edge_set:
                            edge_set.add(edge_id)
                            edges.append({
                                'source': list(nodes.keys())[-2] if len(nodes) > 1 else center['name'],
                                'target': list(nodes.keys())[-1] if nodes else related['name'],
                                'type': rel.type,
                                'properties': dict(rel)
                            })
                
                return {
                    'center': center_name,
                    'nodes': list(nodes.values()),
                    'edges': edges,
                    'stats': {
                        'node_count': len(nodes),
                        'edge_count': len(edges)
                    }
                }
        except Exception as e:
            logger.error(f"获取图谱数据失败 {center_name}: {e}")
            return {'center': center_name, 'nodes': [], 'edges': [], 'stats': {'node_count': 0, 'edge_count': 0}}
    
    def get_entity_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取实体详细信息
        
        Args:
            name: 实体名称
        
        Returns:
            实体信息和相关关系
        """
        query = """
        MATCH (n {name: $name})
        OPTIONAL MATCH (n)-[r]->(m)
        OPTIONAL MATCH (p)-[s]->(n)
        RETURN n as entity, 
               collect(DISTINCT {type: type(r), target: m.name}) as outgoing,
               collect(DISTINCT {type: type(s), source: p.name}) as incoming
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, name=name)
                record = result.single()
                
                if record and record['entity']:
                    entity = dict(record['entity'])
                    return {
                        'entity': entity,
                        'outgoing_relations': [r for r in record['outgoing'] if r['target']],
                        'incoming_relations': [r for r in record['incoming'] if r['source']]
                    }
                return None
        except Exception as e:
            logger.error(f"获取实体信息失败 {name}: {e}")
            return None
    
    def clear_all(self) -> bool:
        """清空所有数据（用于测试）"""
        query = "MATCH (n) DETACH DELETE n"
        try:
            with self.driver.session() as session:
                session.run(query)
                logger.warning("已清空 Neo4j 所有数据")
                return True
        except Exception as e:
            logger.error(f"清空数据失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """获取图谱统计信息"""
        try:
            with self.driver.session() as session:
                node_count = session.run("MATCH (n) RETURN count(n) as count").single()['count']
                rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
                return {'nodes': node_count, 'relationships': rel_count}
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {'nodes': 0, 'relationships': 0}
    
    def compute_pagerank(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        计算实体影响力排名（PageRank算法）
        
        使用 NetworkX 实现 PageRank（兼容 Neo4j Community 版）
        
        Args:
            top_n: 返回前 N 个实体
        
        Returns:
            [{name, score, type}]
        """
        try:
            # 1. 从 Neo4j 导出图数据到 NetworkX
            G = nx.DiGraph()
            
            # 获取所有节点
            with self.driver.session() as session:
                nodes_result = session.run("MATCH (n) RETURN n.name as name, n.type as type, labels(n) as labels")
                
                node_types = {}
                for record in nodes_result:
                    name = record['name']
                    node_type = record['type'] or (record['labels'][0] if record['labels'] else 'unknown')
                    node_types[name] = node_type
                    G.add_node(name)
                
                # 获取所有关系
                edges_result = session.run("MATCH (a)-[r]->(b) RETURN a.name as from_name, b.name as to_name")
                
                for record in edges_result:
                    from_name = record['from_name']
                    to_name = record['to_name']
                    if from_name and to_name:
                        G.add_edge(from_name, to_name)
            
            if G.number_of_nodes() == 0:
                logger.warning("图谱为空，无法计算 PageRank")
                return []
            
            # 2. 计算 PageRank
            pagerank_scores = nx.pagerank(G, alpha=0.85, max_iter=100)
            
            # 3. 排序并返回 top_n
            sorted_nodes = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
            
            result = []
            for name, score in sorted_nodes:
                result.append({
                    'name': name,
                    'score': round(score, 6),
                    'type': node_types.get(name, 'unknown')
                })
            
            logger.info(f"✅ PageRank 计算完成，返回前 {len(result)} 个实体")
            return result
        
        except Exception as e:
            logger.error(f"❌ PageRank 计算失败: {e}")
            return []
