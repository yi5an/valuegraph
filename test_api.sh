#!/bin/bash
# ValueGraph API 测试脚本

BASE_URL="http://localhost:8000"

echo "=== 测试 ValueGraph API ==="
echo ""

# 测试 1：健康检查
echo "1. 测试健康检查..."
curl -s "$BASE_URL/api/health" | python3 -m json.tool
echo ""

# 测试 2：根路径
echo "2. 测试根路径..."
curl -s "$BASE_URL/" | python3 -m json.tool
echo ""

# 测试 3：获取推荐股票
echo "3. 测试获取推荐股票 (可能需要一些时间)..."
curl -s "$BASE_URL/api/stocks/recommend?top_n=5" | python3 -m json.tool
echo ""

# 测试 4：获取股票详情
echo "4. 测试获取股票详情 (600519)..."
curl -s "$BASE_URL/api/stocks/600519" | python3 -m json.tool
echo ""

echo "=== 测试完成 ==="
