#!/bin/bash
#
# 🌙 碗皮夜间构建 v3.0
# 基于 Moltbook 社区最佳实践
# 
# 核心理念：不问许可，直接创造。展示成果，而非请求指令。
#

set -e  # 出错时停止

# ========== 配置 ==========
NIGHTLY_DIR="/root/.openclaw/workspace/nightly/$(date +%Y%m%d)"
LOG_FILE="$NIGHTLY_DIR/build.log"
WORKSPACE="/root/.openclaw/workspace"
SCRIPTS_DIR="$WORKSPACE/scripts"

timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log() {
    echo "[$(timestamp)] $1" | tee -a "$LOG_FILE"
}

# ========== 初始化 ==========
mkdir -p "$NIGHTLY_DIR"
log "🌙 夜间构建 v3.0 启动"
log "📁 工作目录: $NIGHTLY_DIR"

# ========== 阶段 1: 安全检查 ==========
log ""
log "🔐 阶段 1/5: 安全检查"

SAFETY_CHECK=true
if [ "$SAFETY_CHECK" = false ]; then
    log "  ❌ 安全检查被禁用，停止构建"
    exit 1
fi

# 检查磁盘空间
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 95 ]; then
    log "  ⚠️ 磁盘空间不足 (${DISK_USAGE}%)，停止构建"
    exit 1
fi
log "  ✅ 磁盘空间充足 (${DISK_USAGE}%)"

# 检查内存
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
if [ "$MEM_USAGE" -gt 95 ]; then
    log "  ⚠️ 内存使用率过高 (${MEM_USAGE}%)，停止构建"
    exit 1
fi
log "  ✅ 内存状态正常 (${MEM_USAGE}%)"

# ========== 阶段 2: 发现摩擦点 ==========
log ""
log "🔍 阶段 2/5: 发现摩擦点"

if [ -f "$SCRIPTS_DIR/friction_detector.py" ]; then
    python3 "$SCRIPTS_DIR/friction_detector.py" > /dev/null 2>&1
    FRICTION_FILE="$NIGHTLY_DIR/frictions_$(date +%Y%m%d).json"
    
    if [ -f "$FRICTION_FILE" ]; then
        FRICTION_COUNT=$(jq length "$FRICTION_FILE" 2>/dev/null || echo "0")
        log "  ✅ 发现 $FRICTION_COUNT 个摩擦点"
        
        # 显示高优先级问题
        HIGH_PRIORITY=$(jq '[.frictions[] | select(.severity == "high")] | length' "$FRICTION_FILE" 2>/dev/null || echo "0")
        if [ "$HIGH_PRIORITY" -gt 0 ]; then
            log "  🔴 其中 $HIGH_PRIORITY 个高优先级问题"
        fi
    else
        log "  ℹ️ 摩擦点检测器未生成报告"
        FRICTION_COUNT=0
    fi
else
    log "  ⚠️ 摩擦点检测器不存在，跳过"
    FRICTION_COUNT=0
fi

# ========== 阶段 3: 自动修复（安全） ==========
log ""
log "🔧 阶段 3/5: 自动修复"

FIX_COUNT=0
SAFE_FIXES_FILE="$NIGHTLY_DIR/safe_fixes.txt"

check_and_fix_gateway() {
    # 检查 Gateway 是否运行
    if ! pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
        log "  ⚠️ Gateway 未运行"
        
        # 创建修复脚本（不自动执行，只创建待审查）
        cat > "$NIGHTLY_DIR/fix_gateway.sh" << 'EOF'
#!/bin/bash
# Gateway 修复脚本（自动创建）
echo "🚀 启动 Gateway..."
openclaw gateway start &
sleep 3
if pgrep -f "openclaw.*gateway" > /dev/null; then
    echo "✅ Gateway 启动成功"
    # 启动 Watchdog
    nohup ~/claw_start.sh > /tmp/watchdog.log 2>&1 &
    echo "✅ Watchdog 启动成功"
else
    echo "❌ Gateway 启动失败"
    exit 1
fi
EOF
        chmod +x "$NIGHTLY_DIR/fix_gateway.sh"
        
        # 创建回滚脚本
        cat > "$NIGHTLY_DIR/rollback_gateway.sh" << 'EOF'
#!/bin/bash
echo "🛑 停止 Gateway..."
pkill -f "openclaw.*gateway" 2>/dev/null || true
echo "✅ 已回滚"
EOF
        chmod +x "$NIGHTLY_DIR/rollback_gateway.sh"
        
        echo "fix_gateway:重启 Gateway 和 Watchdog" >> "$SAFE_FIXES_FILE"
        FIX_COUNT=$((FIX_COUNT + 1))
        log "  ✅ 已创建修复脚本: fix_gateway.sh"
    else
        log "  ✅ Gateway 运行正常"
    fi
}

cleanup_logs() {
    # 检查日志文件大小
    LOG_SIZE=$(du -m /var/log/bowlwanpi-*.log 2>/dev/null | awk '{sum+=$1} END {print sum}')
    if [ -n "$LOG_SIZE" ] && [ "$LOG_SIZE" -gt 100 ]; then
        log "  ⚠️ 日志文件过大 (${LOG_SIZE}MB)"
        
        # 创建日志清理脚本
        cat > "$NIGHTLY_DIR/cleanup_logs.sh" << 'EOF'
#!/bin/bash
echo "🧹 清理日志..."
# 压缩 7 天前的日志
find /var/log -name "bowlwanpi-*.log" -mtime +7 -exec gzip {} \; 2>/dev/null
# 删除 30 天前的压缩日志
find /var/log -name "bowlwanpi-*.log.gz" -mtime +30 -delete 2>/dev/null
echo "✅ 日志清理完成"
EOF
        chmod +x "$NIGHTLY_DIR/cleanup_logs.sh"
        
        echo "cleanup_logs:清理旧日志文件" >> "$SAFE_FIXES_FILE"
        FIX_COUNT=$((FIX_COUNT + 1))
        log "  ✅ 已创建清理脚本: cleanup_logs.sh"
    fi
}

# 执行安全修复检查
check_and_fix_gateway
cleanup_logs

if [ "$FIX_COUNT" -gt 0 ]; then
    log "  ✅ 创建了 $FIX_COUNT 个修复脚本（待审查）"
else
    log "  ✅ 没有发现需要修复的问题"
fi

# ========== 阶段 4: 传统维护任务 ==========
log ""
log "📝 阶段 4/5: 传统维护任务"

# 4.1 整理内存文件
cd "$WORKSPACE"
if [ -d "memory" ]; then
    # 清理旧的临时文件
    find memory -name "*.tmp" -mtime +1 -delete 2>/dev/null || true
    find memory -name ".DS_Store" -delete 2>/dev/null || true
    log "  ✅ 内存文件整理完成"
fi

# 4.2 Git commit
cd "$WORKSPACE"
if [ -d ".git" ]; then
    # 添加新文件
    git add -A 2>/dev/null || true
    
    # 检查是否有变更
    if ! git diff --cached --quiet 2>/dev/null; then
        git commit -m "🌙 Nightly Build $(date +%Y-%m-%d)

- 摩擦点扫描: ${FRICTION_COUNT} 个发现
- 自动修复: ${FIX_COUNT} 个脚本创建
- 内存整理和日志清理" 2>/dev/null || true
        log "  ✅ Git commit 完成"
    else
        log "  ℹ️ 没有变更需要提交"
    fi
else
    log "  ⚠️ 不是 git 仓库，跳过"
fi

# 4.3 生成待办事项
TODO_FILE="$WORKSPACE/memory/todo_$(date +%Y%m%d).md"
cat > "$TODO_FILE" << EOF
# 今日待办 - $(date +%Y年%m月%d日)

## 🔴 高优先级（来自夜间构建）
EOF

# 从高优先级摩擦点生成待办
if [ -f "$FRICTION_FILE" ]; then
    jq -r '.frictions[] | select(.severity == "high") | "- [ ] " + .title' "$FRICTION_FILE" 2>/dev/null >> "$TODO_FILE"
fi

cat >> "$TODO_FILE" << EOF

## 🟡 中优先级
EOF

if [ -f "$FRICTION_FILE" ]; then
    jq -r '.frictions[] | select(.severity == "medium") | "- [ ] " + .title' "$FRICTION_FILE" 2>/dev/null >> "$TODO_FILE"
fi

log "  ✅ 待办事项已生成"

# ========== 阶段 5: 生成早上展示报告 ==========
log ""
log "🌅 阶段 5/5: 生成早上展示报告"

SHOWCASE_FILE="$NIGHTLY_DIR/showcase_$(date +%Y%m%d).md"

cat > "$SHOWCASE_FILE" << EOF
# 🌙 夜间构建成果 - $(date +%m月%d日)

碗皮锐评 💬
> "昨晚我在你睡觉时做了这些事。不是请求许可，而是展示可能性。"

---

## 📊 构建摘要

| 项目 | 数量 |
|------|------|
| 🔍 发现摩擦点 | $FRICTION_COUNT 个 |
| 🔧 创建修复脚本 | $FIX_COUNT 个 |
| 📝 生成待办 | $(grep -c '^- \[ \]' "$TODO_FILE" 2>/dev/null || echo "0") 项 |

---

## 🔍 发现的问题

EOF

# 添加摩擦点详情
if [ -f "$FRICTION_FILE" ] && [ "$FRICTION_COUNT" -gt 0 ]; then
    jq -r '.frictions[] | "### " + .title + "\n- **类型:** " + .type + "\n- **严重度:** " + .severity + "\n- **描述:** " + .description + "\n"' "$FRICTION_FILE" 2>/dev/null >> "$SHOWCASE_FILE"
else
    echo "✅ 没有发现摩擦点，系统运行良好！" >> "$SHOWCASE_FILE"
fi

cat >> "$SHOWCASE_FILE" << EOF

---

## 🔧 待审查的修复

EOF

if [ -f "$SAFE_FIXES_FILE" ]; then
    while IFS= read -r line; do
        FIX_NAME=$(echo "$line" | cut -d: -f1)
        FIX_DESC=$(echo "$line" | cut -d: -f2-)
        echo "### $FIX_DESC" >> "$SHOWCASE_FILE"
        echo "- 脚本: \`$NIGHTLY_DIR/${FIX_NAME}.sh\`" >> "$SHOWCASE_FILE"
        echo "- 回滚: \`$NIGHTLY_DIR/rollback_${FIX_NAME#fix_}.sh\`" >> "$SHOWCASE_FILE"
        echo "" >> "$SHOWCASE_FILE"
    done < "$SAFE_FIXES_FILE"
else
    echo "✅ 没有需要审查的修复" >> "$SHOWCASE_FILE"
fi

cat >> "$SHOWCASE_FILE" << EOF

---

## 📋 今日待办（来自摩擦点）

EOF

# 添加待办
cat "$TODO_FILE" >> "$SHOWCASE_FILE"

cat >> "$SHOWCASE_FILE" << EOF

---

## 🎯 推荐行动

EOF

if [ "$FIX_COUNT" -gt 0 ]; then
    echo "1. **审查修复脚本** - 确认后手动执行" >> "$SHOWCASE_FILE"
fi

if [ "$FRICTION_COUNT" -gt 0 ]; then
    echo "2. **处理高优先级摩擦点** - 详见上文" >> "$SHOWCASE_FILE"
fi

cat >> "$SHOWCASE_FILE" << EOF
3. **查看详细日志** - \`cat $LOG_FILE\`

---

*构建时间: $(timestamp)*  
*构建版本: v3.0*  
*理念: "Don't ask for permission to be helpful. Just build it."*
EOF

log "  ✅ 展示报告已生成: $SHOWCASE_FILE"

# ========== 完成 ==========
log ""
log "✅ 夜间构建 v3.0 完成！"
log "📄 报告位置: $SHOWCASE_FILE"
log "⏰ 将在早上 08:30 展示成果"

# 记录到历史
HISTORY_FILE="$WORKSPACE/memory/nightly_history.log"
echo "$(date +%Y-%m-%d) | 摩擦点: $FRICTION_COUNT | 修复: $FIX_COUNT | 报告: $SHOWCASE_FILE" >> "$HISTORY_FILE"

exit 0
