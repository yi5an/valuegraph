"""
图谱算法服务 - 社区发现（产业链发现）
"""
import logging
from typing import Dict, Any, List
from app.services.knowledge_graph import KnowledgeGraphService

logger = logging.getLogger(__name__)


class GraphAlgorithms:
    """图谱算法服务"""

    def __init__(self, kg_service: KnowledgeGraphService):
        self.kg = kg_service

    def find_community(self, entity_name: str, max_depth: int = 3) -> Dict[str, Any]:
        """
        查找实体所在的关联社区

        使用 Neo4j Cypher 查询实现：
        1. 查找所有与该实体通过关系连接的实体（BFS）
        2. 按关系类型分组
        3. 计算关系密度

        Args:
            entity_name: 实体名称
            max_depth: 最大搜索深度

        Returns:
            {entity, community_size, members, density}
        """
        # Cypher 查询：获取社区内所有实体和关系
        query = f"""
        MATCH path = (center {{name: $name}})-[*1..{max_depth}]-(related)
        WHERE center.name = $name
        WITH DISTINCT related, 
             [r in relationships(path) | type(r)] as rel_types
        RETURN related.name as name, 
               related.type as type,
               rel_types
        """

        members = []
        rel_type_counter = {}

        try:
            with self.kg.driver.session() as session:
                # 验证实体存在
                check = session.run(
                    "MATCH (n {name: $name}) RETURN n.name as name LIMIT 1",
                    name=entity_name
                ).single()

                if not check:
                    return {
                        "entity": entity_name,
                        "community_size": 0,
                        "members": [],
                        "density": 0,
                        "message": f"实体 '{entity_name}' 不存在"
                    }

                # 获取社区成员
                result = session.run(query, name=entity_name)

                for record in result:
                    member = {
                        "name": record["name"],
                        "type": record.get("type", "unknown"),
                        "relation_type": record["rel_types"][0] if record["rel_types"] else "unknown"
                    }
                    members.append(member)

                    # 统计关系类型
                    for rt in record["rel_types"]:
                        rel_type_counter[rt] = rel_type_counter.get(rt, 0) + 1

                # 计算关系密度：实际关系数 / 最大可能关系数
                n = len(members)
                if n <= 1:
                    density = 0.0
                else:
                    # 查询社区内的实际关系数
                    if members:
                        member_names = [m["name"] for m in members]
                        member_names.append(entity_name)  # 包含中心实体
                        count_query = """
                        MATCH (a)-[r]->(b)
                        WHERE a.name IN $names AND b.name IN $names
                        RETURN count(DISTINCT r) as rel_count
                        """
                        count_result = session.run(count_query, names=member_names).single()
                        actual_rels = count_result["rel_count"] if count_result else 0
                    else:
                        actual_rels = 0

                    max_rels = n * (n - 1)  # 有向图最大关系数（包含中心实体）
                    density = round(actual_rels / max_rels, 4) if max_rels > 0 else 0

            return {
                "entity": entity_name,
                "community_size": len(members),
                "members": members,
                "density": density,
                "relation_types": rel_type_counter
            }

        except Exception as e:
            logger.error(f"社区发现失败 {entity_name}: {e}")
            return {
                "entity": entity_name,
                "community_size": 0,
                "members": [],
                "density": 0,
                "error": str(e)
            }
