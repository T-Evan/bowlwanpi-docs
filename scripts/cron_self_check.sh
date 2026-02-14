#!/bin/bash
#
# 🔍 定时任务自检系统 v1.4
# 全面自检 - 覆盖所有关键功能
#

WORKSPACE="${HOME}/.openclaw/workspace"
LOG_FILE="/var/log/bowlwanpi-self-check.log"
REPORT_FILE="$WORKSPACE/health-checks/self-check-report.md"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# ========== 自检项目 ==========

# 1. 检查 Gateway 状态
check_gateway() {
    log "🔍 检查 Gateway..."
    
    local retry=0
    local max_retry=3
    local status="fail"
    
    while [ $retry -lt $max_retry ]; do
        if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
            if curl -s http://localhost:3000/health > /dev/null 2>&1; then
                status="ok"
                break
            fi
        fi
        retry=$((retry + 1))
        sleep 2
    done
    
    if [ "$status" = "ok" ]; then
        log "✅ Gateway 正常"
        return 0
    else
        log "❌ Gateway 异常，尝试重启..."
        restart_gateway
        return 1
    fi
}

# 2. 检查 Mihomo 代理状态
check_mihomo() {
    log "🔍 检查 Mihomo 代理..."
    
    # 检查进程
    if ! pgrep -f "mihomo" > /dev/null 2>&1; then
        log "   ❌ Mihomo 进程不存在"
        return 1
    fi
    
    # 检查端口
    if ! netstat -tlnp 2>/dev/null | grep -q ":7890"; then
        log "   ❌ 端口 7890 未监听"
        return 1
    fi
    
    # 测试代理
    if curl -s --max-time 5 --proxy http://127.0.0.1:7890 http://www.baidu.com > /dev/null 2>&1; then
        log "   ✅ Mihomo 代理正常"
        return 0
    else
        log "   ⚠️  代理测试失败"
        return 1
    fi
}

# 3. 检查定时任务日志
check_cron_logs() {
    log "🔍 检查定时任务日志..."
    
    local errors=0
    
    for logfile in /var/log/bowlwanpi-*.log; do
        if [ -f "$logfile" ]; then
            local recent_errors=$(grep "$(date '+%Y-%m-%d %H')" "$logfile" 2>/dev/null | grep -iE "error|fail|critical" | wc -l)
            if [ "$recent_errors" -gt 0 ]; then
                log "⚠️  $(basename $logfile) 发现 $recent_errors 个错误"
                errors=$((errors + recent_errors))
            fi
        fi
    done
    
    if [ $errors -eq 0 ]; then
        log "✅ 近期日志无错误"
        return 0
    else
        log "⚠️  共发现 $errors 个错误"
        return 1
    fi
}

# 4. 检查四记忆系统
check_memory_systems() {
    log "🧠 检查四记忆系统..."
    local issues=0
    
    # 4.1 Hippocampus (本地文件)
    if [ -d "$WORKSPACE/memory" ]; then
        local mem_count=$(find "$WORKSPACE/memory" -name "*.md" 2>/dev/null | wc -l)
        log "   ✅ Hippocampus: $mem_count 个记忆文件"
    else
        log "   ❌ Hippocampus: 目录不存在"
        issues=$((issues + 1))
    fi
    
    # 4.2 memU (云端 API)
    if [ -f "$WORKSPACE/secrets/memu-credentials.json" ]; then
        log "   ✅ memU: 配置存在"
    else
        log "   ⚠️  memU: 配置文件不存在"
    fi
    
    # 4.3 MemOS (云端)
    if [ -f "$WORKSPACE/secrets/memos-credentials.json" ] || [ -n "$MEMOS_API_KEY" ]; then
        log "   ✅ MemOS: 配置存在"
    else
        log "   ℹ️  MemOS: 可能通过 HTTP 直接调用"
    fi
    
    # 4.4 QMDR (向量搜索)
    export PATH="$HOME/.bun/bin:$PATH"
    if command -v qmd > /dev/null 2>&1; then
        local qmd_status=$(qmd status 2>/dev/null | grep "Total:" | awk '{print $2}')
        log "   ✅ QMDR: 可用 ($qmd_status 文件)"
    else
        log "   ⚠️  QMDR: 命令不可用"
        issues=$((issues + 1))
    fi
    
    # 4.5 检查同步脚本
    if [ -f "$WORKSPACE/scripts/batch_store_history.py" ]; then
        log "   ✅ 记忆同步脚本存在"
    else
        log "   ❌ 记忆同步脚本不存在"
        issues=$((issues + 1))
    fi
    
    if [ $issues -eq 0 ]; then
        log "✅ 四记忆系统正常"
        return 0
    else
        log "⚠️  记忆系统发现 $issues 个问题"
        return 1
    fi
}

# 5. 检查 QMDR
check_qmdr() {
    log "🔍 检查 QMDR..."
    
    export PATH="$HOME/.bun/bin:$PATH"
    if ! command -v qmd > /dev/null 2>&1; then
        log "   ❌ qmd 命令不可用"
        return 1
    fi
    
    local status_output=$(qmd status 2>&1)
    if [ $? -ne 0 ]; then
        log "   ❌ QMDR 索引异常"
        return 1
    fi
    
    local total_files=$(echo "$status_output" | grep "Total:" | awk '{print $2}')
    local collections=$(echo "$status_output" | grep -c "Collection")
    
    log "   ✅ QMDR 正常 ($total_files 文件, $collections 集合)"
    
    if qmd search "测试" --collection memory -n 1 > /dev/null 2>&1; then
        log "   ✅ QMDR 搜索功能正常"
        return 0
    else
        log "   ⚠️  QMDR 搜索功能异常"
        return 1
    fi
}

# 6. 检查报告生成
check_reports() {
    log "🔍 检查报告生成..."
    
    local latest_report=$(ls -t $WORKSPACE/health-checks/unified_report_*.md 2>/dev/null | head -1)
    
    if [ -n "$latest_report" ]; then
        local report_time=$(stat -c %Y "$latest_report")
        local current_time=$(date +%s)
        local diff=$(( (current_time - report_time) / 60 ))
        
        if [ $diff -lt 35 ]; then
            log "✅ 报告正常生成 (${diff}分钟前)"
            
            if grep -q "CPU.*%" "$latest_report" 2>/dev/null; then
                log "✅ 报告内容完整"
                return 0
            else
                log "⚠️  报告内容为空"
                return 1
            fi
        else
            log "⚠️  报告已过期 (${diff}分钟前)"
            return 1
        fi
    else
        log "❌ 未找到报告文件"
        return 1
    fi
}

# 7. 检查四记忆存储任务
check_memory_storage() {
    log "🔍 检查四记忆存储任务..."
    
    local log_file="/var/log/bowlwanpi-memory-v3.log"
    if [ -f "$log_file" ]; then
        local last_update=$(stat -c %Y "$log_file")
        local current_time=$(date +%s)
        local diff_hours=$(( (current_time - last_update) / 3600 ))
        
        if [ $diff_hours -lt 2 ]; then
            log "   ✅ 四记忆存储任务近期有执行 (${diff_hours}小时前)"
            
            local errors=$(tail -20 "$log_file" | grep -iE "error|fail|❌" | wc -l)
            if [ "$errors" -eq 0 ]; then
                log "   ✅ 近期执行无错误"
                return 0
            else
                log "   ⚠️  近期执行有 $errors 个错误"
                return 1
            fi
        else
            log "   ⚠️  四记忆存储任务已 ${diff_hours} 小时未执行"
            return 1
        fi
    else
        log "   ⚠️  四记忆存储日志不存在"
        return 1
    fi
}

# 8. 检查磁盘空间 (新增)
check_disk_space() {
    log "🔍 检查磁盘空间..."
    
    local usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$usage" -gt 95 ]; then
        log "   🔴 磁盘使用率过高: ${usage}% (>95%)"
        return 1
    elif [ "$usage" -gt 85 ]; then
        log "   🟡 磁盘使用率警告: ${usage}% (>85%)"
        return 1
    else
        log "   ✅ 磁盘空间正常: ${usage}%"
        return 0
    fi
}

# 9. 检查 Git 状态 (新增)
check_git_status() {
    log "🔍 检查 Git 状态..."
    
    cd "$WORKSPACE"
    
    if [ ! -d .git ]; then
        log "   ⚠️  不是 Git 仓库"
        return 0
    fi
    
    # 检查未提交更改
    local uncommitted=$(git status --porcelain 2>/dev/null | wc -l)
    
    if [ "$uncommitted" -gt 0 ]; then
        log "   🟡 有 $uncommitted 个未提交更改"
        return 1
    else
        log "   ✅ Git 状态干净"
        return 0
    fi
}

# 10. 检查备份状态 (新增)
check_backup_status() {
    log "🔍 检查备份状态..."
    
    local backup_dir="/clawd-data/workspace-backup"
    local issues=0
    
    if [ -d "$backup_dir" ]; then
        # 检查最新备份时间
        local latest_backup=$(find "$backup_dir" -type f -name "*.tar.gz" 2>/dev/null | head -1)
        if [ -n "$latest_backup" ]; then
            local backup_time=$(stat -c %Y "$latest_backup")
            local current_time=$(date +%s)
            local diff_hours=$(( (current_time - backup_time) / 3600 ))
            
            if [ $diff_hours -lt 24 ]; then
                log "   ✅ 备份正常 (${diff_hours}小时前)"
            else
                log "   🟡 备份较旧 (${diff_hours}小时前)"
                issues=$((issues + 1))
            fi
        else
            log "   ⚠️  未找到备份文件"
            issues=$((issues + 1))
        fi
    else
        log "   ⚠️  备份目录不存在"
        issues=$((issues + 1))
    fi
    
    return $issues
}

# 11. 检查 HackerNews 监控 (新增)
check_hackernews() {
    log "🔍 检查 HackerNews 监控..."
    
    local log_file="/var/log/bowlwanpi-hackernews.log"
    if [ -f "$log_file" ]; then
        local last_update=$(stat -c %Y "$log_file")
        local current_time=$(date +%s)
        local diff_hours=$(( (current_time - last_update) / 3600 ))
        
        if [ $diff_hours -lt 2 ]; then
            log "   ✅ HN 监控近期有执行"
            
            local errors=$(tail -10 "$log_file" | grep -iE "error|fail" | wc -l)
            if [ "$errors" -eq 0 ]; then
                log "   ✅ HN 监控无错误"
                return 0
            else
                log "   ⚠️  HN 监控有错误"
                return 1
            fi
        else
            log "   ⚠️  HN 监控已 ${diff_hours} 小时未更新"
            return 1
        fi
    else
        log "   ⚠️  HN 监控日志不存在"
        return 1
    fi
}

# 12. 检查夜间构建 (新增)
check_nightly_build() {
    log "🔍 检查夜间构建..."
    
    local log_file="/var/log/bowlwanpi-nightly-build.log"
    if [ -f "$log_file" ]; then
        local last_update=$(stat -c %Y "$log_file")
        local current_time=$(date +%s)
        local diff_hours=$(( (current_time - last_update) / 3600 ))
        
        # 夜间构建每天 3:00 执行
        if [ $diff_hours -lt 26 ]; then
            log "   ✅ 夜间构建近期有执行 (${diff_hours}小时前)"
            
            local errors=$(tail -20 "$log_file" | grep -iE "error|fail|❌" | wc -l)
            if [ "$errors" -eq 0 ]; then
                log "   ✅ 夜间构建无错误"
                return 0
            else
                log "   ⚠️  夜间构建有 $errors 个错误"
                return 1
            fi
        else
            log "   ⚠️  夜间构建已 ${diff_hours} 小时未执行"
            return 1
        fi
    else
        log "   ⚠️  夜间构建日志不存在"
        return 1
    fi
}

# ========== 自动修复 ==========

restart_gateway() {
    log "🔄 重启 Gateway..."
    
    pkill -f "openclaw.*gateway" 2>/dev/null || true
    sleep 3
    
    if command -v openclaw > /dev/null 2>&1; then
        openclaw gateway start &
        sleep 5
        
        if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
            log "✅ Gateway 重启成功"
            return 0
        else
            log "❌ Gateway 重启失败"
            return 1
        fi
    else
        log "❌ openclaw 命令不可用"
        return 1
    fi
}

# 重启四记忆存储任务
restart_memory_storage() {
    log "🔄 手动执行四记忆存储..."
    
    export PATH="$HOME/.bun/bin:$PATH"
    cd /root/.openclaw/workspace
    
    if python3 scripts/batch_store_memory_v3.py >> /var/log/bowlwanpi-memory-v3.log 2>&1; then
        log "✅ 四记忆存储任务执行成功"
        return 0
    else
        log "❌ 四记忆存储任务执行失败"
        return 1
    fi
}

# 执行 Git 提交
auto_git_commit() {
    log "🔄 自动提交 Git 更改..."
    
    cd "$WORKSPACE"
    
    if [ ! -d .git ]; then
        log "   ❌ 不是 Git 仓库"
        return 1
    fi
    
    git add -A 2>/dev/null
    git commit -m "Auto commit: $(date '+%Y-%m-%d %H:%M')" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "✅ Git 提交成功"
        return 0
    else
        log "⚠️  Git 提交失败或无更改"
        return 1
    fi
}

# 清理磁盘空间
cleanup_disk() {
    log "🔄 清理磁盘空间..."
    
    # 清理旧日志
    find /var/log -name "bowlwanpi-*.log" -mtime +7 -delete 2>/dev/null
    
    # 清理旧报告
    find $WORKSPACE/health-checks -name "unified_report_*.md" -mtime +7 -delete 2>/dev/null
    
    log "✅ 磁盘清理完成"
    return 0
}

# ========== 生成报告 ==========

generate_report() {
    local issues="$1"
    local fixed="$2"
    
    cat > "$REPORT_FILE" << EOF
# 🔍 系统全面自检报告 v1.4

**检查时间:** $(date '+%Y-%m-%d %H:%M:%S')  
**发现问题:** $issues  
**自动修复:** $fixed

---

## 系统服务

| 项目 | 状态 |
|------|------|
| Gateway | $(check_gateway &>/dev/null && echo "✅" || echo "❌") |
| Mihomo 代理 | $(check_mihomo &>/dev/null && echo "✅" || echo "⚠️") |
| QMDR | $(check_qmdr &>/dev/null && echo "✅" || echo "⚠️") |

## 数据与存储

| 项目 | 状态 |
|------|------|
| 四记忆系统 | $(check_memory_systems &>/dev/null && echo "✅" || echo "⚠️") |
| 四记忆存储 | $(check_memory_storage &>/dev/null && echo "✅" || echo "⚠️") |
| 磁盘空间 | $(check_disk_space &>/dev/null && echo "✅" || echo "⚠️") |
| Git 状态 | $(check_git_status &>/dev/null && echo "✅" || echo "⚠️") |
| 备份状态 | $(check_backup_status &>/dev/null && echo "✅" || echo "⚠️") |

## 定时任务

| 项目 | 状态 |
|------|------|
| 日志检查 | $(check_cron_logs &>/dev/null && echo "✅" || echo "⚠️") |
| HackerNews | $(check_hackernews &>/dev/null && echo "✅" || echo "⚠️") |
| 夜间构建 | $(check_nightly_build &>/dev/null && echo "✅" || echo "⚠️") |
| 报告生成 | $(check_reports &>/dev/null && echo "✅" || echo "⚠️") |

---

*全面自检系统自动生成 v1.4*
EOF
}

# ========== 主函数 ==========

main() {
    log "========== 开始全面自检 (v1.4) =========="
    
    local total_issues=0
    local fixed_issues=0
    
    # 系统服务
    check_gateway || { total_issues=$((total_issues + 1)); }
    check_mihomo || total_issues=$((total_issues + 1))
    check_qmdr || total_issues=$((total_issues + 1))
    
    # 数据与存储
    check_memory_systems || total_issues=$((total_issues + 1))
    check_memory_storage || { total_issues=$((total_issues + 1)); restart_memory_storage && fixed_issues=$((fixed_issues + 1)); }
    check_disk_space || { total_issues=$((total_issues + 1)); cleanup_disk && fixed_issues=$((fixed_issues + 1)); }
    check_git_status || { total_issues=$((total_issues + 1)); auto_git_commit && fixed_issues=$((fixed_issues + 1)); }
    check_backup_status || total_issues=$((total_issues + 1))
    
    # 定时任务
    check_cron_logs || total_issues=$((total_issues + 1))
    check_hackernews || total_issues=$((total_issues + 1))
    check_nightly_build || total_issues=$((total_issues + 1))
    check_reports || total_issues=$((total_issues + 1))
    
    generate_report "$total_issues" "$fixed_issues"
    
    log "========== 自检完成 =========="
    log "发现问题: $total_issues | 自动修复: $fixed_issues"
    
    if [ $total_issues -gt 0 ]; then
        log "⚠️  发现 $total_issues 个问题"
        exit 1
    else
        log "✅ 所有检查通过"
        exit 0
    fi
}

main "$@"
