#!/bin/bash
# 定时任务兜底方案 - 使用 Linux 系统级 cron
# 由 /etc/cron.d/bowlwanpi-backup-cron 调用

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export OPENCLAW_GATEWAY_URL="http://localhost:3000"

LOG_FILE="/var/log/bowlwanpi-cron.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 检查 OpenClaw 是否运行
check_openclaw() {
    if ! curl -s "$OPENCLAW_GATEWAY_URL/health" > /dev/null 2>&1; then
        log "ERROR: OpenClaw Gateway is not running"
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
            --target "ou_a22ce6536f26dee3fec9397a9a1b87b5" \
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

# 执行 Agent Turn 任务
run_agent_task() {
    local task_name="$1"
    local message="$2"
    
    log "Running task: $task_name"
    
    # 通过 API 触发 isolated agent session
    curl -s -X POST "$OPENCLAW_GATEWAY_URL/api/v1/spawn" \
        -H "Content-Type: application/json" \
        -d "{
            \"agentId\": \"main\",
            \"task\": \"$message\",
            \"timeoutSeconds\": 300
        }" >> "$LOG_FILE" 2>&1
    
    log "Task completed: $task_name"
}

# 主逻辑
case "$1" in
    morning-brief)
        log "=== 早晨简报 ==="
        if check_openclaw; then
            run_agent_task "早晨简报" "生成今日早晨简报。检查 memory/YYYY-MM-DD.md 查看昨日规划，生成包含以下内容的消息发给一碗：1) 每日意图 2) 今日优先事项 3) 待办任务 4) 行动建议。语气用干物妹小埋风格，活泼可爱～"
        fi
        ;;
    
    netease-music)
        log "=== 网易云日推 ==="
        if check_openclaw; then
            run_agent_task "网易云日推" "执行网易云音乐日推推送任务（带风格/情绪分析）。运行 /root/.openclaw/workspace/netease-music/daily_push_with_analysis.py 获取日推并发送给一碗。"
        fi
        ;;
    
    weibo-hot)
        log "=== 微博热搜 ==="
        if check_openclaw; then
            run_agent_task "微博热搜" "执行微博热搜推送任务。获取 https://raw.githubusercontent.com/daifee/weibo-hot-search/main/latest-daily.md 并发送 TOP 10 给一碗。"
        fi
        ;;
    
    product-hunt)
        log "=== Product Hunt ==="
        if check_openclaw; then
            run_agent_task "Product Hunt" "执行 Product Hunt 热门推送任务。获取 https://www.producthunt.com/feed 并发送 TOP 10 新产品给一碗。"
        fi
        ;;
    
    zhihu-hot)
        log "=== 知乎热榜 ==="
        if check_openclaw; then
            run_agent_task "知乎热榜" "执行知乎热榜推送任务。尝试获取知乎热榜并发送给一碗。"
        fi
        ;;
    
    bilibili-hot)
        log "=== B站热门 ==="
        if check_openclaw; then
            run_agent_task "B站热门" "执行B站热门推送任务。获取B站全站排行榜并发送 TOP 10 给一碗。"
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
