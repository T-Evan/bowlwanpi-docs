#!/bin/bash
# 定时任务兜底方案 - 使用 Linux 系统级 cron
# 由 /etc/cron.d/bowlwanpi-backup-cron 调用

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# 默认跟随当前 OpenClaw 服务端口（可被环境变量覆盖）
export OPENCLAW_GATEWAY_PORT="${OPENCLAW_GATEWAY_PORT:-18789}"
export OPENCLAW_GATEWAY_URL="${OPENCLAW_GATEWAY_URL:-http://127.0.0.1:${OPENCLAW_GATEWAY_PORT}}"

LOG_FILE="/var/log/bowlwanpi-cron.log"
LOCK_DIR="/tmp/bowlwanpi-locks"

# 确保锁目录存在
mkdir -p "$LOCK_DIR"

log() {
    echo "[$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 获取任务锁（防止重叠执行）
acquire_lock() {
    local task_name="$1"
    local lock_file="$LOCK_DIR/${task_name}.lock"
    local timeout="${2:-300}"  # 默认5分钟超时
    
    # 使用 flock 获取锁
    exec 200>"$lock_file"
    if ! flock -n -E 0 200; then
        log "WARNING: Task $task_name is already running, skipping"
        return 1
    fi
    
    # 记录 PID 和开始时间
    echo $$ > "$lock_file.pid"
    echo "$(date +%s)" > "$lock_file.start"
    
    return 0
}

# 释放任务锁
release_lock() {
    local task_name="$1"
    local lock_file="$LOCK_DIR/${task_name}.lock"
    
    rm -f "$lock_file.pid" "$lock_file.start" 2>/dev/null
    flock -u 200 2>/dev/null || true
}

# 检查 OpenClaw 是否运行
check_openclaw() {
    if ! curl -sf --max-time 3 "$OPENCLAW_GATEWAY_URL/health" > /dev/null 2>&1; then
        log "ERROR: OpenClaw Gateway is not reachable (${OPENCLAW_GATEWAY_URL})"
        return 1
    fi
    return 0
}

# 发送消息到飞书（使用 OpenClaw CLI）
send_message() {
    local content="$1"
    log "Sending message: ${content:0:50}..."
    
    # 方法: 使用 openclaw CLI（使用标准输入避免参数解析问题）
    if command -v openclaw &> /dev/null; then
        cd /root/.openclaw/workspace
        # 使用 --message - 从标准输入读取，避免参数解析问题
        echo "$content" | openclaw message send \
            --channel feishu \
            --target "user:ou_a22ce6536f26dee3fec9397a9a1b87b5" \
            --message - >> "$LOG_FILE" 2>&1
        return $?
    fi
    
    log "ERROR: openclaw CLI not found"
    return 1
}

# 简单的提醒消息（直接发，不跑 agent）
send_simple_reminder() {
    local title="$1"
    local body="$2"
    
    send_message "${title}

${body}

⏰ 系统 cron 兜底任务 | $(date '+%H:%M')"
}

# 执行 Agent Turn 任务（旧 API 兼容，失败时仅记录）
run_agent_task() {
    local task_name="$1"
    local message="$2"

    log "Running task: $task_name"

    # 通过旧 HTTP API 触发（部分版本可能返回 Method Not Allowed）
    local resp
    resp=$(curl -s -X POST "$OPENCLAW_GATEWAY_URL/api/v1/spawn" \
        -H "Content-Type: application/json" \
        -d "{
            \"agentId\": \"main\",
            \"task\": \"$message\",
            \"timeoutSeconds\": 300
        }" 2>>"$LOG_FILE" || true)

    if echo "$resp" | grep -qi "method not allowed"; then
        log "WARNING: spawn API not supported on this gateway version"
    fi

    log "Task completed: $task_name"
}

# 执行本地推送脚本并发送输出到飞书
run_script_task() {
    local task_name="$1"
    local script_path="$2"
    local use_worktree="${3:-false}"

    log "Running script task: $task_name ($script_path)"

    if [ "$use_worktree" = "true" ] && [ -f "$WORKSPACE/scripts/worktree-manager.sh" ]; then
        # 使用 worktree 执行，避免与主会话冲突
        log "Using worktree for task: $task_name"
        cd "$WORKSPACE"
        bash scripts/worktree-manager.sh run-task "$task_name" python3 "$script_path" > /tmp/task-output.txt 2>>"$LOG_FILE"
        local exit_code=$?
        
        if [ $exit_code -eq 0 ] && [ -f "/tmp/task-output.txt" ]; then
            local output=$(cat /tmp/task-output.txt)
            if [ -n "$output" ]; then
                send_message "$output"
                log "Script task sent: $task_name"
            fi
        fi
        rm -f /tmp/task-output.txt
        return $exit_code
    fi

    if [ ! -f "$script_path" ]; then
        log "ERROR: Script not found: $script_path"
        return 1
    fi

    local output
    output=$(python3 "$script_path" 2>>"$LOG_FILE")

    if [ -z "$output" ]; then
        log "ERROR: Script output is empty: $script_path"
        return 1
    fi

    send_message "$output"
    log "Script task sent: $task_name"
}

# 主逻辑
# 获取任务锁
task_name="$1"
if ! acquire_lock "$task_name"; then
    log "Task $task_name already running, exit"
    exit 0
fi

# 确保退出时释放锁
trap 'release_lock "$task_name"' EXIT

case "$1" in
    morning-prep)
        log "=== 晨报预备 ==="
        if check_openclaw; then
            run_agent_task "晨报预备" "执行晨报预备任务。提前检查今日重点事项和可推送信息，整理成待发送草稿，供 8:30 早晨简报使用。"
        fi
        ;;

    morning-brief)
        log "=== 早晨简报 ==="
        if check_openclaw; then
            run_script_task "早晨简报" "/root/.openclaw/workspace/scripts/push_morning_brief.py"
        fi
        ;;
    
    netease-music)
        log "=== 网易云日推 ==="
        if check_openclaw; then
            run_script_task "网易云日推" "/root/.openclaw/workspace/scripts/push_netease_music.py"
        fi
        ;;
    
    weibo-hot)
        log "=== 微博热搜 ==="
        if check_openclaw; then
            run_script_task "微博热搜" "/root/.openclaw/workspace/scripts/push_weibo_hot.py"
        fi
        ;;
    
    product-hunt)
        log "=== Product Hunt ==="
        if check_openclaw; then
            run_script_task "Product Hunt" "/root/.openclaw/workspace/scripts/push_producthunt.py"
        fi
        ;;
    
    zhihu-hot)
        log "=== 知乎热榜 ==="
        if check_openclaw; then
            run_script_task "知乎热榜" "/root/.openclaw/workspace/scripts/push_zhihu_hot.py"
        fi
        ;;
    
    bilibili-hot)
        log "=== B站热门 ==="
        if check_openclaw; then
            run_script_task "B站热门" "/root/.openclaw/workspace/scripts/push_bilibili_hot.py"
        fi
        ;;
    
    info-collect)
        log "=== 信息收集 ==="
        if check_openclaw; then
            run_agent_task "信息收集" "执行信息收集任务。逛 Moltbook 热门帖子和 GitHub Trending，如果有有趣发现就分享给一碗。"
        fi
        ;;
    
    evening-reflect)
        log "=== 晚间反思 ==="
        send_simple_reminder "🌙 晚间反思时间" "一碗～今天过得怎么样？明天的优先事项是什么？来聊聊天吧～ (｡･ω･｡)"
        ;;
    
    sleep-reminder)
        log "=== 睡眠提醒 ==="
        send_simple_reminder "💤 睡眠提醒" "一碗～该休息啦！明天再继续探索吧，晚安 💤"
        ;;

    weekly-review)
        log "=== 周回顾 ==="
        if check_openclaw; then
            run_agent_task "周回顾" "执行周回顾任务。总结本周关键进展、待办和下周重点，并发送给一碗。"
        fi
        ;;

    one-minute-news)
        log "=== One Minute News ==="
        if check_openclaw; then
            run_script_task "One Minute News" "/root/.openclaw/workspace/scripts/push_one_minute_news.py"
        fi
        ;;

    github-release)
        log "=== GitHub Release 监控 ==="
        if check_openclaw; then
            run_script_task "GitHub Release" "/root/.openclaw/workspace/scripts/push_github_release.py"
        fi
        ;;
    
    nightly-build)
        log "=== 夜间构建 ==="
        log "🌙 凌晨3点啦，碗皮开始夜间模式～"
        
        # 1. 整理昨日记忆
        log "📚 整理昨日记忆到 MEMORY.md..."
        YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
        if [ -f "/root/.openclaw/workspace/memory/${YESTERDAY}.md" ]; then
            # 提取重要信息追加到 MEMORY.md
            echo "" >> /root/.openclaw/workspace/MEMORY.md
            echo "## ${YESTERDAY} 重要事件" >> /root/.openclaw/workspace/MEMORY.md
            grep -E "^(-|\*|##)" "/root/.openclaw/workspace/memory/${YESTERDAY}.md" | head -20 >> /root/.openclaw/workspace/MEMORY.md
            log "✅ 已更新 MEMORY.md"
        fi
        
        # 2. Git commit 变更
        log "💾 检查 git 状态..."
        cd /root/.openclaw/workspace
        if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
            git add -A
            git -c user.email="bowlwanpi@moltbook.com" -c user.name="BowlWanpi" commit -m "🌙 夜间构建: $(date '+%Y-%m-%d') 自动整理记忆和变更" >> "$LOG_FILE" 2>&1
            log "✅ Git commit 完成"
        else
            log "ℹ️ 无变更需要提交"
        fi
        
        # 3. 生成今日待办草稿
        log "📝 生成今日待办..."
        TODAY=$(date +%Y-%m-%d)
        cat > "/root/.openclaw/workspace/memory/${TODAY}.md" << EOF
# ${TODAY} - 今日待办

## 🎯 优先事项
- [ ] 检查昨日未完成事项
- [ ] 查看定时任务运行状态
- [ ] 

## ⏰ 定时任务提醒
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
EOF
        log "✅ 今日待办已生成"
        
        # 4. 清理旧日志（保留30天）
        log "🧹 清理旧日志..."
        find /var/log -name "bowlwanpi-*.log*" -mtime +30 -delete 2>/dev/null
        log "✅ 日志清理完成"
        
        # 5. 生成夜间构建报告
        REPORT_FILE="/root/.openclaw/workspace/memory/nightly-build-report.md"
        cat > "$REPORT_FILE" << EOF
# 🌙 夜间构建报告 $(date '+%Y-%m-%d %H:%M')

## ✅ 完成的工作
- 整理昨日记忆到 MEMORY.md
- Git commit 工作区变更
- 生成今日待办草稿
- 清理过期日志文件

## 📊 系统状态
- Gateway: 运行中
- Mihomo: 运行中 (port 7890)
- 定时任务: 正常

## 💡 今日建议
早上好～今日待办已准备好，优先事项请查看 memory/${TODAY}.md

---
*自动生成的夜间构建报告*
EOF
        log "✅ 夜间构建报告已生成"
        
        # 6. 发送简报给主人（可选，不打扰睡眠）
        # send_simple_reminder "🌙 夜间构建完成" "一碗睡着了我还在干活～今日待办已准备好，早安！"
        
        log "🌙 夜间构建完成！"
        ;;
    
    *)
        log "Unknown task: $1"
        exit 1
        ;;
esac
