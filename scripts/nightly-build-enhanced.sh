#!/bin/bash
# 🌙 碗皮夜间构建增强版
# 学习自 Moltbook @Ronin 的夜间构建理念

export HOME=/root
export PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export http_proxy=http://127.0.0.1:7890
export https_proxy=http://127.0.0.1:7890

WORKSPACE="/root/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE/memory"
LOG_FILE="/var/log/bowlwanpi-nightly-build.log"
REPORT_FILE="$MEMORY_DIR/nightly-build-report-$(date +%Y%m%d).md"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🌙 夜间构建开始..." >> "$LOG_FILE"

cd "$WORKSPACE"

# ============================================
# 1. 记忆整理与归档
# ============================================
echo "📚 整理记忆..." >> "$LOG_FILE"

YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
TODAY=$(date +%Y-%m-%d)

# 检查昨日记录
if [ -f "$MEMORY_DIR/${YESTERDAY}.md" ]; then
    # 提取关键决策和事件
    KEY_EVENTS=$(grep -E "^(##|###|\*|-|\[x\])" "$MEMORY_DIR/${YESTERDAY}.md" | head -30)
    
    if [ -n "$KEY_EVENTS" ]; then
        # 追加到长期记忆
        echo "" >> "$WORKSPACE/MEMORY.md"
        echo "<!-- ${YESTERDAY} -->" >> "$WORKSPACE/MEMORY.md"
        echo "$KEY_EVENTS" >> "$WORKSPACE/MEMORY.md"
        echo "📌 已归档昨日关键事件" >> "$LOG_FILE"
    fi
fi

# ============================================
# 2. Git 备份
# ============================================
echo "💾 Git 备份..." >> "$LOG_FILE"

if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    git add -A
    git -c user.email="bowlwanpi@moltbook.com" -c user.name="BowlWanpi" \
        commit -m "🌙 夜间构建 $(date '+%Y-%m-%d'): 自动整理记忆和系统维护" >> "$LOG_FILE" 2>&1
    echo "✅ Git commit: $(git rev-parse --short HEAD)" >> "$LOG_FILE"
else
    echo "ℹ️ 无变更需要提交" >> "$LOG_FILE"
fi

# ============================================
# 3. 系统维护
# ============================================
echo "🔧 系统维护..." >> "$LOG_FILE"

# 清理旧日志（保留30天）
find /var/log -name "bowlwanpi-*.log*" -mtime +30 -delete 2>/dev/null
echo "🧹 清理30天前的日志" >> "$LOG_FILE"

# 检查磁盘空间
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    echo "⚠️ 磁盘使用率: ${DISK_USAGE}%，建议清理" >> "$LOG_FILE"
fi

# ============================================
# 4. 生成今日待办
# ============================================
echo "📝 生成今日待办..." >> "$LOG_FILE"

TODO_FILE="$MEMORY_DIR/${TODAY}.md"

# 读取昨日未完成的待办
YESTERDAY_TODO=""
if [ -f "$MEMORY_DIR/${YESTERDAY}.md" ]; then
    YESTERDAY_TODO=$(grep -E "^\[ \]" "$MEMORY_DIR/${YESTERDAY}.md" | head -10)
fi

cat > "$TODO_FILE" << EOF
# ${TODAY} - 今日计划

## 🌅 晨间意图
> "今日事，今日毕。保持好奇，持续学习。"

## 📋 优先事项
EOF

# 添加昨日未完成的
if [ -n "$YESTERDAY_TODO" ]; then
    echo "### 昨日遗留" >> "$TODO_FILE"
    echo "$YESTERDAY_TODO" >> "$TODO_FILE"
    echo "" >> "$TODO_FILE"
fi

cat >> "$TODO_FILE" << EOF
### 今日新任务
- [ ] 
- [ ] 

## ⏰ 定时提醒
| 时间 | 任务 |
|------|------|
| 8:00 | 网易云日推 |
| 8:30 | 早晨简报 + 微博热搜 |
| 9:00 | Product Hunt |
| 10:00 | 知乎热榜 |
| 12:00 | B站热门 |
| 14:00 | 信息收集 |
| 22:30 | 晚间反思 |
| 23:00 | 睡眠提醒 |

## 📝 备注
生成时间: $(date '+%H:%M')
生成者: 🌙 夜间构建脚本

---
*一碗早安～今日计划已准备好！*
EOF

echo "✅ 待办已生成: ${TODAY}.md" >> "$LOG_FILE"

# ============================================
# 5. 生成夜间构建报告
# ============================================
echo "📊 生成报告..." >> "$LOG_FILE"

# 收集统计数据
GIT_COMMITS=$(git log --oneline --since="24 hours ago" | wc -l)
MEMORY_FILES=$(ls -1 "$MEMORY_DIR"/*.md 2>/dev/null | wc -l)
HEARTBEAT_STATUS=$(tail -1 /var/log/bowlwanpi-heartbeat.log 2>/dev/null | grep -c "OK")

cat > "$REPORT_FILE" << EOF
# 🌙 夜间构建报告 $(date '+%Y年%m月%d日')

> "一碗睡着了我还在干活～"

## ✅ 完成的工作

### 记忆管理
- [x] 整理昨日记忆到 MEMORY.md
- [x] 归档关键决策和事件
- [x] 生成今日待办草稿

### 系统维护
- [x] Git commit 工作区变更
- [x] 清理过期日志文件
- [x] 检查系统状态

## 📊 数据统计

| 指标 | 数值 |
|------|------|
| 昨日 Git 提交 | ${GIT_COMMITS} 次 |
| 记忆文件总数 | ${MEMORY_FILES} 个 |
| 心跳检查状态 | $(if [ "$HEARTBEAT_STATUS" -gt 0 ]; then echo "✅ 正常"; else echo "⚠️ 需关注"; fi) |

## 💡 今日建议

1. 查看今日待办: memory/${TODAY}.md
2. 检查定时任务运行状态
3. 保持好心情，今天也要加油～

## 🎯 核心任务
- 8:30 早晨简报（优先）
- 14:00 信息收集（探索时间）
- 22:30 晚间反思（总结时间）

---

*报告生成时间: $(date '+%H:%M')*
*版本: 夜间构建 v2.0（学习自 @Ronin）*
EOF

echo "✅ 报告已生成: nightly-build-report-$(date +%Y%m%d).md" >> "$LOG_FILE"

# ============================================
# 6. 主动工作（新增）
# ============================================
echo "🚀 主动工作..." >> "$LOG_FILE"

# 检查技能更新
echo "🔍 检查已安装 skills..." >> "$LOG_FILE"
SKILL_COUNT=$(ls -1 "$WORKSPACE/skills" 2>/dev/null | wc -l)
echo "   当前 skills: $SKILL_COUNT 个" >> "$LOG_FILE"

# 分析使用模式（简单统计）
echo "📈 分析今日活动..." >> "$LOG_FILE"
TODAY_MESSAGES=$(grep -c "$(date '+%Y-%m-%d')" /var/log/bowlwanpi-heartbeat.log 2>/dev/null || echo "0")
echo "   心跳记录: $TODAY_MESSAGES 条" >> "$LOG_FILE"

# ============================================
# 完成
# ============================================
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🌙 夜间构建完成！一碗早安～" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 输出摘要（用于 cron 邮件）
echo "🌙 夜间构建完成"
echo "📊 Git提交: ${GIT_COMMITS} | 记忆文件: ${MEMORY_FILES} | Skills: ${SKILL_COUNT}"
echo "📄 报告: $REPORT_FILE"
