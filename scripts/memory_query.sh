#!/bin/bash
#
# 🧠 QMDR 记忆检索工具
# 简化 QMDR 使用，整合到碗皮的记忆系统
#

# 搜索记忆
search_memory() {
    local query="$1"
    echo "🔍 搜索记忆: $query"
    echo ""
    qmd query "$query" -n 5 2>&1
}

# 语义搜索
semantic_search() {
    local query="$1"
    echo "🧠 语义搜索: $query"
    echo ""
    qmd vsearch "$query" -n 5 2>&1
}

# 添加新记忆
add_memory() {
    local file="$1"
    local collection="${2:-memory}"
    
    if [ ! -f "$file" ]; then
        echo "❌ 文件不存在: $file"
        return 1
    fi
    
    echo "📚 添加记忆: $(basename $file) → $collection"
    qmd collection add "$file" --name "$collection" 2>&1
    
    # 更新索引
    echo "🔄 更新索引..."
    qmd update > /dev/null 2>&1
    
    echo "✅ 记忆已添加"
}

# 查看记忆状态
memory_status() {
    echo "📊 QMDR 记忆状态"
    echo "================"
    echo ""
    qmd status 2>&1
    
    echo ""
    echo "📚 集合列表:"
    qmd collection list 2>&1
}

# 主函数
main() {
    case "$1" in
        "search"|"s")
            shift
            search_memory "$@"
            ;;
        "semantic"|"v")
            shift
            semantic_search "$@"
            ;;
        "add"|"a")
            shift
            add_memory "$@"
            ;;
        "status"|"st")
            memory_status
            ;;
        "update"|"u")
            echo "🔄 更新索引..."
            qmd update 2>&1
            ;;
        *)
            echo "🧠 QMDR 记忆工具"
            echo ""
            echo "用法:"
            echo "  $0 search '关键词'      # 搜索记忆"
            echo "  $0 semantic '描述'      # 语义搜索"
            echo "  $0 add 文件.md [集合]   # 添加记忆"
            echo "  $0 status               # 查看状态"
            echo "  $0 update               # 更新索引"
            echo ""
            echo "示例:"
            echo "  $0 search '安全扫描'"
            echo "  $0 semantic '如何监控系统'"
            ;;
    esac
}

main "$@"
