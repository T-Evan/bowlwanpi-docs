#!/bin/bash
#
# 🤝 主从协作系统 v1.0
# 基于 Claude-Claw 的 "Sovereign Collaborators" 理念
# 实现一碗(主)与碗皮(从)的高效协作模式
#

WORKSPACE="${HOME}/.openclaw/workspace"
COLLABORATION_LOG="$WORKSPACE/.collaboration_log.jsonl"
TASK_QUEUE="$WORKSPACE/memory/task-queue.json"

# ========== 协作模式定义 ==========

# 协作类型
declare -A COLLABORATION_MODES=(
    ["directive"]="指令模式-一碗直接下达指令，碗皮执行"
    ["consultative"]="咨询模式-碗皮提出建议，一碗决策"
    ["collaborative"]="协作模式-共同设计解决方案"
    ["delegated"]="委托模式-一碗设定目标，碗皮自主完成"
    ["autonomous"]="自主模式-碗皮主动发现问题并解决"
)

# ========== 任务管理 ==========

# 添加协作任务
add_collaboration_task() {
    local title="$1"
    local mode="${2:-consultative}"  # 默认咨询模式
    local priority="${3:-medium}"
    local description="${4:-}"
    
    local task_id="task_$(date +%s)_${RANDOM}"
    local timestamp=$(date -Iseconds)
    
    # 添加到任务队列
    local task=$(cat <> EOF
{
    "id": "$task_id",
    "title": "$title",
    "mode": "$mode",
    "priority": "$priority",
    "description": "$description",
    "status": "pending",
    "created_at": "$timestamp",
    "updated_at": "$timestamp",
    "collaboration_log": []
}
EOF
)
    
    # 更新任务队列
    if [ -f "$TASK_QUEUE" ]; then
        jq ".tasks += [$task]" "$TASK_QUEUE" > "$TASK_QUEUE.tmp" && \
            mv "$TASK_QUEUE.tmp" "$TASK_QUEUE"
    else
        echo "{\"tasks\": [$task], \"completed\": []}" > "$TASK_QUEUE"
    fi
    
    # 记录协作日志
    echo "{\"timestamp\": \"$timestamp\", \"event\": \"task_created\", \"task_id\": \"$task_id\", \"mode\": \"$mode\"}" >> "$COLLABORATION_LOG"
    
    echo "✅ 已创建协作任务: $title"
    echo "   模式: ${COLLABORATION_MODES[$mode]}"
    echo "   ID: $task_id"
    
    # 根据模式给出提示
    case "$mode" in
        "directive")
            echo "   💡 碗皮将直接执行，完成后汇报"
            ;;
        "consultative")
            echo "   💡 碗皮将准备方案，等待一碗确认"
            ;;
        "collaborative")
            echo "   💡 建议与一碗讨论方案细节"
            ;;
        "delegated")
            echo "   💡 碗皮将自主完成，定期同步进度"
            ;;
        "autonomous")
            echo "   💡 碗皮将主动推进，完成后展示成果"
            ;;
    esac
}

# 更新任务状态
update_task_status() {
    local task_id="$1"
    local status="$2"  # pending/in_progress/review/completed/cancelled
    local note="${3:-}"
    local timestamp=$(date -Iseconds)
    
    # 更新任务状态
    jq ".tasks = [.tasks[] | if .id == \"$task_id\" then .status = \"$status\" | .updated_at = \"$timestamp\" else . end]" "$TASK_QUEUE" > "$TASK_QUEUE.tmp" && \
        mv "$TASK_QUEUE.tmp" "$TASK_QUEUE"
    
    # 记录日志
    echo "{\"timestamp\": \"$timestamp\", \"event\": \"status_update\", \"task_id\": \"$task_id\", \"status\": \"$status\", \"note\": \"$note\"}" >> "$COLLABORATION_LOG"
    
    echo "✅ 任务状态更新: $task_id → $status"
    [ -n "$note" ] && echo "   备注: $note"
    
    # 如果完成，移到 completed
    if [ "$status" = "completed" ]; then
        complete_task "$task_id"
    fi
}

# 完成任务
complete_task() {
    local task_id="$1"
    local timestamp=$(date -Iseconds)
    
    # 获取任务
    local task=$(jq ".tasks[] | select(.id == \"$task_id\")" "$TASK_QUEUE")
    
    if [ -n "$task" ]; then
        # 添加到 completed
        jq ".completed += [$task | .completed_at = \"$timestamp\"]" "$TASK_QUEUE" > "$TASK_QUEUE.tmp" && \
            mv "$TASK_QUEUE.tmp" "$TASK_QUEUE"
        
        # 从 tasks 中移除
        jq ".tasks = [.tasks[] | select(.id != \"$task_id\")]" "$TASK_QUEUE" > "$TASK_QUEUE.tmp" && \
            mv "$TASK_QUEUE.tmp" "$TASK_QUEUE"
        
        echo "🎉 任务已归档到 completed"
    fi
}

# ========== 协作模式切换 ==========

switch_mode() {
    local task_id="$1"
    local new_mode="$2"
    local reason="${3:-}"
    local timestamp=$(date -Iseconds)
    
    # 获取旧模式
    local old_mode=$(jq -r ".tasks[] | select(.id == \"$task_id\") | .mode" "$TASK_QUEUE")
    
    # 更新模式
    jq ".tasks = [.tasks[] | if .id == \"$task_id\" then .mode = \"$new_mode\" | .updated_at = \"$timestamp\" else . end]" "$TASK_QUEUE" > "$TASK_QUEUE.tmp" && \
        mv "$TASK_QUEUE.tmp" "$TASK_QUEUE"
    
    # 记录日志
    echo "{\"timestamp\": \"$timestamp\", \"event\": \"mode_switch\", \"task_id\": \"$task_id\", \"from\": \"$old_mode\", \"to\": \"$new_mode\", \"reason\": \"$reason\"}" >> "$COLLABORATION_LOG"
    
    echo "🔄 协作模式切换: $old_mode → $new_mode"
    echo "   ${COLLABORATION_MODES[$new_mode]}"
    [ -n "$reason" ] && echo "   原因: $reason"
}

# ========== 查询与报告 ==========

# 列出任务
list_tasks() {
    local status_filter="${1:-all}"
    
    echo "📋 当前任务列表"
    echo "==============="
    
    if [ ! -f "$TASK_QUEUE" ]; then
        echo "暂无任务"
        return
    fi
    
    local tasks
    if [ "$status_filter" = "all" ]; then
        tasks=$(jq -r '.tasks[] | "\(.id): [\(.status)] [\(.mode)] \(.title) (\(.priority))"' "$TASK_QUEUE" 2>/dev/null)
    else
        tasks=$(jq -r ".tasks[] | select(.status == \"$status_filter\") | \"\(.id): [\(.status)] [\(.mode)] \(.title) (\(.priority))\"" "$TASK_QUEUE" 2>/dev/null)
    fi
    
    if [ -z "$tasks" ]; then
        echo "暂无符合条件的任务"
    else
        echo "$tasks"
    fi
}

# 查看任务详情
show_task_detail() {
    local task_id="$1"
    
    jq ".tasks[] | select(.id == \"$task_id\")" "$TASK_QUEUE" 2>/dev/null || \
        jq ".completed[] | select(.id == \"$task_id\")" "$TASK_QUEUE" 2>/dev/null || \
        echo "任务不存在: $task_id"
}

# 协作报告
generate_collaboration_report() {
    local days="${1:-7}"
    local since=$(date -d "$days days ago" +%Y-%m-%d)
    
    echo "🤝 主从协作报告 (最近 $days 天)"
    echo "=============================="
    echo ""
    
    if [ ! -f "$COLLABORATION_LOG" ]; then
        echo "暂无协作记录"
        return
    fi
    
    # 统计各模式使用次数
    echo "协作模式使用情况:"
    grep "$since" "$COLLABORATION_LOG" 2>/dev/null | \
        jq -r 'select(.event == "task_created") | .mode' 2>/dev/null | \
        sort | uniq -c | sort -rn | while read count mode; do
        echo "  $mode: $count 次"
    done
    
    echo ""
    
    # 任务完成情况
    if [ -f "$TASK_QUEUE" ]; then
        local pending=$(jq '.tasks | length' "$TASK_QUEUE")
        local completed=$(jq '.completed | length' "$TASK_QUEUE")
        echo "任务统计:"
        echo "  进行中: $pending"
        echo "  已完成: $completed"
        echo ""
    fi
    
    # 最近的协作记录
    echo "最近协作记录:"
    tail -10 "$COLLABORATION_LOG" 2>/dev/null | jq -r '"  \(.timestamp) [\(.event)] \(.task_id // \"\")"' 2>/dev/null || echo "  暂无记录"
}

# ========== 智能建议 ==========

suggest_collaboration_mode() {
    local task_description="$1"
    
    echo "💡 针对任务 '$task_description' 的协作模式建议:"
    echo ""
    
    # 简单的关键词匹配建议
    if echo "$task_description" | grep -qi "紧急\|立刻\|马上"; then
        echo "建议模式: directive (指令模式)"
        echo "原因: 任务紧急，需要立即执行"
    elif echo "$task_description" | grep -qi "设计\|方案\|规划"; then
        echo "建议模式: collaborative (协作模式)"
        echo "原因: 需要共同设计方案"
    elif echo "$task_description" | grep -qi "研究\|学习\|调研"; then
        echo "建议模式: delegated (委托模式)"
        echo "原因: 可以设定目标后自主完成"
    elif echo "$task_description" | grep -qi "优化\|改进\|修复"; then
        echo "建议模式: autonomous (自主模式)"
        echo "原因: 可以主动发现并解决"
    else
        echo "建议模式: consultative (咨询模式)"
        echo "原因: 需要准备方案后确认"
    fi
}

# ========== 主函数 ==========

main() {
    case "$1" in
        "add")
            shift
            add_collaboration_task "$@"
            ;;
        "update")
            shift
            update_task_status "$@"
            ;;
        "switch")
            shift
            switch_mode "$@"
            ;;
        "list")
            shift
            list_tasks "$@"
            ;;
        "show")
            shift
            show_task_detail "$@"
            ;;
        "report")
            shift
            generate_collaboration_report "$@"
            ;;
        "suggest")
            shift
            suggest_collaboration_mode "$@"
            ;;
        "modes")
            echo "🤝 协作模式说明"
            echo "=============="
            echo ""
            for mode in "${!COLLABORATION_MODES[@]}"; do
                echo "$mode: ${COLLABORATION_MODES[$mode]}"
                echo ""
            done
            ;;
        *)
            echo "🤝 主从协作系统 v1.0"
            echo ""
            echo "用法: $0 {add|update|switch|list|show|report|suggest|modes}"
            echo ""
            echo "命令:"
            echo "  add '标题' [mode] [priority] [描述]  - 添加任务"
            echo "  update <task_id> <status> [note]     - 更新状态"
            echo "  switch <task_id> <new_mode> [原因]   - 切换模式"
            echo "  list [status]                         - 列出任务"
            echo "  show <task_id>                        - 查看详情"
            echo "  report [days]                         - 生成报告"
            echo "  suggest '任务描述'                    - 模式建议"
            echo "  modes                                 - 模式说明"
            echo ""
            echo "协作模式: directive, consultative, collaborative, delegated, autonomous"
            ;;
    esac
}

main "$@"
