#!/bin/bash
# Heartbeat检查脚本 - 检查是否有新的提醒需要发送

WORKSPACE="/home/yi5an/.openclaw/workspace/projects/valuegraph"
LOG_FILE="$WORKSPACE/stock-alerts.log"
SENT_FLAG="$WORKSPACE/.last-sent-time"

# 获取最后发送时间
if [ -f "$SENT_FLAG" ]; then
    LAST_SENT=$(cat "$SENT_FLAG")
else
    LAST_SENT="0"
fi

# 获取最新的提醒（过去1小时内的）
LATEST_ALERT=$(tail -100 "$LOG_FILE" | grep "^\[" | tail -1 | awk -F'[][]' '{print $2}')

if [ ! -z "$LATEST_ALERT" ]; then
    # 转换为时间戳
    LATEST_TIMESTAMP=$(date -d "$LATEST_ALERT" +%s 2>/dev/null || echo "0")
    
    # 如果有新提醒（比上次发送时间更新）
    if [ "$LATEST_TIMESTAMP" -gt "$LAST_SENT" ]; then
        echo "NEW_ALERT_DETECTED"
        # 更新发送时间标记
        echo "$LATEST_TIMESTAMP" > "$SENT_FLAG"
    else
        echo "NO_NEW_ALERT"
    fi
else
    echo "NO_NEW_ALERT"
fi
