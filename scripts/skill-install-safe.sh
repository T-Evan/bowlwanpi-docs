#!/bin/bash
#
# Skill 安装安全包装器
# 安装前扫描，安装后沙箱测试
#

SKILL_DIR="${1:-}"
LOG_FILE="/var/log/bowlwanpi-skill-install.log"

log() {
    echo "[$(TZ='Asia/Shanghai' date '+%H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

if [ -z "$SKILL_DIR" ]; then
    echo "Usage: $0 <skill-directory>"
    exit 1
fi

SKILL_NAME=$(basename "$SKILL_DIR")
log "🔧 安装 Skill: $SKILL_NAME"

# ========== 安装前扫描 ==========
echo ""
echo "🔍 安全检查..."

ISSUES=()

# 1. 检查敏感文件访问
SENSITIVE=$(grep -rE "(\.env|credentials|password|secret|token|api_key)" "$SKILL_DIR" 2>/dev/null | head -5)
if [ -n "$SENSITIVE" ]; then
    ISSUES+=("⚠️  发现潜在敏感信息访问:")
    echo "$SENSITIVE" | while read line; do
        ISSUES+=("  $line")
    done
fi

# 2. 检查网络请求
NETWORK=$(grep -rE "(curl|wget|fetch|http|webhook|requests\.get|urllib)" "$SKILL_DIR"/*.py "$SKILL_DIR"/*.sh 2>/dev/null | head -5)
if [ -n "$NETWORK" ]; then
    ISSUES+=("🌐 发现网络请求代码:")
    echo "$NETWORK" | while read line; do
        ISSUES+=("  $line")
    done
fi

# 3. 检查危险命令
DANGEROUS=$(grep -rE "(rm -rf|mkfs|dd if|system\(|exec\(|eval\()" "$SKILL_DIR" 2>/dev/null | head -5)
if [ -n "$DANGEROUS" ]; then
    ISSUES+=("🚨 发现潜在危险命令:")
    echo "$DANGEROUS" | while read line; do
        ISSUES+=("  $line")
    done
fi

# 4. 检查文件权限修改
PERMS=$(grep -rE "(chmod|chown|777)" "$SKILL_DIR" 2>/dev/null | head -3)
if [ -n "$PERMS" ]; then
    ISSUES+=("⚠️  发现权限修改:")
    echo "$PERMS" | while read line; do
        ISSUES+=("  $line")
    done
fi

# 显示检查结果
if [ ${#ISSUES[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  安全检查发现以下问题:"
    for issue in "${ISSUES[@]}"; do
        echo "  $issue"
    done
    echo ""
    read -p "是否继续安装? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "🚫 用户取消安装"
        exit 1
    fi
    log "⚠️  用户确认安装，存在安全风险"
else
    echo "✅ 安全检查通过"
    log "✅ 安全检查通过"
fi

# ========== 安装 ==========
echo ""
echo "📦 安装中..."

TARGET_DIR="/root/.openclaw/workspace/skills/$SKILL_NAME"
if [ -d "$TARGET_DIR" ]; then
    log "⚠️  Skill 已存在，更新..."
    rm -rf "$TARGET_DIR"
fi

cp -r "$SKILL_DIR" "$TARGET_DIR"
log "✅ 安装完成: $TARGET_DIR"

# ========== 沙箱测试 ==========
echo ""
echo "🧪 沙箱测试运行..."

if [ -f "/root/.openclaw/workspace/scripts/skill-sandbox.sh" ]; then
    bash /root/.openclaw/workspace/scripts/skill-sandbox.sh "$TARGET_DIR" echo "Sandbox test"
    if [ $? -eq 0 ]; then
        log "✅ 沙箱测试通过"
        echo "✅ 沙箱测试通过"
    else
        log "❌ 沙箱测试失败"
        echo "❌ 沙箱测试失败"
    fi
else
    log "⚠️  沙箱系统未安装"
fi

# ========== 完成 ==========
echo ""
echo "🎉 Skill '$SKILL_NAME' 安装完成"
echo ""
echo "安全建议:"
echo "  - 定期审查 skill 代码"
echo "  - 使用 sandbox 执行: skill-sandbox.sh $TARGET_DIR <command>"
echo "  - 监控网络连接: ss -tp | grep skill"

log "🎉 安装完成: $SKILL_NAME"
