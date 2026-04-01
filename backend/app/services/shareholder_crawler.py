"""
股东数据爬虫服务
数据源: 东方财富 F10 API
支持增量同步、失败重试
"""
import requests
import sqlite3
import time
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

EM_F10_API = "https://emweb.securities.eastmoney.com/PC_HSF10/ShareholderResearch/PageAjax"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


class ShareholderCrawler:
    """股东数据爬虫"""

    def __init__(self, db_path: str = "valuegraph.db"):
        self.db_path = db_path
        self._running = False
        self._progress = {"total": 0, "success": 0, "fail": 0, "new_rows": 0, "status": "idle"}

    @property
    def progress(self) -> Dict:
        return self._progress

    def _get_targets(self, limit: int = 0, force: bool = False) -> List[str]:
        """获取待同步的股票列表（有财务数据的优先）"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        if force:
            c.execute("SELECT DISTINCT stock_code FROM financials ORDER BY stock_code")
        else:
            c.execute("SELECT DISTINCT s.stock_code FROM financials f JOIN stocks s ON f.stock_code = s.stock_code WHERE s.market='A' AND f.stock_code NOT IN (SELECT DISTINCT stock_code FROM shareholders) ORDER BY f.stock_code")

        targets = [r[0] for r in c.fetchall()]
        conn.close()
        return targets[:limit] if limit else targets

    def _fetch_shareholders(self, stock_code: str) -> Dict:
        """从东财F10获取股东数据"""
        prefix = "SH" if stock_code.startswith("6") else "SZ"
        params = {
            "code": f"{prefix}{stock_code}",
            "topType": "1",
        }
        r = requests.get(EM_F10_API, params=params, headers=HEADERS, timeout=10)
        data = r.json()
        return {
            "sdgd": data.get("sdgd", []),       # 十大股东
            "sdltgd": data.get("sdltgd", []),     # 十大流通股东
        }

    def sync(self, limit: int = 0, force: bool = False, delay: float = 0.5) -> Dict:
        """执行同步"""
        if self._running:
            return {"error": "同步任务正在进行中", "progress": self._progress}

        self._running = True
        self._progress = {"total": 0, "success": 0, "fail": 0, "new_rows": 0, "status": "running", "started_at": datetime.now().isoformat()}

        try:
            targets = self._get_targets(limit, force)
            self._progress["total"] = len(targets)
            logger.info(f"股东同步开始: {len(targets)} 只股票, force={force}")

            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()

            for i, code in enumerate(targets):
                try:
                    holders = self._fetch_shareholders(code)
                    inserted = 0

                    # 十大股东
                    for h in holders["sdgd"]:
                        c.execute(
                            """INSERT OR REPLACE INTO shareholders 
                            (stock_code,report_date,rank,holder_name,hold_amount,hold_ratio,holder_type)
                            VALUES (?,?,?,?,?,?,?)""",
                            (code, str(h.get("END_DATE", ""))[:10], h.get("HOLDER_RANK"),
                             h.get("HOLDER_NAME", ""), h.get("HOLD_NUM"), h.get("HOLD_NUM_RATIO"), "top10"))
                        if c.rowcount > 0:
                            inserted += 1

                    # 十大流通股东（前5）
                    for h in holders["sdltgd"][:5]:
                        c.execute(
                            """INSERT OR REPLACE INTO shareholders 
                            (stock_code,report_date,rank,holder_name,hold_amount,hold_ratio,holder_type)
                            VALUES (?,?,?,?,?,?,?)""",
                            (code, str(h.get("END_DATE", ""))[:10], h.get("HOLDER_RANK"),
                             h.get("HOLDER_NAME", ""), h.get("HOLD_NUM"), h.get("HOLD_NUM_RATIO"), "float"))
                        if c.rowcount > 0:
                            inserted += 1

                    if inserted > 0:
                        self._progress["success"] += 1
                        self._progress["new_rows"] += inserted
                    else:
                        self._progress["fail"] += 1
                except Exception as e:
                    self._progress["fail"] += 1
                    logger.warning(f"股东同步失败 {code}: {e}")

                time.sleep(delay)

                if (i + 1) % 20 == 0:
                    conn.commit()
                    logger.info(f"股东同步进度: {i+1}/{len(targets)}, ok={self._progress['success']}, fail={self._progress['fail']}")

            conn.commit()

            c.execute("SELECT COUNT(*) FROM shareholders")
            total_rows = c.fetchone()[0]
            c.execute("SELECT COUNT(DISTINCT stock_code) FROM shareholders")
            cov = c.fetchone()[0]
            conn.close()

            self._progress["status"] = "completed"
            self._progress["total_rows"] = total_rows
            self._progress["coverage"] = f"{cov} stocks"
            self._progress["finished_at"] = datetime.now().isoformat()
            logger.info(f"股东同步完成: {self._progress}")

        except Exception as e:
            self._progress["status"] = "failed"
            self._progress["error"] = str(e)
            logger.error(f"股东同步异常: {e}")
        finally:
            self._running = False

        return self._progress
