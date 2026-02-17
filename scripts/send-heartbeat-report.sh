#!/bin/bash
# BowlWanpi 心跳简报发送脚本（降噪版）
# 每5分钟运行一次，但只在异常/状态变化/长间隔摘要时输出

set -u

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

LOG_FILE="/var/log/bowlwanpi-heartbeat.log"
LAST_REPORT_FILE="/tmp/bowlwanpi-last-report-time"
LAST_SIGNATURE_FILE="/tmp/bowlwanpi-last-report-signature"
LAST_LEVEL_FILE="/tmp/bowlwanpi-last-report-level"
OUTPUT_FILE="/tmp/bowlwanpi-heartbeat-report.txt"

# 降噪阈值
NORMAL_INTERVAL_SEC=$((3 * 3600))
WARN_COOLDOWN_SEC=$((30 * 60))
CRITICAL_COOLDOWN_SEC=$((5 * 60))

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

read_int_file() {
    local f="$1"
    if [ -f "$f" ]; then
        local v
        v=$(cat "$f" 2>/dev/null)
        if [[ "$v" =~ ^[0-9]+$ ]]; then
            echo "$v"
            return
        fi
    fi
    echo "0"
}

# 读取最新日志状态
latest_status=$(tail -30 "$LOG_FILE" 2>/dev/null | grep -E "(Gateway:|Mihomo:|CPU:|Memory:|Disk:)" | tail -10)
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
level="normal"

if [ "$agent_status" != "OK" ]; then
    issues+=("Agent未运行")
    level="critical"
fi

if [[ "$gateway_status" != OK* ]]; then
    issues+=("Gateway异常: ${gateway_status:-Unknown}")
    level="critical"
fi

if [[ "$mihomo_status" != OK* ]]; then
    issues+=("Mihomo异常: ${mihomo_status:-Unknown}")
    [ "$level" = "normal" ] && level="warning"
fi

if [[ "$cpu_pct" =~ ^[0-9]+$ ]] && [ "$cpu_pct" -ge 90 ]; then
    issues+=("CPU偏高: ${cpu_pct}%")
    [ "$level" = "normal" ] && level="warning"
fi

if [[ "$mem_pct" =~ ^[0-9]+$ ]] && [ "$mem_pct" -ge 90 ]; then
    issues+=("内存偏高: ${mem_pct}%")
    [ "$level" = "normal" ] && level="warning"
fi

if [[ "$disk_pct" =~ ^[0-9]+$ ]] && [ "$disk_pct" -ge 90 ]; then
    issues+=("磁盘偏高: ${disk_pct}%")
    [ "$level" = "normal" ] && level="warning"
fi

current_ts=$(date +%s)
current_time_str=$(date "+%H:%M")
current_hour=$(date +%H)
last_report=$(read_int_file "$LAST_REPORT_FILE")
last_signature=$(cat "$LAST_SIGNATURE_FILE" 2>/dev/null || echo "")
last_level=$(cat "$LAST_LEVEL_FILE" 2>/dev/null || echo "normal")
elapsed=$((current_ts - last_report))

# 统一签名，避免同类噪声反复提示
signature="${level}|${agent_status}|${gateway_status}|${mihomo_status}|${cpu_pct:-na}|${mem_pct:-na}|${disk_pct:-na}|$(IFS=';'; echo "${issues[*]}")"

# 深夜时段（23:00-08:00）仅保留 warning/critical
if [ "$level" = "normal" ] && { [ "$current_hour" -ge 23 ] || [ "$current_hour" -lt 8 ]; }; then
    exit 0
fi

should_send=0

case "$level" in
    critical)
        if [ "$signature" != "$last_signature" ] || [ "$elapsed" -ge "$CRITICAL_COOLDOWN_SEC" ]; then
            should_send=1
        fi
        ;;
    warning)
        if [ "$signature" != "$last_signature" ] || [ "$elapsed" -ge "$WARN_COOLDOWN_SEC" ]; then
            should_send=1
        fi
        ;;
    normal)
        # 异常恢复时立即报一次；否则仅做长间隔摘要
        if [ "$last_level" != "normal" ] || [ "$elapsed" -ge "$NORMAL_INTERVAL_SEC" ]; then
            should_send=1
        fi
        ;;
esac

if [ "$should_send" -eq 0 ]; then
    exit 0
fi

if [ "$level" = "normal" ]; then
    if [ "$last_level" != "normal" ]; then
        message="✅ 自愈恢复(${current_time_str})：系统已恢复正常｜Agent OK｜CPU ${cpu_pct:-N/A}%｜内存 ${mem_pct:-N/A}%｜磁盘 ${disk_pct:-N/A}%"
    else
        message="💓 自愈摘要(${current_time_str})：系统正常｜Agent OK｜CPU ${cpu_pct:-N/A}%｜内存 ${mem_pct:-N/A}%｜磁盘 ${disk_pct:-N/A}%"
    fi
elif [ "$level" = "warning" ]; then
    issue_text=$(IFS='；'; echo "${issues[*]}")
    message="⚠️ 自愈告警(${current_time_str})：${issue_text}"
else
    issue_text=$(IFS='；'; echo "${issues[*]}")
    message="🚨 自愈紧急(${current_time_str})：${issue_text}"
fi

# 写入队列文件（由外部流程读取并决定是否发送）
echo "$message" > "$OUTPUT_FILE"

echo "$current_ts" > "$LAST_REPORT_FILE"
echo "$signature" > "$LAST_SIGNATURE_FILE"
echo "$level" > "$LAST_LEVEL_FILE"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ${message}" >> "/var/log/bowlwanpi-reports.log"
