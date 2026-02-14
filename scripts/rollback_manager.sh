#!/bin/bash
#
# 🔄 Rollback Manager - 回滚管理器
# 自动创建回滚点，支持快速恢复
#

set -e

WORKSPACE="/root/.openclaw/workspace"
ROLLBACK_DIR="$WORKSPACE/.rollbacks"
MAX_ROLLBACKS=10

# 初始化回滚目录
mkdir -p "$ROLLBACK_DIR"

# 创建回滚点
create_rollback_point() {
    local name="${1:-$(date +%Y%m%d_%H%M%S)}"
    local rollback_path="$ROLLBACK_DIR/$name"
    
    echo "🔄 创建回滚点: $name"
    
    # 创建回滚目录
    mkdir -p "$rollback_path"
    
    # 备份关键文件
    cp -r "$WORKSPACE/scripts" "$rollback_path/" 2>/dev/null || true
    cp -r "$WORKSPACE/learning" "$rollback_path/" 2>/dev/null || true
    cp "$WORKSPACE/SECURITY.md" "$rollback_path/" 2>/dev/null || true
    
    # 记录元数据
    cat > "$rollback_path/meta.json" << META
{
    "name": "$name",
    "created": "$(date -Iseconds)",
    "files": [
        "scripts/",
        "learning/",
        "SECURITY.md"
    ]
}
META
    
    echo "✅ 回滚点已创建: $rollback_path"
    
    # 清理旧回滚点
    cleanup_old_rollbacks
}

# 回滚到指定点
rollback_to() {
    local name="$1"
    local rollback_path="$ROLLBACK_DIR/$name"
    
    if [ ! -d "$rollback_path" ]; then
        echo "❌ 回滚点不存在: $name"
        return 1
    fi
    
    echo "🔄 开始回滚到: $name"
    
    # 先创建当前状态的回滚点（以防万一）
    create_rollback_point "pre_rollback_$(date +%Y%m%d_%H%M%S)"
    
    # 执行回滚
    if [ -d "$rollback_path/scripts" ]; then
        cp -r "$rollback_path/scripts/"* "$WORKSPACE/scripts/" 2>/dev/null || true
        echo "✅ 脚本已回滚"
    fi
    
    if [ -d "$rollback_path/learning" ]; then
        cp -r "$rollback_path/learning/"* "$WORKSPACE/learning/" 2>/dev/null || true
        echo "✅ 学习资料已回滚"
    fi
    
    if [ -f "$rollback_path/SECURITY.md" ]; then
        cp "$rollback_path/SECURITY.md" "$WORKSPACE/"
        echo "✅ 安全文档已回滚"
    fi
    
    echo "✅ 回滚完成"
}

# 清理旧回滚点
cleanup_old_rollbacks() {
    local count=$(ls -1d "$ROLLBACK_DIR"/* 2>/dev/null | wc -l)
    
    if [ "$count" -gt "$MAX_ROLLBACKS" ]; then
        echo "🧹 清理旧回滚点..."
        ls -1td "$ROLLBACK_DIR"/* | tail -n +$((MAX_ROLLBACKS + 1)) | xargs rm -rf
    fi
}

# 列出回滚点
list_rollbacks() {
    echo "📋 可用回滚点:"
    ls -1td "$ROLLBACK_DIR"/* 2>/dev/null | while read path; do
        local name=$(basename "$path")
        local time=$(stat -c %y "$path" 2>/dev/null | cut -d'.' -f1)
        echo "  - $name ($time)"
    done
}

# 主函数
main() {
    local command="$1"
    shift
    
    case "$command" in
        create)
            create_rollback_point "$@"
            ;;
        rollback)
            rollback_to "$@"
            ;;
        list)
            list_rollbacks
            ;;
        cleanup)
            cleanup_old_rollbacks
            echo "🧹 旧回滚点已清理"
            ;;
        *)
            echo "用法: $0 {create|rollback|list|cleanup} [参数]"
            echo ""
            echo "命令:"
            echo "  create [name]     - 创建回滚点"
            echo "  rollback <name>   - 回滚到指定点"
            echo "  list              - 列出回滚点"
            echo "  cleanup           - 清理旧回滚点"
            ;;
    esac
}

main "$@"
