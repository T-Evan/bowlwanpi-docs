#!/bin/bash
#
# 🤖 OpenClaw Auto Restart Guardian v2.2
# 基于 umico8832/openclaw_auto_restart 优化
# 功能: 监控 + 自动重启 + 预警 + 自愈 + 网络代理 + QMDR
#

set -e

# 配置
WORKSPACE="${HOME}/.openclaw/workspace"
LOG_DIR="/var/log"
PID_FILE="/tmp/openclaw_guardian.pid"
GUARDIAN_LOG="$LOG_DIR/openclaw-guardian.log"
ALERT_COOLDOWN=300

# 状态文件
STATUS_FILE="$WORKSPACE/.guardian_status.json"
RESTART_COUNT_FILE="$WORKSPACE/.restart_count"
PROXY_RESTART_COUNT="$WORKSPACE/.proxy_restart_count"
QMDR_RESTART_COUNT="$WORKSPACE/.qmdr_restart_count"

# 初始化
mkdir -p "$LOG_DIR"
touch "$GUARDIAN_LOG"

# ========== 日志函数 ==========
log() {
    local level="${2:-INFO}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $1" | tee -a "$GUARDIAN_LOG"
}

# ========== 状态管理 ==========
save_status() {
    local status="$1"
    local message="${2:-}"
    
    cat > "$STATUS_FILE" << EOF
{
    "timestamp": "$(date -Iseconds)",
    "status": "$status",
    "message": "$message",
    "gateway_restarts": $(cat "$RESTART_COUNT_FILE" 2>/dev/null || echo "0"),
    "proxy_restarts": $(cat "$PROXY_RESTART_COUNT" 2>/dev/null || echo "0"),
    "pid": $$
}
EOF
}

load_count() {
    cat "$1" 2>/dev/null || echo "0"
}

increment_count() {
    local file="$1"
    local count=$(($(load_count "$file") + 1))
    echo "$count" > "$file"
    
    if [ "$count" -gt 10 ]; then
        log "⚠️ 重启次数过多: $count 次" "WARN"
    fi
}

reset_daily_counts() {
    local today=$(date +%Y-%m-%d)
    local last_reset=$(stat -c %y "$RESTART_COUNT_FILE" 2>/dev/null | cut -d' ' -f1)
    
    if [ "$last_reset" != "$today" ]; then
        echo "0" > "$RESTART_COUNT_FILE"
        echo "0" > "$PROXY_RESTART_COUNT"
        log "新的一天，重置重启计数"
    fi
}

# ========== Gateway 检查 ==========
check_gateway_health() {
    local retry=0
    local max_retry=3
    
    while [ $retry -lt $max_retry ]; do
        if ! pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
            return 1
        fi
        
        if curl -s --max-time 3 http://localhost:3000/health > /dev/null 2>&1; then
            return 0
        fi
        
        retry=$((retry + 1))
        sleep 2
    done
    
    return 1
}

restart_gateway() {
    log "🔄 重启 Gateway..."
    
    pkill -f "openclaw.*gateway" 2>/dev/null || true
    sleep 3
    
    if command -v openclaw > /dev/null 2>&1; then
        openclaw gateway start &
        sleep 5
        
        if check_gateway_health; then
            increment_count "$RESTART_COUNT_FILE"
            log "✅ Gateway 重启成功"
            return 0
        fi
    fi
    
    log "❌ Gateway 重启失败"
    return 1
}

# ========== 代理检查 (新增) ==========
check_proxy_health() {
    # 检查进程
    if ! pgrep -f "mihomo" > /dev/null 2>&1; then
        return 1
    fi
    
    # 检查端口
    if ! netstat -tlnp 2>/dev/null | grep -q ":7890"; then
        return 1
    fi
    
    # 测试代理 (使用国内站点避免网络问题)
    if curl -s --max-time 5 --proxy http://127.0.0.1:7890 http://www.baidu.com > /dev/null 2>&1; then
        return 0
    fi
    
    return 1
}

restart_proxy() {
    log "🔄 重启网络代理..."
    
    # 停止
    pkill -f "mihomo" 2>/dev/null || true
    sleep 2
    
    # 启动
    if [ -f /root/mihomo/start.sh ]; then
        cd /root/mihomo
        bash start.sh &
    elif [ -f /root/mihomo/config.yaml ]; then
        cd /root/mihomo
        nohup /usr/local/bin/mihomo -f config.yaml > mihomo.log 2>&1 &
    else
        log "❌ 找不到代理配置" "ERROR"
        return 1
    fi
    
    # 等待启动
    sleep 5
    
    if check_proxy_health; then
        increment_count "$PROXY_RESTART_COUNT"
        log "✅ 代理重启成功"
        return 0
    else
        log "❌ 代理重启失败"
        return 1
    fi
}

# ========== QMDR 检查 (新增) ==========
check_qmdr_health() {
    # 检查 qmd 命令是否可用
    if ! command -v qmd > /dev/null 2>&1; then
        if [ ! -f ~/.bun/bin/qmd ]; then
            return 1
        fi
        export PATH="$HOME/.bun/bin:$PATH"
    fi
    
    # 检查索引是否存在且可查询
    if ! qmd status > /dev/null 2>&1; then
        return 1
    fi
    
    # 测试搜索功能
    if qmd search "test" --collection memory -n 1 > /dev/null 2>&1; then
        return 0
    fi
    
    return 1
}

restart_qmdr() {
    log "🔄 重新索引 QMDR..."
    
    export PATH="$HOME/.bun/bin:$PATH"
    export QMD_ALLOW_SQLITE_EXTENSIONS=1
    
    # 更新索引
    cd ~/.openclaw/workspace
    
    # 重新索引所有集合
    if qmd update --pull > /dev/null 2>&1; then
        log "✅ QMDR 索引更新成功"
        
        # 异步创建向量嵌入
        (qmd embed > /dev/null 2>&1 &)
        
        increment_count "$QMDR_RESTART_COUNT"
        log "✅ QMDR 重建完成"
        return 0
    else
        log "❌ QMDR 重建失败"
        return 1
    fi
}

# ========== 系统资源检查 ==========
check_system_resources() {
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$mem_usage" -gt 95 ]; then
        log "内存使用率过高: ${mem_usage}%" "WARN"
        return 1
    fi
    
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 95 ]; then
        log "磁盘使用率过高: ${disk_usage}%" "WARN"
        return 1
    fi
    
    return 0
}

# ========== 主循环 ==========
guardian_loop() {
    log "🚀 Guardian v2.2 启动 (含代理+QMDR监控)"
    reset_daily_counts
    
    while true; do
        local issues=0
        
        # 1. 检查 Gateway
        if ! check_gateway_health; then
            log "⚠️ Gateway 异常"
            if check_system_resources; then
                restart_gateway || issues=$((issues + 1))
            else
                log "⚠️ 资源不足，延迟重启 Gateway"
                issues=$((issues + 1))
            fi
        fi
        
        # 2. 检查代理 (新增)
        if ! check_proxy_health; then
            log "⚠️ 网络代理异常"
            if check_system_resources; then
                restart_proxy || issues=$((issues + 1))
            else
                log "⚠️ 资源不足，延迟重启代理"
                issues=$((issues + 1))
            fi
        fi
        
        # 3. 检查 QMDR (新增)
        if ! check_qmdr_health; then
            log "⚠️ QMDR 异常"
            if check_system_resources; then
                restart_qmdr || issues=$((issues + 1))
            else
                log "⚠️ 资源不足，延迟重启 QMDR"
                issues=$((issues + 1))
            fi
        fi
        
        # 3. 检查资源
        check_system_resources || issues=$((issues + 1))
        
        # 保存状态
        if [ $issues -eq 0 ]; then
            save_status "running" "系统正常"
        else
            save_status "warning" "发现 $issues 个问题"
        fi
        
        # 休眠
        sleep 30
    done
}

# ========== 命令处理 ==========
case "$1" in
    "start")
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Guardian 已在运行 (PID: $(cat "$PID_FILE"))"
            exit 0
        fi
        
        echo $$ > "$PID_FILE"
        guardian_loop
        ;;
    
    "stop")
        if [ -f "$PID_FILE" ]; then
            kill $(cat "$PID_FILE") 2>/dev/null || true
            rm -f "$PID_FILE"
            echo "Guardian 已停止"
        else
            echo "Guardian 未运行"
        fi
        ;;
    
    "restart")
        $0 stop
        sleep 2
        $0 start
        ;;
    
    "status")
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "✅ Guardian 运行中"
            if [ -f "$STATUS_FILE" ]; then
                cat "$STATUS_FILE"
            fi
        else
            echo "❌ Guardian 未运行"
        fi
        
        echo ""
        echo "📊 今日重启统计:"
        echo "   Gateway: $(load_count "$RESTART_COUNT_FILE") 次"
        echo "   代理: $(load_count "$PROXY_RESTART_COUNT") 次"
        echo "   QMDR: $(load_count "$QMDR_RESTART_COUNT") 次"
        ;;
    
    "check")
        echo "🔍 快速检查..."
        check_gateway_health && echo "✅ Gateway 正常" || echo "❌ Gateway 异常"
        check_proxy_health && echo "✅ 代理正常" || echo "❌ 代理异常"
        check_qmdr_health && echo "✅ QMDR 正常" || echo "❌ QMDR 异常"
        ;;
    
    *)
        echo "🤖 OpenClaw Guardian v2.2 (含代理+QMDR监控)"
        echo ""
        echo "用法: $0 {start|stop|restart|status|check}"
        ;;
esac
