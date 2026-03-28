# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

---

## 股价监控任务

### 任务描述
定期检查持仓股票的股价，在关键价位发送操作提醒。

---

### 持仓组合监控（5只股票）

#### 1. 迈瑞医疗（SZ300760）- 医疗器械龙头
- **成本价**：¥192.25 | **数量**：200股 | **当前**：**¥165.83** | **浮亏**：-13.7%
- 🔴 止损：<¥160 | 🟡 **已进入加仓区**（¥160-175） | 🔵 减仓：¥210-230 | 🟣 清仓：>¥250

#### 2. 全志科技（SZ300458）- 芯片设计
- **成本价**：¥42.822 | **数量**：1000股 | **当前**：**¥35.33** | **浮亏**：-17.5%
- 🔴 **接近止损线**（差¥0.33） | 🟡 **已进入加仓区**（¥35-38） | 🔵 减仓：¥45-48

#### 3. 比亚迪（SZ002594）- 新能源汽车
- **成本价**：¥92.828 | **数量**：500股 | **当前**：**¥106.00** | **浮盈**：+14.2% ✅
- 🔴 止损：<¥85 | 🟢 **持有中**（¥90-110） | 🔵 减仓：¥115-120 | 🟣 清仓：>¥130

#### 4. 潮宏基（SZ002345）- 珠宝零售
- **成本价**：¥14.02 | **数量**：1400股 | **当前**：**¥10.20** | **浮亏**：-27.2% ⚠️
- 🔴 **接近止损线**（差¥0.20） | 建议：**考虑止损**

#### 5. 招商银行（SH600036）- 银行龙头
- **成本价**：¥39.0229 | **数量**：400股 | **当前**：**¥39.08** | **浮盈**：+0.1%
- 🟡 加仓：¥36-38 | 🟢 **持有中**（¥38-42） | 🔵 减仓：¥45-48

---

### 提醒规则

**价格触发**：
- 触及止损线：立即提醒
- 触及减仓/加仓位：当日收盘提醒
- 涨跌幅>5%：即时提醒

**定时报告**：
- 每日收盘后发送持仓日报
- 每周一发送持仓周报

**重大事件**：
- 财报发布
- 重大政策/行业变化
- 大额交易异动

---

### 执行频率
- **开盘前分析**：9:15（集合竞价阶段）
  - 获取实时股价
  - 分析隔夜新闻/公告
  - 给出开盘操作建议
  
- **收盘前分析**：14:45
  - 评估当日走势
  - 决定是否调仓
  - 给出尾盘操作建议

- **波动监控**：实时（涨跌幅>3%）

### 提醒方式
- **发送Telegram消息**：主动推送至 chat_id=6138938751（使用 message 工具）
  - 在heartbeat时检查日志文件中的最新提醒
  - 如果有新提醒，立即使用 message 工具推送
  - channel: telegram, target: 6138938751
- 记录到 stock-alerts.log
- 生成每日操作报告

### Heartbeat执行流程

**每次heartbeat触发时**：
1. 检查日志文件中的最新提醒（使用 heartbeat-check.sh）
2. 如果有未发送的提醒：
   - 读取提醒内容
   - 使用 `message` 工具发送Telegram消息到 chat_id=6138938751
   - 标记为已发送（更新 .last-sent-time）
3. 获取5只股票实时价格
4. 检查是否触发关键价位
5. 如果触发，记录到日志文件

**注意**：定时任务（9:15/14:45）会自动运行 stock-alert-cron.sh，将提醒记录到日志。我在 heartbeat 时检查日志并发送消息。

### 股票推荐机制
每次分析时，推荐2-3只可操作股票：
1. **价值股**：低估优质股（安全边际>30%）
2. **成长股**：高增长行业龙头
3. **防御股**：稳健分红股

### 最后更新
2026-03-18 23:15

---

## Heartbeat执行指令

**每次heartbeat时自动执行以下任务**：

### 1. 检查待发送提醒
```bash
# 检查是否有待发送的提醒
if [ -f /home/yi5an/.openclaw/workspace/projects/valuegraph/.stock-alert-pending ]; then
  # 读取提醒内容
  ALERT=$(cat /home/yi5an/.openclaw/workspace/projects/valuegraph/.stock-alert-pending)
  
  # 使用 sessions_send 发送Telegram消息
  # sessionKey: agent:valueanalyzer:telegram:direct:6138938751
  # message: $ALERT
  
  # 发送后清空文件
  > /home/yi5an/.openclaw/workspace/projects/valuegraph/.stock-alert-pending
fi
```

### 2. 定时触发（crontab已配置）
- **9:15** - 开盘前分析（触发stock-alert-cron.sh）
- **14:45** - 收盘前分析（触发stock-alert-cron.sh）

### 3. 主动推送流程
```
定时任务 → stock-alert-cron.sh → 创建.stock-alert-pending
    ↓
heartbeat → 检查.stock-alert-pending → sessions_send → Telegram消息
```

### 4. 消息格式
```
📊 持仓提醒 - [时间]

[股票名称]（代码）：当前价 ¥XX.XX
🔴 触发：[加仓/止损/减仓]区间
💡 操作建议：[具体建议]

---
ValueAnalyzer 自动提醒
```
