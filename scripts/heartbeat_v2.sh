#!/bin/bash
#
# 💓 碗皮心跳监控系统 v2.0
# 集成详细健康检查
#

HEARTBEAT_LOG="/var/log/bowlwanpi-heartbeat.log"
ALERT_LOG="/var/log/bowlwanpi-alerts.log"
WORKSPACE="/root/.openclaw/workspace"
SCRIPTS_DIR="$WORKSPACE/scripts"

# 创建日志目录
mkdir -p /var/log
mkdir -p "$WORKSPACE/health-checks"

# 获取当前时间
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATE=$(date '+%Y-%m-%d')

# ========== 日志函数 ==========
log() {
    echo "[$TIMESTAMP] $1" | tee -a "$HEARTBEAT_LOG"
}

alert() {
    local level="$1"
    local message="$2"
    echo "[$TIMESTAMP] [$level] $message" | tee -a "$ALERT_LOG"
    
    # 发送飞书通知（如果配置）
    if [ -n "$FEISHU_WEBHOOK" ]; then
        curl -s -X POST "$FEISHU_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"🚨 [$level] $message\"}}" \
            > /dev/null 2>&1 || true
    fi
}

# ========== 系统状态检查 ==========
check_system() {
    log ""
    log "=== Heartbeat check started ==="
    
    local alerts=()
    
    # 1. 检查 Gateway
    log "Checking Gateway..."
    if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
        log "Gateway: OK (process running)"
    else
        log "Gateway: FAIL (process not found)"
        alerts+=("🔴 Gateway 未运行")
        alert "CRITICAL" "Gateway 进程未运行"
    fi
    
    # 2. 检查 Mihomo
    log "Checking Mihomo..."
    if pgrep -f "mihomo" > /dev/null 2>&1; then
        log "Mihomo: OK (running)"
    else
        log "Mihomo: FAIL"
        alerts+=("🟡 Mihomo 未运行")
        alert "WARNING" "Mihomo 代理未运行"
    fi
    
    # 3. 检查系统资源
    log "Checking system resources..."
    
    # CPU
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    if [ -n "$CPU_USAGE" ] && [ "${CPU_USAGE%.*}" -gt 80 ]; then
        log "CPU: HIGH (${CPU_USAGE}%)"
        alerts+=("🟡 CPU 使用率过高: ${CPU_USAGE}%")
        alert "WARNING" "CPU 使用率过高: ${CPU_USAGE}%"
    else
        log "CPU: OK (${CPU_USAGE:-N/A}%)"
    fi
    
    # 内存
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$MEM_USAGE" -gt 90 ]; then
        log "Memory: HIGH (${MEM_USAGE}%)"
        alerts+=("🔴 内存使用率过高: ${MEM_USAGE}%")
        alert "CRITICAL" "内存使用率过高: ${MEM_USAGE}%"
    else
        log "Memory: OK (${MEM_USAGE}%)"
    fi
    
    # 磁盘
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        log "Disk: HIGH (${DISK_USAGE}%)"
        alerts+=("🔴 磁盘使用率过高: ${DISK_USAGE}%")
        alert "CRITICAL" "磁盘使用率过高: ${DISK_USAGE}%"
    else
        log "Disk: OK (${DISK_USAGE}%)"
    fi
    
    echo "${alerts[@]}"
}

# ========== 详细的定时任务健康检查 ==========
check_cron_health() {
    log ""
    log "Checking cron health (detailed)..."
    
    # 运行详细的定时任务健康检查
    if [ -f "$SCRIPTS_DIR/cron_health_checker.py" ]; then
        log "Running detailed cron health check..."
        
        # 执行检查并捕获输出
        PYTHON_OUTPUT=$(python3 "$SCRIPTS_DIR/cron_health_checker.py" 2>&1)
        EXIT_CODE=$?
        
        # 提取关键信息
        ERROR_COUNT=$(echo "$PYTHON_OUTPUT" | grep -oP '错误次数: \K\d+' || echo "0")
        ERROR_RATE=$(echo "$PYTHON_OUTPUT" | grep -oP '错误率: \K[\d.]+' || echo "0")
        
        # 检查是否真的发现了关键错误（不只是建议）
        CRITICAL_ERRORS=$(echo "$PYTHON_OUTPUT" | grep -c '"severity": "critical"' || echo "0")
        
        log "Cron errors (24h): $ERROR_COUNT"
        log "Cron error rate: ${ERROR_RATE}%"
        log "Critical issues: $CRITICAL_ERRORS"
        
        # 只有真正发现关键错误时才发送警报
        if [ "$CRITICAL_ERRORS" -gt 0 ]; then
            log "ALERT: Critical cron issues detected"
            alert "CRITICAL" "定时任务发现关键问题: ${CRITICAL_ERRORS} 个严重错误"
        elif [ "${ERROR_RATE%.*}" -gt 50 ]; then
            log "ALERT: High cron error rate detected (${ERROR_RATE}%)"
            alert "WARNING" "定时任务错误率偏高: ${ERROR_RATE}%"
        else
            log "Cron health check passed (no critical issues)"
        fi
    else
        log "Detailed cron checker not found, using basic check..."
        
        # 基本检查：查看今天的 cron 错误
        if [ -f "/var/log/bowlwanpi-cron.log" ]; then
            TODAY=$(date '+%Y-%m-%d')
            ERROR_COUNT=$(grep -c "$TODAY.*ERROR" /var/log/bowlwanpi-cron.log 2>/dev/null || echo "0")
            
            log "Basic cron errors (today): $ERROR_COUNT"
            
            if [ "$ERROR_COUNT" -gt 5 ]; then
                alert "WARNING" "今日定时任务错误: $ERROR_COUNT 次"
            fi
        fi
    fi
}

# ========== 服务健康检查 ==========
check_services() {
    log ""
    log "Checking services..."
    
    # 检查关键服务
    SERVICES=(
        "openclaw:OpenClaw Gateway"
        "mihomo:Mihomo Proxy"
        "cron:Cron Service"
    )
    
    for service_info in "${SERVICES[@]}"; do
        IFS=':' read -r process name <<< "$service_info"
        
        if pgrep -f "$process" > /dev/null 2>&1; then
            log "$name: OK"
        else
            log "$name: FAIL"
            alert "WARNING" "$name 未运行"
        fi
    done
}

# ========== 生成健康报告 ==========
generate_health_report() {
    log ""
    log "Generating health report..."
    
    REPORT_FILE="$WORKSPACE/health-checks/heartbeat_${DATE}.md"
    
    cat > "$REPORT_FILE" << EOF
# 💓 心跳监控报告 - $DATE

**检查时间:** $TIMESTAMP

## 📊 系统状态

| 组件 | 状态 |
|------|------|
| Gateway | $(pgrep -f "openclaw.*gateway" > /dev/null && echo "✅ 运行中" || echo "❌ 未运行") |
| Mihomo | $(pgrep -f "mihomo" > /dev/null && echo "✅ 运行中" || echo "❌ 未运行") |
| CPU | ${CPU_USAGE:-N/A}% |
| 内存 | ${MEM_USAGE}% |
| 磁盘 | ${DISK_USAGE}% |

## ⏰ 定时任务健康

$(if [ -f "$WORKSPACE/health-checks/cron_health_${DATE}_*.md" ]; then
    echo "📄 详细报告: $(ls -t $WORKSPACE/health-checks/cron_health_${DATE}_*.md | head -1)"
else
    echo "ℹ️ 详细定时任务检查未运行"
fi)

## 🚨 警报历史

$(tail -20 "$ALERT_LOG" 2>/dev/null | grep "$DATE" || echo "今日无警报")

---

*自动生成的健康检查报告*
EOF

    log "Health report saved: $REPORT_FILE"
}

# ========== 主函数 ==========
main() {
    log ""
    log "================================"
    log "💓 Heartbeat Monitor v2.0"
    log "================================"
    
    # 执行所有检查
    check_system
    check_cron_health
    check_services
    generate_health_report
    
    log ""
    log "=== Heartbeat check completed ==="
    log ""
}

# 运行
main
