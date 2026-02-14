#!/bin/bash
#
# 🔮 预测性协助系统 v1.0
# 基于历史数据和模式预测一碗的需求
#
# 与一碗共同设计: 主动发现问题，提前准备

WORKSPACE="/root/.openclaw/workspace"
PREDICTION_DB="$WORKSPACE/.prediction_patterns.json"
LOG_FILE="/var/log/bowlwanpi-prediction.log"

# ========== 模式学习 ==========

# 记录交互模式
record_interaction() {
    local type="$1"      # query/command/preference
    local content="$2"
    local context="${3:-$(date +%H)}"  # 小时
    local weekday="$(date +%u)"
    
    # 简化内容作为模式键
    local pattern=$(echo "$content" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g' | cut -c1-20)
    
    # 更新数据库
    if [ -f "$PREDICTION_DB" ]; then
        local current=$(jq ".patterns[\"$pattern\"] // {count: 0, contexts: [], last: 0}" "$PREDICTION_DB")
        local new_count=$(echo "$current" | jq '.count + 1')
        
        jq ".patterns[\"$pattern\"] = {
            count: $new_count,
            type: \"$type\",
            contexts: (.patterns[\"$pattern\"].contexts + [\"${context}_${weekday}\"] | unique),
            last: $(date +%s)
        }" "$PREDICTION_DB" > "$PREDICTION_DB.tmp" && \
            mv "$PREDICTION_DB.tmp" "$PREDICTION_DB"
    else
        echo "{\"patterns\": {}, \"predictions\": []}" > "$PREDICTION_DB"
        record_interaction "$type" "$content" "$context"
    fi
}

# ========== 预测引擎 ==========

# 预测可能的需求
predict_needs() {
    local current_hour=$(date +%H)
    local current_weekday=$(date +%u)
    local current_context="${current_hour}_${current_weekday}"
    
    if [ ! -f "$PREDICTION_DB" ]; then
        echo "暂无历史数据"
        return 1
    fi
    
    # 查找在当前时间上下文中最频繁的模式
    local predictions=$(jq -r ".patterns | to_entries | map(select(.value.contexts | contains([\"$current_context\"]))) | sort_by(.value.count) | reverse | .[0:5] | .[] | \"\(.key):\(.value.count):\(.value.type)\"" "$PREDICTION_DB" 2>/dev/null)
    
    if [ -z "$predictions" ]; then
        echo "当前时间暂无预测模式"
        return 1
    fi
    
    echo "🔮 基于当前时间 ($current_hour:00, $(date +%A)) 的预测:"
    echo ""
    
    local i=1
    echo "$predictions" | while IFS=: read -r pattern count type; do
        # 还原模式为可读文本
        local readable=$(echo "$pattern" | sed 's/\(.\)/\1 /g' | sed 's/ $//')
        
        echo "$i. 模式: $readable"
        echo "   类型: $type"
        echo "   历史次数: $count"
        echo "   置信度: $(calculate_confidence $count)%"
        echo ""
        
        ((i++))
    done
}

# 计算置信度
calculate_confidence() {
    local count="$1"
    # 简单的置信度计算: 次数越多置信度越高，但边际递减
    if [ "$count" -lt 3 ]; then
        echo "30"
    elif [ "$count" -lt 5 ]; then
        echo "50"
    elif [ "$count" -lt 10 ]; then
        echo "70"
    else
        echo "85"
    fi
}

# ========== 主动建议 ==========

# 生成主动建议
generate_proactive_suggestions() {
    local current_hour=$(date +%H)
    local current_weekday=$(date +%u)
    
    echo "💡 主动建议 (基于时间和历史模式):"
    echo "==================================="
    echo ""
    
    # 基于时间的常规建议
    case "$current_hour" in
        08|09)
            echo "🌅 早晨时段建议:"
            echo "  - 检查今日优先事项"
            echo "  - 查看昨日未完成任务"
            echo "  - 准备早晨简报"
            ;;
        12|13)
            echo "🍽️  午休时段建议:"
            echo "  - 整理上午工作成果"
            echo "  - 规划下午任务"
            ;;
        18|19)
            echo "🌆 晚间时段建议:"
            echo "  - 总结今日完成项"
            echo "  - 准备明日计划"
            ;;
        22|23)
            echo "🌙 睡前时段建议:"
            echo "  - 查看夜间构建报告"
            echo "  - 确认无紧急待办"
            ;;
    esac
    
    echo ""
    
    # 基于历史数据的个性化建议
    if [ -f "$PREDICTION_DB" ]; then
        local frequent_queries=$(jq -r '.patterns | to_entries | map(select(.value.type == "query" and .value.count >= 3)) | sort_by(.value.count) | reverse | .[0:3] | .[] | "  - 你可能会问: \(.key) (\(.value.count)次)"' "$PREDICTION_DB" 2>/dev/null)
        
        if [ -n "$frequent_queries" ]; then
            echo "📊 基于历史行为的预测:"
            echo "$frequent_queries"
            echo ""
        fi
    fi
    
    # 基于上下文的即时建议
    generate_contextual_suggestions
}

# 基于当前上下文的建议
generate_contextual_suggestions() {
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    echo "⚡ 基于当前状态的建议:"
    
    if [ "$mem_usage" -gt 80 ]; then
        echo "  - 🔴 内存使用率较高 ($mem_usage%)，建议重启非必要服务"
    fi
    
    if [ "$disk_usage" -gt 80 ]; then
        echo "  - 🟡 磁盘使用率较高 ($disk_usage%)，建议清理日志"
    fi
    
    # 检查是否有待处理的延迟消息
    local delay_queue="$WORKSPACE/.smart_push_delay_queue.jsonl"
    if [ -f "$delay_queue" ]; then
        local queue_size=$(wc -l < "$delay_queue")
        if [ "$queue_size" -gt 0 ]; then
            echo "  - 📤 有 $queue_size 条延迟消息等待发送"
        fi
    fi
    
    # 检查安全扫描报告
    local latest_report=$(ls -t $WORKSPACE/learning/security-reports/security_scan_*.md 2>/dev/null | head -1)
    if [ -f "$latest_report" ]; then
        local report_time=$(stat -c %Y "$latest_report")
        local current_time=$(date +%s)
        local diff=$(( (current_time - report_time) / 86400 ))
        
        if [ "$diff" -gt 7 ]; then
            echo "  - 🔐 安全扫描已 $diff 天未执行，建议运行"
        fi
    fi
}

# ========== 学习一碗的偏好 ==========

learn_preference() {
    local topic="$1"
    local preference="$2"  # like/dislike/neutral
    
    if [ ! -f "$PREDICTION_DB" ]; then
        echo "{\"patterns\": {}, \"preferences\": {}}" > "$PREDICTION_DB"
    fi
    
    jq ".preferences[\"$topic\"] = \"$preference\"" "$PREDICTION_DB" > "$PREDICTION_DB.tmp" && \
        mv "$PREDICTION_DB.tmp" "$PREDICTION_DB"
    
    echo "✅ 已记录偏好: $topic → $preference"
}

# 获取一碗的偏好
get_preference() {
    local topic="$1"
    
    if [ -f "$PREDICTION_DB" ]; then
        jq -r ".preferences[\"$topic\"] // \"unknown\"" "$PREDICTION_DB"
    else
        echo "unknown"
    fi
}

# ========== 主函数 ==========

main() {
    case "$1" in
        "record")
            shift
            record_interaction "$@"
            ;;
        "predict")
            predict_needs
            ;;
        "suggest")
            generate_proactive_suggestions
            ;;
        "preference")
            shift
            learn_preference "$@"
            ;;
        "status")
            echo "🔮 预测性协助系统状态"
            echo "======================"
            if [ -f "$PREDICTION_DB" ]; then
                local pattern_count=$(jq '.patterns | length' "$PREDICTION_DB")
                local pref_count=$(jq '.preferences | length' "$PREDICTION_DB")
                echo "已学习模式: $pattern_count 个"
                echo "已记录偏好: $pref_count 项"
            else
                echo "暂无学习数据"
            fi
            ;;
        "test")
            echo "测试预测系统..."
            record_interaction "query" "查看系统状态" "14"
            record_interaction "query" "查看系统状态" "15"
            record_interaction "command" "运行安全扫描" "20"
            predict_needs
            echo ""
            generate_proactive_suggestions
            ;;
        *)
            echo "用法: $0 {record|predict|suggest|preference|status|test}"
            echo ""
            echo "命令:"
            echo "  record <type> <content> [context]  - 记录交互"
            echo "  predict                                 - 预测需求"
            echo "  suggest                                 - 生成建议"
            echo "  preference <topic> <like|dislike>     - 学习偏好"
            echo "  status                                  - 查看状态"
            echo "  test                                    - 测试系统"
            ;;
    esac
}

main "$@"
