#!/usr/bin/env python3
"""测试 Brave API 通过代理的脚本"""

import urllib.request
import json
import sys

# Brave API 配置
BRAVE_API_KEY = "BSAbGkPzwk6pm3PqTPR77RT0-5JjLHQ"
PROXY = "http://127.0.0.1:7890"

def test_brave_api(use_proxy=True):
    """测试 Brave API"""
    # URL 编码查询参数
    import urllib.parse
    query = urllib.parse.quote("比亚迪")
    url = f"https://api.search.brave.com/res/v1/web/search?q={query}&count=2&search_lang=zh"
    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": BRAVE_API_KEY
    }

    try:
        req = urllib.request.Request(url, headers=headers)

        if use_proxy:
            # 使用代理
            import ssl
            proxy_handler = urllib.request.ProxyHandler({
                'http': PROXY,
                'https': PROXY
            })
            # 创建不验证 SSL 的上下文（仅用于测试）
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            https_handler = urllib.request.HTTPSHandler(context=ssl_context)
            opener = urllib.request.build_opener(proxy_handler, https_handler)
        else:
            # 不使用代理
            proxy_handler = urllib.request.ProxyHandler({})
            opener = urllib.request.build_opener(proxy_handler)

        response = opener.open(req, timeout=15)
        data = json.loads(response.read().decode('utf-8'))

        print(f"✅ Brave API 请求成功！")
        print(f"响应类型: {data.get('type', 'unknown')}")

        if 'web' in data and 'results' in data['web']:
            results = data['web']['results']
            print(f"找到 {len(results)} 条结果:")
            for i, result in enumerate(results[:2], 1):
                print(f"\n{i}. {result.get('title', 'No title')}")
                print(f"   URL: {result.get('url', 'No URL')}")
                print(f"   摘要: {result.get('description', 'No description')[:100]}...")

        return True

    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

if __name__ == "__main__":
    use_proxy = len(sys.argv) > 1 and sys.argv[1] == '--proxy'

    print(f"=== 测试 Brave API {'(使用代理)' if use_proxy else '(不使用代理)'} ===")
    test_brave_api(use_proxy)
