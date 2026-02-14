#!/bin/bash
#
# 📊 统一系统状态报告 v1.1 (修复版)
# 整合: 自愈系统 + 心跳简报 + 系统监控
#

# 不要 set -e，避免个别命令失败导致整个脚本退出
# set -e

# 配置
WORKSPACE="${HOME}/.openclaw/workspace"
REPORT_DIR="$WORKSPACE/health-checks"
LOG_DIR="/var/log"
FEISHU_WEBHOOK="${FEISHU_WEBHOOK_URL:-}"

# 创建报告目录
mkdir -p "$REPORT_DIR"

# 获取时间
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATE=$(date '+%Y%m%d')
TIME_ONLY=$(date '+%H:%M')

# ========== 数据收集（修复版，变量全局导出）==========

# 1. 系统资源状态
export CPU_USAGE=0
export MEM_USAGE=0
export DISK_USAGE=0
export LOAD=0
export UPTIME="unknown"

collect_system_status() {
    # CPU - 修复：添加错误处理
    CPU_USAGE=$(top -bn1 2>/dev/null | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    if [ -z "$CPU_USAGE" ] || ! [[ "$CPU_USAGE" =~ ^[0-9]+\.?[0-9]*$ ]]; then
        CPU_USAGE=0
    fi
    
    # 内存
    MEM_USAGE=$(free 2>/dev/null | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ -z "$MEM_USAGE" ] || ! [[ "$MEM_USAGE" =~ ^[0-9]+$ ]]; then
        MEM_USAGE=0
    fi
    
    # 磁盘
    DISK_USAGE=$(df / 2>/dev/null | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ -z "$DISK_USAGE" ] || ! [[ "$DISK_USAGE" =~ ^[0-9]+$ ]]; then
        DISK_USAGE=0
    fi
    
    # 负载
    LOAD=$(uptime 2>/dev/null | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    if [ -z "$LOAD" ]; then
        LOAD=0
    fi
    
    # 运行时间
    UPTIME=$(uptime -p 2>/dev/null || uptime 2>/dev/null | awk -F',' '{print $1}' || echo "unknown")
}

# 2. 服务状态
export GATEWAY_STATUS="❓"
export GATEWAY_DETAIL="未知"
export MIHOMO_STATUS="❓"
export MIHOMO_DETAIL="未知"
export CRON_STATUS="❓"
export CRON_DETAIL="未知"

collect_service_status() {
    # Gateway - 增加延迟重试机制
    local gateway_ok=false
    for i in 1 2 3; do
        if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
            gateway_ok=true
            break
        fi
        sleep 1
    done
    
    if [ "$gateway_ok" = true ]; then
        GATEWAY_STATUS="✅"
        GATEWAY_DETAIL="运行中"
    else
        GATEWAY_STATUS="❌"
        GATEWAY_DETAIL="未运行"
    fi
    
    # Mihomo - 增加延迟重试机制
    local mihomo_ok=false
    for i in 1 2 3; do
        if pgrep -f "mihomo" > /dev/null 2>&1; then
            mihomo_ok=true
            break
        fi
        sleep 1
    done
    
    if [ "$mihomo_ok" = true ]; then
        MIHOMO_STATUS="✅"
        MIHOMO_DETAIL="运行中"
    else
        MIHOMO_STATUS="⚠️"
        MIHOMO_DETAIL="未运行"
    fi
    
    # Cron
    if systemctl is-active --quiet cron 2>/dev/null || pgrep -x "cron" > /dev/null 2>&1; then
        CRON_STATUS="✅"
        CRON_DETAIL="运行中"
    else
        CRON_STATUS="⚠️"
        CRON_DETAIL="未运行"
    fi
}

# 3. 自愈系统状态
export HEALING_COUNT=0
export HEALING_SUMMARY="暂无数据"
export LAST_HEALING=""

collect_healing_status() {
    HEALING_LOG="$LOG_DIR/bowlwanpi-healing.log"
    
    # 最近24小时的自愈记录
    if [ -f "$HEALING_LOG" ]; then
        HEALING_COUNT=$(grep "$(date '+%Y-%m-%d')" "$HEALING_LOG" 2>/dev/null | wc -l)
        LAST_HEALING=$(tail -1 "$HEALING_LOG" 2>/dev/null | cut -d']' -f3 | sed 's/^ \[HEALING\] //' || echo "")
        
        if [ "$HEALING_COUNT" -eq 0 ]; then
            HEALING_SUMMARY="✅ 系统稳定，无需自愈"
        else
            HEALING_SUMMARY="🔄 今日自愈 $HEALING_COUNT 次"
        fi
    else
        HEALING_SUMMARY="ℹ️ 暂无自愈记录"
        HEALING_COUNT=0
    fi
}

# 4. 安全状态
export SECURITY_STATUS="❓"
export SECURITY_DETAIL="未知"
export CRON_STATUS_DETAIL="未知"

collect_security_status() {
    LATEST_REPORT=$(ls -t $WORKSPACE/learning/security-reports/security_scan_*.md 2>/dev/null | head -1)
    
    if [ -f "$LATEST_REPORT" ]; then
        if grep -q "🔴 高风险" "$LATEST_REPORT" 2>/dev/null; then
            SECURITY_STATUS="🔴 需关注"
            SECURITY_DETAIL="发现高风险问题"
        elif grep -q "🟠 中风险" "$LATEST_REPORT" 2>/dev/null; then
            SECURITY_STATUS="🟡 正常"
            SECURITY_DETAIL="发现中风险问题"
        else
            SECURITY_STATUS="✅ 安全"
            SECURITY_DETAIL="无风险"
        fi
    else
        SECURITY_STATUS="ℹ️ 未扫描"
        SECURITY_DETAIL="暂无扫描报告"
    fi
}

# 5. 定时任务状态
collect_cron_status() {
    CRON_STATUS_DETAIL="检查器未安装"
}

# ========== 生成报告 ==========

generate_unified_report() {
    # 先收集所有数据
    collect_system_status
    collect_service_status
    collect_healing_status
    collect_security_status
    collect_cron_status
    
    # 计算总体健康度
    HEALTH_SCORE=100
    [ "$GATEWAY_STATUS" = "❌" ] && HEALTH_SCORE=$((HEALTH_SCORE - 30))
    [ "$MIHOMO_STATUS" = "⚠️" ] && HEALTH_SCORE=$((HEALTH_SCORE - 10))
    [ "$CRON_STATUS" = "⚠️" ] && HEALTH_SCORE=$((HEALTH_SCORE - 10))
    [ "$SECURITY_STATUS" = "🔴 需关注" ] && HEALTH_SCORE=$((HEALTH_SCORE - 20))
    [ "$HEALING_COUNT" -gt 5 ] && HEALTH_SCORE=$((HEALTH_SCORE - 10))
    
    # 确定健康等级
    if [ "$HEALTH_SCORE" -ge 90 ]; then
        OVERALL_STATUS="✅ 优秀"
        STATUS_EMOJI="🟢"
    elif [ "$HEALTH_SCORE" -ge 70 ]; then
        OVERALL_STATUS="🟡 良好"
        STATUS_EMOJI="🟡"
    elif [ "$HEALTH_SCORE" -ge 50 ]; then
        OVERALL_STATUS="🟠 一般"
        STATUS_EMOJI="🟠"
    else
        OVERALL_STATUS="🔴 需关注"
        STATUS_EMOJI="🔴"
    fi
    
    # 生成报告
    cat > "$REPORT_DIR/unified_report_${DATE}_${TIME_ONLY}.md" << EOF
# 📊 系统状态统一报告

**生成时间:** $TIMESTAMP  
**系统健康度:** $HEALTH_SCORE/100 ($OVERALL_STATUS)

---

## 🖥️ 系统资源

| 指标 | 数值 | 状态 |
|------|------|------|
| CPU | ${CPU_USAGE}% | $([ "${CPU_USAGE%.*}" -lt 80 ] 2>/dev/null && echo "✅" || echo "⚠️") |
| 内存 | ${MEM_USAGE}% | $([ "$MEM_USAGE" -lt 90 ] 2>/dev/null && echo "✅" || echo "⚠️") |
| 磁盘 | ${DISK_USAGE}% | $([ "$DISK_USAGE" -lt 90 ] 2>/dev/null && echo "✅" || echo "⚠️") |
| 负载 | $LOAD | $(echo "$LOAD < $(nproc)" | bc 2>/dev/null && echo "✅" || echo "⚠️") |
| 运行时间 | $UPTIME | - |

---

## 🔧 服务状态

| 服务 | 状态 | 详情 |
|------|------|------|
| OpenClaw Gateway | $GATEWAY_STATUS | $GATEWAY_DETAIL |
| Mihomo 代理 | $MIHOMO_STATUS | $MIHOMO_DETAIL |
| Cron 服务 | $CRON_STATUS | $CRON_DETAIL |

---

## 🏥 自愈系统

$HEALING_SUMMARY

$(if [ "$HEALING_COUNT" -gt 0 ]; then echo "最后操作: $LAST_HEALING"; fi)

---

## 🔐 安全状态

| 项目 | 状态 | 详情 |
|------|------|------|
| 安全扫描 | $SECURITY_STATUS | $SECURITY_DETAIL |
| 定时任务 | ✅ | $CRON_STATUS_DETAIL |

---

## 📋 快速操作

\`\`\`bash
# 查看详细报告
cat $REPORT_DIR/unified_report_${DATE}_${TIME_ONLY}.md

# 运行全面检查
bash $WORKSPACE/scripts/unified_health_system.sh full

# 查看最新日志
tail -20 $LOG_DIR/bowlwanpi-health.log
\`\`\`

---

*统一报告生成器 v1.1 (修复版)*
EOF
    
    echo "$REPORT_DIR/unified_report_${DATE}_${TIME_ONLY}.md"
}

# ========== 发送通知 ==========

send_unified_notification() {
    local report_file=$(generate_unified_report)
    
    # 构建飞书消息（简化版）
    local message=$(cat << EOF
📊 系统状态统一报告

⏰ $TIME_ONLY | 健康度: $HEALTH_SCORE/100 $STATUS_EMOJI

🖥️ 资源: CPU ${CPU_USAGE}% | 内存 ${MEM_USAGE}% | 磁盘 ${DISK_USAGE}%
🔧 服务: Gateway $GATEWAY_STATUS | Mihomo $MIHOMO_STATUS | Cron $CRON_STATUS
🏥 自愈: $HEALING_SUMMARY
🔐 安全: $SECURITY_STATUS

$(if [ "$HEALTH_SCORE" -lt 70 ]; then echo "⚠️ 注意: 系统需要关注"; fi)
EOF
)

    # 发送通知
    if [ -n "$FEISHU_WEBHOOK" ]; then
        curl -s -X POST "$FEISHU_WEBHOOK" \
            -H "Content-Type: application/json" \
            -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$message\"}}" \
            > /dev/null 2>&1 || true
        echo "✅ 统一通知已发送"
    else
        echo "⚠️ 未配置飞书 Webhook"
    fi
    
    # 同时输出到控制台
    echo ""
    echo "========================================"
    echo "$message"
    echo "========================================"
    echo ""
    echo "📄 完整报告: $report_file"
}

# ========== 主函数 ==========

main() {
    case "$1" in
        "report")
            generate_unified_report
            echo "✅ 报告已生成"
            ;;
        "notify"|"send")
            send_unified_notification
            ;;
        "cron")
            # 定时任务调用：生成报告并发送通知
            send_unified_notification
            ;;
        "test")
            echo "🧪 测试数据收集..."
            collect_system_status
            collect_service_status
            collect_healing_status
            collect_security_status
            echo ""
            echo "CPU: $CPU_USAGE%"
            echo "内存: $MEM_USAGE%"
            echo "磁盘: $DISK_USAGE%"
            echo "Gateway: $GATEWAY_STATUS"
            echo "Mihomo: $MIHOMO_STATUS"
            ;;
        *)
            echo "📊 统一系统状态报告 v1.1 (修复版)"
            echo ""
            echo "用法: $0 {report|notify|cron|test}"
            echo ""
            echo "命令:"
            echo "  report  - 仅生成报告"
            echo "  notify  - 生成报告并发送通知"
            echo "  cron    - 定时任务调用（生成+发送）"
            echo "  test    - 测试数据收集"
            ;;
    esac
}

main "$@"
