"""
杜邦分析服务 - ROE 三因子拆解

ROE = 净利率 × 资产周转率 × 权益乘数
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.financial import Financial

logger = logging.getLogger(__name__)


class DupontAnalysis:
    """杜邦分析服务"""

    def __init__(self, db: Session):
        self.db = db

    def analyze(self, stock_code: str, quarters: int = 4) -> Dict[str, Any]:
        """
        对指定股票进行杜邦分析

        Args:
            stock_code: 股票代码
            quarters: 返回最近几个季度（默认4）

        Returns:
            杜邦分析结果
        """
        # 查询最近 N 个季度的财报数据
        financials = (
            self.db.query(Financial)
            .filter(Financial.stock_code == stock_code)
            .order_by(desc(Financial.report_date))
            .limit(quarters)
            .all()
        )

        if not financials:
            return {
                "stock_code": stock_code,
                "quarters": [],
                "message": "暂无财报数据"
            }

        # 按时间正序排列（最早的在前）
        financials = list(reversed(financials))

        # 构建每季度的杜邦分析数据
        quarter_data = []
        for i, f in enumerate(financials):
            # 计算三因子
            net_profit_margin = f.net_profit / f.revenue if f.revenue and f.revenue != 0 else None
            asset_turnover_val = f.revenue / f.total_assets if f.total_assets and f.total_assets != 0 else None

            # 权益乘数: total_assets / equity = total_assets / (total_assets - total_liabilities)
            equity = (f.total_assets - f.total_liabilities) if f.total_assets is not None and f.total_liabilities is not None else None
            equity_multiplier = f.total_assets / equity if equity and equity != 0 else None

            # ROE（使用数据库中的值，如果没有则用三因子计算）
            if f.roe is not None:
                roe = f.roe
            elif net_profit_margin is not None and asset_turnover_val is not None and equity_multiplier is not None:
                roe = net_profit_margin * asset_turnover_val * equity_multiplier
            else:
                roe = None

            entry = {
                "report_date": str(f.report_date) if f.report_date else None,
                "report_type": f.report_type,
                "revenue": f.revenue,
                "net_profit": f.net_profit,
                "total_assets": f.total_assets,
                "total_liabilities": f.total_liabilities,
                "roe": round(roe, 6) if roe is not None else None,
                "net_profit_margin": round(net_profit_margin, 6) if net_profit_margin is not None else None,
                "asset_turnover": round(asset_turnover_val, 6) if asset_turnover_val is not None else None,
                "equity_multiplier": round(equity_multiplier, 6) if equity_multiplier is not None else None,
                "trends": {}
            }

            # 趋势分析（对比上一期）
            if i > 0:
                prev = quarter_data[i - 1]
                entry["trends"] = self._compare_trends(prev, entry)

            quarter_data.append(entry)

        return {
            "stock_code": stock_code,
            "total_quarters": len(quarter_data),
            "quarters": quarter_data,
            "summary": self._build_summary(quarter_data)
        }

    def _compare_trends(self, prev: Dict, curr: Dict) -> Dict[str, str]:
        """对比两期数据，生成趋势标注"""
        fields = ["roe", "net_profit_margin", "asset_turnover", "equity_multiplier"]
        trends = {}

        for field in fields:
            prev_val = prev.get(field)
            curr_val = curr.get(field)

            if prev_val is None or curr_val is None:
                trends[field] = "unknown"
            elif curr_val > prev_val * 1.001:  # 考虑浮点误差
                trends[field] = "up"
            elif curr_val < prev_val * 0.999:
                trends[field] = "down"
            else:
                trends[field] = "flat"

        return trends

    def _build_summary(self, quarters: List[Dict]) -> Dict[str, Any]:
        """构建汇总信息"""
        if not quarters:
            return {}

        latest = quarters[-1]
        latest_trends = latest.get("trends", {})

        # 找出主要驱动因素
        drivers = []
        for factor, trend in latest_trends.items():
            if trend == "up":
                label_map = {
                    "roe": "ROE",
                    "net_profit_margin": "净利率",
                    "asset_turnover": "资产周转率",
                    "equity_multiplier": "权益乘数"
                }
                drivers.append({"factor": label_map.get(factor, factor), "direction": "up"})

        return {
            "latest_period": latest["report_date"],
            "roe": latest["roe"],
            "improvement_drivers": drivers,
            "data_completeness": sum(
                1 for q in quarters
                if q["roe"] is not None
            ) / len(quarters)
        }
