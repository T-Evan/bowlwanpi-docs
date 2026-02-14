#!/bin/bash
#
# 💓 碗皮心跳监控系统 v3.0
# 优化版：告警聚合、频率控制、上下文增强
#

HEARTBEAT_LOG="/var/log/bowlwanpi-heartbeat.log"
ALERT_LOG="/var/log/bowlwanpi-alerts.log"
ALERT_STATE="/var/log/bowlwanpi-alert-state.json"
WORKSPACE="/root/.openclaw/workspace"
SCRIPTS_DIR="$WORKSPACE/scripts"

# 告警频率控制（分钟）
ALERT_COOLDOWN_CRITICAL=5    # Critical 告警冷却时间
ALERT_COOLDOWN_WARNING=30    # Warning 告警冷却时间
ALERT_COOLDOWN_INFO=120      # Info 告警冷却时间

# 创建日志目录
mkdir -p /var/log
mkdir -p "$WORKSPACE/health-checks"

# 获取当前时间
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATE=$(date '+%Y-%m-%d')
EPOCH=$(date +%s)

# ========== 初始化状态文件 ==========
init_state_file() {
    if [ ! -f "$ALERT_STATE" ]; then
        echo '{}' > "$ALERT_STATE"
    fi
}

# ========== 日志函数 ==========
log() {
    local level="${2:-INFO}"
    echo "[$TIMESTAMP] [$level] $1" | tee -a "$HEARTBEAT_LOG"
}

# ========== 检查告警是否应该发送（频率控制）==========
should_send_alert() {
    local alert_key="$1"
    local level="$2"
    local cooldown=0
    
    case "$level" in
        "CRITICAL") cooldown=$ALERT_COOLDOWN_CRITICAL ;;
        "WARNING") cooldown=$ALERT_COOLDOWN_WARNING ;;
        "INFO") cooldown=$ALERT_COOLDOWN_INFO ;;
    esac
    
    # 转换为秒
    cooldown=$((cooldown * 60))
    
    # 读取上次告警时间
    local last_alert=$(jq -r ".[\"$alert_key\"] // 0" "$ALERT_STATE" 2>/dev/null || echo "0")
    local time_diff=$((EPOCH - last_alert))
    
    if [ $time_diff -ge $cooldown ]; then
        # 更新上次告警时间
        jq ".[\"$alert_key\"] = $EPOCH" "$ALERT_STATE" > "$ALERT_STATE.tmp" 2>/dev/null && \
            mv "$ALERT_STATE.tmp" "$ALERT_STATE"
        return 0
    else
        return 1
    fi
}

# ========== 发送告警（带聚合）==========
alert() {
    local level="$1"
    local message="$2"
    local context="${3:-}"
    local alert_key="${4:-$(echo "$message" | md5sum | cut -d' ' -f1)}"
    
    # 记录到日志
    echo "[$TIMESTAMP] [$level] $message" | tee -a "$ALERT_LOG"
    
    # 检查是否应该发送告警（频率控制）
    if ! should_send_alert "$alert_key" "$level"; then
        log "告警已聚合 (冷却中): [$level] $message" "DEBUG"
        return 0
    fi
    
    # 构建告警消息
    local alert_msg=""
    case "$level" in
        "CRITICAL")
            alert_msg="🔴 [CRITICAL] $message"
            ;;
        "WARNING")
            alert_msg="🟡 [WARNING] $message"
            ;;
        "INFO")
            alert_msg="ℹ️  [INFO] $message"
            ;;
    esac
    
    # 添加上下文信息
    if [ -n "$context" ]; then
        alert_msg="$alert_msg\n\n📋 上下文:\n$context"
    fi
    
    # 添加时间戳
    alert_msg="$alert_msg\n\n🕐 $TIMESTAMP"
    
    # 发送飞书通知（如果配置）
    if [ -n "$FEISHU_WEBHOOK" ]; then
        # 构建 JSON（处理换行）
        local json_msg=$(echo "$alert_msg" | sed 's/"/\\"/g' | tr '\n' ' ')
        curl -s -X POST "$FEISHU_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$json_msg\"}}" \
            > /dev/null 2>&1 || true
    fi
    
    log "告警已发送: [$level] $message" "DEBUG"
}

# ========== 系统状态检查 ==========
check_system() {
    log "=== Heartbeat check started ==="
    
    local has_critical=0
    local has_warning=0
    local alerts=()
    
    # 1. 检查 Gateway
    if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
        log "Gateway: OK"
    else
        log "Gateway: FAIL" "ERROR"
        alert "CRITICAL" \
              "Gateway 进程未运行" \
              "影响: OpenClaw 无法接收消息\n建议: 运行 'openclaw gateway start' 启动" \
              "gateway_process"
        has_critical=1
    fi
    
    # 2. 检查 Mihomo
    if pgrep -f "mihomo" > /dev/null 2>&1; then
        log "Mihomo: OK"
    else
        log "Mihomo: FAIL" "WARNING"
        alert "WARNING" \
              "Mihomo 代理未运行" \
              "影响: 外部网络请求可能失败\n建议: 检查代理配置或手动启动" \
              "mihomo_process"
        has_warning=1
    fi
    
    # 3. 检查系统资源
    check_resources
    
    # 4. 发送聚合报告（如果有告警）
    if [ $has_critical -eq 0 ] && [ $has_warning -eq 0 ]; then
        log "所有检查通过"
    fi
    
    return $has_critical
}

# ========== 资源检查 ==========
check_resources() {
    # CPU
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    if [ -n "$CPU_USAGE" ] && [ "${CPU_USAGE%.*}" -gt 80 ]; then
        log "CPU: HIGH (${CPU_USAGE}%)" "WARNING"
        if [ "${CPU_USAGE%.*}" -gt 95 ]; then
            alert "CRITICAL" \
                  "CPU 使用率极高: ${CPU_USAGE}%" \
                  "影响: 系统响应可能变慢\n建议: 检查是否有异常进程" \
                  "cpu_high"
        else
            alert "WARNING" \
                  "CPU 使用率过高: ${CPU_USAGE}%" \
                  "建议: 监控进程资源使用" \
                  "cpu_warning"
        fi
    else
        log "CPU: OK (${CPU_USAGE:-N/A}%)"
    fi
    
    # 内存
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$MEM_USAGE" -gt 90 ]; then
        log "Memory: HIGH (${MEM_USAGE}%)" "ERROR"
        alert "CRITICAL" \
              "内存使用率过高: ${MEM_USAGE}%" \
              "影响: 可能导致 OOM\n建议: 重启服务或增加内存" \
              "memory_high"
    else
        log "Memory: OK (${MEM_USAGE}%)"
    fi
    
    # 磁盘
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        log "Disk: HIGH (${DISK_USAGE}%)" "ERROR"
        alert "CRITICAL" \
              "磁盘使用率过高: ${DISK_USAGE}%" \
              "影响: 可能导致系统无法写入\n建议: 清理日志或扩展磁盘" \
              "disk_high"
    elif [ "$DISK_USAGE" -gt 80 ]; then
        log "Disk: WARNING (${DISK_USAGE}%)" "WARNING"
        alert "WARNING" \
              "磁盘使用率偏高: ${DISK_USAGE}%" \
              "建议: 考虑清理旧文件" \
              "disk_warning"
    else
        log "Disk: OK (${DISK_USAGE}%)"
    fi
}

# ========== 主函数 ==========
main() {
    init_state_file
    check_system
    
    log "=== Heartbeat check completed ==="
}

main "$@"
