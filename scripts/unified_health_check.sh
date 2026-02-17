#!/bin/bash
#
# 🏥 统一系统健康检查 v4.1
# 合并: 自愈系统 + 监控报告 + 告警分级
# 频率: 每小时
# 策略: P0立即通知, P1汇总通知, P2静默记录
#

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="/var/log/bowlwanpi-health.log"
REPORT_FILE="/tmp/bowlwanpi-health-report.txt"
ALERT_STATE="/tmp/bowlwanpi-alert-state.json"

# 告警计数器（用于P1汇总）
P1_COUNT=0
P1_DETAILS=""

log() {
    echo "[$(date '+%H:%M')] $1" >> "$LOG_FILE"
}

# ========== 告警分级记录 ==========
record_alert() {
    local level="$1"  # P0, P1, P2
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 记录到状态文件
    if [ ! -f "$ALERT_STATE" ]; then
        echo "{\"alerts\": [], \"last_report\": \"\"}" > "$ALERT_STATE"
    fi
    
    # 使用 Python 更新 JSON
    python3 -c "
import json
import sys
try:
    with open('$ALERT_STATE', 'r') as f:
        data = json.load(f)
except:
    data = {'alerts': [], 'last_report': ''}

data['alerts'].append({
    'level': '$level',
    'message': '$message',
    'timestamp': '$timestamp'
})

# 只保留最近100条
data['alerts'] = data['alerts'][-100:]

with open('$ALERT_STATE', 'w') as f:
    json.dump(data, f)
" 2>/dev/null || true
    
    log "[$level] $message"
}

# ========== 代理健康检查 ==========
check_proxy_health() {
    local p0_issues=()
    local p1_issues=()
    local fixed=()
    local PROXY_PORT=7890
    
    # 1. 检查 Mihomo 进程 (P0 - 完全失效)
    if ! pgrep -f "mihomo" > /dev/null 2>&1; then
        if [ -f /root/mihomo/start.sh ]; then
            cd /root/mihomo && bash start.sh &
            fixed+=("Mihomo进程已重启")
            log "FIX: Mihomo restarted"
            record_alert "P2" "Mihomo自动重启"
        else
            p0_issues+=("🚨 P0: Mihomo未运行且无启动脚本")
            record_alert "P0" "Mihomo完全失效"
        fi
    fi
    
    # 2. 检查代理端口连通性 (P1 - 性能下降)
    if command -v curl >/dev/null 2>&1; then
        local http_code
        http_code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 --proxy "http://127.0.0.1:$PROXY_PORT" "https://www.google.com" 2>/dev/null || echo "000")
        if [ "$http_code" != "200" ]; then
            p1_issues+=("⚠️ P1: 代理端口异常(HTTP $http_code)")
            record_alert "P1" "代理端口异常: $http_code"
        fi
    fi
    
    # 3. 磁盘空间 (P0 > 95%, P1 > 90%)
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 95 ]; then
        p0_issues+=("🚨 P0: 磁盘严重不足 ${DISK_USAGE}%")
        record_alert "P0" "磁盘严重不足: ${DISK_USAGE}%"
    elif [ "$DISK_USAGE" -gt 90 ]; then
        # 尝试自动清理
        find /var/log -name "bowlwanpi-*.log*" -mtime +7 -delete 2>/dev/null
        find "$WORKSPACE/health-checks" -name "*.json" -mtime +3 -delete 2>/dev/null
        fixed+=("磁盘清理完成(${DISK_USAGE}%)")
        record_alert "P2" "磁盘自动清理: ${DISK_USAGE}%"
    fi
    
    # 4. Gateway 检查 (P0 - 完全不可用)
    if ! curl -sf --max-time 3 http://127.0.0.1:18789/health > /dev/null 2>&1; then
        p0_issues+=("🚨 P0: Gateway 完全不可用")
        record_alert "P0" "Gateway完全失效"
    fi
    
    # 输出结果
    local result=""
    
    if [ ${#fixed[@]} -gt 0 ]; then
        result+="🔧 自动修复: ${fixed[*]}\n"
    fi
    
    if [ ${#p0_issues[@]} -gt 0 ]; then
        result+="$(printf '%s\n' "${p0_issues[@]}")\n"
    fi
    
    if [ ${#p1_issues[@]} -gt 0 ]; then
        result+="$(printf '%s\n' "${p1_issues[@]}")\n"
        P1_COUNT=${#p1_issues[@]}
        P1_DETAILS="${p1_issues[*]}"
    fi
    
    echo -e "$result"
    
    # 返回是否有 P0 问题
    if [ ${#p0_issues[@]} -gt 0 ]; then
        return 2  # P0 级别
    elif [ ${#p1_issues[@]} -gt 0 ]; then
        return 1  # P1 级别
    fi
    
    return 0  # 正常
}

# ========== 状态摘要 ==========
status_summary() {
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    MEM=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    DISK=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    # P0 告警
    local p0_alerts=()
    [ "${CPU%.*}" -gt 95 ] && p0_alerts+=("🚨 CPU严重:${CPU}%")
    [ "$MEM" -gt 95 ] && p0_alerts+=("🚨 内存严重不足:${MEM}%")
    
    # P1 告警
    local p1_alerts=()
    [ "${CPU%.*}" -gt 80 ] && p1_alerts+=("⚠️ CPU高:${CPU}%")
    [ "$MEM" -gt 90 ] && p1_alerts+=("⚠️ 内存高:${MEM}%")
    [ "$DISK" -gt 85 ] && p1_alerts+=("⚠️ 磁盘:${DISK}%")
    
    # 记录告警
    for alert in "${p0_alerts[@]}"; do
        record_alert "P0" "$alert"
    done
    for alert in "${p1_alerts[@]}"; do
        record_alert "P1" "$alert"
        ((P1_COUNT++))
    done
    
    # 输出
    if [ ${#p0_alerts[@]} -gt 0 ]; then
        echo "${p0_alerts[*]}"
        return 2
    elif [ ${#p1_alerts[@]} -gt 0 ]; then
        echo "${p1_alerts[*]}"
        return 1
    else
        echo "📊 正常 CPU:${CPU%.*}% 内存:${MEM}% 磁盘:${DISK}%"
        return 0
    fi
}

# ========== P1 汇总检查 ==========
should_report_p1() {
    # 每小时检查一次P1汇总
    local last_report_file="/tmp/bowlwanpi-p1-last-report"
    local current_hour=$(date +%H)
    
    if [ -f "$last_report_file" ]; then
        local last_hour=$(cat "$last_report_file")
        if [ "$last_hour" = "$current_hour" ]; then
            return 1  # 本小时已报告
        fi
    fi
    
    echo "$current_hour" > "$last_report_file"
    return 0
}

# ========== 主逻辑 ==========
main() {
    log "=== 健康检查 v4.1 开始 ==="
    
    # 执行自愈（含代理检查）
    healing_result=$(check_proxy_health)
    proxy_level=$?
    
    # 获取状态
    status=$(status_summary)
    status_level=$?
    
    # 确定最高告警级别
    alert_level=0
    [ "$proxy_level" -eq 2 ] || [ "$status_level" -eq 2 ] && alert_level=2
    [ "$alert_level" -lt 2 ] && ([ "$proxy_level" -eq 1 ] || [ "$status_level" -eq 1 ]) && alert_level=1
    
    # 生成报告
    report="💓 系统健康 $(date +%H:%M)

$status

$healing_result"

    echo "$report" > "$REPORT_FILE"
    
    # 决策: 是否发送通知
    case $alert_level in
        2)  # P0 - 立即通知
            echo "$report"
            log "ALERT: P0 紧急告警，立即通知"
            ;;
        1)  # P1 - 每小时汇总通知
            if should_report_p1; then
                echo "⚠️ 系统警告汇总 (过去1小时)"
                echo "$report"
                log "ALERT: P1 警告汇总报告"
            else
                log "INFO: P1 告警已记录，本小时已汇总"
            fi
            ;;
        0)  # 正常
            log "OK: 系统健康，静默记录"
            ;;
    esac
    
    # 记录代理状态
    local mihomo_status="✅"
    pgrep -f "mihomo" > /dev/null 2>&1 || mihomo_status="❌"
    log "Proxy: Mihomo$mihomo_status"
    
    log "=== 健康检查完成 ==="
}

main
