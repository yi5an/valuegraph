#!/usr/bin/env python3
"""
财务数据同步脚本
从市值前 200 的股票中同步财务数据
"""
import sys
import time
import logging
from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.services.data_collector import AkShareCollector
from app.services.financial_analysis import FinancialService
from app.models.financial import Financial

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
        # 获取市值前 200 的股票
        logger.info("📊 正在获取 A 股股票列表...")
        all_stocks = AkShareCollector.get_a_stock_list()
        
        if not all_stocks:
            logger.error("❌ 获取股票列表失败")
            return 0, 0, 0
        
        # 按市值排序（降序）
        all_stocks_sorted = sorted(
            all_stocks,
            key=lambda x: x.get('market_cap', 0) or 0,
            reverse=True
        )
        
        # 取前 200 只
        top_200 = all_stocks_sorted[:200]
        logger.info(f"✅ 已选取市值前 {len(top_200)} 只股票")
        
        # 获取已有数据的股票
        existing_stocks = get_existing_stocks(db)
        logger.info(f"📊 数据库中已有 {len(existing_stocks)} 只股票的财务数据")
        
        # 统计变量
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        # 创建 FinancialService 实例
        service = FinancialService(db)
        
        # 遍历前 200 只股票
        for i, stock in enumerate(top_200, 1):
            stock_code = stock['stock_code']
            stock_name = stock['name']
            
            # 跳过已有数据的股票
            if stock_code in existing_stocks:
                logger.info(f"[{i}/200] ⏭️  跳过 {stock_code} {stock_name} (已有数据)")
                skip_count += 1
                continue
            
            # 获取财务数据
            logger.info(f"[{i}/200] 📈 正在获取 {stock_code} {stock_name} 的财务数据...")
            try:
                financial_data = AkShareCollector.get_financial_data(stock_code)
                
                if financial_data:
                    # 保存到数据库
                    service._save_financial_data(stock_code, financial_data)
                    logger.info(f"[{i}/200] ✅ {stock_code} {stock_name} 同步成功，共 {len(financial_data)} 条记录")
                    success_count += 1
                else:
                    logger.warning(f"[{i}/200] ⚠️  {stock_code} {stock_name} 无财务数据")
                    fail_count += 1
                
                # 防止被封，每次请求后暂停
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"[{i}/200] ❌ {stock_code} {stock_name} 同步失败: {e}")
                fail_count += 1
                time.sleep(0.5)  # 失败后多等待一下
        
        # 查询最终数据库记录数
        total_records = db.query(Financial).count()
        
        logger.info("=" * 60)
        logger.info("📊 同步完成！")
        logger.info(f"✅ 成功: {success_count} 只")
        logger.info(f"❌ 失败: {fail_count} 只")
        logger.info(f"⏭️  跳过: {skip_count} 只")
        logger.info(f"💾 数据库总记录数: {total_records} 条")
        logger.info("=" * 60)
        
        return success_count, fail_count, total_records
        
    except Exception as e:
        logger.error(f"❌ 同步过程出错: {e}")
        return 0, 0, 0
    finally:
        db.close()


if __name__ == "__main__":
    success, fail, total = sync_financial_data()
    
    # 输出结果供外部脚本使用
    print(f"SUCCESS={success}")
    print(f"FAIL={fail}")
    print(f"TOTAL={total}")
