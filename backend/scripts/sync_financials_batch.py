#!/usr/bin/env python3
"""
财务数据批量同步脚本
从市值前 500 的股票中同步财务数据（市值 > 50 亿）
"""
import sys
import os
import time
import logging

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database import SessionLocal, init_db
from app.services.data_collector import AkShareCollector
from app.services.financial_analysis import FinancialService
from app.models.financial import Financial
from app.models.stock import Stock

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_existing_stocks(db: Session) -> set:
    """获取已有财务数据的股票代码"""
    stocks = db.query(Financial.stock_code).distinct().all()
    return {stock[0] for stock in stocks}


def sync_financial_data():
    """同步财务数据主函数"""
    db = SessionLocal()
    
    try:
        # 获取所有 A 股股票，按市值筛选
        logger.info("📊 正在从 stocks 表获取 A 股股票列表...")
        
        # 筛选条件：市值 > 50 亿（5000000000）
        # 按市值排序，取前 500 只
        stocks = db.query(Stock).filter(
            Stock.market == 'A',
            Stock.market_cap > 5000000000  # 50 亿
        ).order_by(Stock.market_cap.desc()).limit(500).all()
        
        logger.info(f"✅ 已选取市值 > 50 亿的前 {len(stocks)} 只股票")
        
        # 获取已有数据的股票
        existing_stocks = get_existing_stocks(db)
        logger.info(f"📊 数据库中已有 {len(existing_stocks)} 只股票的财务数据")
        
        # 统计变量
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        # 创建 FinancialService 实例
        service = FinancialService(db)
        
        # 遍历股票
        for i, stock in enumerate(stocks, 1):
            stock_code = stock.stock_code
            stock_name = stock.name
            market_cap = stock.market_cap
            
            # 跳过已有数据的股票
            if stock_code in existing_stocks:
                if i % 50 == 0:
                    logger.info(f"[{i}/{len(stocks)}] 已处理 {i} 只股票，跳过 {skip_count} 只（已有数据）")
                skip_count += 1
                continue
            
            # 获取财务数据
            if i % 50 == 1:
                logger.info(f"[{i}/{len(stocks)}] 正在处理 {stock_code} {stock_name} (市值: {market_cap/1e8:.2f}亿)")
            
            retry_count = 0
            max_retries = 1  # 失败重试 1 次
            success = False
            
            while retry_count <= max_retries and not success:
                try:
                    financial_data = AkShareCollector.get_financial_data(stock_code)
                    
                    if financial_data:
                        # 保存到数据库
                        service._save_financial_data(stock_code, financial_data)
                        if i % 50 == 1:
                            logger.info(f"[{i}/{len(stocks)}] ✅ {stock_code} {stock_name} 同步成功，共 {len(financial_data)} 条记录")
                        success_count += 1
                        success = True
                    else:
                        if retry_count < max_retries:
                            logger.warning(f"[{i}/{len(stocks)}] ⚠️  {stock_code} {stock_name} 无财务数据，准备重试...")
                            retry_count += 1
                            time.sleep(0.5)
                        else:
                            logger.warning(f"[{i}/{len(stocks)}] ⚠️  {stock_code} {stock_name} 无财务数据")
                            fail_count += 1
                            break
                    
                except Exception as e:
                    if retry_count < max_retries:
                        logger.warning(f"[{i}/{len(stocks)}] ⚠️  {stock_code} {stock_name} 同步失败: {e}，准备重试...")
                        retry_count += 1
                        time.sleep(0.5)
                    else:
                        logger.error(f"[{i}/{len(stocks)}] ❌ {stock_code} {stock_name} 同步失败: {e}")
                        fail_count += 1
                        break
            
            # 防止被封，每次请求后暂停
            if not success or retry_count > 0:
                time.sleep(0.5)
            else:
                time.sleep(0.3)
        
        # 查询最终数据库记录数
        total_stocks = db.query(Financial.stock_code).distinct().count()
        total_records = db.query(Financial).count()
        
        logger.info("=" * 60)
        logger.info("📊 同步完成！")
        logger.info(f"✅ 成功: {success_count} 只")
        logger.info(f"❌ 失败: {fail_count} 只")
        logger.info(f"⏭️  跳过: {skip_count} 只")
        logger.info(f"📊 数据库中股票数: {total_stocks} 只")
        logger.info(f"💾 数据库总记录数: {total_records} 条")
        logger.info("=" * 60)
        
        return success_count, fail_count, total_stocks, total_records
        
    except Exception as e:
        logger.error(f"❌ 同步过程出错: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0, 0, 0
    finally:
        db.close()


if __name__ == "__main__":
    # 初始化数据库
    init_db()
    
    success, fail, total_stocks, total_records = sync_financial_data()
    
    # 输出结果供外部脚本使用
    print(f"SUCCESS={success}")
    print(f"FAIL={fail}")
    print(f"TOTAL_STOCKS={total_stocks}")
    print(f"TOTAL_RECORDS={total_records}")
