#!/usr/bin/env python3
"""
同步股东数据脚本
从热门股票列表中获取前100只股票的十大股东数据
"""
import sys
import os
import time
from datetime import datetime

# 添加项目路径到 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.shareholder import Shareholder
from app.services.data_collector import AkShareCollector
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def clear_shareholders(db: Session):
    """清空股东表（可选）"""
    try:
        db.query(Shareholder).delete()
        db.commit()
        logger.info("✅ 已清空股东表")
    except Exception as e:
        logger.error(f"❌ 清空股东表失败: {e}")
        db.rollback()


def sync_shareholders(db: Session, limit: int = 100, clear_before: bool = False):
    """
    同步股东数据
    
    Args:
        db: 数据库会话
        limit: 要处理的股票数量
        clear_before: 是否在同步前清空表
    """
    if clear_before:
        clear_shareholders(db)
    
    # 1. 获取股票列表
    logger.info(f"📥 正在获取 A 股股票列表...")
    stocks = AkShareCollector.get_a_stock_list()
    
    if not stocks:
        logger.error("❌ 获取股票列表失败")
        return 0
    
    # 取前 limit 只
    stocks = stocks[:limit]
    logger.info(f"📊 将处理 {len(stocks)} 只股票的股东数据")
    
    success_count = 0
    fail_count = 0
    total_shareholders = 0
    
    # 2. 逐只股票获取股东数据
    for idx, stock in enumerate(stocks, 1):
        stock_code = stock['stock_code']
        stock_name = stock.get('name', '')
        
        try:
            # 调用 AkShare 获取股东信息
            shareholder_data = AkShareCollector.get_shareholders(stock_code)
            
            if not shareholder_data or not shareholder_data.get('top_10_shareholders'):
                logger.warning(f"⚠️  [{idx}/{len(stocks)}] {stock_code} {stock_name}: 无股东数据")
                fail_count += 1
                time.sleep(0.5)
                continue
            
            # 获取报告期
            report_date = shareholder_data.get('report_date', datetime.now().strftime('%Y-%m-%d'))
            
            # 3. 存入数据库
            holders_added = 0
            for holder_info in shareholder_data['top_10_shareholders']:
                try:
                    # 检查是否已存在（同一股票+同一报告期+同一股东）
                    existing = db.query(Shareholder).filter(
                        Shareholder.stock_code == stock_code,
                        Shareholder.report_date == report_date,
                        Shareholder.holder_name == holder_info['holder_name']
                    ).first()
                    
                    if existing:
                        # 更新现有记录
                        existing.rank = holder_info.get('rank', 0)
                        existing.hold_amount = holder_info.get('hold_amount')
                        existing.hold_ratio = holder_info.get('hold_ratio')
                        existing.holder_type = holder_info.get('holder_type', '')
                        existing.change = holder_info.get('change', '')
                    else:
                        # 创建新记录
                        shareholder = Shareholder(
                            stock_code=stock_code,
                            report_date=report_date,
                            rank=holder_info.get('rank', 0),
                            holder_name=holder_info['holder_name'],
                            hold_amount=holder_info.get('hold_amount'),
                            hold_ratio=holder_info.get('hold_ratio'),
                            holder_type=holder_info.get('holder_type', ''),
                            change=holder_info.get('change', ''),
                        )
                        db.add(shareholder)
                        holders_added += 1
                
                except Exception as e:
                    logger.error(f"  ❌ 保存股东 {holder_info.get('holder_name', '')} 失败: {e}")
            
            db.commit()
            total_shareholders += holders_added
            success_count += 1
            
            # 每10只打印一次进度
            if idx % 10 == 0:
                logger.info(f"✅ 进度: {idx}/{len(stocks)} | 成功: {success_count} | 失败: {fail_count} | 累计股东: {total_shareholders}")
            else:
                logger.info(f"✅ [{idx}/{len(stocks)}] {stock_code} {stock_name}: 新增 {holders_added} 条股东数据")
            
        except Exception as e:
            logger.error(f"❌ [{idx}/{len(stocks)}] {stock_code} {stock_name}: 处理失败 - {e}")
            fail_count += 1
            db.rollback()
        
        # 避免限流，每只股票间 sleep 0.5s
        time.sleep(0.5)
    
    # 4. 最终统计
    logger.info("=" * 60)
    logger.info(f"🎉 同步完成!")
    logger.info(f"📊 统计:")
    logger.info(f"  - 处理股票: {len(stocks)} 只")
    logger.info(f"  - 成功: {success_count} 只")
    logger.info(f"  - 失败: {fail_count} 只")
    logger.info(f"  - 新增股东记录: {total_shareholders} 条")
    logger.info("=" * 60)
    
    return total_shareholders


def verify_shareholders(db: Session):
    """验证股东数据"""
    count = db.query(Shareholder).count()
    logger.info(f"📊 验证结果: shareholders 表共有 {count} 条数据")
    return count


if __name__ == "__main__":
    db = SessionLocal()
    
    try:
        logger.info("🚀 开始同步股东数据...")
        start_time = time.time()
        
        # 同步数据（取前100只股票）
        total = sync_shareholders(db, limit=100, clear_before=False)
        
        # 验证
        count = verify_shareholders(db)
        
        elapsed = time.time() - start_time
        logger.info(f"⏱️  总耗时: {elapsed:.2f} 秒")
        
        # 写结果到文件
        result = {
            "success": count > 0,
            "total_shareholders": count,
            "elapsed_seconds": round(elapsed, 2),
            "message": f"成功同步 {count} 条股东数据" if count > 0 else "同步失败，表仍为空"
        }
        
        with open('/tmp/shareholders_sync_result.txt', 'w') as f:
            import json
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📝 结果已写入 /tmp/shareholders_sync_result.txt")
        
        if count == 0:
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ 脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 写失败结果
        with open('/tmp/shareholders_sync_result.txt', 'w') as f:
            import json
            json.dump({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }, f, indent=2, ensure_ascii=False)
        
        sys.exit(1)
    
    finally:
        db.close()
