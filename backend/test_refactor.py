#!/usr/bin/env python3
"""
测试股票推荐系统重构

验证：
1. 策略模块加载正常
2. 价值投资策略评分正常
3. RecommendationService 策略调度正常
4. API 端点注册正常
"""

import sys
sys.path.insert(0, '/home/yi5an/.openclaw/workspace/projects/valuegraph/backend')

from app.services.strategies import get_strategy, list_strategies
from app.services.recommendation import RecommendationService
from app.api import stocks

def test_strategy_registry():
    """测试策略注册表"""
    print("=" * 50)
    print("测试 1: 策略注册表")
    print("=" * 50)
    
    strategies = list_strategies()
    print(f"✓ 可用策略: {list(strategies.keys())}")
    
    strategy = get_strategy('value')
    print(f"✓ 策略名称: {strategy.name}")
    print(f"✓ 策略描述: {strategy.description}")
    
    print("✅ 测试通过\n")


def test_value_strategy():
    """测试价值投资策略"""
    print("=" * 50)
    print("测试 2: 价值投资策略评分")
    print("=" * 50)
    
    strategy = get_strategy('value')
    
    # 测试数据（高 ROE、低负债、高增长）
    financial_data = {
        'roe': 25.0,
        'debt_ratio': 30.0,
        'gross_margin': 40.0,
        'net_profit': 1000000,
        'operating_cash_flow': 1500000,
        'net_profit_yoy': 30.0,
        'revenue_yoy': 25.0,
        'eps': 3.0,
        'bvps': 20.0,
    }
    
    stock_data = {
        'latest_pe': 12.0,
    }
    
    # 筛选测试
    passed, reasons = strategy.screen(financial_data)
    print(f"✓ 筛选结果: {passed}")
    assert passed, f"应该通过筛选，但失败了: {reasons}"
    
    # 评分测试
    score = strategy.calculate_score(financial_data, stock_data)
    print(f"✓ 综合得分: {score}")
    assert 0 <= score <= 100, "得分应在 0-100 之间"
    
    # 安全边际测试
    safety_margin = strategy.calculate_safety_margin(financial_data, stock_data)
    print(f"✓ 安全边际: {safety_margin:.2f}%")
    assert safety_margin is not None, "应该能计算安全边际"
    
    # 评级测试
    grade = strategy.get_grade(score, safety_margin)
    print(f"✓ 评级: {grade}")
    assert grade in ["A+", "A", "B", "C", "D"], "评级应该是有效的"
    
    # 得分明细测试
    breakdown = strategy.get_score_breakdown(financial_data, stock_data)
    print(f"✓ 得分明细: {breakdown}")
    assert len(breakdown) == 5, "应该有 5 个维度的得分"
    
    print("✅ 测试通过\n")


def test_recommendation_service():
    """测试 RecommendationService"""
    print("=" * 50)
    print("测试 3: RecommendationService 策略调度")
    print("=" * 50)
    
    strategies = RecommendationService.get_available_strategies()
    print(f"✓ 可用策略: {list(strategies.keys())}")
    
    assert 'value' in strategies, "应该有 value 策略"
    
    print("✅ 测试通过\n")


def test_api_routes():
    """测试 API 路由注册"""
    print("=" * 50)
    print("测试 4: API 路由注册")
    print("=" * 50)
    
    routes = [route.path for route in stocks.router.routes if hasattr(route, 'path')]
    print(f"✓ 已注册路由: {routes}")
    
    assert '/recommend' in routes, "应该有 /recommend 路由"
    assert '/strategies' in routes, "应该有 /strategies 路由"
    assert '/compare' in routes, "应该有 /compare 路由"
    
    print("✅ 测试通过\n")


def test_backward_compatibility():
    """测试向后兼容性"""
    print("=" * 50)
    print("测试 5: 向后兼容性")
    print("=" * 50)
    
    # 测试旧的 calculate_score 方法
    service = RecommendationService(db=None)
    
    # 模拟旧版调用
    score = service.calculate_score(roe=20.0, debt_ratio=40.0, pe=15.0)
    print(f"✓ 旧版评分方法: {score}")
    assert 0 <= score <= 100, "得分应在 0-100 之间"
    
    # 测试旧版 generate_reason 方法
    reason = service.generate_reason(roe=20.0, debt_ratio=40.0, pe=15.0)
    print(f"✓ 旧版推荐理由: {reason}")
    assert isinstance(reason, str), "推荐理由应该是字符串"
    
    print("✅ 测试通过\n")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("股票推荐系统重构测试")
    print("=" * 50 + "\n")
    
    try:
        test_strategy_registry()
        test_value_strategy()
        test_recommendation_service()
        test_api_routes()
        test_backward_compatibility()
        
        print("=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)
        
        print("\n验收标准验证：")
        print("✅ 1. 策略模块可正常加载和实例化")
        print("✅ 2. 价值投资策略评分体系正常工作")
        print("✅ 3. 安全边际计算正常")
        print("✅ 4. 评级体系正常")
        print("✅ 5. API 路由已正确注册")
        print("✅ 6. 向后兼容性保持")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
