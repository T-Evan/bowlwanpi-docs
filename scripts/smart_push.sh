#!/bin/bash
#
# 🧠 智能推送系统 v1.0
# 基于一碗状态的智能信息推送
#
# 设计理念: 从"定时推送"进化为"基于状态的智能推送"
# 与一碗共同设计的第一个工作流

WORKSPACE="/root/.openclaw/workspace"
STATE_FILE="$WORKSPACE/.bowlwanpi_state.json"
LOG_FILE="/var/log/bowlwanpi-smart-push.log"

# ========== 状态检测 ==========

# 检测当前时间类别
detect_time_context() {
    local hour=$(date +%H)
    local weekday=$(date +%u)  # 1-5 工作日, 6-7 周末
    
    # 工作日判断
    if [ $weekday -le 5 ]; then
        case $hour in
            06|07|08) echo "morning_prep" ;;      # 早晨准备时间
            09|10|11) echo "work_morning" ;;      # 工作日上午
            12|13) echo "lunch_break" ;;          # 午休时间
            14|15|16|17) echo "work_afternoon" ;; # 工作日下午
            18|19) echo "evening_transition" ;;   # 晚间过渡
            20|21|22) echo "evening_leisure" ;;   # 晚间休闲
            23|00|01|02|03|04|05) echo "sleep" ;; # 睡眠时间
        esac
    else
        # 周末
        case $hour in
            08|09|10) echo "weekend_morning" ;;
            11|12|13|14|15|16|17|18) echo "weekend_active" ;;
            19|20|21|22) echo "weekend_evening" ;;
            *) echo "sleep" ;;
        esac
    fi
}

# 获取推送偏好
get_push_preference() {
    local context="$1"
    
    # 基于时间上下文的推送偏好
    # 返回: allow(允许) / delay(延迟) / block(禁止)
    case "$context" in
        "morning_prep")
            echo "allow:high"      # 早晨: 高优先级信息
            ;;
        "work_morning"|"work_afternoon")
            echo "delay:medium"    # 工作时间: 中等优先级延迟推送
            ;;
        "lunch_break")
            echo "allow:medium"    # 午休: 中等优先级允许
            ;;
        "evening_transition")
            echo "allow:all"       # 晚间过渡: 允许所有
            ;;
        "evening_leisure"|"weekend_*")
            echo "allow:all"       # 休闲时间: 允许所有
            ;;
        "sleep")
            echo "block:emergency_only"  # 睡眠: 仅紧急
            ;;
        *)
            echo "allow:normal"    # 默认
            ;;
    esac
}

# ========== 智能决策 ==========

# 决定是否推送
should_push() {
    local message_priority="$1"  # emergency/high/medium/normal/low
    local context=$(detect_time_context)
    local preference=$(get_push_preference "$context")
    
    local action=$(echo "$preference" | cut -d: -f1)
    local allowed_priority=$(echo "$preference" | cut -d: -f2)
    
    # 优先级数值 (越高越重要)
    declare -A priority_value=(
        ["emergency"]=5
        ["high"]=4
        ["medium"]=3
        ["normal"]=2
        ["low"]=1
    )
    
    local msg_val=${priority_value[$message_priority]:-2}
    local allowed_val=${priority_value[$allowed_priority]:-2}
    
    case "$action" in
        "allow")
            if [ $msg_val -ge $allowed_val ]; then
                echo "yes:context_allow"
                return 0
            fi
            ;;
        "delay")
            echo "delay:wait_for_better_time"
            return 1
            ;;
        "block")
            if [ "$message_priority" = "emergency" ]; then
                echo "yes:emergency_override"
                return 0
            fi
            echo "no:blocked_by_context"
            return 1
            ;;
    esac
    
    echo "no:priority_too_low"
    return 1
}

# ========== 消息队列 ==========

# 延迟队列文件
DELAY_QUEUE="$WORKSPACE/.smart_push_delay_queue.jsonl"

# 添加消息到延迟队列
queue_delayed_message() {
    local message="$1"
    local priority="$2"
    local context=$(detect_time_context)
    
    # JSON 格式: {timestamp, message, priority, context}
    cat >> "$DELAY_QUEUE" << EOF
{"ts":$(date +%s),"msg":"$message","priority":"$priority","context":"$context"}
EOF
    
    echo "⏳ 消息已加入延迟队列 (当前: $context)"
}

# 处理延迟队列
process_delay_queue() {
    local current_context=$(detect_time_context)
    local processed=0
    
    if [ ! -f "$DELAY_QUEUE" ]; then
        return 0
    fi
    
    # 读取队列并处理符合条件的消息
    local temp_queue="$DELAY_QUEUE.tmp"
    
    while IFS= read -r line; do
        local msg_priority=$(echo "$line" | jq -r '.priority')
        local decision=$(should_push "$msg_priority")
        
        if [[ "$decision" == yes* ]]; then
            # 可以发送
            local msg=$(echo "$line" | jq -r '.msg')
            echo "📤 发送延迟消息: $msg"
            # 这里调用实际的推送函数
            # send_feishu "$msg"
            ((processed++))
        else
            # 还不能发送，保留在队列
            echo "$line" >> "$temp_queue"
        fi
    done < "$DELAY_QUEUE"
    
    # 更新队列
    if [ -f "$temp_queue" ]; then
        mv "$temp_queue" "$DELAY_QUEUE"
    else
        > "$DELAY_QUEUE"
    fi
    
    return $processed
}

# ========== 推送函数 ==========

# 智能推送入口
smart_push() {
    local message="$1"
    local priority="${2:-normal}"  # emergency/high/medium/normal/low
    
    local context=$(detect_time_context)
    local decision=$(should_push "$priority")
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 推送决策" >> "$LOG_FILE"
    echo "  消息: $message" >> "$LOG_FILE"
    echo "  优先级: $priority" >> "$LOG_FILE"
    echo "  当前上下文: $context" >> "$LOG_FILE"
    echo "  决策: $decision" >> "$LOG_FILE"
    
    if [[ "$decision" == yes* ]]; then
        echo "✅ 立即推送: $message"
        # 调用实际推送
        # send_feishu "$message"
        return 0
    elif [[ "$decision" == delay* ]]; then
        queue_delayed_message "$message" "$priority"
        return 1
    else
        echo "❌ 当前不适合推送，已忽略"
        return 1
    fi
}

# ========== 状态报告 ==========

show_status() {
    local context=$(detect_time_context)
    local preference=$(get_push_preference "$context")
    
    echo "🧠 智能推送系统状态"
    echo "===================="
    echo "当前时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "时间上下文: $context"
    echo "推送偏好: $preference"
    echo ""
    
    if [ -f "$DELAY_QUEUE" ]; then
        local queue_size=$(wc -l < "$DELAY_QUEUE")
        echo "延迟队列: $queue_size 条消息"
    else
        echo "延迟队列: 空"
    fi
    echo ""
    
    echo "时间上下文说明:"
    echo "  - morning_prep: 早晨准备时间 (06-08)"
    echo "  - work_morning: 工作日上午 (09-11)"
    echo "  - lunch_break: 午休时间 (12-13)"
    echo "  - work_afternoon: 工作日下午 (14-17)"
    echo "  - evening_transition: 晚间过渡 (18-19)"
    echo "  - evening_leisure: 晚间休闲 (20-22)"
    echo "  - sleep: 睡眠时间 (23-05)"
    echo "  - weekend_*: 周末时间"
}

# ========== 主函数 ==========

main() {
    case "$1" in
        "status")
            show_status
            ;;
        "process-queue")
            process_delay_queue
            ;;
        "push")
            shift
            smart_push "$@"
            ;;
        "test")
            echo "测试智能推送..."
            smart_push "这是一条测试消息" "normal"
            smart_push "这是一条高优先级消息" "high"
            smart_push "这是一条紧急消息" "emergency"
            ;;
        *)
            echo "用法: $0 {status|process-queue|push|test}"
            echo ""
            echo "命令:"
            echo "  status         - 显示系统状态"
            echo "  process-queue  - 处理延迟队列"
            echo "  push 'msg' pri - 推送消息 (优先级: emergency/high/medium/normal/low)"
            echo "  test           - 测试推送"
            ;;
    esac
}

main "$@"
