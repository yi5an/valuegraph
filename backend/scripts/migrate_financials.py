"""迁移脚本：为 financials 表添加资产负债表、现金流量表、运营指标字段"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'valuegraph.db')

NEW_COLUMNS = [
    ("current_assets", "REAL"),
    ("current_liabilities", "REAL"),
    ("inventory", "REAL"),
    ("accounts_receivable", "REAL"),
    ("monetary_fund", "REAL"),
    ("investing_cash_flow", "REAL"),
    ("financing_cash_flow", "REAL"),
    ("free_cash_flow", "REAL"),
    ("asset_turnover", "REAL"),
    ("inventory_turnover", "REAL"),
    ("current_ratio", "REAL"),
    ("quick_ratio", "REAL"),
    ("roa", "REAL"),
]

def migrate():
    db_path = os.path.abspath(DB_PATH)
    print(f"数据库: {db_path}")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 获取已有列
    c.execute("PRAGMA table_info(financials)")
    existing = {row[1] for row in c.fetchall()}
    
    added = 0
    for col_name, col_type in NEW_COLUMNS:
        if col_name not in existing:
            c.execute(f"ALTER TABLE financials ADD COLUMN {col_name} {col_type}")
            print(f"  + {col_name}")
            added += 1
        else:
            print(f"  . {col_name} (已存在)")
    
    conn.commit()
    conn.close()
    print(f"完成，新增 {added} 列")

if __name__ == "__main__":
    migrate()
