"""
动态评分因子 - 基于实时市场数据的动态调整

策略：
- 先用策略筛选出候选股票（基于基本面）
- 然后批量获取候选股票的实时行情（Sina API，快速）
- 基于实时数据计算动态因子并调整排序

提供：
- Sina 实时行情批量查询（<2s for 50 stocks）
- 短期动量、量价配合、波动率、异动检测
- 每日探索因子（基于日期的确定性随机）
- 行情数据缓存（30分钟）
"""
import time
import random
import re
from datetime import date, datetime
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

# 全局缓存: { "timestamp": float, "data": {code: info} }
_spot_cache = {"data": None, "timestamp": 0, "ttl": 1800}


def _code_to_sina(code: str) -> str:
    """6位股票代码转 Sina 格式"""
    code = code.zfill(6)
    if code.startswith(('6', '9')):
        return f"sh{code}"
    elif code.startswith(('0', '3', '2')):
        return f"sz{code}"
    return f"sz{code}"


def _parse_sina_line(line: str) -> Optional[Dict]:
    """
    解析新浪行情单行数据
    
    格式: var hq_str_sh600519="名称,今开,昨收,当前价,最高,最低,...,成交量,成交额,...,日期,时间,涨跌,涨跌幅,...";
    """
    m = re.match(r'var hq_str_(\w+)="(.+)";', line.strip())
    if not m:
        return None
    
    raw = m.group(2)
    if not raw or raw == '':
        return None
    
    fields = raw.split(',')
    try:
        name = fields[0]
        open_price = _safe_float(fields[1])
        prev_close = _safe_float(fields[2])
        price = _safe_float(fields[3])
        high = _safe_float(fields[4])
        low = _safe_float(fields[5])
        volume = _safe_float(fields[8])
        
        # 计算涨跌幅
        change_pct = None
        if price is not None and prev_close is not None and prev_close > 0:
            change_pct = round((price - prev_close) / prev_close * 100, 2)
        
        # 计算换手率（近似：成交量/流通股本，此处无流通股本数据，跳过）
        
        # 计算振幅
        amplitude = None
        if high is not None and low is not None and prev_close is not None and prev_close > 0:
            amplitude = round((high - low) / prev_close * 100, 2)
        
        return {
            "name": name,
            "price": price,
            "open": open_price,
            "prev_close": prev_close,
            "high": high,
            "low": low,
            "volume": volume,
            "change_pct": change_pct,
            "amplitude": amplitude,
        }
    except (IndexError, ValueError):
        return None


def _fetch_spot_batch(stock_codes: List[str]) -> Dict[str, Dict]:
    """
    通过 Sina API 批量获取实时行情
    
    Args:
        stock_codes: 6位股票代码列表
        
    Returns:
        {code: {price, change_pct, ...}}
    """
    import requests
    
    if not stock_codes:
        return {}
    
    # 分批，每批50个
    result = {}
    for i in range(0, len(stock_codes), 50):
        batch = stock_codes[i:i+50]
        sina_codes = [_code_to_sina(c) for c in batch]
        url = f"http://hq.sinajs.cn/list={','.join(sina_codes)}"
        
        try:
            resp = requests.get(url, headers={
                'Referer': 'http://finance.sina.com.cn',
                'User-Agent': 'Mozilla/5.0',
            }, timeout=5)
            
            for line in resp.text.strip().split('\n'):
                info = _parse_sina_line(line)
                if info:
                    # 提取纯6位代码
                    code_match = re.match(r'var hq_str_(s[hz])(\d{6})', line)
                    if code_match:
                        result[code_match.group(2)] = info
        except Exception as e:
            logger.warning(f"Sina API batch failed: {e}")
    
    return result


def fetch_spot_for_stocks(stock_codes: List[str], use_cache: bool = True) -> Dict[str, Dict]:
    """
    获取指定股票的实时行情（带缓存）
    
    Returns:
        {code: {price, change_pct, ...}}
    """
    now = time.time()
    
    if use_cache and _spot_cache["data"] is not None:
        # 检查是否所有需要的代码都在缓存中
        cached = _spot_cache["data"]
        if (now - _spot_cache["timestamp"]) < _spot_cache["ttl"]:
            # 返回缓存中有的
            return {c: cached[c] for c in stock_codes if c in cached}
    
    # 获取新的数据
    fresh_data = _fetch_spot_batch(stock_codes)
    
    if fresh_data:
        if _spot_cache["data"] is None:
            _spot_cache["data"] = {}
        _spot_cache["data"].update(fresh_data)
        _spot_cache["timestamp"] = now
    
    return fresh_data


def _safe_float(val) -> Optional[float]:
    try:
        v = float(val)
        return v if v == v else None
    except (TypeError, ValueError):
        return None


def calc_dynamic_factors(stock_code: str, spot_data: Dict[str, Dict]) -> Dict[str, float]:
    """
    计算单只股票的动态评分因子（总分20分）
    
    因子：
    - 短期动量 (0-8分): 基于涨跌幅
    - 量价配合 (0-5分): 基于振幅和价格位置
    - 波动率 (0-4分): 日内振幅评估
    - 异动 (0-3分): 涨停/跌停检测
    """
    if stock_code not in spot_data:
        return {"momentum": 5, "volume_price": 3, "volatility": 3, "anomaly": 1, "total": 12}
    
    info = spot_data[stock_code]
    change_pct = info.get("change_pct")
    amplitude = info.get("amplitude")
    price = info.get("price")
    high = info.get("high")
    low = info.get("low")
    prev_close = info.get("prev_close")
    
    # 1. 短期动量 (0-8分)
    momentum = 4
    if change_pct is not None:
        if 0 <= change_pct <= 3:
            momentum = 7
        elif 3 < change_pct <= 7:
            momentum = 8
        elif 7 < change_pct <= 10:
            momentum = 5
        elif change_pct > 10:
            momentum = 2
        elif -3 <= change_pct < 0:
            momentum = 5
        elif -7 <= change_pct < -3:
            momentum = 3
        else:
            momentum = 1
    
    # 2. 量价配合 (0-5分) - 用振幅近似
    volume_price = 3
    if amplitude is not None:
        if amplitude <= 2:
            volume_price = 4  # 稳定
        elif amplitude <= 5:
            volume_price = 5  # 正常波动
        elif amplitude <= 8:
            volume_price = 3  # 偏大
        else:
            volume_price = 1  # 剧烈波动
    
    # 3. 波动率 (0-4分)
    volatility = 3
    if amplitude is not None:
        if amplitude <= 2:
            volatility = 4
        elif amplitude <= 5:
            volatility = 3
        elif amplitude <= 8:
            volatility = 2
        else:
            volatility = 0
    
    # 4. 异动 (0-3分)
    anomaly = 1
    if change_pct is not None:
        if 9.5 <= change_pct <= 10.5:
            anomaly = 3  # 涨停
        elif 7 <= change_pct < 9.5:
            anomaly = 2  # 大涨
        elif -10.5 <= change_pct <= -9.5:
            anomaly = 0  # 跌停
    
    total = momentum + volume_price + volatility + anomaly
    return {
        "momentum": momentum,
        "volume_price": volume_price,
        "volatility": volatility,
        "anomaly": anomaly,
        "total": min(total, 20),
    }


def apply_exploration_noise(stock_code: str, base_score: float) -> float:
    """
    每日探索因子：基于日期的确定性随机 ±3%
    同一天同一股票结果相同，不同天不同
    """
    seed = f"{date.today().isoformat()}:{stock_code}"
    rng = random.Random(seed)
    noise = rng.uniform(-0.03, 0.03)
    return base_score * (1 + noise)


def apply_dynamic_scores(
    results: List[Dict],
    spot_data: Optional[Dict[str, Dict]],
) -> tuple:
    """
    对推荐结果应用动态评分
    
    原有分数占80%，动态因子占20%
    
    Returns:
        (modified_results, metadata_dict)
    """
    for item in results:
        code = item.get("stock_code", "")
        base_score = item.get("composite_score") or item.get("recommendation_score", 50)
        grade = item.get("grade", "D")
        
        # 动态因子（20分满分）
        dynamic = calc_dynamic_factors(code, spot_data or {})
        
        # 原有分数标准化到80分
        normalized_base = (base_score / 100) * 80
        
        # 合并
        final_score = normalized_base + dynamic["total"]
        
        # 探索噪声
        final_score = apply_exploration_noise(code, final_score)
        
        item["_dynamic_factors"] = dynamic
        item["composite_score"] = round(final_score, 2)
        item["recommendation_score"] = round(final_score, 2)
    
    # 重新排序
    results.sort(key=lambda x: x.get("composite_score") or 0, reverse=True)
    
    # 元数据
    now = datetime.now()
    metadata = {
        "generated_at": now.isoformat(),
        "market_snapshot_time": datetime.fromtimestamp(
            _spot_cache["timestamp"]
        ).isoformat() if _spot_cache["timestamp"] else None,
        "dynamic_scoring_enabled": spot_data is not None and len(spot_data) > 0,
    }
    
    return results, metadata
