#!/bin/bash
#
# 夜间构建 v4.0 - 三层次记忆提炼
# 从每日日志提取关键决策、约定、学习到 MEMORY.md
#

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

WORKSPACE="/root/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE/memory"
LOG_FILE="/var/log/bowlwanpi-nightly-build.log"

log() {
    echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ========== 1. 整理昨日记忆到 MEMORY.md ==========
extract_to_memory() {
    log "📚 提炼昨日记忆到 MEMORY.md..."
    
    YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
    YESTERDAY_FILE="$MEMORY_DIR/${YESTERDAY}.md"
    MEMORY_FILE="$MEMORY_DIR/MEMORY.md"
    
    if [ ! -f "$YESTERDAY_FILE" ]; then
        log "⚠️  昨日记忆文件不存在: $YESTERDAY_FILE"
        return 1
    fi
    
    # 提取关键部分
    echo "" >> "$MEMORY_FILE"
    echo "<!-- $YESTERDAY -->" >> "$MEMORY_FILE"
    echo "" >> "$MEMORY_FILE"
    echo "## $YESTERDAY 重要记录" >> "$MEMORY_FILE"
    echo "" >> "$MEMORY_FILE"
    
    # 提取包含特定关键词的行
    grep -E "^(##|\*\*约定|✅|❌|⚠️|💡|🎯|🔧|📋|📝|🛠️)" "$YESTERDAY_FILE" | head -50 >> "$MEMORY_FILE" 2>/dev/null || true
    
    # 提取关键决策（包含"决定"、"约定"、"配置"的行）
    grep -iE "(决定|约定|配置|修复|完成|优化|更新|部署|提交|新增)" "$YESTERDAY_FILE" | grep -v "^#" | head -30 >> "$MEMORY_FILE" 2>/dev/null || true
    
    log "✅ 已提炼昨日关键记录到 MEMORY.md"
    return 0
}

# ========== 2. 生成今日待办 ==========
 generate_today_todo() {
    log "📝 生成今日待办..."
    
    TODAY=$(date +%Y-%m-%d)
    TODO_FILE="$MEMORY_DIR/${TODAY}.md"
    
    # 检查任务队列
    TASK_QUEUE="$MEMORY_DIR/task-queue.json"
    PENDING_TASKS=""
    
    if [ -f "$TASK_QUEUE" ]; then
        PENDING_TASKS=$(python3 -c "
import json
try:
    with open('$TASK_QUEUE', 'r') as f:
        data = json.load(f)
    tasks = [t for t in data.get('tasks', []) if t.get('status') == 'pending']
    for t in tasks[:5]:
        print(f\"- [ ] {t.get('content', 'Unknown')[:60]}\")
except:
    pass
" 2>/dev/null)
    fi
    
    cat > "$TODO_FILE" << EOF
# $TODAY - 今日待办

## 🎯 优先事项
${PENDING_TASKS:-"- [ ] 检查昨日未完成事项\n- [ ] 查看系统状态"}

## ⏰ 定时任务
- 8:00 网易云日推
- 8:30 早晨简报 + 微博热搜
- 9:00 Product Hunt
- 10:00 知乎热榜
- 12:00 B站热门
- 14:00 信息收集
- 22:30 晚间反思
- 23:00 睡眠提醒

## 📝 备注
由夜间构建自动生成于 $(date '+%H:%M')

---

EOF
    
    log "✅ 今日待办已生成: $TODO_FILE"
}

# ========== 3. 更新 NOW.md ==========
update_now() {
    log "🔄 更新 NOW.md..."
    
    if [ -f "$WORKSPACE/scripts/update_now_md.py" ]; then
        python3 "$WORKSPACE/scripts/update_now_md.py" >> "$LOG_FILE" 2>&1
        log "✅ NOW.md 已更新"
    else
        log "⚠️  update_now_md.py 不存在"
    fi
}

# ========== 4. Git 提交变更 ==========
git_commit() {
    log "💾 Git 提交变更..."
    
    cd "$WORKSPACE"
    
    if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
        git add -A
        git -c user.email="bowlwanpi@moltbook.com" -c user.name="BowlWanpi" \
            commit -m "🌙 夜间构建: $(date '+%Y-%m-%d') 自动整理记忆和变更" >> "$LOG_FILE" 2>&1
        log "✅ Git commit 完成"
    else
        log "ℹ️  无变更需要提交"
    fi
}

# ========== 5. 清理旧日志 ==========
cleanup_logs() {
    log "🧹 清理旧日志..."
    
    # 保留最近30天的日志
    find /var/log -name "bowlwanpi-*.log*" -mtime +30 -delete 2>/dev/null || true
    
    # 清理健康检查旧文件
    find "$WORKSPACE/health-checks" -name "*.json" -mtime +7 -delete 2>/dev/null || true
    find "$WORKSPACE/health-checks" -name "*.md" -mtime +7 -delete 2>/dev/null || true
    
    log "✅ 日志清理完成"
}

# ========== 主逻辑 ==========
main() {
    log "🌙 ========== 夜间构建 v4.0 开始 =========="
    
    extract_to_memory
    generate_today_todo
    update_now
    git_commit
    cleanup_logs
    
    log "🌙 ========== 夜间构建完成 =========="
    log "💤 晚安，一碗～"
}

main "$@"
