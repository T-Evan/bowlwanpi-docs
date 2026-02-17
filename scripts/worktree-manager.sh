#!/bin/bash
#
# Git Worktree 并行任务管理系统
# 实现用户对话与定时任务隔离执行
#

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

WORKSPACE="/root/.openclaw/workspace"
TASKS_WORKTREE="${WORKSPACE}-tasks"
BG_WORKTREE="${WORKSPACE}-background"

log() {
    echo "[$(TZ='Asia/Shanghai' date '+%H:%M:%S')] $1" >&2
}

# ========== 初始化 Worktree ==========
init_worktrees() {
    log "🔧 初始化 Git Worktree..."
    
    cd "$WORKSPACE"
    
    # 创建任务分支和工作目录
    if [ ! -d "$TASKS_WORKTREE" ]; then
        git worktree add "$TASKS_WORKTREE" -B worktree-tasks 2>/dev/null || \
        git worktree add "$TASKS_WORKTREE" worktree-tasks
        log "✅ 创建任务 worktree: $TASKS_WORKTREE"
    fi
    
    # 创建后台任务分支和工作目录
    if [ ! -d "$BG_WORKTREE" ]; then
        git worktree add "$BG_WORKTREE" -B worktree-bg 2>/dev/null || \
        git worktree add "$BG_WORKTREE" worktree-bg
        log "✅ 创建后台 worktree: $BG_WORKTREE"
    fi
    
    # 同步主分支的最新变更
    sync_worktrees
}

# ========== 同步 Worktree ==========
sync_one_worktree() {
    local wt_path="$1"
    local wt_branch="$2"
    local wt_label="$3"
    local latest_commit="$4"

    [ -d "$wt_path" ] || return 0

    cd "$wt_path"
    git checkout "$wt_branch" >/dev/null 2>&1 || true

    # 避免覆盖未提交改动，脏目录只提示不强推同步
    if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
        log "⚠️ ${wt_label} worktree 有未提交变更，跳过同步"
        return 0
    fi

    git merge --ff-only "$latest_commit" >/dev/null 2>&1 ||     git merge "$latest_commit" --no-edit >/dev/null 2>&1 || true

    log "✅ 同步${wt_label} worktree"
}

sync_worktrees() {
    log "🔄 同步 worktree..."

    cd "$WORKSPACE"

    local latest_commit
    latest_commit=$(git rev-parse HEAD 2>/dev/null) || {
        log "❌ 无法获取主分支提交"
        return 1
    }

    sync_one_worktree "$TASKS_WORKTREE" "worktree-tasks" "任务" "$latest_commit"
    sync_one_worktree "$BG_WORKTREE" "worktree-bg" "后台" "$latest_commit"
}

# ========== 执行任务 ==========
run_in_task_worktree() {
    local task_name="$1"
    shift

    log "🎯 在任务 worktree 执行: $task_name"

    if [ ! -d "$TASKS_WORKTREE" ]; then
        init_worktrees
    else
        sync_worktrees
    fi

    cd "$TASKS_WORKTREE"

    export BOWLWANPI_WORKTREE="tasks"
    export BOWLWANPI_TASK_NAME="$task_name"

    "$@"
    local exit_code=$?

    if [ $exit_code -eq 0 ] && [ -n "$(git status --porcelain 2>/dev/null)" ]; then
        log "📝 检测到任务变更，提交到 worktree 分支"
        git add -A
        git commit -m "[worktree-tasks] $task_name - $(date '+%H:%M')" >/dev/null 2>&1 || true

        # 主分支有未提交改动时，避免强行 merge 造成冲突
        if [ -z "$(cd "$WORKSPACE" && git status --porcelain 2>/dev/null)" ]; then
            cd "$WORKSPACE"
            git merge worktree-tasks --no-edit >/dev/null 2>&1 || true
            log "✅ 变更已尝试合并到主分支"
        else
            log "⚠️ 主工作区有未提交改动，跳过自动合并"
        fi
    fi

    return $exit_code
}

# ========== 后台任务 ==========
run_in_bg_worktree() {
    local task_name="$1"
    shift

    log "🌙 在后台 worktree 执行: $task_name"

    if [ ! -d "$BG_WORKTREE" ]; then
        init_worktrees
    else
        sync_worktrees
    fi

    cd "$BG_WORKTREE"

    export BOWLWANPI_WORKTREE="background"
    export BOWLWANPI_TASK_NAME="$task_name"

    nohup "$@" > "/tmp/bowlwanpi-bg-${task_name}.log" 2>&1 &
    local pid=$!

    log "✅ 后台任务已启动 PID: $pid"
    echo "$pid" > "/tmp/bowlwanpi-bg-${task_name}.pid"

    return 0
}

# ========== 清理 Worktree ==========
cleanup_worktrees() {
    log "🧹 清理 worktree..."
    
    # 删除已合并的分支
    cd "$WORKSPACE"
    git worktree prune
    
    log "✅ Worktree 清理完成"
}

# ========== 状态检查 ==========
status() {
    log "📊 Worktree 状态:"
    
    cd "$WORKSPACE"
    git worktree list
    
    echo ""
    log "📁 目录状态:"
    echo "  主目录: $WORKSPACE"
    [ -d "$TASKS_WORKTREE" ] && echo "  ✅ 任务目录: $TASKS_WORKTREE" || echo "  ❌ 任务目录不存在"
    [ -d "$BG_WORKTREE" ] && echo "  ✅ 后台目录: $BG_WORKTREE" || echo "  ❌ 后台目录不存在"
    
    echo ""
    log "🔍 后台任务:"
    for pidfile in /tmp/bowlwanpi-bg-*.pid; do
        if [ -f "$pidfile" ]; then
            local name=$(basename "$pidfile" .pid | sed 's/bowlwanpi-bg-//')
            local pid=$(cat "$pidfile")
            if kill -0 "$pid" 2>/dev/null; then
                echo "  🟢 $name (PID: $pid) 运行中"
            else
                echo "  ⚪ $name (PID: $pid) 已结束"
                rm "$pidfile"
            fi
        fi
    done
}

# ========== 主逻辑 ==========
case "${1:-status}" in
    init)
        init_worktrees
        ;;
    sync)
        sync_worktrees
        ;;
    run-task)
        shift
        run_in_task_worktree "$@"
        ;;
    run-bg)
        shift
        run_in_bg_worktree "$@"
        ;;
    cleanup)
        cleanup_worktrees
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {init|sync|run-task <name> <cmd>|run-bg <name> <cmd>|cleanup|status}"
        exit 1
        ;;
esac
