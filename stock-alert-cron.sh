#!/bin/bash
# 持仓监控定时提醒脚本 - 最终版
# 用于在开盘前和收盘前触发ValueAnalyzer发送Telegram消息

WORKSPACE="/home/yi5an/.openclaw/workspace/projects/valuegraph"
LOG_FILE="$WORKSPACE/stock-alerts.log"
PENDING_FILE="$WORKSPACE/.stock-alert-pending"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 获取实时股价
get_stock_price() {
    local code=$1
    local price=$(curl -s "https://hq.sinajs.cn/list=$code" -H 'Referer: https://finance.sina.com.cn' 2>/dev/null | awk -F'"' '{split($2,a,","); print a[4]}')
    echo "$price"
}

# 记录日志
log_message() {
    echo "[$TIMESTAMP] $1" | tee -a "$LOG_FILE"
}

# 主函数
main() {
    log_message "=== 定时提醒触发 ==="
    log_message "时间: $TIMESTAMP"
    
    # 获取当前小时和分钟（强制10进制）
    HOUR=$(date '+%-H')
    MINUTE=$(date '+%-M')
    TIME=$((HOUR * 60 + MINUTE))
    
    # 判断是开盘前还是收盘前
    if [ $TIME -ge 555 ] && [ $TIME -le 560 ]; then  # 9:15-9:20
        PERIOD="开盘前分析"
        log_message "触发类型: $PERIOD"
    elif [ $TIME -ge 885 ] && [ $TIME -le 890 ]; then  # 14:45-14:50
        PERIOD="收盘前分析"
        log_message "触发类型: $PERIOD"
    else
        PERIOD="定时检查"
        log_message "触发类型: $PERIOD"
    fi
    
    # 获取持仓股票价格
    log_message "--- 持仓股票实时价格 ---"
    
    # 迈瑞医疗
    PRICE_MR=$(get_stock_price "sz300760")
    log_message "迈瑞医疗(300760): ¥$PRICE_MR"
    
    # 全志科技
    PRICE_QZ=$(get_stock_price "sz300458")
    log_message "全志科技(300458): ¥$PRICE_QZ"
    
    # 比亚迪
    PRICE_BYD=$(get_stock_price "sz002594")
    log_message "比亚迪(002594): ¥$PRICE_BYD"
    
    # 潮宏基
    PRICE_CH=$(get_stock_price "sz002345")
    log_message "潮宏基(002345): ¥$PRICE_CH"
    
    # 招商银行
    PRICE_CMB=$(get_stock_price "sh600036")
    log_message "招商银行(600036): ¥$PRICE_CMB"
    
    log_message "--- 价格获取完成 ---"
    
    # 检查关键价位提醒
    ALERT_MSG=""
    
    # 全志科技加仓提醒
    if (( $(echo "$PRICE_QZ <= 38" | bc -l) )); then
        ALERT_MSG+="🔴 全志科技(¥$PRICE_QZ)已进入加仓区间（¥35-38）\n"
    fi
    
    # 迈瑞医疗加仓提醒
    if (( $(echo "$PRICE_MR <= 175" | bc -l) )); then
        ALERT_MSG+="🟡 迈瑞医疗(¥$PRICE_MR)已进入加仓区间（¥160-175）\n"
    fi
    
    # 潮宏基止损提醒
    if (( $(echo "$PRICE_CH <= 10.5" | bc -l) )); then
        ALERT_MSG+="⚠️ 潮宏基(¥$PRICE_CH)接近止损线（¥10），考虑止损\n"
    fi
    
    # 比亚迪减仓提醒
    if (( $(echo "$PRICE_BYD >= 105" | bc -l) )); then
        ALERT_MSG+="✅ 比亚迪(¥$PRICE_BYD)接近减仓位（¥105+），可减仓200股\n"
    fi
    
    # 如果有提醒，直接使用 message 工具发送
    if [ ! -z "$ALERT_MSG" ]; then
        log_message "=== 关键提醒 ==="
        log_message "$ALERT_MSG"
        
        # 记录提醒到文件（供日志查看）
        echo "$TIMESTAMP|$PERIOD|$ALERT_MSG" >> "$LOG_FILE"
        
        log_message "提醒已记录到日志: $LOG_FILE"
        log_message "ValueAnalyzer将在下次响应时检查并发送Telegram消息"
    else
        log_message "无关键价位触发"
    fi
    
    log_message ""
}

main "$@"
