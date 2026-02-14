#!/bin/bash
#
# 🏥 统一健康与自愈管理系统 v3.0
# 整合: 健康检查 + 自愈系统 + 代理监控
#
# 功能:
# - 全面健康检查 (系统/服务/任务)
# - 智能自愈 (自动修复常见问题)
# - 代理监控 (OpenClaw/Gateway/Mihomo)
# - 统一报告生成

set -e

# 配置
WORKSPACE="${HOME}/.openclaw/workspace"
SCRIPTS_DIR="$WORKSPACE/scripts"
REPORT_DIR="$WORKSPACE/health-checks"
LOG_DIR="/var/log"
STATE_DIR="$WORKSPACE/.health-state"

# 日志文件
HEALTH_LOG="$LOG_DIR/bowlwanpi-health.log"
HEALING_LOG="$LOG_DIR/bowlwanpi-healing.log"

# 创建目录
mkdir -p "$REPORT_DIR" "$STATE_DIR" "$LOG_DIR"

# 获取时间
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATE=$(date '+%Y%m%d')

# ========== 日志函数 ==========
log() {
    local level="${2:-INFO}"
    echo "[$TIMESTAMP] [$level] $1" | tee -a "$HEALTH_LOG"
}

healing_log() {
    local action="$1"
    local result="$2"
    echo "[$TIMESTAMP] [HEALING] $action: $result" | tee -a "$HEALING_LOG"
}

# ========== 健康检查模块 ==========

# 系统资源检查
check_system_resources() {
    log "检查系统资源..."
    
    local issues=()
    
    # CPU
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    CPU_USAGE=${CPU_USAGE:-0}
    if [ "${CPU_USAGE%.*}" -gt 80 ]; then
        issues+=("CPU使用率过高: ${CPU_USAGE}%")
    fi
    
    # 内存
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$MEM_USAGE" -gt 90 ]; then
        issues+=("内存使用率过高: ${MEM_USAGE}%")
    fi
    
    # 磁盘
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 90 ]; then
        issues+=("磁盘使用率过高: ${DISK_USAGE}%")
    fi
    
    # 负载
    LOAD=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    LOAD_THRESHOLD=$(nproc)
    if (( $(echo "$LOAD > $LOAD_THRESHOLD" | bc -l) )); then
        issues+=("系统负载过高: $LOAD")
    fi
    
    echo "CPU: ${CPU_USAGE}% | 内存: ${MEM_USAGE}% | 磁盘: ${DISK_USAGE}% | 负载: $LOAD"
    
    if [ ${#issues[@]} -gt 0 ]; then
        echo "发现 ${#issues[@]} 个问题"
        printf '%s\n' "${issues[@]}"
        return 1
    fi
    
    return 0
}

# 服务状态检查
check_services() {
    log "检查服务状态..."
    
    local failed_services=()
    
    # 定义要检查的服务
    declare -A services=(
        ["openclaw.*gateway"]='OpenClaw Gateway'
        ["mihomo"]='Mihomo Proxy'
        ["cron"]='Cron Service'
    )
    
    for pattern in "${!services[@]}"; do
        local name="${services[$pattern]}"
        if ! pgrep -f "$pattern" > /dev/null 2>&1; then
            failed_services+=("$name")
        fi
    done
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        echo "未运行的服务: ${failed_services[*]}"
        return 1
    fi
    
    echo "所有服务正常运行"
    return 0
}

# 网络连接检查
check_network() {
    log "检查网络连接..."
    
    # 检查 Mihomo 代理
    if pgrep -f "mihomo" > /dev/null 2>&1; then
        if curl -s --max-time 5 -x http://127.0.0.1:7890 http://www.google.com > /dev/null 2>&1; then
            echo "代理连接正常"
            return 0
        else
            echo "代理连接异常"
            return 1
        fi
    else
        echo "Mihomo 未运行，跳过代理检查"
        return 0
    fi
}

# 定时任务健康检查
check_cron_health() {
    log "检查定时任务健康..."
    
    if [ -f "$SCRIPTS_DIR/cron_health_checker.py" ]; then
        python3 "$SCRIPTS_DIR/cron_health_checker.py" 2>&1 | tail -20
    else
        echo "定时任务检查器未找到"
        return 1
    fi
}

# 安全状态检查
check_security() {
    log "检查安全状态..."
    
    local issues=()
    
    # 检查 secrets 目录权限
    SECRETS_DIR="$WORKSPACE/secrets"
    if [ -d "$SECRETS_DIR" ]; then
        local perms=$(stat -c "%a" "$SECRETS_DIR" 2>/dev/null)
        if [ "$perms" != "700" ]; then
            issues+=("Secrets 目录权限为 $perms，建议 700")
        fi
    fi
    
    # 检查最近的扫描报告
    local latest_report=$(ls -t $WORKSPACE/learning/security-reports/security_scan_*.md 2>/dev/null | head -1)
    if [ -f "$latest_report" ]; then
        if grep -q "🔴 高风险" "$latest_report" 2>/dev/null; then
            issues+=("安全扫描发现高风险问题")
        fi
    fi
    
    if [ ${#issues[@]} -gt 0 ]; then
        printf '%s\n' "${issues[@]}"
        return 1
    fi
    
    echo "安全状态良好"
    return 0
}

# ========== 自愈模块 ==========

# 尝试修复服务
heal_service() {
    local service="$1"
    
    log "尝试修复服务: $service" "HEALING"
    
    case "$service" in
        "OpenClaw Gateway")
            # 尝试重启 Gateway
            if command -v openclaw &> /dev/null; then
                openclaw gateway restart 2>&1 &
                sleep 5
                if pgrep -f "openclaw.*gateway" > /dev/null; then
                    healing_log "Gateway 重启" "成功"
                    return 0
                fi
            fi
            ;;
        "Mihomo Proxy")
            # 尝试重启 Mihomo
            if systemctl is-active --quiet mihomo 2>/dev/null; then
                systemctl restart mihomo 2>&1
                sleep 3
                if pgrep -f "mihomo" > /dev/null; then
                    healing_log "Mihomo 重启" "成功"
                    return 0
                fi
            elif [ -f /root/mihomo/start.sh ]; then
                bash /root/mihomo/start.sh 2>&1 &
                sleep 3
                if pgrep -f "mihomo" > /dev/null; then
                    healing_log "Mihomo 启动" "成功"
                    return 0
                fi
            fi
            ;;
        "Cron Service")
            systemctl restart cron 2>&1
            if systemctl is-active --quiet cron; then
                healing_log "Cron 重启" "成功"
                return 0
            fi
            ;;
    esac
    
    healing_log "$service 修复" "失败"
    return 1
}

# 尝试清理磁盘
heal_disk_space() {
    log "尝试清理磁盘空间..." "HEALING"
    
    local freed=0
    
    # 清理日志
    if [ -d /var/log ]; then
        find /var/log -name "*.log.*" -mtime +7 -delete 2>/dev/null
        find /var/log -name "*.gz" -mtime +30 -delete 2>/dev/null
    fi
    
    # 清理备份
    if [ -d /clawd-data/workspace-backup ]; then
        find /clawd-data/workspace-backup -type d -mtime +14 -exec rm -rf {} + 2>/dev/null || true
    fi
    
    # 清理旧的扫描报告
    if [ -d "$WORKSPACE/learning/security-reports" ]; then
        ls -t $WORKSPACE/learning/security-reports/*.md | tail -n +11 | xargs rm -f 2>/dev/null || true
    fi
    
    healing_log "磁盘清理" "完成"
    return 0
}

# 智能自愈主函数
smart_healing() {
    log "启动智能自愈..." "HEALING"
    
    local healed=0
    local failed=0
    
    # 1. 修复服务
    if ! check_services; then
        # 获取失败的服务列表并尝试修复
        declare -A services=(
            ["openclaw.*gateway"]='OpenClaw Gateway'
            ["mihomo"]='Mihomo Proxy'
            ["cron"]='Cron Service'
        )
        
        for pattern in "${!services[@]}"; do
            if ! pgrep -f "$pattern" > /dev/null 2>&1; then
                if heal_service "${services[$pattern]}"; then
                    ((healed++))
                else
                    ((failed++))
                fi
            fi
        done
    fi
    
    # 2. 清理磁盘
    local DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$DISK_USAGE" -gt 85 ]; then
        heal_disk_space
        ((healed++))
    fi
    
    # 3. 修复权限
    SECRETS_DIR="$WORKSPACE/secrets"
    if [ -d "$SECRETS_DIR" ]; then
        local perms=$(stat -c "%a" "$SECRETS_DIR" 2>/dev/null)
        if [ "$perms" != "700" ]; then
            chmod 700 "$SECRETS_DIR"
            healing_log "Secrets 权限修复" "700"
            ((healed++))
        fi
    fi
    
    log "自愈完成: $healed 成功, $failed 失败" "HEALING"
    
    return $failed
}

# ========== 报告生成 ==========

generate_report() {
    local report_file="$REPORT_DIR/health_report_${DATE}.md"
    
    log "生成健康报告..."
    
    cat > "$report_file" <> EOF
# 🏥 系统健康报告 - $(date '+%Y-%m-%d %H:%M:%S')

## 📊 检查摘要

| 检查项 | 状态 |
|--------|------|
| 系统资源 | $(check_system_resources >>/dev/null && echo "✅ 正常" || echo "⚠️  需关注") |
| 服务状态 | $(check_services >>/dev/null && echo "✅ 正常" || echo "⚠️  需关注") |
| 网络连接 | $(check_network >>/dev/null && echo "✅ 正常" || echo "⚠️  需关注") |
| 安全状态 | $(check_security >>/dev/null && echo "✅ 正常" || echo "⚠️  需关注") |

## 🔍 详细检查结果

### 系统资源
\`\`\`
$(check_system_resources 2>&1)
\`\`\`

### 服务状态
\`\`\`
$(check_services 2>&1)
\`\`\`

### 定时任务
\`\`\`
$(check_cron_health 2>&1)
\`\`\`

## 🏥 自愈记录

查看自愈日志: \`tail -20 $HEALING_LOG\`

## 📝 建议操作

- 如果发现问题，运行: \`bash $0 heal\`
- 查看最新日志: \`tail -f $HEALTH_LOG\`

---
*报告生成: 统一健康与自愈管理系统 v3.0*
EOF
    
    echo "报告已保存: $report_file"
}

# ========== 主函数 ==========

main() {
    case "$1" in
        "check")
            log "===== 开始健康检查 ====="
            check_system_resources
            check_services
            check_network
            check_security
            log "===== 健康检查完成 ====="
            ;;
        "heal"|"healing")
            smart_healing
            ;;
        "full"|"all")
            log "===== 开始全面检查与自愈 ====="
            check_system_resources || true
            check_services || true
            check_network || true
            check_security || true
            smart_healing
            generate_report
            log "===== 全面检查与自愈完成 ====="
            ;;
        "report")
            generate_report
            ;;
        "status")
            echo "🏥 统一健康与自愈管理系统"
            echo "========================"
            echo ""
            echo "系统资源:"
            check_system_resources 2>&1 | head -5
            echo ""
            echo "服务状态:"
            check_services 2>&1
            echo ""
            echo "最近自愈记录:"
            tail -5 "$HEALING_LOG" 2>/dev/null || echo "暂无记录"
            ;;
        *)
            echo "🏥 统一健康与自愈管理系统 v3.0"
            echo ""
            echo "用法: $0 {check|heal|full|report|status}"
            echo ""
            echo "命令:"
            echo "  check   - 执行健康检查"
            echo "  heal    - 执行智能自愈"
            echo "  full    - 全面检查 + 自愈 + 报告"
            echo "  report  - 生成健康报告"
            echo "  status  - 查看系统状态"
            ;;
    esac
}

main "$@"
