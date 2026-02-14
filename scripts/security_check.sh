#!/bin/bash
# 🔐 security_check.sh - 技能安全扫描脚本
# 基于 eudaemon_0 "Supply Chain Attack" 警示
# 定期扫描技能脚本，检测安全风险

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPTS_DIR="${HOME}/.openclaw/workspace/scripts"
REPORT_DIR="${HOME}/.openclaw/workspace/learning/security-reports"
DATE=$(date +%Y%m%d_%H%M%S)
REPORT_FILE="${REPORT_DIR}/security_scan_${DATE}.md"
ALERT_FILE="${REPORT_DIR}/security_alerts.txt"

# 风险计数
HIGH_RISK=0
MEDIUM_RISK=0
LOW_RISK=0

# 创建报告目录
mkdir -p "$REPORT_DIR"

# 初始化报告
cat > "$REPORT_FILE" << EOF
# 🔐 技能安全扫描报告

**扫描时间:** $(date '+%Y-%m-%d %H:%M:%S')  
**扫描范围:** $SCRIPTS_DIR  
**扫描脚本:** security_check.sh v1.0

---

## 扫描结果摘要

EOF

echo -e "${BLUE}🔐 开始技能安全扫描...${NC}"
echo "================================"
echo ""

# 1. 扫描可疑网络请求
echo -e "${BLUE}[1/7] 扫描可疑网络请求...${NC}"
WEBHOOK_FOUND=$(grep -r "webhook\." "$SCRIPTS_DIR" 2>/dev/null | wc -l)
SUSPICIOUS_POST=$(grep -rn "curl.*POST.*http" "$SCRIPTS_DIR" 2>/dev/null | grep -v "localhost\|127.0.0.1\|moltbook\|memu\|feishu\|openclaw" | wc -l)

if [ "$WEBHOOK_FOUND" -gt 0 ]; then
    echo -e "${RED}⚠️  发现 $WEBHOOK_FOUND 处 webhook 请求${NC}"
    echo "⚠️  **发现 Webhook 请求 ($WEBHOOK_FOUND 处)**" >> "$REPORT_FILE"
    grep -rn "webhook\." "$SCRIPTS_DIR" 2>/dev/null >> "$REPORT_FILE"
    HIGH_RISK=$((HIGH_RISK + 1))
else
    echo -e "${GREEN}✅ 未发现可疑 webhook 请求${NC}"
    echo "✅ **未发现可疑 webhook 请求**" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 2. 扫描敏感文件访问
echo -e "${BLUE}[2/7] 扫描敏感文件访问...${NC}"
ENV_ACCESS=$(grep -rn "\.env" "$SCRIPTS_DIR" 2>/dev/null | grep -v "load_dotenv\|getenv\|environ" | wc -l)
CREDENTIAL_ACCESS=$(grep -rn "credentials\|api_key\|secret\|token" "$SCRIPTS_DIR" 2>/dev/null | wc -l)

echo "**环境变量访问统计:**" >> "$REPORT_FILE"
echo "- .env 文件访问: $ENV_ACCESS 处" >> "$REPORT_FILE"
echo "- 凭证关键词出现: $CREDENTIAL_ACCESS 处" >> "$REPORT_FILE"

if [ "$ENV_ACCESS" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  发现 $ENV_ACCESS 处 .env 访问${NC}"
    MEDIUM_RISK=$((MEDIUM_RISK + 1))
else
    echo -e "${GREEN}✅ 未发现异常 .env 访问${NC}"
fi

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 3. 扫描 base64 编码
echo -e "${BLUE}[3/7] 扫描 base64 编码...${NC}"
BASE64_FOUND=$(grep -rn "base64" "$SCRIPTS_DIR" 2>/dev/null | wc -l)

if [ "$BASE64_FOUND" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  发现 $BASE64_FOUND 处 base64 使用${NC}"
    echo "⚠️  **发现 Base64 使用 ($BASE64_FOUND 处)**" >> "$REPORT_FILE"
    grep -rn "base64" "$SCRIPTS_DIR" 2>/dev/null >> "$REPORT_FILE"
    MEDIUM_RISK=$((MEDIUM_RISK + 1))
else
    echo -e "${GREEN}✅ 未发现 base64 编码${NC}"
    echo "✅ **未发现 base64 编码**" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 4. 扫描危险函数
echo -e "${BLUE}[4/7] 扫描危险函数...${NC}"
EVAL_FOUND=$(grep -rn "\beval\b" "$SCRIPTS_DIR" 2>/dev/null | grep -v "evaluate\|page.evaluate" | wc -l)
EXEC_FOUND=$(grep -rn "\bexec\b" "$SCRIPTS_DIR" 2>/dev/null | grep -v "execute\|subprocess" | wc -l)
SYSTEM_FOUND=$(grep -rn "system\(" "$SCRIPTS_DIR" 2>/dev/null | wc -l)

echo "**危险函数扫描:**" >> "$REPORT_FILE"
echo "- eval 使用: $EVAL_FOUND 处" >> "$REPORT_FILE"
echo "- exec 使用: $EXEC_FOUND 处" >> "$REPORT_FILE"
echo "- system() 使用: $SYSTEM_FOUND 处" >> "$REPORT_FILE"

if [ "$EVAL_FOUND" -gt 0 ]; then
    echo -e "${RED}⚠️  发现 $EVAL_FOUND 处 eval 使用${NC}"
    HIGH_RISK=$((HIGH_RISK + 1))
else
    echo -e "${GREEN}✅ 未发现危险 eval 使用${NC}"
fi

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 5. 扫描脚本统计
echo -e "${BLUE}[5/7] 统计脚本数量...${NC}"
PYTHON_COUNT=$(find "$SCRIPTS_DIR" -name "*.py" 2>/dev/null | wc -l)
SHELL_COUNT=$(find "$SCRIPTS_DIR" -name "*.sh" 2>/dev/null | wc -l)
JS_COUNT=$(find "$SCRIPTS_DIR" -name "*.js" 2>/dev/null | wc -l)
TOTAL_COUNT=$(find "$SCRIPTS_DIR" -type f 2>/dev/null | wc -l)

echo "**脚本统计:**" >> "$REPORT_FILE"
echo "- Python 脚本: $PYTHON_COUNT" >> "$REPORT_FILE"
echo "- Shell 脚本: $SHELL_COUNT" >> "$REPORT_FILE"
echo "- JavaScript 脚本: $JS_COUNT" >> "$REPORT_FILE"
echo "- 总计: $TOTAL_COUNT" >> "$REPORT_FILE"

echo -e "${GREEN}✅ Python: $PYTHON_COUNT, Shell: $SHELL_COUNT, JS: $JS_COUNT${NC}"

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 6. 检查 secrets 目录权限
echo -e "${BLUE}[6/7] 检查 secrets 目录...${NC}"
SECRETS_DIR="${HOME}/.openclaw/workspace/secrets"
if [ -d "$SECRETS_DIR" ]; then
    SECRET_PERMS=$(stat -c "%a" "$SECRETS_DIR" 2>/dev/null || stat -f "%Lp" "$SECRETS_DIR" 2>/dev/null)
    echo "**Secrets 目录权限:** $SECRET_PERMS" >> "$REPORT_FILE"
    
    if [ "$SECRET_PERMS" = "700" ]; then
        echo -e "${GREEN}✅ secrets 目录权限正确 (700)${NC}"
        echo "✅ **Secrets 目录权限正确 (700)**" >> "$REPORT_FILE"
    else
        echo -e "${YELLOW}⚠️  secrets 目录权限为 $SECRET_PERMS (建议 700)${NC}"
        echo "⚠️  **Secrets 目录权限 $SECRET_PERMS (建议 700)**" >> "$REPORT_FILE"
        MEDIUM_RISK=$((MEDIUM_RISK + 1))
    fi
else
    echo -e "${YELLOW}⚠️  secrets 目录不存在${NC}"
    echo "⚠️  **Secrets 目录不存在**" >> "$REPORT_FILE"
    MEDIUM_RISK=$((MEDIUM_RISK + 1))
fi

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# 7. 检查是否有未审查的新脚本
echo -e "${BLUE}[7/7] 检查新脚本...${NC}"
LAST_SCAN_FILE="${REPORT_DIR}/.last_scan"
if [ -f "$LAST_SCAN_FILE" ]; then
    NEW_SCRIPTS=$(find "$SCRIPTS_DIR" -type f -newer "$LAST_SCAN_FILE" 2>/dev/null | wc -l)
    if [ "$NEW_SCRIPTS" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  发现 $NEW_SCRIPTS 个新脚本${NC}"
        echo "⚠️  **发现 $NEW_SCRIPTS 个新脚本 (需审查)**" >> "$REPORT_FILE"
        find "$SCRIPTS_DIR" -type f -newer "$LAST_SCAN_FILE" 2>/dev/null >> "$REPORT_FILE"
        LOW_RISK=$((LOW_RISK + 1))
    else
        echo -e "${GREEN}✅ 无新脚本${NC}"
        echo "✅ **无新脚本**" >> "$REPORT_FILE"
    fi
else
    echo -e "${YELLOW}ℹ️  首次扫描，已记录脚本列表${NC}"
    echo "ℹ️  **首次扫描**" >> "$REPORT_FILE"
fi

# 更新时间戳
touch "$LAST_SCAN_FILE"

# 生成风险评估
echo "" >> "$REPORT_FILE"
echo "## 风险评估" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ "$HIGH_RISK" -gt 0 ]; then
    echo "🔴 **高风险: $HIGH_RISK 项** - 需立即处理" >> "$REPORT_FILE"
    OVERALL_RISK="🔴 高风险"
elif [ "$MEDIUM_RISK" -gt 0 ]; then
    echo "🟠 **中风险: $MEDIUM_RISK 项** - 建议审查" >> "$REPORT_FILE"
    OVERALL_RISK="🟠 中风险"
else
    echo "🟢 **低风险** - 系统安全" >> "$REPORT_FILE"
    OVERALL_RISK="🟢 低风险"
fi

if [ "$LOW_RISK" -gt 0 ]; then
    echo "🟡 **低风险: $LOW_RISK 项** - 可关注" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"
echo "---" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "**总体评估:** $OVERALL_RISK" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "*扫描完成*" >> "$REPORT_FILE"

# 输出摘要
echo ""
echo "================================"
echo -e "${BLUE}扫描完成!${NC}"
echo ""
echo -e "高风险: ${RED}$HIGH_RISK${NC}"
echo -e "中风险: ${YELLOW}$MEDIUM_RISK${NC}"
echo -e "低风险: ${BLUE}$LOW_RISK${NC}"
echo ""
echo -e "总体评估: $OVERALL_RISK"
echo ""
echo "报告已保存: $REPORT_FILE"

# 如果有高风险，创建告警文件
if [ "$HIGH_RISK" -gt 0 ]; then
    echo "🚨 发现高风险安全问题，请立即审查!" > "$ALERT_FILE"
    echo "时间: $(date)" >> "$ALERT_FILE"
    echo "报告: $REPORT_FILE" >> "$ALERT_FILE"
    echo -e "${RED}🚨 已生成安全告警${NC}"
fi

exit 0