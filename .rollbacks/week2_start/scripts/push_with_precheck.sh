#!/bin/bash
#
# 📱 定时推送任务包装器
# 带前置检查，确保服务正常后才执行
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRECHECK_SCRIPT="$SCRIPT_DIR/precheck.sh"

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 日志
log() {
    echo "[$(date '+%H:%M:%S')] $1"
}

# 检查前置检查脚本是否存在
if [ ! -f "$PRECHECK_SCRIPT" ]; then
    log "${RED}❌ 前置检查脚本不存在: $PRECHECK_SCRIPT${NC}"
    exit 1
fi

# 根据任务类型执行不同的推送
case "$1" in
    netease)
        TASK_NAME="网易云日推"
        COMMAND="python3 $SCRIPT_DIR/netease_chart.py 2>&1 | head -30"
        ;;
    weibo)
        TASK_NAME="微博热搜"
        COMMAND="curl -s 'https://weibo.com/ajax/side/hotSearch' 2>/dev/null | head -c 1000 || echo '获取失败'"
        ;;
    zhihu)
        TASK_NAME="知乎热榜"
        COMMAND="curl -s 'https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total' 2>/dev/null | head -c 1000 || echo '获取失败'"
        ;;
    bili)
        TASK_NAME="B站热门"
        COMMAND="curl -s 'https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all' 2>/dev/null | head -c 1000 || echo '获取失败'"
        ;;
    producthunt)
        TASK_NAME="Product Hunt"
        COMMAND="curl -s 'https://www.producthunt.com/feed' 2>/dev/null | head -c 1000 || echo '获取失败'"
        ;;
    *)
        log "用法: $0 [netease|weibo|zhihu|bili|producthunt]"
        exit 1
        ;;
esac

log "================================"
log "🚀 开始执行: $TASK_NAME"
log "================================"

# 运行前置检查
if bash "$PRECHECK_SCRIPT" check "$TASK_NAME" "true"; then
    log ""
    log "✅ 前置检查通过，执行推送..."
    log "================================"
    
    # 执行实际的推送命令
    OUTPUT=$(eval "$COMMAND" 2>&1)
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        log "✅ $TASK_NAME 执行成功"
        # 这里可以添加实际的消息推送逻辑
        # 例如: echo "$OUTPUT" | python3 send_message.py
    else
        log "${RED}❌ $TASK_NAME 执行失败 (exit code: $EXIT_CODE)${NC}"
        log "输出: $OUTPUT"
    fi
    
    exit $EXIT_CODE
else
    log ""
    log "${RED}❌ $TASK_NAME 因前置检查失败未执行${NC}"
    
    # 记录到失败日志
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $TASK_NAME - 前置检查失败" >> /var/log/bowlwanpi-push-failures.log
    
    # 发送告警（如果需要）
    # 可以在这里添加飞书/微信告警
    
    exit 1
fi
