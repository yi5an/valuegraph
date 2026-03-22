#!/usr/bin/env python3
"""
简单的 AkShare 测试脚本
"""

import sys
import os

os.environ['TQDM_DISABLE'] = '1'

try:
    import akshare as ak
    print("✅ AkShare 导入成功")
except Exception as e:
    print(f"❌ AkShare 导入失败: {e}")
    sys.exit(1)

print("\n=== 测试 AkShare API ===\n")

# 测试 1：获取股票列表
print("1. 测试获取 A 股股票列表...")
try:
    df = ak.stock_zh_a_spot_em()
    print(f"   ✅ 成功获取到 {len(df)} 只股票")
    print(f"   列名: {df.columns.tolist()}")
    if not df.empty:
        print(f"   前 3 只股票:")
        for i, row in df.head(3).iterrows():
            print(f"      {row.get('代码', 'N/A')}: {row.get('名称', 'N/A')}")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    print("   注意：可能是网络或代理问题")

# 测试 2：获取财务数据
print("\n2. 测试获取财务数据 (600519 - 贵州茅台)...")
try:
    df = ak.stock_financial_analysis_indicator(symbol="600519")
    print(f"   ✅ 成功获取到财务数据")
    print(f"   列名: {df.columns.tolist()}")
    print(f"   数据行数: {len(df)}")
    if not df.empty:
        print(f"   第一条记录: {df.iloc[0].to_dict()}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 测试 3：获取股东信息（使用 stock_main_stock_holder）
print("\n3. 测试获取股东信息 (600519 - 贵州茅台)...")
try:
    df = ak.stock_main_stock_holder(stock="600519")
    print(f"   ✅ 成功获取到股东数据")
    print(f"   股东数量: {len(df)}")
    print(f"   列名: {df.columns.tolist()}")
    if not df.empty:
        print(f"   前 3 大股东:")
        for i, row in df.head(3).iterrows():
            print(f"      {row.to_dict()}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 测试 4：使用另一个股东函数
print("\n4. 测试获取流通股东 (600519 - 贵州茅台)...")
try:
    df = ak.stock_circulate_stock_holder(symbol="600519")
    print(f"   ✅ 成功获取到流通股东数据")
    print(f"   股东数量: {len(df)}")
    print(f"   列名: {df.columns.tolist()}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

print("\n=== 测试完成 ===")
