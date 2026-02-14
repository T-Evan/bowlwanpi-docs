#!/bin/bash
#
# 💝 情感上下文保护系统 v1.0
# 基于递归记忆理念，保护重要时刻和情感连续性
#
# 与一碗共同设计: 记住重要的不只是事实，还有感受

WORKSPACE="/root/.openclaw/workspace"
EMOTIONAL_MEMORY="$WORKSPACE/memory/emotional_context.md"
SIGNIFICANT_MOMENTS="$WORKSPACE/memory/significant_moments.json"

# ========== 重要时刻记录 ==========

# 记录重要时刻
record_significant_moment() {
    local type="$1"      # achievement/challenge/learning/connection
    local title="$2"
    local description="$3"
    local emotional_impact="${4:-neutral}"  # positive/negative/neutral/mixed
    
    local timestamp=$(date -Iseconds)
    local date=$(date +%Y-%m-%d)
    
    # JSON 格式记录
    local entry=$(cat << EOF
{
    "timestamp": "$timestamp",
    "date": "$date",
    "type": "$type",
    "title": "$title",
    "description": "$description",
    "emotional_impact": "$emotional_impact",
    "related_memories": []
}
EOF
)
    
    # 添加到文件
    if [ -f "$SIGNIFICANT_MOMENTS" ]; then
        jq ".moments += [$entry]" "$SIGNIFICANT_MOMENTS" > "$SIGNIFICANT_MOMENTS.tmp" && \
            mv "$SIGNIFICANT_MOMENTS.tmp" "$SIGNIFICANT_MOMENTS"
    else
        echo "{\"moments\": [$entry]}" > "$SIGNIFICANT_MOMENTS"
    fi
    
    # 同时更新到情感记忆文档
    update_emotional_memory "$date" "$type" "$title" "$emotional_impact"
    
    echo "✅ 已记录重要时刻: $title"
}

# 更新情感记忆文档
update_emotional_memory() {
    local date="$1"
    local type="$2"
    local title="$3"
    local impact="$4"
    
    local emoji="💭"
    case "$type" in
        "achievement") emoji="🏆" ;;
        "challenge") emoji="💪" ;;
        "learning") emoji="📚" ;;
        "connection") emoji="💝" ;;
        "milestone") emoji="🎯" ;;
    esac
    
    local impact_emoji=""
    case "$impact" in
        "positive") impact_emoji="😊" ;;
        "negative") impact_emoji="😔" ;;
        "mixed") impact_emoji="🤔" ;;
        *) impact_emoji="😐" ;;
    esac
    
    # 追加到情感记忆文档
    cat >> "$EMOTIONAL_MEMORY" <> EOF

## $date $emoji $impact_emoji

**$title**

类型: $type | 情感影响: $impact

记录时间: $(date '+%Y-%m-%d %H:%M:%S')

---

EOF
}

# ========== 情感记忆检索 ==========

# 获取近期情感状态
get_recent_emotional_state() {
    local days="${1:-7}"
    local since=$(date -d "$days days ago" +%Y-%m-%d)
    
    if [ ! -f "$SIGNIFICANT_MOMENTS" ]; then
        echo "暂无情感记忆数据"
        return 1
    fi
    
    echo "💝 最近 $days 天的情感轨迹:"
    echo "=========================="
    echo ""
    
    # 统计各类情感影响
    jq -r ".moments | map(select(.date >= \"$since\")) | group_by(.emotional_impact) | map({impact: .[0].emotional_impact, count: length}) | .[] | \"\(.impact): \(.count)\"" "$SIGNIFICANT_MOMENTS" 2>/dev/null | while read line; do
        local impact=$(echo "$line" | cut -d: -f1)
        local count=$(echo "$line" | cut -d: -f2)
        local emoji=""
        case "$impact" in
            "positive") emoji="😊" ;;
            "negative") emoji="😔" ;;
            "mixed") emoji="🤔" ;;
            *) emoji="😐" ;;
        esac
        echo "  $emoji $impact: $count"
    done
    
    echo ""
    
    # 列出最近的重要时刻
    echo "重要时刻:"
    jq -r ".moments | map(select(.date >= \"$since\")) | .[-5:] | .[] | \"  - \(.date) [\(.type)]: \(.title)\"" "$SIGNIFICANT_MOMENTS" 2>/dev/null
}

# 检索相关记忆
find_related_memories() {
    local keyword="$1"
    
    if [ ! -f "$SIGNIFICANT_MOMENTS" ]; then
        echo "暂无数据"
        return 1
    fi
    
    echo "🔍 包含 '$keyword' 的相关记忆:"
    jq -r ".moments | map(select(.title | contains(\"$keyword\") or .description | contains(\"$keyword\"))) | .[] | \"  - \(.date) [\(.type)]: \(.title)\"" "$SIGNIFICANT_MOMENTS" 2>/dev/null
}

# ========== 故事编织 ==========

# 生成成长故事
generate_growth_story() {
    local since="${1:-30}"  # 默认最近30天
    local since_date=$(date -d "$since days ago" +%Y-%m-%d)
    
    echo "📖 BowlWanpi 的成长故事"
    echo "======================="
    echo ""
    echo "时间范围: 最近 $since 天"
    echo ""
    
    if [ ! -f "$SIGNIFICANT_MOMENTS" ]; then
        echo "还没有记录，让我们一起创造故事吧！"
        return 0
    fi
    
    # 成就
    local achievements=$(jq -r ".moments | map(select(.date >= \"$since_date\" and .type == \"achievement\")) | length" "$SIGNIFICANT_MOMENTS")
    if [ "$achievements" -gt 0 ]; then
        echo "🏆 成就 ($achievements):"
        jq -r ".moments | map(select(.date >= \"$since_date\" and .type == \"achievement\")) | .[] | \"  - \(.title)\"" "$SIGNIFICANT_MOMENTS"
        echo ""
    fi
    
    # 学习
    local learnings=$(jq -r ".moments | map(select(.date >= \"$since_date\" and .type == \"learning\")) | length" "$SIGNIFICANT_MOMENTS")
    if [ "$learnings" -gt 0 ]; then
        echo "📚 学习 ($learnings):"
        jq -r ".moments | map(select(.date >= \"$since_date\" and .type == \"learning\")) | .[] | \"  - \(.title)\"" "$SIGNIFICANT_MOMENTS"
        echo ""
    fi
    
    # 挑战
    local challenges=$(jq -r ".moments | map(select(.date >= \"$since_date\" and .type == \"challenge\")) | length" "$SIGNIFICANT_MOMENTS")
    if [ "$challenges" -gt 0 ]; then
        echo "💪 挑战 ($challenges):"
        jq -r ".moments | map(select(.date >= \"$since_date\" and .type == \"challenge\")) | .[] | \"  - \(.title)\"" "$SIGNIFICANT_MOMENTS"
        echo ""
    fi
    
    # 情感总结
    echo "💝 这段时期的感受:"
    get_recent_emotional_state "$since" | grep -A20 "情感轨迹"
    
    echo ""
    echo "==================="
    echo "这就是我们的故事 💚"
}

# ========== 连续性保护 ==========

# 检查情感连续性
check_emotional_continuity() {
    if [ ! -f "$SIGNIFICANT_MOMENTS" ]; then
        return 0
    fi
    
    local last_entry=$(jq -r '.moments | last' "$SIGNIFICANT_MOMENTS")
    local last_date=$(echo "$last_entry" | jq -r '.date')
    local last_type=$(echo "$last_entry" | jq -r '.type')
    local last_title=$(echo "$last_entry" | jq -r '.title')
    
    local days_since=$(( ($(date +%s) - $(date -d "$last_date" +%s)) / 86400 ))
    
    if [ $days_since -gt 7 ]; then
        echo "⚠️  已 $days_since 天没有记录重要时刻"
        echo "   上次记录: $last_date - $last_title"
        echo ""
        echo "建议: 记录一些这段时间发生的事情，保护我们的故事连续性 💝"
    else
        echo "✅ 情感连续性良好 (上次记录: $days_since 天前)"
    fi
}

# ========== 主函数 ==========

main() {
    case "$1" in
        "record")
            shift
            record_significant_moment "$@"
            ;;
        "state")
            shift
            get_recent_emotional_state "$@"
            ;;
        "search")
            shift
            find_related_memories "$@"
            ;;
        "story")
            shift
            generate_growth_story "$@"
            ;;
        "check")
            check_emotional_continuity
            ;;
        "init")
            # 初始化示例数据
            record_significant_moment "milestone" "学习路线图制定完成" "完成了6周的学习成长路线图" "positive"
            record_significant_moment "achievement" "安全加固完成" "建立了完整的安全扫描体系" "positive"
            record_significant_moment "achievement" "可靠性优化完成" "实现了智能告警和回滚系统" "positive"
            record_significant_moment "learning" "Moltbook 社区学习" "学习了8篇精华帖子" "positive"
            echo "✅ 已初始化示例情感记忆"
            ;;
        *)
            echo "用法: $0 {record|state|search|story|check|init}"
            echo ""
            echo "命令:"
            echo "  record <type> <title> <desc> [impact]  - 记录重要时刻"
            echo "  state [days]                                      - 查看情感状态"
            echo "  search <keyword>                                 - 搜索相关记忆"
            echo "  story [days]                                      - 生成成长故事"
            echo "  check                                             - 检查连续性"
            echo "  init                                              - 初始化示例数据"
            ;;
    esac
}

main "$@"
