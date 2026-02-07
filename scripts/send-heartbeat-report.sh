#!/bin/bash
# BowlWanpi 心跳简报发送脚本
# 每5分钟运行一次，读取最新状态并发送简报

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

LOG_FILE="/var/log/bowlwanpi-heartbeat.log"
LAST_REPORT_FILE="/tmp/bowlwanpi-last-report-time"

# 检查是否应该发送简报（每5分钟一次）
current_time=$(date +%s)
last_report=0
if [ -f "$LAST_REPORT_FILE" ]; then
    last_report=$(cat "$LAST_REPORT_FILE")
fi

# 至少间隔 4 分钟才发（避免重复）
if [ $((current_time - last_report)) -lt 240 ]; then
    exit 0
fi

# 读取最新日志状态
latest_status=$(tail -20 "$LOG_FILE" 2>/dev/null | grep -E "(Gateway|Mihomo|CPU:|Memory:|Disk:|Load:)" | tail -6)

if [ -z "$latest_status" ]; then
    exit 0
fi

# 解析状态
gateway_status=$(echo "$latest_status" | grep "Gateway:" | tail -1 | sed 's/.*Gateway: //' | cut -d'(' -f1 | xargs)
mihomo_status=$(echo "$latest_status" | grep "Mihomo:" | tail -1 | sed 's/.*Mihomo: //' | xargs)
cpu_status=$(echo "$latest_status" | grep "CPU:" | tail -1 | sed 's/.*CPU: //' | cut -d'(' -f1 | xargs)
mem_status=$(echo "$latest_status" | grep "Memory:" | tail -1 | sed 's/.*Memory: //' | xargs)
disk_status=$(echo "$latest_status" | grep "Disk:" | tail -1 | sed 's/.*Disk: //' | xargs)
load_status=$(echo "$latest_status" | grep "Load:" | tail -1 | sed 's/.*Load: //' | xargs)

# 生成简报时间
current_time_str=$(date "+%H:%M")

# 生成消息内容（单行格式，便于发送）
message="💓 心跳简报 (${current_time_str})

🖥️ 系统状态：
• Gateway: ${gateway_status:-Unknown}
• Mihomo: ${mihomo_status:-Unknown}
• CPU: ${cpu_status:-Unknown}
• 内存: ${mem_status:-Unknown}
• 磁盘: ${disk_status:-Unknown}
• 负载: ${load_status:-Unknown}

⏱️ 下次检查: 5分钟后
💡 深夜时段(23:00-08:00)只报告异常"

# 写入消息队列文件，由主会话或另一个脚本读取发送
echo "$message" > "/tmp/bowlwanpi-heartbeat-report.txt"
echo "$current_time" > "$LAST_REPORT_FILE"

# 同时写入带时间戳的历史记录
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Report generated" >> "/var/log/bowlwanpi-reports.log"

# 尝试直接发送（如果方法可用）
# 方法1: 使用 openclaw sessions_send（如果有）
if command -v openclaw &> /dev/null; then
    # 尝试找到主会话并发送
    openclaw sessions list --json 2>/dev/null | grep -q "main" && \
    echo "$message" >> "/tmp/bowlwanpi-urgent-messages" 2>/dev/null
fi
