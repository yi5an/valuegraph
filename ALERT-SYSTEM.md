# ValueAnalyzer 定时提醒系统 - 完整文档

**创建时间**：2026-03-24  
**状态**：✅ 已上线运行

---

## 📊 系统概述

基于 message 工具的主动推送系统，实现持仓股票实时监控和关键价位提醒。

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────┐
│          crontab 定时触发                    │
│     9:15 / 14:45 (工作日)                   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│      stock-alert-cron.sh                    │
│  - 获取实时股价（新浪财经API）               │
│  - 检测关键价位触发                          │
│  - 记录到 stock-alerts.log                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│      heartbeat 检查（用户发消息时）          │
│  - 运行 heartbeat-check.sh                  │
│  - 检测新提醒                               │
│  - 使用 message 工具推送                    │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│         Telegram 消息推送                   │
│  - chat_id: 6138938751                     │
│  - 实时持仓提醒                             │
│  - 操作建议                                 │
└─────────────────────────────────────────────┘
```

---

## 📁 核心文件

### 1. 定时任务脚本
**文件**：`stock-alert-cron.sh`  
**路径**：`/home/yi5an/.openclaw/workspace/projects/valuegraph/`  
**执行时间**：9:15 / 14:45（工作日）  
**功能**：
- 获取5只持仓股票实时价格
- 检测关键价位触发
- 记录到日志文件

### 2. Heartbeat检查脚本
**文件**：`heartbeat-check.sh`  
**路径**：`/home/yi5an/.openclaw/workspace/projects/valuegraph/`  
**触发时机**：用户发送消息时  
**功能**：
- 检查日志中的新提醒
- 返回 "NEW_ALERT_DETECTED" 或 "NO_NEW_ALERT"

### 3. 日志文件
**文件**：`stock-alerts.log`  
**路径**：`/home/yi5an/.openclaw/workspace/projects/valuegraph/`  
**格式**：
```
[2026-03-24 09:44:40] === 定时提醒触发 ===
2026-03-24 09:44:40|定时检查|🔴 全志科技...
```

### 4. 发送标记
**文件**：`.last-sent-time`  
**路径**：`/home/yi5an/.openclaw/workspace/projects/valuegraph/`  
**功能**：记录上次发送时间戳，避免重复发送

---

## 📊 持仓配置（5只股票）

| 股票 | 代码 | 数量 | 成本价 | 关键价位 |
|------|------|------|--------|---------|
| **迈瑞医疗** | 300760 | 200股 | ¥192.25 | 🟡 加仓：¥160-175<br>🔵 减仓：¥210-230 |
| **全志科技** | 300458 | 1000股 | ¥42.822 | 🔴 加仓：¥35-38<br>🔵 减仓：¥45-48 |
| **比亚迪** | 002594 | 500股 | ¥92.828 | 🟢 持有：¥90-110<br>🔵 减仓：¥115-120 |
| **潮宏基** | 002345 | 1400股 | ¥14.02 | ⚠️ 止损：<¥10 |
| **招商银行** | 600036 | 400股 | ¥39.02 | 🟡 加仓：¥36-38<br>🔵 减仓：¥45-48 |

---

## ⏰ 定时任务配置

### crontab 配置
```bash
# 开盘前分析（9:15）
15 9 * * 1-5 /home/yi5an/.openclaw/workspace/projects/valuegraph/stock-alert-cron.sh

# 收盘前分析（14:45）
45 14 * * 1-5 /home/yi5an/.openclaw/workspace/projects/valuegraph/stock-alert-cron.sh
```

### 查看定时任务
```bash
crontab -l | grep stock-alert
```

### 手动触发
```bash
/home/yi5an/.openclaw/workspace/projects/valuegraph/stock-alert-cron.sh
```

---

## 💬 消息推送机制

### 推送方式
- **工具**：`message`（OpenClaw内置）
- **channel**：`telegram`
- **target**：`6138938751`

### 消息格式
```
📊 持仓实时监控 - [时间]

=== 持仓股票实时价格 ===
迈瑞医疗(300760): ¥165.71
全志科技(300458): ¥35.46
比亚迪(002594): ¥105.09
潮宏基(002345): ¥9.72
招商银行(600036): ¥38.92

=== 关键提醒 ===
🔴 全志科技(¥35.46)已进入加仓区间（¥35-38）
💡 建议：可加仓500股

---
ValueAnalyzer 自动监控
```

---

## 🔧 使用方法

### 1. 自动运行（推荐）
- crontab 已配置，每天 9:15 和 14:45 自动运行
- 无需手动干预

### 2. 手动触发
```bash
# 执行监控脚本
/home/yi5an/.openclaw/workspace/projects/valuegraph/stock-alert-cron.sh

# 检查是否有新提醒
/home/yi5an/.openclaw/workspace/projects/valuegraph/heartbeat-check.sh

# 查看日志
tail -50 /home/yi5an/.openclaw/workspace/projects/valuegraph/stock-alerts.log
```

### 3. 测试推送
发送任何消息给 ValueAnalyzer，他会检查日志并推送新提醒。

---

## 📋 维护指南

### 日志管理
```bash
# 查看最新日志
tail -100 /home/yi5an/.openclaw/workspace/projects/valuegraph/stock-alerts.log

# 清空日志（谨慎）
> /home/yi5an/.openclaw/workspace/projects/valuegraph/stock-alerts.log

# 重置发送标记
rm /home/yi5an/.openclaw/workspace/projects/valuegraph/.last-sent-time
```

### 更新持仓
编辑 `HEARTBEAT.md` 文件，更新持仓信息和关键价位。

### 调整定时任务
```bash
# 编辑crontab
crontab -e

# 查看当前配置
crontab -l
```

---

## ⚠️ 注意事项

1. **数据源**：新浪财经API（`https://hq.sinajs.cn/list=股票代码`）
2. **更新频率**：9:15 和 14:45（交易日）
3. **推送延迟**：用户发送消息时立即检查并推送
4. **避免重复**：使用 `.last-sent-time` 标记避免重复发送

---

## 🚀 未来扩展

### 可添加功能
- [ ] 实时涨跌幅监控（>3%触发）
- [ ] 成交量异常监控
- [ ] 技术指标提醒（MA、MACD等）
- [ ] 每日收盘报告（自动推送）
- [ ] 每周持仓周报（周日推送）
- [ ] 财报发布提醒
- [ ] 分红日期提醒

---

## 📊 系统状态

| 组件 | 状态 | 说明 |
|------|------|------|
| **crontab** | ✅ 已配置 | 9:15/14:45 |
| **stock-alert-cron.sh** | ✅ 正常 | 获取实时股价 |
| **heartbeat-check.sh** | ✅ 正常 | 检查新提醒 |
| **message 工具** | ✅ 可用 | 主动推送 |
| **日志系统** | ✅ 正常 | stock-alerts.log |

---

**最后更新**：2026-03-24 09:45  
**维护者**：ValueAnalyzer
