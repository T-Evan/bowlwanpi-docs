#!/bin/bash
# 🔍 配置一致性检查脚本
# 夜间构建时自动检查常见配置问题

CONFIG_FILE="/root/.openclaw/openclaw.json"
REPORT_FILE="/root/.openclaw/workspace/memory/config-check-report.json"
ISSUES=()

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 开始配置一致性检查..."

# 检查1: Feishu 配置一致性
if command -v jq &> /dev/null; then
    FEISHU_CHANNEL=$(jq -r '.channels.feishu.enabled // "null"' "$CONFIG_FILE" 2>/dev/null)
    FEISHU_PLUGIN=$(jq -r '.plugins.entries.feishu.enabled // "null"' "$CONFIG_FILE" 2>/dev/null)
    
    if [ "$FEISHU_CHANNEL" = "true" ] && [ "$FEISHU_PLUGIN" = "false" ]; then
        ISSUES+=("{\"type\":\"warning\",\"component\":\"feishu\",\"message\":\"频道启用但插件未激活\",\"suggestion\":\"统一配置或禁用频道\"}")
        echo -e "${YELLOW}⚠️ Feishu: 频道启用但插件未激活${NC}"
    fi
fi

# 检查2: 心跳日志大小
HEARTBEAT_LOG="/var/log/bowlwanpi-heartbeat.log"
if [ -f "$HEARTBEAT_LOG" ]; then
    LOG_SIZE=$(stat -f%z "$HEARTBEAT_LOG" 2>/dev/null || stat -c%s "$HEARTBEAT_LOG" 2>/dev/null)
    LOG_SIZE_MB=$((LOG_SIZE / 1024 / 1024))
    
    if [ "$LOG_SIZE_MB" -gt 10 ]; then
        ISSUES+=("{\"type\":\"warning\",\"component\":\"heartbeat_log\",\"message\":\"日志过大(${LOG_SIZE_MB}MB)\",\"suggestion\":\"考虑轮转或清理\"}")
        echo -e "${YELLOW}⚠️ Heartbeat日志过大: ${LOG_SIZE_MB}MB${NC}"
    fi
fi

# 检查3: Cron 健康状态
CRON_ALERTS=$(grep -c "Cron health check failed" "$HEARTBEAT_LOG" 2>/dev/null || echo "0")
if [ "$CRON_ALERTS" -gt 10 ]; then
    ISSUES+=("{\"type\":\"error\",\"component\":\"cron\",\"message\":\"检测到${CRON_ALERTS}次cron失败\",\"suggestion\":\"检查gateway服务状态\"}")
    echo -e "${RED}❌ Cron: 检测到 ${CRON_ALERTS} 次健康检查失败${NC}"
fi

# 检查4: Task queue 过期任务
TASK_QUEUE="/root/.openclaw/workspace/memory/task-queue.json"
if [ -f "$TASK_QUEUE" ] && command -v jq &> /dev/null; then
    PENDING_TASKS=$(jq '.tasks | length' "$TASK_QUEUE" 2>/dev/null || echo "0")
    if [ "$PENDING_TASKS" -gt 0 ]; then
        echo -e "${YELLOW}ℹ️ Task Queue: 有 ${PENDING_TASKS} 个待办任务${NC}"
    fi
fi

# 生成报告
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
ISSUES_JSON=$(printf '%s\n' "${ISSUES[@]}" | paste -sd ',' -)

if [ -z "$ISSUES_JSON" ]; then
    ISSUES_JSON=""
    echo -e "${GREEN}✅ 配置检查通过，未发现明显问题${NC}"
else
    ISSUES_JSON=",\"issues\":[$ISSUES_JSON]"
fi

cat > "$REPORT_FILE" << EOF
{
  "timestamp": "$TIMESTAMP",
  "status": "$(if [ ${#ISSUES[@]} -eq 0 ]; then echo "ok"; else echo "warning"; fi)",
  "checks_performed": ["feishu_config", "heartbeat_log", "cron_health", "task_queue"]
  $ISSUES_JSON
}
EOF

echo "📄 报告已保存: $REPORT_FILE"
