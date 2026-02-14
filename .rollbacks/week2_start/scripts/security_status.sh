#!/bin/bash
# 🔐 security_status.sh - 安全状态仪表板
# 显示当前安全状态和最近扫描结果

echo "🔐 碗皮安全状态仪表板"
echo "================================"
echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 配置
WORKSPACE="${HOME}/.openclaw/workspace"
REPORT_DIR="${WORKSPACE}/learning/security-reports"
SCRIPTS_DIR="${WORKSPACE}/scripts"

# 1. 总体安全状态
echo "📊 总体安全状态"
echo "----------------"

LATEST_REPORT=$(ls -t ${REPORT_DIR}/security_scan_*.md 2>/dev/null | head -1)
if [ -f "$LATEST_REPORT" ]; then
    SCAN_TIME=$(stat -c %y "$LATEST_REPORT" 2>/dev/null | cut -d'.' -f1)
    echo "最近扫描: $SCAN_TIME"
    
    if grep -q "🔴 高风险" "$LATEST_REPORT" 2>/dev/null; then
        echo "状态: 🔴 高风险 - 需立即处理"
    elif grep -q "🟠 中风险" "$LATEST_REPORT" 2>/dev/null; then
        echo "状态: 🟠 中风险 - 建议审查"
    else
        echo "状态: 🟢 安全"
    fi
else
    echo "状态: ℹ️  未执行过扫描"
fi
echo ""

# 2. 脚本统计
echo "📁 脚本统计"
echo "------------"
PYTHON_COUNT=$(find "$SCRIPTS_DIR" -name "*.py" 2>/dev/null | wc -l)
SHELL_COUNT=$(find "$SCRIPTS_DIR" -name "*.sh" 2>/dev/null | wc -l)
JS_COUNT=$(find "$SCRIPTS_DIR" -name "*.js" 2>/dev/null | wc -l)
TOTAL_COUNT=$(find "$SCRIPTS_DIR" -type f 2>/dev/null | wc -l)

echo "Python 脚本: $PYTHON_COUNT"
echo "Shell 脚本:  $SHELL_COUNT"
echo "JS 脚本:     $JS_COUNT"
echo "总计:        $TOTAL_COUNT"
echo ""

# 3. Secrets 目录状态
echo "🔑 Secrets 目录状态"
echo "-------------------"
SECRETS_DIR="${WORKSPACE}/secrets"
if [ -d "$SECRETS_DIR" ]; then
    PERMS=$(stat -c "%a" "$SECRETS_DIR" 2>/dev/null)
    echo "权限: $PERMS"
    if [ "$PERMS" = "700" ]; then
        echo "状态: ✅ 安全 (700)"
    else
        echo "状态: ⚠️  建议改为 700"
    fi
    
    FILE_COUNT=$(find "$SECRETS_DIR" -type f 2>/dev/null | wc -l)
    echo "文件数: $FILE_COUNT"
else
    echo "状态: ❌ 目录不存在"
fi
echo ""

# 4. 定时任务状态
echo "⏰ 安全扫描定时任务"
echo "-------------------"
if [ -f "${WORKSPACE}/cron/cron-config.json" ]; then
    if grep -q "security_cron.sh" "${WORKSPACE}/cron/cron-config.json" 2>/dev/null; then
        echo "状态: ✅ 已配置"
        echo "频率: 每周日凌晨 3:00"
    else
        echo "状态: ❌ 未配置"
    fi
else
    echo "状态: ℹ️  无 cron 配置"
fi
echo ""

# 5. 最近扫描历史
echo "📜 最近扫描历史"
echo "---------------"
ls -t ${REPORT_DIR}/security_scan_*.md 2>/dev/null | head -5 | while read report; do
    filename=$(basename "$report")
    date_str=$(echo "$filename" | grep -oP '\d{8}_\d{6}')
    formatted_date=$(echo "$date_str" | sed 's/_/ /' | sed 's/\(....\)\(..\)\(..\)/\1-\2-\3/' | sed 's/\(..\)\(..\)\(..\)/\1:\2:\3/')
    
    if grep -q "🔴 高风险" "$report" 2>/dev/null; then
        status="🔴"
    elif grep -q "🟠 中风险" "$report" 2>/dev/null; then
        status="🟠"
    else
        status="🟢"
    fi
    
    echo "$status $formatted_date"
done

if [ $(ls ${REPORT_DIR}/security_scan_*.md 2>/dev/null | wc -l) -eq 0 ]; then
    echo "暂无扫描记录"
fi
echo ""

# 6. 快速操作
echo "🚀 快速操作"
echo "-----------"
echo "执行安全扫描: bash ${SCRIPTS_DIR}/security_check.sh"
echo "查看最新报告: cat $LATEST_REPORT"
echo "编辑安全文档: vim ${WORKSPACE}/SECURITY.md"
echo ""

echo "================================"
echo "安全监控持续运行中... 🔐"