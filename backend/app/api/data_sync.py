"""
数据同步 API
提供爬虫服务的 HTTP 接口
"""
from fastapi import APIRouter, BackgroundTasks, Query
from pydantic import BaseModel
from typing import Optional
import logging

from app.services.financial_crawler import FinancialCrawler
from app.services.shareholder_crawler import ShareholderCrawler

logger = logging.getLogger(__name__)
router = APIRouter()

# 全局单例（跨请求保持进度状态）
financial_crawler = FinancialCrawler()
shareholder_crawler = ShareholderCrawler()


class SyncRequest(BaseModel):
    limit: int = 0          # 0=全部, >0=限制数量
    force: bool = False     # 是否强制全量（忽略已有数据）
    delay: float = 0.2      # 请求间隔(秒)


@router.post("/financials")
async def sync_financials(req: SyncRequest, background_tasks: BackgroundTasks):
    """同步财务数据（后台任务）"""
    background_tasks.add_task(financial_crawler.sync, limit=req.limit, force=req.force, delay=req.delay)
    return {"success": True, "message": "财务数据同步已启动", "progress": financial_crawler.progress}


@router.post("/shareholders")
async def sync_shareholders(req: SyncRequest, background_tasks: BackgroundTasks):
    """同步股东数据（后台任务）"""
    background_tasks.add_task(shareholder_crawler.sync, limit=req.limit, force=req.force, delay=req.delay)
    return {"success": True, "message": "股东数据同步已启动", "progress": shareholder_crawler.progress}


@router.get("/progress")
async def get_progress():
    """查看同步进度"""
    return {
        "success": True,
        "data": {
            "financials": financial_crawler.progress,
            "shareholders": shareholder_crawler.progress,
        }
    }
