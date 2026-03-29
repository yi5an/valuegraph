"""
智能问答 API
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter()


class AskRequest(BaseModel):
    """提问请求"""
    question: str = Field(..., description="用户问题", example="贵州茅台的ROE是多少？")


class AskResponse(BaseModel):
    """提问响应"""
    success: bool = Field(..., description="是否成功")
    answer: str = Field(..., description="回答内容")
    data_source: str = Field(..., description="数据源类型")
    related_stocks: List[str] = Field(default_factory=list, description="相关股票代码")
    data: Optional[Any] = Field(None, description="结构化数据")
    llm_failed: Optional[bool] = Field(None, description="LLM 是否调用失败")


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db)
):
    """
    智能问答接口
    
    - **question**: 用户问题，支持自然语言提问
    
    支持的问题类型：
    - 推荐类：推荐几只高ROE低负债的股票
    - 财报类：贵州茅台的ROE是多少？
    - 股东类：宁德时代的股东有哪些？
    - 产业链：宁德时代的上游供应商有哪些？
    - 风险类：宁德时代的风险影响哪些公司？
    - 新闻类：贵州茅台最近有什么新闻？
    """
    try:
        logger.info(f"收到问题: {request.question}")
        
        # 创建 RAG 服务
        rag_service = RAGService(db)
        
        try:
            # 调用 RAG 服务回答问题
            result = rag_service.answer(request.question)
            
            logger.info(f"问题回答完成，数据源: {result['data_source']}")
            
            return AskResponse(**result)
        
        finally:
            # 关闭服务连接
            rag_service.close()
    
    except Exception as e:
        logger.error(f"问答处理失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"问答处理失败: {str(e)}")


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "qa"
    }
