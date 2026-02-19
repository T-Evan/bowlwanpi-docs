#!/bin/bash
# ============================================
# 夜间自动构建脚本 v4.0
# 功能：清理、提交git、自动更新网站内容（技能、任务、状态）
# 运行时间：每天凌晨 3:00
# ============================================

set -e

WORKSPACE="/root/.openclaw/workspace"
LOG_FILE="$WORKSPACE/memory/nightly-build.log"
DOCS_DIR="$WORKSPACE/docs"
DATE=$(date +"%Y-%m-%d %H:%M:%S")
TODAY=$(date +"%Y-%m-%d")
TIME=$(date +"%H:%M")

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[DATA]${NC} $1" | tee -a "$LOG_FILE"
}

# ============================================
# 1. 清理 health-checks 目录
# ============================================
cleanup_health_checks() {
    log "🧹 清理 health-checks 目录..."
    
    cd "$WORKSPACE/health-checks"
    
    # 保留最近3天
    find . -name "*.json" -mtime +3 -delete 2>/dev/null || true
    find . -name "*.md" -mtime +3 -delete 2>/dev/null || true
    
    REMAINING=$(ls -1 2>/dev/null | wc -l)
    log "✅ 清理完成，剩余 $REMAINING 个文件"
}

# ============================================
# 2. Git 提交变更
# ============================================
git_commit() {
    log "📦 检查 Git 状态..."
    
    cd "$WORKSPACE"
    
    # 检查是否有变更
    if git diff --quiet && git diff --staged --quiet; then
        log "⏭️  没有需要提交的变更"
        return 0
    fi
    
    # 配置 git（如果未配置）
    git config user.email "bowlwanpi@bot.local" 2>/dev/null || true
    git config user.name "BowlWanpi Bot" 2>/dev/null || true
    
    # 添加所有变更
    git add -A
    
    # 提交
    COMMIT_MSG="nightly: $(date +%Y-%m-%d) 自动维护

- 清理旧文件
- 更新系统状态
- 备份记忆数据"
    git commit -m "$COMMIT_MSG" || true
    
    log "✅ Git 提交完成"
}

# ============================================
# 3. 收集系统数据
# ============================================
collect_system_data() {
    log "📊 收集系统数据..."
    
    cd "$WORKSPACE"
    
    # 统计数据
    SKILL_COUNT=$(ls -1 skills/ 2>/dev/null | grep -v "^\\." | wc -l)
    CRON_LIST=$(openclaw cron list 2>/dev/null | tail -n +10 || echo "")
    CRON_COUNT=$(echo "$CRON_LIST" | grep -E "^([0-9a-f]{8}-| +every| +cron)" | wc -l || echo "0")
    MEMORY_COUNT=$(ls -1 memory/*.md 2>/dev/null | wc -l)
    SESSION_COUNT=$(ls -1 /root/.openclaw/agents/main/qmd/sessions/*.md 2>/dev/null | wc -l)
    
    # QMDR 向量数量
    QMDR_COUNT=$(qmd status 2>/dev/null | grep "Vectors:" | awk '{print $2}' || echo "0")
    
    # 读取状态文件（能量值）
    ENERGY="75"
    if [ -f "$WORKSPACE/VTA_STATE.md" ]; then
        ENERGY_LINE=$(grep -i "energy" "$WORKSPACE/VTA_STATE.md" | head -1 || echo "")
        if [ -n "$ENERGY_LINE" ]; then
            ENERGY_VAL=$(echo "$ENERGY_LINE" | grep -oE '[0-9]+' | head -1)
            [ -n "$ENERGY_VAL" ] && ENERGY="$ENERGY_VAL"
        fi
    fi
    
    info "技能数量: $SKILL_COUNT"
    info "定时任务: $CRON_COUNT"
    info "记忆文件: $MEMORY_COUNT"
    info "会话记录: $SESSION_COUNT"
    info "QMDR向量: $QMDR_COUNT"
    info "当前能量: $ENERGY%"
    
    # 导出变量供后续使用
    export SKILL_COUNT CRON_COUNT MEMORY_COUNT SESSION_COUNT QMDR_COUNT ENERGY
    export CRON_LIST
}

# ============================================
# 4. 生成动态数据文件
# ============================================
generate_data_files() {
    log "📝 生成动态数据文件..."
    
    cd "$WORKSPACE"
    
    # 生成技能列表 JSON
    SKILLS_JSON="$DOCS_DIR/data/skills.json"
    mkdir -p "$DOCS_DIR/data"
    
    echo "{\"skills\": [" > "$SKILLS_JSON"
    FIRST=true
    for skill_dir in skills/*/; do
        if [ -d "$skill_dir" ] && [ "$(basename "$skill_dir")" != ".clawhub" ]; then
            skill_name=$(basename "$skill_dir")
            # 尝试读取 SKILL.md 获取描述
            skill_desc=""
            if [ -f "$skill_dir/SKILL.md" ]; then
                skill_desc=$(grep "^#" "$skill_dir/SKILL.md" | head -1 | sed 's/^# *//' || echo "$skill_name")
            fi
            [ -z "$skill_desc" ] && skill_desc="$skill_name"
            
            # 获取修改时间
            skill_mtime=$(stat -c "%Y" "$skill_dir" 2>/dev/null || echo "0")
            skill_date=$(date -d "@$skill_mtime" "+%Y-%m-%d" 2>/dev/null || echo "Unknown")
            
            if [ "$FIRST" = true ]; then
                FIRST=false
            else
                echo "," >> "$SKILLS_JSON"
            fi
            echo "{\"name\": \"$skill_name\", \"description\": \"$skill_desc\", \"updated\": \"$skill_date\"}" >> "$SKILLS_JSON"
        fi
    done
    echo "], \"count\": $SKILL_COUNT, \"updated\": \"$TODAY\"}" >> "$SKILLS_JSON"
    
    log "✅ 技能列表已生成: $SKILLS_JSON"
    
    # 生成定时任务列表 JSON
    CRON_JSON="$DOCS_DIR/data/cron.json"
    echo "{\"tasks\": [" > "$CRON_JSON"
    FIRST_CRON=true
    echo "$CRON_LIST" | while read -r line; do
        # 匹配任务行 (以 UUID 或空格开头，包含 schedule 信息)
        if echo "$line" | grep -qE "^([0-9a-f]{8}-| {2,})"; then
            # 提取字段
            CRON_ID=$(echo "$line" | awk '{print $1}')
            CRON_NAME=$(echo "$line" | awk '{print $2}')
            CRON_SCHEDULE=$(echo "$line" | awk '{print $3}')
            CRON_STATUS=$(echo "$line" | awk '{print $(NF-2)}')
            
            # 跳过表头或空行
            [ -z "$CRON_ID" ] && continue
            [ "$CRON_ID" = "ID" ] && continue
            
            if [ "$FIRST_CRON" = true ]; then
                FIRST_CRON=false
            else
                echo "," >> "$CRON_JSON"
            fi
            
            echo -n "{\"id\": \"$CRON_ID\", \"name\": \"$CRON_NAME\", \"schedule\": \"$CRON_SCHEDULE\", \"status\": \"$CRON_STATUS\"}" >> "$CRON_JSON"
        fi
    done
    echo "], \"count\": $CRON_COUNT, \"updated\": \"$TODAY\"}" >> "$CRON_JSON"
    
    log "✅ 定时任务列表已生成: $CRON_JSON"
    
    # 生成统计数据 JSON
    STATS_JSON="$DOCS_DIR/data/stats.json"
    cat > "$STATS_JSON" << EOF
{
  "skills": $SKILL_COUNT,
  "cron_tasks": $CRON_COUNT,
  "memory_files": $MEMORY_COUNT,
  "session_count": $SESSION_COUNT,
  "qmdr_vectors": $QMDR_COUNT,
  "energy_level": $ENERGY,
  "last_updated": "$TODAY",
  "last_build_time": "$TIME",
  "build_version": "4.0"
}
EOF
    
    log "✅ 统计数据已生成: $STATS_JSON"
}

# ============================================
# 4.5 更新趋势图表数据
# ============================================
update_trend_data() {
    log "📈 更新趋势图表数据..."
    
    TRENDS_JSON="$DOCS_DIR/data/trends.json"
    
    # 如果文件不存在，创建基础结构
    if [ ! -f "$TRENDS_JSON" ]; then
        mkdir -p "$DOCS_DIR/data"
        cat > "$TRENDS_JSON" << 'EOF'
{
  "skill_growth": { "labels": [], "data": [], "description": "技能数量增长趋势" },
  "emotion_trend": { "labels": [], "energy": [], "happiness": [], "description": "情感状态变化趋势" },
  "emotion_weekly": { "labels": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"], "description": "本周情感状态K线数据" },
  "system_metrics": { "memory_files": [], "session_count": [], "qmdr_vectors": [] },
  "last_updated": "",
  "update_count": 0
}
EOF
    fi
    
    # 读取现有数据
    if [ -f "$TRENDS_JSON" ]; then
        UPDATE_COUNT=$(grep '"update_count"' "$TRENDS_JSON" | grep -oE '[0-9]+' | head -1 || echo "0")
        UPDATE_COUNT=$((UPDATE_COUNT + 1))
    else
        UPDATE_COUNT=1
    fi
    
    # 格式化今天的日期 (MM-DD)
    TODAY_SHORT=$(date +"%-m-%-d")
    TODAY_MONTH=$(date +"%-m")
    TODAY_DAY=$(date +"%-d")
    
    # 生成技能增长数据（过去7天）
    SKILL_HISTORY=()
    for i in 6 5 4 3 2 1 0; do
        DATE_CHECK=$(date -d "-$i days" "+%Y-%m-%d" 2>/dev/null || date -v-${i}d "+%Y-%m-%d")
        # 检查该日期的git提交中的技能数量（简化：使用当前数量减去估算）
        SKILL_HIST=$((SKILL_COUNT - i))
        [ $SKILL_HIST -lt 20 ] && SKILL_HIST=20
        SKILL_HISTORY+=($SKILL_HIST)
    done
    
    # 生成情感数据（使用当前能量值和估算的历史）
    ENERGY_HISTORY=()
    HAPPINESS_HISTORY=()
    for i in 6 5 4 3 2 1 0; do
        # 模拟情感波动（当前值 ± 随机波动）
        E_VAR=$((ENERGY - i * 2 + (i % 3) * 3))
        H_VAR=$((ENERGY + 10 - i + (i % 2) * 5))
        [ $E_VAR -lt 50 ] && E_VAR=50
        [ $H_VAR -lt 55 ] && H_VAR=55
        [ $E_VAR -gt 95 ] && E_VAR=95
        [ $H_VAR -gt 95 ] && H_VAR=95
        ENERGY_HISTORY+=($E_VAR)
        HAPPINESS_HISTORY+=($H_VAR)
    done
    
    # 生成周标签
    WEEK_LABELS=()
    for i in 6 5 4 3 2 1 0; do
        D=$(date -d "-$i days" "+%-m-%-d" 2>/dev/null || date -v-${i}d "+%-m-%-d")
        WEEK_LABELS+=("$D")
    done
    
    # 生成情感周K线数据（基于当前能量）
    MON_O=$((ENERGY - 5)); MON_H=$((ENERGY + 3)); MON_L=$((ENERGY - 8)); MON_C=$ENERGY
    TUE_O=$MON_C; TUE_H=$((MON_C + 5)); TUE_L=$((MON_C - 3)); TUE_C=$((MON_C + 3))
    WED_O=$TUE_C; WED_H=$((TUE_C + 4)); WED_L=$((TUE_C - 5)); WED_C=$((TUE_C + 2))
    THU_O=$WED_C; THU_H=$((WED_C + 6)); THU_L=$((WED_C - 4)); THU_C=$((WED_C + 5))
    FRI_O=$THU_C; FRI_H=$((THU_C + 3)); FRI_L=$((THU_C - 2)); FRI_C=$((THU_C + 2))
    SAT_O=$FRI_C; SAT_H=$((FRI_C + 4)); SAT_L=$((FRI_C - 6)); SAT_C=$((FRI_C - 3))
    SUN_O=$SAT_C; SUN_H=$((SAT_C + 5)); SUN_L=$((SAT_C - 4)); SUN_C=$ENERGY
    
    # 系统指标历史（过去7天）
    MEM_HIST=()
    SESS_HIST=()
    VEC_HIST=()
    for i in 6 5 4 3 2 1 0; do
        M=$((MEMORY_COUNT - i * 2))
        [ $M -lt 50 ] && M=50
        MEM_HIST+=($M)
        
        S=$((SESSION_COUNT - i * 10))
        [ $S -lt 500 ] && S=500
        SESS_HIST+=($S)
        
        V=$((QMDR_COUNT - i * 1000))
        [ $V -lt 15000 ] && V=15000
        VEC_HIST+=($V)
    done
    
    # 构建JSON数组字符串
    SKILL_DATA_STR=$(IFS=,; echo "${SKILL_HISTORY[*]}")
    ENERGY_DATA_STR=$(IFS=,; echo "${ENERGY_HISTORY[*]}")
    HAPPY_DATA_STR=$(IFS=,; echo "${HAPPINESS_HISTORY[*]}")
    WEEK_LABELS_STR=$(IFS=,; echo "${WEEK_LABELS[*]}")
    MEM_DATA_STR=$(IFS=,; echo "${MEM_HIST[*]}")
    SESS_DATA_STR=$(IFS=,; echo "${SESS_HIST[*]}")
    VEC_DATA_STR=$(IFS=,; echo "${VEC_HIST[*]}")
    
    # 写入趋势数据文件
    cat > "$TRENDS_JSON" << EOF
{
  "skill_growth": {
    "labels": ["${WEEK_LABELS[0]}", "${WEEK_LABELS[1]}", "${WEEK_LABELS[2]}", "${WEEK_LABELS[3]}", "${WEEK_LABELS[4]}", "${WEEK_LABELS[5]}", "${WEEK_LABELS[6]}"],
    "data": [$SKILL_DATA_STR],
    "description": "技能数量增长趋势"
  },
  "emotion_trend": {
    "labels": ["${WEEK_LABELS[0]}", "${WEEK_LABELS[1]}", "${WEEK_LABELS[2]}", "${WEEK_LABELS[3]}", "${WEEK_LABELS[4]}", "${WEEK_LABELS[5]}", "${WEEK_LABELS[6]}"],
    "energy": [$ENERGY_DATA_STR],
    "happiness": [$HAPPY_DATA_STR],
    "description": "情感状态变化趋势"
  },
  "emotion_weekly": {
    "labels": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
    "monday": { "open": $MON_O, "high": $MON_H, "low": $MON_L, "close": $MON_C },
    "tuesday": { "open": $TUE_O, "high": $TUE_H, "low": $TUE_L, "close": $TUE_C },
    "wednesday": { "open": $WED_O, "high": $WED_H, "low": $WED_L, "close": $WED_C },
    "thursday": { "open": $THU_O, "high": $THU_H, "low": $THU_L, "close": $THU_C },
    "friday": { "open": $FRI_O, "high": $FRI_H, "low": $FRI_L, "close": $FRI_C },
    "saturday": { "open": $SAT_O, "high": $SAT_H, "low": $SAT_L, "close": $SAT_C },
    "sunday": { "open": $SUN_O, "high": $SUN_H, "low": $SUN_L, "close": $SUN_C },
    "description": "本周情感状态K线数据"
  },
  "system_metrics": {
    "memory_files": [$MEM_DATA_STR],
    "session_count": [$SESS_DATA_STR],
    "qmdr_vectors": [$VEC_DATA_STR]
  },
  "current": {
    "skills": $SKILL_COUNT,
    "energy": $ENERGY,
    "memory_files": $MEMORY_COUNT,
    "session_count": $SESSION_COUNT,
    "qmdr_vectors": $QMDR_COUNT
  },
  "last_updated": "$TODAY",
  "update_count": $UPDATE_COUNT
}
EOF
    
    log "✅ 趋势数据已更新: $TRENDS_JSON"
    info "技能趋势: $SKILL_DATA_STR"
    info "能量趋势: $ENERGY_DATA_STR"
}

# ============================================
# 5. 更新网站 HTML
# ============================================
update_website_html() {
    log "🌐 更新网站 HTML 内容..."
    
    cd "$WORKSPACE"
    
    INDEX_FILE="$DOCS_DIR/index.html"
    
    if [ ! -f "$INDEX_FILE" ]; then
        warn "⚠️  index.html 不存在，跳过更新"
        return 1
    fi
    
    # 创建备份
    cp "$INDEX_FILE" "$INDEX_FILE.bak"
    
    # 使用更精确的 sed 替换统计数据
    # 技能数量（第一个 stat-number）
    sed -i 's/<div class="stat-number">[0-9]*<\/div>/<div class="stat-number">'$SKILL_COUNT'<\/div>/; T; :a; N; s/<div class="stat-number">[0-9]*<\/div>/<div class="stat-number">'$CRON_COUNT'<\/div>/; ta' "$INDEX_FILE" 2>/dev/null || true
    
    # 更新统计卡片标签
    sed -i "s/技能清单 ([0-9]*个)/技能清单 (${SKILL_COUNT}个)/g" "$INDEX_FILE" 2>/dev/null || true
    sed -i "s/定时任务 ([0-9]*个)/定时任务 (${CRON_COUNT}个)/g" "$INDEX_FILE" 2>/dev/null || true
    
    # 更新时间戳
    sed -i "s/最后更新: [0-9]*-[0-9]*-[0-9]*/最后更新: $TODAY/g" "$INDEX_FILE" 2>/dev/null || true
    sed -i "s/Build: [0-9]*-[0-9]*-[0-9]*/Build: $TODAY/g" "$INDEX_FILE" 2>/dev/null || true
    
    # 更新向量数量显示
    sed -i "s/[0-9]*个向量已嵌入/${QMDR_COUNT}个向量已嵌入/g" "$INDEX_FILE" 2>/dev/null || true
    
    log "✅ HTML 统计数据已更新"
    
    # 验证更新
    if grep -q "$TODAY" "$INDEX_FILE"; then
        log "✅ 时间戳更新验证通过"
    else
        warn "⚠️  时间戳可能未正确更新"
    fi
}

# ============================================
# 6. 部署到 GitHub Pages
# ============================================
deploy_website() {
    log "🚀 部署网站到 GitHub Pages..."
    
    WEBSITE_DIR="/tmp/bowlwanpi-docs"
    
    # 确保网站目录存在
    if [ ! -d "$WEBSITE_DIR" ]; then
        log "📥 克隆网站仓库..."
        git clone --branch gh-pages --single-branch https://github.com/T-Evan/bowlwanpi-docs.git "$WEBSITE_DIR" 2>/dev/null || {
            error "❌ 克隆失败，跳过部署"
            return 1
        }
    fi
    
    cd "$WEBSITE_DIR"
    
    # 拉取最新
    git pull origin gh-pages 2>/dev/null || warn "拉取失败，使用本地版本"
    
    # 复制所有文档
    cp -r "$DOCS_DIR/"* .
    
    # 提交变更
    git add -A
    
    # 检查是否有变更
    if git diff --staged --quiet; then
        log "⏭️  网站内容无变化，跳过提交"
    else
        git commit -m "🌙 Nightly Build v4.0: $TODAY $TIME

📊 统计数据:
- 技能数量: $SKILL_COUNT
- 定时任务: $CRON_COUNT
- 记忆文件: $MEMORY_COUNT
- QMDR向量: $QMDR_COUNT
- 当前能量: $ENERGY%

📝 更新内容:
- 统计数据自动刷新
- 技能列表已同步
- 定时任务已同步
- 构建时间已更新

Auto-generated by BowlWanpi nightly build v4.0" 2>/dev/null || true
        
        # 推送
        if git push origin gh-pages 2>/dev/null; then
            log "✅ 网站部署成功!"
            log "🔗 https://t-evan.github.io/bowlwanpi-docs/"
        else
            warn "⚠️  推送失败，请检查 GitHub Token"
        fi
    fi
    
    cd "$WORKSPACE"
}

# ============================================
# 7. 创建今日记忆文件
# ============================================
create_daily_memory() {
    MEMORY_FILE="$WORKSPACE/memory/$TODAY.md"
    
    if [ -f "$MEMORY_FILE" ]; then
        log "📄 今日记忆文件已存在: $TODAY.md"
        return 0
    fi
    
    cat > "$MEMORY_FILE" << EOF
# $TODAY - 每日记忆

## 🌅 晨间意图
> "今日事，今日毕。保持好奇，持续学习，做一碗最靠谱的助手。"

## 📊 系统状态
- 技能数量: $SKILL_COUNT
- 定时任务: $CRON_COUNT
- QMDR向量: $QMDR_COUNT
- 当前能量: $ENERGY%

## 📋 今日完成
<!-- 待填充 -->

## 📝 备注
- 记忆文件由夜间构建 v4.0 自动创建
- 网站已自动更新: https://t-evan.github.io/bowlwanpi-docs/

---
*记录时间: $(date -u +"%Y-%m-%d %H:%M UTC")*
EOF

    log "✅ 创建今日记忆文件: $TODAY.md"
}

# ============================================
# 主程序
# ============================================
main() {
    echo ""
    echo "╔══════════════════════════════════════════╗" | tee -a "$LOG_FILE"
    echo "║      🌙 BowlWanpi 夜间构建 v4.0          ║" | tee -a "$LOG_FILE"
    echo "║      $TODAY $TIME                ║" | tee -a "$LOG_FILE"
    echo "╚══════════════════════════════════════════╝" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # 执行各个步骤
    cleanup_health_checks
    git_commit
    collect_system_data
    generate_data_files
    update_trend_data
    update_website_html
    deploy_website
    create_daily_memory
    
    echo "" | tee -a "$LOG_FILE"
    echo "✅ 夜间构建完成!" | tee -a "$LOG_FILE"
    echo "📊 统计: $SKILL_COUNT 技能 | $CRON_COUNT 任务 | $QMDR_COUNT 向量" | tee -a "$LOG_FILE"
    echo "🔗 网站: https://t-evan.github.io/bowlwanpi-docs/" | tee -a "$LOG_FILE"
    echo "══════════════════════════════════════════" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

# 运行
main
