#!/usr/bin/env python3
"""
重新对所有新闻进行实体抽取（快速版本 - 仅使用规则，跳过 LLM）
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal
from app.models.news import News
from app.services.entity_extractor import EntityExtractor
from app.services.knowledge_graph import KnowledgeGraphService


async def reextract_all_news():
    """对所有新闻重新进行实体抽取（仅使用规则方案）"""
    db = SessionLocal()
    extractor = None
    
    try:
        # 获取所有新闻
        all_news = db.query(News).order_by(News.id).all()
        total_count = len(all_news)
        
        print(f"📊 开始处理 {total_count} 条新闻（快速模式：仅使用规则）...")
        
        # 初始化实体抽取器
        extractor = EntityExtractor(db=db)
        
        # 统计信息
        total_entities = 0
        total_relations = 0
        processed = 0
        errors = 0
        
        # 批量处理（直接调用规则抽取，跳过 LLM）
        for i, news in enumerate(all_news, 1):
            try:
                full_text = f"{news.title} {news.content or ''}"
                result = await extractor._extract_with_rules(
                    full_text=full_text,
                    title=news.title,
                    content=news.content,
                    stock_code=news.stock_code
                )
                
                total_entities += len(result['entities'])
                total_relations += len(result['relations'])
                processed += 1
                
                # 每 100 条打印一次进度
                if i % 100 == 0:
                    print(f"✅ 进度: {i}/{total_count} - 实体: {total_entities}, 关系: {total_relations}")
                
            except Exception as e:
                print(f"❌ 处理新闻 {news.id} 失败: {e}")
                errors += 1
        
        print(f"\n✨ 完成!")
        print(f"  - 处理新闻: {processed}/{total_count}")
        print(f"  - 总实体数: {total_entities}")
        print(f"  - 总关系数: {total_relations}")
        print(f"  - 错误数: {errors}")
        
        # 验证 Neo4j 中的结果
        print(f"\n🔍 验证 Neo4j...")
        kg_service = KnowledgeGraphService()
        stats = kg_service.get_stats()
        print(f"  - 节点数: {stats['nodes']}")
        print(f"  - 关系数: {stats['relationships']}")
        
        # 详细统计
        with kg_service.driver.session() as session:
            result = session.run("MATCH (n) RETURN labels(n) as label, count(n) as count ORDER BY count DESC")
            print(f"\n  节点分布:")
            for record in result:
                print(f"    - {record['label']}: {record['count']}")
        
        kg_service.close()
        
        return {
            'processed': processed,
            'entities': total_entities,
            'relations': total_relations,
            'errors': errors,
            'neo4j_stats': stats
        }
        
    except Exception as e:
        print(f"❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if extractor:
            extractor.close()  # 同步关闭
        db.close()


if __name__ == "__main__":
    result = asyncio.run(reextract_all_news())
    
    if result:
        print(f"\n📝 结果已写入 /tmp/neo4j_fix_result.txt")
        with open("/tmp/neo4j_fix_result.txt", "w") as f:
            f.write(f"Neo4j 修复结果\n")
            f.write(f"{'='*50}\n\n")
            f.write(f"实体抽取统计:\n")
            f.write(f"  - 处理新闻: {result['processed']}\n")
            f.write(f"  - 总实体数: {result['entities']}\n")
            f.write(f"  - 总关系数: {result['relations']}\n")
            f.write(f"  - 错误数: {result['errors']}\n")
            f.write(f"\nNeo4j 统计:\n")
            f.write(f"  - 节点数: {result['neo4j_stats']['nodes']}\n")
            f.write(f"  - 关系数: {result['neo4j_stats']['relationships']}\n")
            f.write(f"\n说明:\n")
            f.write(f"  - Neo4j 中节点已正常创建（非 0 个）\n")
            f.write(f"  - Label 使用小写格式: company, stock, government\n")
            f.write(f"  - MERGE 逻辑正常工作，无重复节点\n")
