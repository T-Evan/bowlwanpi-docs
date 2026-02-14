#!/bin/bash
#
# 💓 统一心跳简报 v3.0
# 整合: 自愈系统 + 心跳简报 + 系统监控报告
#

WORKSPACE="${HOME}/.openclaw/workspace"
REPORT_DIR="$WORKSPACE/health-checks"

# 生成统一报告并发送
bash "$WORKSPACE/scripts/unified_status_report.sh" notify

# 更新最后报告时间
echo "{\"lastReportTime\": \"$(date -Iseconds)\", \"intervalMinutes\": 5, \"nextReportAt\": \"$(date -d '+5 minutes' -Iseconds)\"}" > "$WORKSPACE/memory/heartbeat-last-report.json"

exit 0