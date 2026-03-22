#!/usr/bin/env python3
"""
AkShare API 测试脚本
测试股票列表、财务数据、股东信息等功能
"""

import sys
sys.path.insert(0, '/usr/local/soft/anaconda3/lib/python3.9/site-packages')

import akshare as ak
import asyncio


async def test_akshare():
    """测试 AkShare API"""
    print("=" * 60)
    print("🚀 开始测试 AkShare API")
    print("=" * 60)
    
    # 测试 1：获取 A 股股票列表
    print("\n📊 测试 1：获取 A 股股票列表...")
    try:
        df = ak.stock_zh_a_spot_em()
        print(f"✅ 成功获取到 {len(df)} 只股票")
        print("\n前 5 只股票：")
        print(df.head())
        print("\n列名：", df.columns.tolist())
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False
    
    # 测试 2：获取财务数据（以贵州茅台为例）
    print("\n" + "=" * 60)
    print("📈 测试 2：获取财务数据（600519 - 贵州茅台）...")
    try:
        df = ak.stock_financial_analysis_indicator(symbol="600519")
        print(f"✅ 成功获取到财务数据")
        print("\n前 5 条记录：")
        print(df.head())
        print("\n列名：", df.columns.tolist())
        
        # 提取关键指标
        if not df.empty:
            latest = df.iloc[0]
            print("\n关键财务指标：")
            print(f"  - ROE: {latest.get('roe', 'N/A')}")
            print(f"  - ROA: {latest.get('roa', 'N/A')}")
            print(f"  - 毛利率: {latest.get('毛利率', 'N/A')}")
            print(f"  - 资产负债率: {latest.get('资产负债率', 'N/A')}")
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False
    
    # 测试 3：获取十大股东
    print("\n" + "=" * 60)
    print("👥 测试 3：获取十大股东（600519 - 贵州茅台）...")
    try:
        df = ak.stock_gdfx_holding_analyse(symbol="600519")
        print(f"✅ 成功获取到股东数据")
        print("\n前 10 条记录：")
        print(df.head(10))
        print("\n列名：", df.columns.tolist())
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False
    
    # 测试 4：获取另一只股票的数据（测试稳定性）
    print("\n" + "=" * 60)
    print("🔄 测试 4：获取另一只股票的数据（000001 - 平安银行）...")
    try:
        df = ak.stock_financial_analysis_indicator(symbol="000001")
        print(f"✅ 成功获取到财务数据")
        print("\n前 3 条记录：")
        print(df.head(3))
    except Exception as e:
        print(f"❌ 失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ AkShare API 测试完成")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(test_akshare())
    sys.exit(0 if success else 1)
