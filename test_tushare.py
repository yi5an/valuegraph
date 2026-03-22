#!/usr/bin/env python3
"""Tushare API 测试脚本"""
import sys

try:
    import tushare as ts
    
    # 设置 token
    token = 'b59437be53ff5015a8bc97dd3fe11e6e1736c8572352be2398927838'
    ts.set_token(token)
    pro = ts.pro_api()
    
    print("=" * 60)
    print("Tushare API 测试开始")
    print("=" * 60)
    
    # 测试 1：验证 Token 有效性
    print("\n[测试 1] 验证 Tushare Token...")
    try:
        # 尝试获取交易日历（这个接口通常不需要高级权限）
        cal = pro.trade_cal(exchange='SSE', start_date='20260101', end_date='20260110')
        print(f"✓ Token 验证成功，可以访问 Tushare API")
        print(f"  获取到 {len(cal)} 条交易日历数据")
        if len(cal) > 0:
            print(f"  示例数据：{cal.head(3)}")
    except Exception as e:
        print(f"⚠ 交易日历接口访问受限: {str(e)}")
    
    # 测试 2：获取股票列表（尝试不同方式）
    print("\n[测试 2] 尝试获取股票列表...")
    try:
        stocks = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
        print(f"✓ 获取到 {len(stocks)} 只股票")
        print(f"前 5 条数据：\n{stocks.head()}")
    except Exception as e:
        print(f"⚠ 股票列表接口需要更高级别权限: {str(e)}")
        print(f"  提示：请访问 https://tushare.pro/document/1?doc_id=108 查看权限详情")
    
    # 测试 3：尝试获取基础财务数据
    print("\n[测试 3] 尝试获取贵州茅台财务数据...")
    try:
        df = pro.daily_basic(ts_code='600519.SH', fields='ts_code,trade_date,pe,pb,ps,total_mv,circ_mv')
        print(f"✓ 获取到 {len(df)} 条财务数据")
        if len(df) > 0:
            print(f"前 5 条数据：\n{df.head()}")
    except Exception as e:
        print(f"⚠ 财务数据接口需要更高级别权限: {str(e)}")
    
    # 测试 4：尝试获取 ROE 数据
    print("\n[测试 4] 尝试获取贵州茅台 ROE 数据...")
    try:
        roe = pro.fina_indicator(ts_code='600519.SH', fields='ts_code,end_date,roe,roa,grossprofit_margin')
        print(f"✓ 获取到 {len(roe)} 条 ROE 数据")
        if len(roe) > 0:
            print(f"前 5 条数据：\n{roe.head()}")
    except Exception as e:
        print(f"⚠ ROE 数据接口需要更高级别权限: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✓ Tushare API 连接测试完成")
    print("  注意：部分接口可能需要更高级别的 Tushare 权限")
    print("  请访问 https://tushare.pro/document/1?doc_id=108 了解权限说明")
    print("=" * 60)
    
except ImportError as e:
    print(f"\n✗ 缺少依赖: {str(e)}")
    print("  请运行: pip install tushare pandas")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
