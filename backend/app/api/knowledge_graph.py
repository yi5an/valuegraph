"""
知识图谱 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.news import News
from app.services.knowledge_graph import KnowledgeGraphService
from app.services.entity_extractor import EntityExtractor
from app.services.graph_algorithms import GraphAlgorithms

router = APIRouter()


# ========== 请求/响应模型 ==========

class ExtractRequest(BaseModel):
    """实体抽取请求"""
    news_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    stock_code: Optional[str] = None


class ExtractResponse(BaseModel):
    """实体抽取响应"""
    entities: list
    relations: list
    message: str


class SyncNewsResponse(BaseModel):
    """批量同步新闻响应"""
    processed: int
    total_entities: int
    total_relations: int
    errors: int
    message: str


# ========== API 端点 ==========

@router.post("/extract", response_model=ExtractResponse, summary="对新闻做实体抽取（使用 LLM）")
async def extract_entities(request: ExtractRequest, db: Session = Depends(get_db)):
    """
    对新闻做实体抽取（优先使用 LLM，失败则 fallback 到规则）
    
    - **news_id**: 新闻ID（如果提供，将从数据库读取新闻）
    - **title**: 新闻标题（如果未提供news_id，则必须提供）
    - **content**: 新闻内容
    - **stock_code**: 关联股票代码
    """
    # 如果提供了 news_id，从数据库读取
    if request.news_id:
        news = db.query(News).filter(News.id == request.news_id).first()
        if not news:
            raise HTTPException(status_code=404, detail=f"新闻 {request.news_id} 不存在")
        
        title = news.title
        content = news.content
        stock_code = news.stock_code
    else:
        title = request.title
        content = request.content
        stock_code = request.stock_code
    
    if not title:
        raise HTTPException(status_code=400, detail="必须提供 title 或 news_id")
    
    # 执行实体抽取（使用 LLM）
    kg_service = KnowledgeGraphService()
    extractor = EntityExtractor(db, kg_service)
    
    try:
        result = await extractor.extract_from_news(
            title=title,
            content=content or '',
            stock_code=stock_code
        )
        
        return ExtractResponse(
            entities=result['entities'],
            relations=result['relations'],
            message=f"成功提取 {len(result['entities'])} 个实体, {len(result['relations'])} 个关系"
        )
    finally:
        await extractor.close()


@router.get("/entity/{name}", summary="查询实体详情和关系")
def get_entity(name: str, db: Session = Depends(get_db)):
    """
    查询实体详情和关系
    
    - **name**: 实体名称（公司名）
    """
    kg_service = KnowledgeGraphService()
    
    try:
        entity_info = kg_service.get_entity_info(name)
        
        if not entity_info:
            raise HTTPException(status_code=404, detail=f"实体 '{name}' 不存在")
        
        return entity_info
    finally:
        kg_service.close()


@router.get("/graph/{name}", summary="获取可视化图谱数据")
def get_graph(name: str, depth: int = Query(2, ge=1, le=5, description="查询深度")):
    """
    获取可视化图谱数据（nodes + edges 格式）
    
    - **name**: 中心实体名称
    - **depth**: 查询深度（1-5）
    """
    kg_service = KnowledgeGraphService()
    
    try:
        graph_data = kg_service.get_graph_data(name, depth)
        return graph_data
    finally:
        kg_service.close()


@router.get("/supply_chain/{name}", summary="产业链查询")
def get_supply_chain(
    name: str, 
    direction: str = Query("upstream", regex="^(upstream|downstream)$", description="查询方向")
):
    """
    产业链查询
    
    - **name**: 公司名称
    - **direction**: upstream=上游供应商, downstream=下游客户
    """
    kg_service = KnowledgeGraphService()
    
    try:
        supply_chain = kg_service.get_supply_chain(name, direction)
        return supply_chain
    finally:
        kg_service.close()


@router.get("/risk/{name}", summary="风险传导分析")
def get_risk_propagation(
    name: str, 
    depth: int = Query(3, ge=1, le=5, description="传导深度")
):
    """
    风险传导分析 - 返回可能受影响的关联公司
    
    - **name**: 公司名称
    - **depth**: 传导深度（1-5）
    """
    kg_service = KnowledgeGraphService()
    
    try:
        risk_data = kg_service.get_risk_propagation(name, depth)
        return risk_data
    finally:
        kg_service.close()


@router.get("/path", summary="最短路径查询")
def find_path(
    from_name: str = Query(..., description="起始实体名称"),
    to_name: str = Query(..., description="目标实体名称")
):
    """
    查找两个实体间最短路径
    
    - **from_name**: 起始实体名称
    - **to_name**: 目标实体名称
    """
    kg_service = KnowledgeGraphService()
    
    try:
        path = kg_service.find_path(from_name, to_name)
        
        if not path:
            raise HTTPException(status_code=404, detail=f"未找到 {from_name} 到 {to_name} 的路径")
        
        return {
            'from': from_name,
            'to': to_name,
            'path': path
        }
    finally:
        kg_service.close()


@router.post("/sync_news", response_model=SyncNewsResponse, summary="批量对已入库新闻做实体抽取（使用 LLM）")
async def sync_news(db: Session = Depends(get_db)):
    """
    批量对已入库新闻做实体抽取（优先使用 LLM，失败则 fallback 到规则）
    
    将处理 news 表中的所有新闻，提取实体和关系并写入 Neo4j
    """
    # 获取所有新闻
    news_list = db.query(News).all()
    
    if not news_list:
        return SyncNewsResponse(
            processed=0,
            total_entities=0,
            total_relations=0,
            errors=0,
            message="数据库中没有新闻"
        )
    
    # 转换为字典列表
    news_data = [
        {
            'title': news.title,
            'content': news.content,
            'stock_code': news.stock_code
        }
        for news in news_list
    ]
    
    # 批量抽取（使用 LLM）
    kg_service = KnowledgeGraphService()
    extractor = EntityExtractor(db, kg_service)
    
    try:
        result = await extractor.extract_from_news_list(news_data)
        
        return SyncNewsResponse(
            processed=result['processed'],
            total_entities=result['total_entities'],
            total_relations=result['total_relations'],
            errors=result['errors'],
            message=f"成功处理 {result['processed']} 条新闻，"
                   f"提取 {result['total_entities']} 个实体，"
                   f"{result['total_relations']} 个关系"
        )
    finally:
        await extractor.close()


@router.get("/community/{name}", summary="社区发现（产业链发现）")
def get_community(
    name: str,
    depth: int = Query(3, ge=1, le=5, description="搜索深度")
):
    """
    查询实体所在社区（产业链发现）

    - **name**: 实体名称
    - **depth**: 搜索深度（1-5）

    返回：entity, community_size, members, density, relation_types
    """
    kg_service = KnowledgeGraphService()

    try:
        algo = GraphAlgorithms(kg_service)
        result = algo.find_community(name, max_depth=depth)
        return {
            "success": True,
            "data": result
        }
    finally:
        kg_service.close()


@router.get("/anomalies", summary="获取所有异常关联")
def get_anomalies(db: Session = Depends(get_db)):
    """获取所有异常关联检测"""
    from app.services.anomaly_detector import AnomalyDetector
    detector = AnomalyDetector(db)
    anomalies = detector.detect_anomaly_relations()
    return {"success": True, "data": anomalies, "total": len(anomalies)}


@router.get("/anomalies/{stock_code}", summary="获取某股票的异常关联")
def get_stock_anomalies(stock_code: str, db: Session = Depends(get_db)):
    """获取某股票的异常关联检测"""
    from app.services.anomaly_detector import AnomalyDetector
    detector = AnomalyDetector(db)
    anomalies = detector.detect_anomaly_relations(stock_code=stock_code)
    return {"success": True, "data": anomalies, "total": len(anomalies), "stock_code": stock_code}


@router.get("/stats", summary="获取图谱统计信息")
def get_stats():
    """获取 Neo4j 图谱统计信息"""
    kg_service = KnowledgeGraphService()
    
    try:
        stats = kg_service.get_stats()
        return {
            'status': 'ok',
            'stats': stats
        }
    finally:
        kg_service.close()


@router.get("/influence", summary="影响力排名（PageRank）")
def get_influence_ranking(
    top: int = Query(20, ge=1, le=100, description="返回前 N 个实体")
):
    """
    获取实体影响力排名（基于 PageRank 算法）
    
    - **top**: 返回前 N 个实体（1-100）
    
    返回格式：[{name, score, type}]
    """
    kg_service = KnowledgeGraphService()
    
    try:
        ranking = kg_service.compute_pagerank(top_n=top)
        
        return {
            'success': True,
            'data': ranking,
            'total': len(ranking)
        }
    finally:
        kg_service.close()
