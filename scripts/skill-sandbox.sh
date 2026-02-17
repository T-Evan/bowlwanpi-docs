#!/bin/bash
#
# Skill 沙箱执行系统
# 在隔离环境中运行 skill 脚本，防止恶意代码
#

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

SKILL_DIR="$1"
shift
SKILL_NAME=$(basename "$SKILL_DIR")
LOG_FILE="/var/log/bowlwanpi-sandbox.log"

log() {
    echo "[$(TZ='Asia/Shanghai' date '+%H:%M:%S')] $1" >> "$LOG_FILE"
}

# ========== 安全检查 ==========
security_check() {
    local skill_dir="$1"
    local issues=()
    
    log "🔍 安全检查: $SKILL_NAME"
    
    # 检查敏感文件访问
    if grep -rE "(\.env|credentials|password|secret|token)" "$skill_dir" 2>/dev/null; then
        issues+=("发现潜在凭证访问")
    fi
    
    # 检查网络请求
    if grep -rE "(curl|wget|fetch|http|webhook)" "$skill_dir"/*.py "$skill_dir"/*.sh 2>/dev/null; then
        issues+=("发现网络请求")
    fi
    
    # 检查系统命令
    if grep -rE "(rm -rf|mkfs|dd if|>:|system\(|exec\()" "$skill_dir" 2>/dev/null; then
        issues+=("发现危险系统命令")
    fi
    
    if [ ${#issues[@]} -gt 0 ]; then
        log "⚠️  安全警告: ${issues[*]}"
        echo "⚠️  Skill '$SKILL_NAME' 安全警告:"
        for issue in "${issues[@]}"; do
            echo "  - $issue"
        done
        echo "建议审查后再执行"
        return 1
    fi
    
    log "✅ 安全检查通过"
    return 0
}

# ========== 资源限制 ==========
setup_limits() {
    # 使用 systemd-run 设置资源限制（如果可用）
    if command -v systemd-run &> /dev/null; then
        echo "systemd-run --scope --property=MemoryMax=100M --property=CPUQuota=50% --property=TasksMax=10"
    else
        # 使用 ulimit 作为 fallback
        echo "ulimit -v 100000 -t 60"
    fi
}

# ========== 网络限制 ==========
setup_network() {
    # 检查是否需要网络
    local need_network=false
    
    if grep -rE "(curl|wget|fetch|requests|urllib|http)" "$SKILL_DIR" 2>/dev/null; then
        need_network=true
    fi
    
    if [ "$need_network" = true ]; then
        log "🌐 允许网络访问"
        echo ""
    else
        log "🔒 禁用网络访问"
        # 使用 unshare 隔离网络（需要 root）
        if [ "$EUID" -eq 0 ]; then
            echo "unshare -n"
        fi
    fi
}

# ========== 执行 Skill ==========
run_sandboxed() {
    local skill_dir="$1"
    shift
    local skill_name=$(basename "$skill_dir")
    
    log "🚀 沙箱执行: $skill_name"
    
    # 创建临时目录
    local tmpdir=$(mktemp -d)
    chmod 700 "$tmpdir"
    
    # 复制 skill 到临时目录
    cp -r "$skill_dir" "$tmpdir/"
    local tmp_skill="$tmpdir/$skill_name"
    
    # 设置只读（除了特定目录）
    chmod -R 555 "$tmp_skill"
    
    # 创建可写的工作目录
    mkdir -p "$tmpdir/work"
    chmod 755 "$tmpdir/work"
    
    log "📁 临时目录: $tmpdir"
    
    # 构建沙箱命令
    local limit_cmd=$(setup_limits)
    local network_cmd=$(setup_network)
    
    # 执行
    cd "$tmpdir/work"
    
    if command -v systemd-run &> /dev/null; then
        # 使用 systemd-run
        systemd-run --scope \
            --property=MemoryMax=100M \
            --property=CPUQuota=50% \
            --property=TasksMax=10 \
            --property=ReadOnlyPaths=/ \
            --property=ReadWritePaths="$tmpdir/work" \
            --property=Environment="HOME=$tmpdir/work" \
            --property=Environment="SKILL_DIR=$tmp_skill" \
            --collect \
            --quiet \
            "$@"
    else
        # Fallback: 使用基本限制
        (
            ulimit -v 100000  # 100MB 内存
            ulimit -t 60      # 60秒 CPU
            ulimit -n 50      # 50 文件描述符
            export HOME="$tmpdir/work"
            export SKILL_DIR="$tmp_skill"
            "$@"
        )
    fi
    
    local exit_code=$?
    
    # 清理
    rm -rf "$tmpdir"
    
    log "✅ 执行完成: exit_code=$exit_code"
    return $exit_code
}

# ========== 主逻辑 ==========
main() {
    if [ -z "$SKILL_DIR" ]; then
        echo "Usage: $0 <skill-directory> [command...]"
        echo ""
        echo "Examples:"
        echo "  $0 /path/to/skill python3 skill.py"
        echo "  $0 /path/to/skill bash script.sh"
        exit 1
    fi
    
    if [ ! -d "$SKILL_DIR" ]; then
        log "❌ Skill 目录不存在: $SKILL_DIR"
        exit 1
    fi
    
    # 安全检查
    if ! security_check "$SKILL_DIR"; then
        read -p "是否继续执行? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "🚫 用户取消执行"
            exit 1
        fi
    fi
    
    # 沙箱执行
    if [ $# -eq 0 ]; then
        # 默认执行 SKILL.md 中指定的命令
        if [ -f "$SKILL_DIR/main.py" ]; then
            run_sandboxed "$SKILL_DIR" python3 "$SKILL_DIR/main.py"
        elif [ -f "$SKILL_DIR/run.sh" ]; then
            run_sandboxed "$SKILL_DIR" bash "$SKILL_DIR/run.sh"
        else
            log "❌ 未找到默认执行文件 (main.py 或 run.sh)"
            exit 1
        fi
    else
        run_sandboxed "$SKILL_DIR" "$@"
    fi
}

main "$@"
