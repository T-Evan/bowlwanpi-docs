#!/bin/bash
# BowlWanpi 心跳监控脚本
# 每5分钟运行一次，检查系统状态和定时任务健康度

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

LOG_FILE="/var/log/bowlwanpi-heartbeat.log"
ALERT_FILE="/tmp/bowlwanpi-last-alert"
LOCK_FILE="/tmp/bowlwanpi-heartbeat.lock"

# 防止并发执行
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "[$(date)] Heartbeat already running (PID: $PID), skipping" >> "$LOG_FILE"
        exit 0
    fi
fi
echo $$ > "$LOCK_FILE"

# 清理锁文件
cleanup() {
    rm -f "$LOCK_FILE"
}
trap cleanup EXIT

log() {
    echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 发送警报（带冷却时间，避免轰炸）
send_alert() {
    local message="$1"
    local alert_type="$2"
    local cooldown_minutes="${3:-30}"  # 默认30分钟冷却
    
    local alert_key="${ALERT_FILE}-${alert_type}"
    local last_alert=0
    
    if [ -f "$alert_key" ]; then
        last_alert=$(cat "$alert_key")
    fi
    
    local current_time=$(date +%s)
    local cooldown_seconds=$((cooldown_minutes * 60))
    
    if [ $((current_time - last_alert)) -gt $cooldown_seconds ]; then
        log "ALERT [$alert_type]: $message"
        
        # 写入消息队列文件，由主会话读取后发送
        local msg_file="/tmp/bowlwanpi-pending-messages"
        local alert_content="⚠️ 心跳警报

${message}

🕐 时间: $(date '+%Y-%m-%d %H:%M:%S')
💻 服务器: $(hostname)"
        
        echo "$(date '+%Y-%m-%d %H:%M:%S')|ALERT|$alert_type|$alert_content" >> "$msg_file"
        
        echo "$current_time" > "$alert_key"
        log "Alert queued for delivery"
    else
        log "Alert [$alert_type] suppressed (cooldown: ${cooldown_minutes}min)"
    fi
}

# 检查 OpenClaw Gateway
check_gateway() {
    # 方法1: 检查进程
    if pgrep -f "openclaw.*gateway" > /dev/null 2>&1 || pgrep -f "clawd" > /dev/null 2>&1; then
        log "Gateway: OK (process running)"
        return 0
    fi
    
    # 方法2: 检查端口
    if netstat -tlnp 2>/dev/null | grep -q ":3000"; then
        log "Gateway: OK (port 3000 open)"
        return 0
    fi
    
    # 方法3: 检查 lock 文件
    if [ -f "/tmp/clawd.lock" ] || [ -f "/var/run/openclaw.pid" ]; then
        log "Gateway: OK (lock file exists)"
        return 0
    fi
    
    # 都失败，发送警报
    send_alert "❌ OpenClaw Gateway 未运行！\n\n定时任务可能无法正常执行，请检查服务状态。" "gateway_down" 30
    return 1
}

# 检查内存使用
check_memory() {
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$mem_usage" -gt 90 ]; then
        send_alert "🔴 内存使用率过高: ${mem_usage}%\n\n建议检查是否有内存泄漏。" "high_memory" 60
    elif [ "$mem_usage" -gt 80 ]; then
        log "WARNING: Memory usage high: ${mem_usage}%"
    else
        log "Memory: ${mem_usage}% OK"
    fi
}

# 检查磁盘空间
check_disk() {
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        send_alert "💾 磁盘空间不足: ${disk_usage}%\n\n请尽快清理磁盘空间。" "disk_full" 120
    elif [ "$disk_usage" -gt 80 ]; then
        log "WARNING: Disk usage high: ${disk_usage}%"
    else
        log "Disk: ${disk_usage}% OK"
    fi
}

# 检查定时任务日志
check_cron_logs() {
    local log_file="/var/log/bowlwanpi-cron.log"
    if [ -f "$log_file" ]; then
        # 检查最近1小时是否有错误
        local errors=$(grep -c "ERROR" "$log_file" 2>/dev/null || echo "0")
        errors=$(echo "$errors" | tr -d ' ')
        if [ -n "$errors" ] && [ "$errors" -gt 5 ] 2>/dev/null; then
            send_alert "📋 定时任务最近错误较多: ${errors} 个错误\n\n请检查 /var/log/bowlwanpi-cron.log" "cron_errors" 60
        fi
    fi
}

# 检查系统负载
check_load() {
    local load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    local cores=$(nproc)
    local load_pct=$(echo "$load $cores" | awk '{printf "%.0f", ($1/$2)*100}')
    
    # 确保 load_pct 是纯数字
    load_pct=$(echo "$load_pct" | tr -d ' ')
    
    if [ -n "$load_pct" ] && [ "$load_pct" -gt 150 ] 2>/dev/null; then
        send_alert "⚡ 系统负载过高: ${load} (${load_pct}%)\n\nCPU 核心数: ${cores}\n建议检查是否有异常进程。" "high_load" 30
    else
        log "Load: ${load} (${load_pct}%) OK"
    fi
}

# 检查 CPU 状态（详细）
check_cpu() {
    # 获取 CPU 使用率（使用 top 命令）
    local cpu_idle=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print $1}')
    local cpu_usage=$(echo "100 - $cpu_idle" | bc 2>/dev/null || echo "0")
    cpu_usage=$(printf "%.0f" "$cpu_usage" 2>/dev/null || echo "0")
    
    # 获取 CPU 温度（如果有 sensors）
    local cpu_temp="N/A"
    if command -v sensors &> /dev/null; then
        cpu_temp=$(sensors 2>/dev/null | grep -i "core\|cpu" | head -1 | awk '{print $3}' | sed 's/+//;s/°C//')
    fi
    
    # 获取 CPU 型号
    local cpu_model=$(cat /proc/cpuinfo | grep "model name" | head -1 | cut -d':' -f2 | sed 's/^ *//' | cut -c1-30)
    
    if [ -n "$cpu_usage" ] && [ "$cpu_usage" -gt 90 ] 2>/dev/null; then
        send_alert "🔥 CPU 使用率过高: ${cpu_usage}%\n\n型号: ${cpu_model}\n温度: ${cpu_temp}\n建议检查是否有 CPU 密集型进程。" "high_cpu" 20
    elif [ -n "$cpu_usage" ] && [ "$cpu_usage" -gt 80 ] 2>/dev/null; then
        log "WARNING: CPU usage high: ${cpu_usage}%"
    else
        log "CPU: ${cpu_usage}% OK (型号: ${cpu_model})"
    fi
}

# 检查 Mihomo 运行状态
check_mihomo() {
    # 检查 mihomo 进程
    local mihomo_running=false
    local mihomo_port=""
    
    # 方法1: 检查进程名
    if pgrep -f "mihomo" > /dev/null 2>&1 || pgrep -f "clash" > /dev/null 2>&1; then
        mihomo_running=true
    fi
    
    # 方法2: 检查常见端口 (7890, 7891, 9090)
    for port in 7890 7891 9090 7892; do
        if netstat -tlnp 2>/dev/null | grep -q ":$port "; then
            mihomo_running=true
            mihomo_port="$port"
            break
        fi
    done
    
    # 方法3: 检查 systemd 服务
    if command -v systemctl &> /dev/null; then
        if systemctl is-active --quiet mihomo 2>/dev/null || systemctl is-active --quiet clash 2>/dev/null; then
            mihomo_running=true
        fi
    fi
    
    if [ "$mihomo_running" = true ]; then
        if [ -n "$mihomo_port" ]; then
            log "Mihomo: OK (running on port $mihomo_port)"
        else
            log "Mihomo: OK (running)"
        fi
    else
        send_alert "🌐 Mihomo/Clash 代理未运行！\n\n网络代理服务可能已停止，请检查服务状态。" "mihomo_down" 60
    fi
}

# 每日状态报告（8:00发送）
daily_report() {
    local current_hour=$(date +%H)
    local current_min=$(date +%M)
    local report_file="/tmp/bowlwanpi-daily-report"
    local today=$(date +%Y%m%d)
    
    # 只在8:00-8:05之间发送一次
    if [ "$current_hour" == "08" ] && [ "$current_min" -lt "05" ]; then
        if [ ! -f "$report_file" ] || [ "$(cat "$report_file")" != "$today" ]; then
            local uptime_info=$(uptime -p 2>/dev/null || uptime)
            local mem_info=$(free -h | grep Mem | awk '{print $3"/"$2}')
            local disk_info=$(df -h / | tail -1 | awk '{print $3"/"$2 " ("$5")"}')
            local gateway_status=$(pgrep -f "openclaw\|clawd" > /dev/null 2>&1 && echo "✅ 正常" || echo "❌ 异常")
            
            # 写入消息队列
            local msg_file="/tmp/bowlwanpi-pending-messages"
            local report_content="💓 每日心跳报告

📊 系统状态:
• 运行时间: ${uptime_info}
• 内存使用: ${mem_info}
• 磁盘使用: ${disk_info}

⏰ 定时任务:
• 系统 Cron: ✅ 运行中
• OpenClaw 调度器: ${gateway_status}

💡 一句话: 所有系统正常运行中～"
            
            echo "$(date '+%Y-%m-%d %H:%M:%S')|REPORT|daily|$report_content" >> "$msg_file"
            
            echo "$today" > "$report_file"
            log "Daily report queued"
        fi
    fi
}

# 主逻辑
main() {
    log "=== Heartbeat check started ==="
    
    # 各项检查
    check_gateway
    check_mihomo
    check_cpu
    check_memory
    check_disk
    check_load
    check_cron_logs
    daily_report
    
    log "=== Heartbeat check completed ==="
}

main "$@"
