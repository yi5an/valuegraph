#!/usr/bin/env python3
"""
股价监控脚本 - 定期检查股价并在达到理想价格时发送提醒
支持：宁德时代（SZ300750）、比亚迪（SZ002594）
"""

import json
import urllib.request
import ssl
from datetime import datetime
import sys

# 目标价格设置
TARGET_PRICES = {
    "SZ300750": {  # 宁德时代
        "name": "宁德时代",
        "buy_low": 280,    # 理想买入价下限
        "buy_high": 300,   # 理想买入价上限
        "current": 342.01
    },
    "SZ002594": {  # 比亚迪
        "name": "比亚迪",
        "buy_low": 60,     # 理想买入价下限
        "buy_high": 70,    # 理想买入价上限
        "current": 89.32
    }
}

# 飞书 webhook URL（需要配置）
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-token"

def get_stock_price(stock_code):
    """从雪球获取股价"""
    try:
        # 创建不验证 SSL 的上下文
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # 使用代理
        proxy_handler = urllib.request.ProxyHandler({
            'http': 'http://127.0.0.1:7890',
            'https': 'http://127.0.0.1:7890'
        })
        opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_context))
        
        url = f"https://xueqiu.com/v4/stock/quote.json?code={stock_code}&_=1"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        response = opener.open(req, timeout=10)
        data = json.loads(response.read().decode('utf-8'))
        
        if stock_code in data:
            return {
                'price': float(data[stock_code]['current']),
                'change': float(data[stock_code]['percentage']),
                'name': data[stock_code]['name']
            }
        return None
    except Exception as e:
        print(f"获取股价失败: {e}")
        return None

def send_feishu_alert(stock_name, current_price, target_range, action):
    """发送飞书提醒"""
    try:
        message = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": True
                },
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": f"💰 股价提醒：{stock_name}"
                    },
                    "template": "green" if action == "buy" else "red"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": f"**当前价格**: ¥{current_price:.2f}\n**目标区间**: ¥{target_range}\n**建议操作**: {'✅ 可以买入' if action == 'buy' else '⚠️ 观望'}"
                        }
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"提醒时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                            }
                        ]
                    }
                ]
            }
        }
        
        data = json.dumps(message).encode('utf-8')
        req = urllib.request.Request(FEISHU_WEBHOOK, data=data, headers={'Content-Type': 'application/json'})
        response = urllib.request.urlopen(req, timeout=10)
        
        print(f"飞书提醒已发送: {stock_name}")
        return True
    except Exception as e:
        print(f"发送飞书提醒失败: {e}")
        return False

def save_alert(stock_name, current_price, target_range, action):
    """保存提醒到文件"""
    alert_file = "/home/yi5an/.openclaw/workspace/projects/valuegraph/stock-alerts.log"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(alert_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {stock_name} | 当前: ¥{current_price:.2f} | 目标: ¥{target_range} | 操作: {action}\n")

def check_stocks():
    """检查所有股票价格"""
    print(f"\n=== 股价监控 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    
    alerts = []
    
    for stock_code, config in TARGET_PRICES.items():
        print(f"检查 {config['name']} ({stock_code})...")
        
        # 获取实时价格
        stock_data = get_stock_price(stock_code)
        
        if stock_data:
            current_price = stock_data['price']
            print(f"  当前价格: ¥{current_price:.2f}")
            print(f"  目标区间: ¥{config['buy_low']}-{config['buy_high']}")
            
            # 检查是否达到买入价
            if current_price <= config['buy_high']:
                action = "buy"
                target_range = f"{config['buy_low']}-{config['buy_high']}"
                
                print(f"  ✅ 达到目标价格！建议操作: 买入")
                
                # 保存提醒
                save_alert(config['name'], current_price, target_range, action)
                alerts.append({
                    'name': config['name'],
                    'price': current_price,
                    'range': target_range,
                    'action': action
                })
                
                # 发送飞书提醒（需要配置 webhook）
                # send_feishu_alert(config['name'], current_price, target_range, action)
            else:
                distance = ((current_price - config['buy_high']) / config['buy_high']) * 100
                print(f"  ⚠️ 距离目标价还差 {distance:.2f}%")
        else:
            print(f"  ❌ 获取股价失败")
        
        print()
    
    return alerts

if __name__ == "__main__":
    alerts = check_stocks()
    
    if alerts:
        print(f"\n发现 {len(alerts)} 个买入机会！")
        for alert in alerts:
            print(f"  - {alert['name']}: ¥{alert['price']:.2f}")
    else:
        print("\n暂无买入机会，继续观望。")
    
    # 返回状态码供 cron 使用
    sys.exit(0 if not alerts else 1)
