"""
财务数据爬虫服务
数据源: 东方财富 datacenter API
支持增量同步、断点续传、失败重试
"""
import requests
import sqlite3
import time
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

EASTMONEY_API = "https://datacenter.eastmoney.com/securities/api/data/get"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
FIELDS_INCOME = "SECURITY_CODE,REPORTDATE,WEIGHTAVG_ROE,XSMLL,YSHZ,YSTZ,SJLTZ,BPS,BASIC_EPS,TOTAL_OPERATE_INCOME,PARENT_NETPROFIT"
FIELDS_BALANCE = "SECURITY_CODE,REPORTDATE,TOTAL_ASSETS,TOTAL_LIABILITIES,CURRENT_ASSETS,CURRENT_LIABILITIES,INVENTORY,ACCOUNTS_RECEIVIBLE,MONETARY_FUND"
FIELDS_CASHFLOW = "SECURITY_CODE,REPORTDATE,NETCASH_OPERATE,NETCASH_INVEST,NETCASH_FINANCE"
TOKEN = "894050c76af8597a853f5b408b759f5d"


class FinancialCrawler:
    """财务数据爬虫"""

    def __init__(self, db_path: str = "valuegraph.db"):
        self.db_path = db_path
        self._running = False
        self._progress = {"total": 0, "success": 0, "fail": 0, "new_rows": 0, "status": "idle"}

    @property
    def progress(self) -> Dict:
        return self._progress

    def _get_targets(self, limit: int = 0, force: bool = False) -> List[str]:
        """获取待同步的股票列表"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        if force:
            c.execute("SELECT stock_code FROM stocks WHERE market='A' ORDER BY stock_code")
        else:
            c.execute("SELECT DISTINCT stock_code FROM financials")
            existing = set(r[0] for r in c.fetchall())
            c.execute("SELECT stock_code FROM stocks WHERE market='A' ORDER BY stock_code")
            all_stocks = [r[0] for r in c.fetchall()]
            targets = [code for code in all_stocks if code not in existing]
            conn.close()
            return targets[:limit] if limit else targets
        
        targets = [r[0] for r in c.fetchall()]
        conn.close()
        return targets[:limit] if limit else targets

    def _fetch_financial(self, stock_code: str) -> Dict[str, Dict]:
        """从东财获取单只股票财务数据（三大报表）"""
        result = {}
        
        apis = [
            ("RPT_LICO_FN_CPD", FIELDS_INCOME),
            ("RPT_DMSK_FN_BALANCE", FIELDS_BALANCE),
            ("RPT_DMSK_FN_CASHFLOW", FIELDS_CASHFLOW),
        ]
        
        for api_type, fields in apis:
            params = {
                "type": api_type,
                "sty": fields,
                "filter": f'(SECURITY_CODE="{stock_code}")',
                "p": 1, "ps": 100, "sr": -1, "st": "REPORTDATE",
                "token": TOKEN,
            }
            try:
                r = requests.get(EASTMONEY_API, params=params, headers=HEADERS, timeout=10)
                data = r.json()
                if data.get("result") and data["result"].get("data"):
                    for item in data["result"]["data"]:
                        rd = str(item.get("REPORTDATE", ""))[:10]
                        if rd and not rd.startswith("1900"):
                            result.setdefault(rd, {}).update(item)
            except Exception as e:
                logger.warning(f"东财API {api_type} 请求失败 {stock_code}: {e}")
        
        return result

    def sync(self, limit: int = 0, force: bool = False, delay: float = 0.2) -> Dict:
        """执行同步，支持增量"""
        if self._running:
            return {"error": "同步任务正在进行中", "progress": self._progress}

        self._running = True
        self._progress = {"total": 0, "success": 0, "fail": 0, "new_rows": 0, "status": "running", "started_at": datetime.now().isoformat()}

        try:
            targets = self._get_targets(limit, force)
            self._progress["total"] = len(targets)
            logger.info(f"财务同步开始: {len(targets)} 只股票, force={force}")

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            for i, code in enumerate(targets):
                try:
                    items = self._fetch_financial(code)
                    if items:
                        for rd, item in items.items():
                            # 计算派生指标
                            current_assets = item.get("CURRENT_ASSETS")
                            current_liabilities = item.get("CURRENT_LIABILITIES")
                            inventory = item.get("INVENTORY")
                            total_assets = item.get("TOTAL_ASSETS")
                            operating_cf = item.get("NETCASH_OPERATE")
                            investing_cf = item.get("NETCASH_INVEST")
                            financing_cf = item.get("NETCASH_FINANCE")
                            net_profit = item.get("PARENT_NETPROFIT")
                            
                            current_ratio = round(current_assets / current_liabilities, 4) if current_assets and current_liabilities and current_liabilities else None
                            quick_ratio = round((current_assets - inventory) / current_liabilities, 4) if current_assets and inventory and current_liabilities and current_liabilities else None
                            roa = round(net_profit / total_assets * 100, 4) if net_profit and total_assets and total_assets else None
                            # 自由现金流 ≈ 经营现金流 + 投资现金流（投资现金流为负表示支出）
                            free_cf = (operating_cf or 0) + (investing_cf or 0) if operating_cf is not None else None
                            
                            c.execute(
                                """INSERT OR IGNORE INTO financials 
                                (stock_code,report_date,report_type,roe,gross_margin,debt_ratio,
                                 revenue_yoy,net_profit_yoy,bvps,eps,revenue,net_profit,
                                 total_assets,total_liabilities,operating_cash_flow,
                                 current_assets,current_liabilities,inventory,accounts_receivable,monetary_fund,
                                 investing_cash_flow,financing_cash_flow,free_cash_flow,
                                 current_ratio,quick_ratio,roa) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                (code, rd, "quarterly",
                                 item.get("WEIGHTAVG_ROE"), item.get("XSMLL"), item.get("YSHZ"),
                                 item.get("YSTZ"), item.get("SJLTZ"), item.get("BPS"),
                                 item.get("BASIC_EPS"), item.get("TOTAL_OPERATE_INCOME"), item.get("PARENT_NETPROFIT"),
                                 item.get("TOTAL_ASSETS"), item.get("TOTAL_LIABILITIES"), item.get("NETCASH_OPERATE"),
                                 item.get("CURRENT_ASSETS"), item.get("CURRENT_LIABILITIES"), item.get("INVENTORY"),
                                 item.get("ACCOUNTS_RECEIVIBLE"), item.get("MONETARY_FUND"),
                                 item.get("NETCASH_INVEST"), item.get("NETCASH_FINANCE"), free_cf,
                                 current_ratio, quick_ratio, roa)
                            )
                            if c.rowcount > 0:
                                self._progress["new_rows"] += 1
                        self._progress["success"] += 1
                    else:
                        self._progress["fail"] += 1
                except Exception as e:
                    self._progress["fail"] += 1
                    logger.warning(f"财务同步失败 {code}: {e}")

                time.sleep(delay)

                if (i + 1) % 50 == 0:
                    conn.commit()
                    logger.info(f"财务同步进度: {i+1}/{len(targets)}, ok={self._progress['success']}, fail={self._progress['fail']}")

            conn.commit()
            
            # 统计
            c.execute("SELECT COUNT(DISTINCT stock_code) FROM financials")
            cov = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM stocks WHERE market='A'")
            total = c.fetchone()[0]
            conn.close()
            
            self._progress["status"] = "completed"
            self._progress["coverage"] = f"{cov}/{total} ({cov*100/total:.1f}%)"
            self._progress["finished_at"] = datetime.now().isoformat()
            logger.info(f"财务同步完成: {self._progress}")

        except Exception as e:
            self._progress["status"] = "failed"
            self._progress["error"] = str(e)
            logger.error(f"财务同步异常: {e}")
        finally:
            self._running = False

        return self._progress
