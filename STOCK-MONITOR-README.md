# 股价监控系统使用说明

## 📊 监控目标

### 宁德时代（SZ300750）
- **当前价格**: ¥342.01（2026-02-27 15:34）
- **理想买入价**: ¥280-300
- **距离目标**: -14%
- **建议**: 等待回调至 ¥300 以下

### 比亚迪（SZ002594）
- **当前价格**: ¥89.32（2026-02-27 15:04）
- **理想买入价**: ¥60-70
- **距离目标**: -27%
- **建议**: 等待回调至 ¥70 以下

---

## ⏰ 监控设置

### 执行频率
- **工作日（周一至周五）**: 每小时检查一次（09:00, 10:00, ..., 15:00）
- **周末**: 不检查

### 监控脚本
- **位置**: `/home/yi5an/.openclaw/workspace/projects/valuegraph/check-stock.sh`
- **日志文件**: `stock-monitor.log`
- **提醒记录**: `stock-alerts.log`

### Cron 任务
```bash
0 * * * 1-5 /home/yi5an/.openclaw/workspace/projects/valuegraph/check-stock.sh
```

---

## 🔔 提醒方式

### 当前状态
✅ **日志记录**: 监控结果记录到 `stock-monitor.log`
✅ **提醒记录**: 达到目标价时记录到 `stock-alerts.log`
⚠️ **飞书提醒**: 需要配置 webhook 才能启用

### 启用飞书提醒
1. 获取飞书群机器人 webhook URL
2. 编辑 `check-stock.sh`，添加 webhook URL
3. 取消注释发送飞书提醒的代码

---

## 📝 手动检查

### 立即检查股价
```bash
/home/yi5an/.openclaw/workspace/projects/valuegraph/check-stock.sh
```

### 查看监控日志
```bash
tail -50 /home/yi5an/.openclaw/workspace/projects/valuegraph/stock-monitor.log
```

### 查看提醒记录
```bash
cat /home/yi5an/.openclaw/workspace/projects/valuegraph/stock-alerts.log
```

---

## 🎯 价值投资建议

### 宁德时代
- **护城河**: ⭐⭐⭐⭐⭐（全球龙头）
- **ROE**: 20.29%（优秀）
- **安全边际**: 22%（不足 30%）
- **建议**: 等待 ¥300 以下再买入

### 比亚迪
- **护城河**: ⭐⭐⭐⭐（较宽）
- **ROE**: 17.46%（良好）
- **安全边际**: 16%（不足 30%）
- **建议**: 等待 ¥70 以下再买入

### 组合投资方案
- **宁德时代 60%**（护城河更宽、ROE 更高）
- **比亚迪 40%**（估值更低、业务多元）

---

## 📈 下次操作

### 当股价达到目标时
1. 收到提醒后，立即查看实时股价
2. 检查市场情绪和新闻
3. 确认财务指标（ROE、PE、PB）
4. 分批建仓（不要一次性买入）

### 调整目标价
如需调整目标价格，编辑以下文件：
```bash
nano /home/yi5an/.openclaw/workspace/projects/valuegraph/check-stock.sh
```

修改 `TARGET_HIGH` 变量即可。

---

## 🛠️ 维护

### 更新当前价格
每周更新一次当前价格（手动）：
```bash
# 编辑配置文件
nano /home/yi5an/.openclaw/workspace/projects/valuegraph/stock-alert-config.json
```

### 停止监控
```bash
crontab -e
# 注释掉或删除相关行
```

### 重新启动监控
```bash
(crontab -l 2>/dev/null | grep -v "check-stock.sh"; echo "0 * * * 1-5 /home/yi5an/.openclaw/workspace/projects/valuegraph/check-stock.sh") | crontab -
```

---

**最后更新**: 2026-02-27 18:30
**创建者**: ValueAnalyzer
