#!/bin/bash
# BowlWanpi 心跳简报发送脚本
# 每5分钟运行一次，读取最新状态并生成精简简报（含代理状态）

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

LOG_FILE="/var/log/bowlwanpi-heartbeat.log"
LAST_REPORT_FILE="/tmp/bowlwanpi-last-report-time"
OUTPUT_FILE="/tmp/bowlwanpi-heartbeat-report.txt"

extract_pct() {
    echo "$1" | grep -o '[0-9]\+' | head -1
}

check_agent() {
    if pgrep -f "openclaw.*gateway\|clawd" > /dev/null 2>&1; then
        echo "OK"
    elif netstat -tlnp 2>/dev/null | grep -q ":18789"; then
        echo "OK"
    else
        echo "FAIL"
    fi
}

# 检查是否应该发送简报（至少间隔4分钟，避免重复）
current_time=$(date +%s)
last_report=0
if [ -f "$LAST_REPORT_FILE" ]; then
    last_report=$(cat "$LAST_REPORT_FILE")
fi

if [ $((current_time - last_report)) -lt 240 ]; then
    exit 0
fi

# 读取最新日志状态
latest_status=$(tail -30 "$LOG_FILE" 2>/dev/null | grep -E "(Gateway:|Mihomo:|CPU:|Memory:|Disk:|Load:)" | tail -10)

if [ -z "$latest_status" ]; then
    exit 0
fi

# 解析状态
agent_status=$(check_agent)
gateway_status=$(echo "$latest_status" | grep "Gateway:" | tail -1 | sed 's/.*Gateway: //' | xargs)
mihomo_status=$(echo "$latest_status" | grep "Mihomo:" | tail -1 | sed 's/.*Mihomo: //' | xargs)
cpu_status=$(echo "$latest_status" | grep "CPU:" | tail -1 | sed 's/.*CPU: //' | xargs)
mem_status=$(echo "$latest_status" | grep "Memory:" | tail -1 | sed 's/.*Memory: //' | xargs)
disk_status=$(echo "$latest_status" | grep "Disk:" | tail -1 | sed 's/.*Disk: //' | xargs)

cpu_pct=$(extract_pct "$cpu_status")
mem_pct=$(extract_pct "$mem_status")
disk_pct=$(extract_pct "$disk_status")

issues=()

if [ "$agent_status" != "OK" ]; then
    issues+=("Agent未运行")
fi

if [[ "$gateway_status" != OK* ]]; then
    issues+=("Gateway异常: ${gateway_status:-Unknown}")
fi

if [[ "$mihomo_status" != OK* ]]; then
    issues+=("Mihomo异常: ${mihomo_status:-Unknown}")
fi

if [[ "$cpu_pct" =~ ^[0-9]+$ ]] && [ "$cpu_pct" -ge 85 ]; then
    issues+=("CPU偏高: ${cpu_pct}%")
fi

if [[ "$mem_pct" =~ ^[0-9]+$ ]] && [ "$mem_pct" -ge 85 ]; then
    issues+=("内存偏高: ${mem_pct}%")
fi

if [[ "$disk_pct" =~ ^[0-9]+$ ]] && [ "$disk_pct" -ge 85 ]; then
    issues+=("磁盘偏高: ${disk_pct}%")
fi

current_time_str=$(date "+%H:%M")
current_hour=$(date +%H)

# 深夜时段(23:00-08:00)只报告异常
if [ ${#issues[@]} -eq 0 ] && { [ "$current_hour" -ge 23 ] || [ "$current_hour" -lt 8 ]; }; then
    exit 0
fi

if [ ${#issues[@]} -eq 0 ]; then
    message="💓 自愈检查(${current_time_str}) 正常：Agent OK｜CPU ${cpu_pct:-N/A}%｜内存 ${mem_pct:-N/A}%｜磁盘 ${disk_pct:-N/A}%"
else
    issue_text=$(IFS='；'; echo "${issues[*]}")
    message="⚠️ 自愈检查(${current_time_str})：${issue_text}"
fi

# 写入消息队列文件，由主会话或其他脚本读取发送
echo "$message" > "$OUTPUT_FILE"
echo "$current_time" > "$LAST_REPORT_FILE"

# 写入简报日志（精简）
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${message}" >> "/var/log/bowlwanpi-reports.log"
