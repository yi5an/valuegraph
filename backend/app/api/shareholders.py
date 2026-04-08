"""
持股查询 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.shareholder import ShareholderResponse, ShareholderDetail, TopShareholder, InstitutionalHolder as InstHolderSchema
from app.models.shareholder import Shareholder as SHModel, InstitutionalHolder as InstHolderModel
from app.services.shareholder_crawler import ShareholderCrawler
from app.services.data_collector import AkShareCollector
from app.utils.cache import cache
from app.utils.rate_limiter import limiter
from typing import Optional
from pydantic import BaseModel
import os

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "valuegraph.db")

# 知名投资者关键词列表
FAMOUS_INVESTORS = [
    "巴菲特", "高瓴", "社保基金", "证金公司", "汇金公司",
    "挪威中央银行", "香港中央结算", "全国社保", "中金公司",
    "摩根", "高盛", "UBS", "瑞银", "黑石",
]


class InstitutionalHolderItem(BaseModel):
    """机构持仓响应项"""
    institution_name: str
    institution_type: Optional[str] = None
    hold_amount: Optional[float] = None
    hold_ratio: Optional[float] = None
    change_ratio: Optional[float] = None
    report_date: Optional[str] = None


class InvestorHolding(BaseModel):
    """投资者持仓项"""
    stock_code: str
    holder_name: str
    hold_amount: Optional[int] = None
    hold_ratio: Optional[float] = None
    report_date: Optional[str] = None
    holder_type: Optional[str] = None


# ==================== 原有接口 ====================

@router.get("/{stock_code}", response_model=ShareholderResponse)
async def get_shareholders(
    request: Request,
    stock_code: str,
    db: Session = Depends(get_db)
):
    """获取股东信息 - 十大股东"""
    cache_key = f"shareholder:{stock_code}"
    cached = cache.get(cache_key)
    if cached:
        return ShareholderResponse(success=True, data=ShareholderDetail(**cached))

    try:
        db_shareholders = db.query(SHModel).filter(
            SHModel.stock_code == stock_code
        ).order_by(SHModel.id.desc()).limit(10).all()

        if db_shareholders:
            data = {
                'stock_code': stock_code,
                'top_10_shareholders': [
                    {'rank': s.rank, 'holder_name': s.holder_name, 'hold_amount': s.hold_amount,
                     'hold_ratio': s.hold_ratio, 'holder_type': s.holder_type, 'change': s.change}
                    for s in db_shareholders
                ],
                'report_date': str(db_shareholders[0].report_date) if db_shareholders else '',
                'name': '',
                'institutional_holders': [],
                'holder_distribution': None,
            }
            cache.set(cache_key, data)
            shareholder_detail = ShareholderDetail(**data)
        else:
            # 数据库没有数据，从 AkShare 实时获取
            data = AkShareCollector.get_shareholders(stock_code)
            
            if not data.get('top_10_shareholders'):
                return ShareholderResponse(
                    success=False,
                    data=None,
                    message="暂无股东数据"
                )
            
            cache.set(cache_key, data)
            shareholder_detail = ShareholderDetail(**data)

        return ShareholderResponse(success=True, data=shareholder_detail)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ==================== 机构持仓接口 ====================

@router.get("/institutional/{stock_code}")
async def get_institutional_holders(
    request: Request,
    stock_code: str,
    db: Session = Depends(get_db)
):
    """
    获取机构持仓数据

    - **stock_code**: 股票代码（如 600519）

    优先从数据库读取，无数据时实时从东方财富 F10 抓取
    """
    cache_key = f"institutional_holders:{stock_code}"
    cached = cache.get(cache_key)
    if cached:
        return {"success": True, "data": cached, "meta": {"stock_code": stock_code, "total": len(cached)}}

    try:
        # 先查数据库
        db_records = db.query(InstHolderModel).filter(
            InstHolderModel.stock_code == stock_code
        ).order_by(InstHolderModel.hold_ratio.desc()).limit(50).all()

        if db_records:
            data = [
                {
                    "institution_name": r.institution_name,
                    "institution_type": r.institution_type,
                    "hold_amount": r.hold_amount,
                    "hold_ratio": r.hold_ratio,
                    "change_ratio": r.change_ratio,
                    "report_date": str(r.report_date) if r.report_date else None,
                }
                for r in db_records
            ]
            cache.set(cache_key, data)
            return {"success": True, "data": data, "meta": {"stock_code": stock_code, "total": len(data), "source": "db"}}

        # 实时从东财 F10 抓取
        crawler = ShareholderCrawler(db_path=DB_PATH)
        data = crawler.fetch_institutional_holders(stock_code)
        
        # 如果爬虫失败，使用 AkShare 基金持仓作为备用
        if not data:
            fund_data = AkShareCollector.get_institutional_holders(stock_code)
            # 转换数据格式
            data = [
                {
                    "institution_name": item.get("fund_name", ""),
                    "institution_type": "基金",
                    "hold_amount": item.get("hold_amount"),
                    "hold_ratio": item.get("hold_ratio"),
                    "change_ratio": None,
                    "report_date": item.get("report_date"),
                }
                for item in fund_data
            ]

        # 存入数据库
        for item in data:
            # 转换 report_date 为 date 对象
            report_date_str = item.get("report_date") or "2024-12-31"
            try:
                from datetime import datetime
                if isinstance(report_date_str, str):
                    report_date = datetime.strptime(report_date_str, "%Y-%m-%d").date()
                else:
                    report_date = report_date_str
            except:
                from datetime import date
                report_date = date(2024, 12, 31)
            
            record = InstHolderModel(
                stock_code=stock_code,
                report_date=report_date,
                institution_name=item["institution_name"],
                institution_type=item.get("institution_type"),
                hold_amount=item.get("hold_amount"),
                hold_ratio=item.get("hold_ratio"),
                change_ratio=item.get("change_ratio"),
            )
            db.add(record)
        if data:
            db.commit()

        cache.set(cache_key, data)
        return {"success": True, "data": data, "meta": {"stock_code": stock_code, "total": len(data), "source": "live"}}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


# ==================== 知名投资者持仓接口 ====================

@router.get("/investor/{investor_name}")
async def get_investor_holdings(
    request: Request,
    investor_name: str,
    limit: int = Query(default=50, le=200),
    db: Session = Depends(get_db)
):
    """
    查询知名投资者持仓一览

    - **investor_name**: 投资者名称或关键词（如 社保基金、高瓴、巴菲特）
    - **limit**: 返回条数上限

    遍历所有有股东数据的股票，查找股东名包含关键词的记录
    """
    cache_key = f"investor:{investor_name}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return {"success": True, "data": cached, "meta": {"investor_name": investor_name, "total": len(cached)}}

    try:
        crawler = ShareholderCrawler(db_path=DB_PATH)
        holdings = crawler.search_investor_holdings(investor_name, limit)

        cache.set(cache_key, holdings)
        return {
            "success": True,
            "data": holdings,
            "meta": {
                "investor_name": investor_name,
                "total": len(holdings),
                "hint": f"搜索关键词: {investor_name}" if len(holdings) == 0 else None,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/investor")
async def list_famous_investors():
    """获取内置知名投资者列表"""
    return {
        "success": True,
        "data": FAMOUS_INVESTORS,
        "meta": {"total": len(FAMOUS_INVESTORS), "usage": "GET /api/shareholders/investor/{name} 查询具体投资者持仓"}
    }


# ==================== 持股变化监控接口 ====================

@router.get("/changes/{stock_code}")
async def get_shareholder_changes(
    request: Request,
    stock_code: str,
    db: Session = Depends(get_db)
):
    """
    获取股东增减持变化

    - **stock_code**: 股票代码（如 600519）

    返回近期大股东增减持变动记录
    """
    cache_key = f"shareholder_changes:{stock_code}"
    cached = cache.get(cache_key)
    if cached:
        return {"success": True, "data": cached, "meta": {"stock_code": stock_code, "total": len(cached.get("changes", []))}}

    try:
        # 先查数据库中已有变化记录
        db_changes = db.query(SHModel).filter(
            SHModel.stock_code == stock_code,
            SHModel.change.isnot(None),
            SHModel.change != "",
        ).order_by(SHModel.report_date.desc()).limit(20).all()

        changes = [
            {
                "holder_name": s.holder_name,
                "change": s.change,
                "hold_amount": s.hold_amount,
                "hold_ratio": s.hold_ratio,
                "report_date": str(s.report_date) if s.report_date else None,
            }
            for s in db_changes
        ]

        # 如果数据库记录不足，实时从东财补充
        if len(changes) < 5:
            crawler = ShareholderCrawler(db_path=DB_PATH)
            live_changes = crawler.fetch_holder_changes(stock_code)
            # 合并去重
            existing_names = {c["holder_name"] for c in changes}
            for lc in live_changes:
                if lc["holder_name"] not in existing_names:
                    changes.append(lc)

        result = {
            "stock_code": stock_code,
            "changes": changes,
            "total": len(changes),
        }

        cache.set(cache_key, result)
        return {"success": True, "data": result, "meta": {"stock_code": stock_code, "total": len(changes)}}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
