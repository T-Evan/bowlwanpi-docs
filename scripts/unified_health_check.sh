#!/bin/bash
#
# 🏥 统一系统健康检查 v4.0
# 合并: 自愈系统 + 监控报告
# 频率: 每小时
# 策略: 自愈优先，异常才报，精简输出
#

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="/var/log/bowlwanpi-health.log"
REPORT_FILE="/tmp/bowlwanpi-health-report.txt"

log() {
    echo "[$(date '+%H:%M')] $1" >> "$LOG_FILE"
}

# ========== 代理健康检查 ==========
check_proxy_health() {
    local issues=()
    local fixed=()
    local PROXY_PORT=7890
    
    # 1. 检查 Mihomo 进程
    if ! pgrep -f "mihomo" > /dev/null 2>&1; then
        if [ -f /root/mihomo/start.sh ]; then
            cd /root/mihomo && bash start.sh &
            fixed+=("Mihomo进程已重启")
            log "FIX: Mihomo process restarted"
        else
            issues+=("⚠️ Mihomo未运行且无启动脚本")
        fi
    fi
    
    # 2. 检查代理端口连通性
    if command -v curl >/dev/null 2>&1; then
        local http_code
        http_code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 --proxy "http://127.0.0.1:$PROXY_PORT" "https://www.google.com" 2>/dev/null || echo "000")
        if [ "$http_code" != "200" ]; then
            issues+=("⚠️ 代理端口$PROXY_PORT异常(HTTP $http_code)")
        fi
    fi
    
    # 2. 磁盘空间
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        find /var/log -name "bowlwanpi-*.log*" -mtime +7 -delete 2>/dev/null
        find "$WORKSPACE/health-checks" -name "*.json" -mtime +3 -delete 2>/dev/null
        fixed+=("磁盘清理完成(>${DISK_USAGE}%)")
        log "FIX: Disk cleaned (${DISK_USAGE}%)"
    fi
    
    # 3. Gateway 检查
    if ! curl -sf --max-time 3 http://127.0.0.1:18789/health > /dev/null 2>&1; then
        issues+=("⚠️ Gateway 异常，需检查")
    fi
    
    # 输出结果
    if [ ${#fixed[@]} -gt 0 ]; then
        echo "🔧 自动修复: ${fixed[*]}"
    fi
    
    if [ ${#issues[@]} -gt 0 ]; then
        echo "❌ 需关注: ${issues[*]}"
        return 1
    fi
    
    # 记录代理状态日志
    local mihomo_status="✅"
    pgrep -f "mihomo" > /dev/null 2>&1 || mihomo_status="❌"
    log "Proxy: Mihomo$mihomo_status Port${PROXY_PORT}"
    
    return 0
}

# ========== 状态摘要 ==========
status_summary() {
    # 只收集关键指标
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    MEM=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    DISK=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    # 检查是否有异常值
    local alerts=()
    [ "${CPU%.*}" -gt 80 ] && alerts+=("CPU高:${CPU}%")
    [ "$MEM" -gt 90 ] && alerts+=("内存高:${MEM}%")
    [ "$DISK" -gt 85 ] && alerts+=("磁盘:${DISK}%")
    
    if [ ${#alerts[@]} -gt 0 ]; then
        echo "📊 ${alerts[*]}"
    else
        echo "📊 正常 CPU:${CPU%.*}% 内存:${MEM}% 磁盘:${DISK}%"
    fi
}

# ========== 主逻辑 ==========
main() {
    log "=== 健康检查开始 ==="
    
    # 执行自愈（含代理检查）
    healing_result=$(check_proxy_health)
    
    # 获取状态
    status=$(status_summary)
    
    # 生成报告
    report="💓 系统健康 $(date +%H:%M)

$status

$healing_result"

    echo "$report" > "$REPORT_FILE"
    
    # 决策: 是否发送
    # 只有以下情况才通知:
    # 1. 有需关注的问题
    # 2. 有自动修复发生
    # 3. 资源使用异常
    
    if echo "$report" | grep -qE "(需关注|❌|已重启|清理完成|CPU高|内存高)"; then
        echo "$report"
        log "ALERT: 发送健康报告"
    else
        log "OK: 系统健康，静默记录"
    fi
    
    log "=== 健康检查完成 ==="
}

main
