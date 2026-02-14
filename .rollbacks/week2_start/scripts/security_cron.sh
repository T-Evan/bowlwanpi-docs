#!/bin/bash
# 🔐 security_cron.sh - 安全扫描定时任务脚本
# 添加到 crontab: 0 3 * * 0 /root/.openclaw/workspace/scripts/security_cron.sh
# 每周日凌晨 3:00 执行安全扫描

set -e

# 配置
WORKSPACE="${HOME}/.openclaw/workspace"
SECURITY_SCRIPT="${WORKSPACE}/scripts/security_check.sh"
REPORT_DIR="${WORKSPACE}/learning/security-reports"
LOG_FILE="${REPORT_DIR}/cron.log"
FEISHU_WEBHOOK="${FEISHU_WEBHOOK_URL:-}"

# 创建日志目录
mkdir -p "$REPORT_DIR"

# 记录开始时间
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始安全扫描..." >> "$LOG_FILE"

# 执行安全扫描
if [ -f "$SECURITY_SCRIPT" ]; then
    bash "$SECURITY_SCRIPT" > /tmp/security_scan_output.log 2>&1
    SCAN_STATUS=$?
    
    # 获取最新报告
    LATEST_REPORT=$(ls -t ${REPORT_DIR}/security_scan_*.md 2>/dev/null | head -1)
    
    if [ $SCAN_STATUS -eq 0 ] && [ -f "$LATEST_REPORT" ]; then
        # 检查是否有高风险
        if grep -q "🔴 高风险" "$LATEST_REPORT" 2>/dev/null; then
            ALERT_MSG="🚨 安全扫描发现高风险问题！\n请立即检查: ${LATEST_REPORT}"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ 发现高风险问题" >> "$LOG_FILE"
            
            # 发送告警 (如果有飞书 webhook)
            if [ -n "$FEISHU_WEBHOOK" ]; then
                curl -s -X POST "$FEISHU_WEBHOOK" \
                    -H "Content-Type: application/json" \
                    -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$ALERT_MSG\"}}" > /dev/null 2>&1 || true
            fi
            
            exit 1
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 安全扫描完成，无高风险问题" >> "$LOG_FILE"
        fi
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 安全扫描失败" >> "$LOG_FILE"
        exit 1
    fi
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ 安全扫描脚本不存在: $SECURITY_SCRIPT" >> "$LOG_FILE"
    exit 1
fi

# 清理旧报告 (保留最近 10 份)
ls -t ${REPORT_DIR}/security_scan_*.md 2>/dev/null | tail -n +11 | xargs -r rm -f

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 安全扫描任务完成" >> "$LOG_FILE"
exit 0