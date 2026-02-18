#!/bin/bash
# ============================================
# 夜间自动清理脚本
# 功能：清理 health-checks、提交 git、维护系统
# 运行时间：每天凌晨 3:00
# ============================================

set -e

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="$WORKSPACE/memory/nightly-build.log"
DATE=$(date +"%Y-%m-%d %H:%M:%S")

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

# ============================================
# 1. 清理 health-checks 目录
# ============================================
cleanup_health_checks() {
    log "清理 health-checks 目录..."
    
    cd "$WORKSPACE/health-checks"
    
    # 保留最近3天
    find . -name "*.json" -mtime +3 -delete 2>/dev/null || true
    find . -name "*.md" -mtime +3 -delete 2>/dev/null || true
    
    REMAINING=$(ls -1 | wc -l)
    log "清理完成，剩余 $REMAINING 个文件"
}

# ============================================
# 2. Git 提交变更
# ============================================
git_commit() {
    log "检查 Git 状态..."
    
    cd "$WORKSPACE"
    
    # 检查是否有变更
    if git diff --quiet && git diff --staged --quiet; then
        log "没有需要提交的变更"
        return 0
    fi
    
    # 配置 git（如果未配置）
    git config user.email "bowlwanpi@bot.local" 2>/dev/null || true
    git config user.name "BowlWanpi Bot" 2>/dev/null || true
    
    # 添加所有变更
    git add -A
    
    # 提交
    COMMIT_MSG="nightly: $(date +%Y-%m-%d) 自动维护"
    git commit -m "$COMMIT_MSG" || true
    
    log "Git 提交完成: $COMMIT_MSG"
}

# ============================================
# 3. 更新 GitHub Pages 网站
# ============================================
update_website() {
    log "检查网站更新..."
    
    cd "$WORKSPACE"
    
    # 检查 docs/ 目录是否有变更
    if git diff --quiet docs/ 2>/dev/null && git diff --staged --quiet docs/ 2>/dev/null; then
        log "网站内容无变更，跳过更新"
        return 0
    fi
    
    # 更新统计数据（技能数、任务数等）
    SKILL_COUNT=$(ls -1 skills/ 2>/dev/null | wc -l)
    CRON_COUNT=$(openclaw cron list 2>/dev/null | grep -c "enabled.*true" || echo "0")
    TODAY=$(date +"%Y-%m-%d")
    
    # 更新 index.html 中的统计数据
    sed -i "s/总技能数<\/div>.*<div class=\"stat-number\">[0-9]*/总技能数<\/div>\n                <div class=\"stat-number\">$SKILL_COUNT/" docs/index.html 2>/dev/null || true
    sed -i "s/最后更新: [0-9]*/最后更新: $TODAY/" docs/index.html 2>/dev/null || true
    
    # 提交到 gh-pages 分支
    if [ -d "/tmp/bowlwanpi-docs" ]; then
        cd /tmp/bowlwanpi-docs
        git pull origin gh-pages 2>/dev/null || true
        cp "$WORKSPACE/docs/index.html" .
        git add .
        git commit -m "🌙 Nightly update: $TODAY
- Auto-sync from workspace
- Skills: $SKILL_COUNT | Tasks: $CRON_COUNT
- Updated: $(date +"%Y-%m-%d %H:%M")" 2>/dev/null || true
        git push origin gh-pages 2>/dev/null || warn "网站推送失败，请检查token"
        log "网站更新完成"
    else
        warn "网站目录不存在，跳过更新"
    fi
    
    cd "$WORKSPACE"
}

# ============================================
# 4. 创建今日记忆文件
# ============================================
create_daily_memory() {
    TODAY=$(date +"%Y-%m-%d")
    MEMORY_FILE="$WORKSPACE/memory/$TODAY.md"
    
    if [ -f "$MEMORY_FILE" ]; then
        log "今日记忆文件已存在: $TODAY.md"
        return 0
    fi
    
    cat > "$MEMORY_FILE" << EOF
# $TODAY 记忆

## 🌅 晨间意图
> "今日事，今日毕。保持好奇，持续学习，做一碗最靠谱的助手。"

## 📋 今日完成
<!-- 待填充 -->

## 📝 备注
- 记忆文件由夜间构建自动创建

---
*记录时间: $(date -u +"%Y-%m-%d %H:%M UTC")*
EOF

    log "创建今日记忆文件: $TODAY.md"
}

# ============================================
# 主程序
# ============================================
main() {
    echo "========================================" | tee -a "$LOG_FILE"
    echo "🌙 夜间构建开始 - $DATE" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"
    
    cleanup_health_checks
    git_commit
    update_website
    create_daily_memory
    
    echo "" | tee -a "$LOG_FILE"
    echo "✅ 夜间构建完成 - $(date +"%Y-%m-%d %H:%M:%S")" | tee -a "$LOG_FILE"
    echo "========================================" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

# 运行
main
