#!/bin/bash
#
# 带性能监控的任务执行包装器
# 用法: monitor-wrapper.sh <task-name> <command>
#

TASK_NAME="$1"
shift

STATS_DIR="/root/.openclaw/workspace/stats"
mkdir -p "$STATS_DIR"

# 记录开始时间
START_TIME=$(date +%s%N)
START_MS=$((START_TIME / 1000000))

# 执行命令
"$@"
EXIT_CODE=$?

# 记录结束时间
END_TIME=$(date +%s%N)
END_MS=$((END_TIME / 1000000))

# 计算耗时
DURATION_MS=$((END_MS - START_MS))

# 判断成功/失败
if [ $EXIT_CODE -eq 0 ]; then
    SUCCESS="true"
else
    SUCCESS="false"
fi

# 记录到日志
LOG_FILE="/var/log/bowlwanpi-performance.log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Task: $TASK_NAME, Duration: ${DURATION_MS}ms, Success: $SUCCESS" >> "$LOG_FILE"

# 更新统计（通过Python脚本）
python3 /root/.openclaw/workspace/scripts/performance_monitor.py record "$TASK_NAME" "$DURATION_MS" "$SUCCESS" 2>/dev/null || true

exit $EXIT_CODE
