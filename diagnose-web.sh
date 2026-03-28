#!/bin/bash
# Web Search 诊断脚本

echo "=== 1. 检查网络连接 ==="
ping -c 2 api.search.brave.com 2>&1 | grep "time=" || echo "❌ 无法连接到 Brave API"

echo -e "\n=== 2. 检查代理配置 ==="
echo "HTTP_PROXY: $HTTP_PROXY"
echo "HTTPS_PROXY: $HTTPS_PROXY"

echo -e "\n=== 3. 测试不使用代理 ==="
curl -s --noproxy "*" --max-time 5 "https://api.search.brave.com/res/v1/web/search?q=test&count=1" \
  -H "Accept: application/json" \
  -H "X-Subscription-Token: BSAbGkPzwk6pm3PqTPR77RT0-5JjLHQ" | jq -r '.type // .error // "无响应"' 2>&1

echo -e "\n=== 4. 测试使用代理 ==="
curl -s --proxy http://127.0.0.1:7890 --max-time 5 "https://api.search.brave.com/res/v1/web/search?q=test&count=1" \
  -H "Accept: application/json" \
  -H "X-Subscription-Token: BSAbGkPzwk6pm3PqTPR77RT0-5JjLHQ" | jq -r '.type // .error // "无响应"' 2>&1

echo -e "\n=== 5. 检查 API Key 长度 ==="
KEY="BSAbGkPzwk6pm3PqTPR77RT0-5JjLHQ"
echo "API Key 长度: ${#KEY} 字符"
if [ ${#KEY} -lt 30 ]; then
  echo "⚠️  API Key 可能不完整（通常 30+ 字符）"
fi

echo -e "\n诊断完成！"
