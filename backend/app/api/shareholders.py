"""
持股查询 API
"""
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.shareholder import ShareholderResponse, ShareholderDetail
from app.services.data_collector import AkShareCollector
from app.utils.cache import cache
from app.utils.rate_limiter import limiter
from typing import List
from pydantic import BaseModel

router = APIRouter()


class InstitutionalHolder(BaseModel):
    """机构持仓"""
    fund_name: str
    fund_code: str
    hold_amount: float = None
    hold_ratio: float = None
    hold_value: float = None
    net_value_ratio: float = None
    report_date: str = None


class InstitutionalHolderResponse(BaseModel):
    """机构持仓响应"""
    success: bool
    stock_code: str
    data: List[InstitutionalHolder] = []
    total: int = 0


@router.get("/{stock_code}", response_model=ShareholderResponse)
async def get_shareholders(
    request: Request,
    stock_code: str,
    db: Session = Depends(get_db)
):
    """
    获取股东信息
    
    - **stock_code**: 股票代码（如 600519）
    """
    cache_key = f"shareholder:{stock_code}"
    
    # 尝试从缓存获取
    cached = cache.get(cache_key)
    if cached:
        return ShareholderResponse(success=True, data=ShareholderDetail(**cached))
    
    try:
        # 先查数据库 shareholder 表
        from app.models.shareholder import Shareholder as SHModel
        db_shareholders = db.query(SHModel).filter(
            SHModel.stock_code == stock_code
        ).order_by(SHModel.id.desc()).limit(10).all()
        
        if db_shareholders:
            data = {
                'stock_code': stock_code,
                'top_10_shareholders': [
                    {'name': s.holder_name, 'ratio': s.hold_ratio, 'amount': s.hold_amount}
                    for s in db_shareholders
                ],
                'report_date': str(db_shareholders[0].report_date) if db_shareholders else ''
            }
            cache.set(cache_key, data)
            shareholder_detail = ShareholderDetail(**data)
        else:
            # 数据库无数据，返回暂无（不实时调 AkShare 避免阻塞）
            return ShareholderResponse(
                success=False,
                data=None,
                message="暂无股东数据，请通过 /api/shareholders/sync 同步"
            )
        
        return ShareholderResponse(
            success=True,
            data=shareholder_detail
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/changes/{stock_code}")
async def get_shareholder_changes(
    request: Request,
    stock_code: str
):
    """
    获取股东增减持变化
    
    - **stock_code**: 股票代码（如 600519）
    
    返回近期股东增减持记录
    """
    cache_key = f"shareholder_changes:{stock_code}"
    
    # 尝试从缓存获取
    cached = cache.get(cache_key)
    if cached:
        return {
            'success': True,
            'data': cached
        }
    
    try:
        import akshare as ak
        
        changes = []
        data_available = False
        
        # 尝试获取股东增减持数据
        try:
            # 尝试获取股东增减持详情
            df_changes = ak.stock_gdfx_free_holding_detail_em(symbol=stock_code)
            
            if df_changes is not None and not df_changes.empty:
                data_available = True
                for _, row in df_changes.head(20).iterrows():
                    changes.append({
                        'holder_name': row.get('股东名称', ''),
                        'change_type': row.get('增减持', ''),
                        'change_amount': row.get('增减持数量', None),
                        'change_ratio': row.get('占流通股比例', None),
                        'change_date': str(row.get('变动日期', '')),
                        'after_holding': row.get('变动后持股数', None),
                    })
        except Exception as e:
            # 此接口可能不可用，继续尝试其他接口
            pass
        
        # 尝试获取股东户数变化
        holder_count_changes = []
        try:
            df_count = ak.stock_zh_a_gdhs_detail_em(symbol=stock_code)
            
            if df_count is not None and not df_count.empty:
                data_available = True
                for _, row in df_count.head(10).iterrows():
                    holder_count_changes.append({
                        'report_date': str(row.get('股东户数统计截止日', '')),
                        'holder_count': row.get('股东户数', None),
                        'change_pct': row.get('股东户数较上期变化', None),
                    })
        except Exception as e:
            # 此接口可能不可用
            pass
        
        result = {
            'stock_code': stock_code,
            'changes': changes,
            'holder_count_changes': holder_count_changes,
            'data_available': data_available,
            'message': '暂无数据' if not data_available else None
        }

        # 写入缓存
        cache.set(cache_key, result)

        return {
            'success': True,
            'data': result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/institutional/{stock_code}", response_model=InstitutionalHolderResponse)
async def get_institutional_holders(
    request: Request,
    stock_code: str
):
    """
    获取机构持仓数据

    - **stock_code**: 股票代码（如 600519）

    返回基金持仓数据（作为机构持仓的代表）
    """
    cache_key = f"institutional_holders:{stock_code}"

    # 尝试从缓存获取
    cached = cache.get(cache_key)
    if cached:
        return InstitutionalHolderResponse(
            success=True,
            stock_code=stock_code,
            data=[InstitutionalHolder(**h) for h in cached],
            total=len(cached)
        )

    try:
        # 暂时返回空数据（AkShare 实时调用会阻塞，改为后台同步）
        return InstitutionalHolderResponse(
            success=True,
            stock_code=stock_code,
            data=[],
            total=0,
            message="机构持仓数据待同步"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")
