#!/bin/bash
#
# 🛡️ 定时任务前置检查器
# 在执行推送任务前检查依赖服务
#

# 配置
CHECK_TIMEOUT=10
RETRIES=3
RETRY_DELAY=5

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ========== 检查函数 ==========

check_gateway() {
    local retry=0
    
    while [ $retry -lt $RETRIES ]; do
        if pgrep -f "openclaw.*gateway" > /dev/null 2>&1; then
            # 进一步检查端口
            if nc -z localhost 18789 2>/dev/null; then
                echo -e "${GREEN}✅${NC} Gateway 运行正常 (PID: $(pgrep -f 'openclaw.*gateway' | head -1), 端口: 18789)"
                return 0
            else
                echo -e "${YELLOW}⚠️${NC} Gateway 进程存在但端口无响应，尝试重启..."
            fi
        fi
        
        retry=$((retry + 1))
        if [ $retry -lt $RETRIES ]; then
            echo "  重试 ($retry/$RETRIES)..."
            sleep $RETRY_DELAY
        fi
    done
    
    echo -e "${RED}❌${NC} Gateway 未运行或无法访问"
    return 1
}

check_mihomo() {
    if pgrep -f "mihomo" > /dev/null 2>&1; then
        # 检查端口
        if nc -z localhost 7890 2>/dev/null; then
            echo -e "${GREEN}✅${NC} Mihomo 代理运行正常 (端口: 7890)"
            return 0
        else
            echo -e "${YELLOW}⚠️${NC} Mihomo 进程存在但端口无响应"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️${NC} Mihomo 未运行 (可选依赖)"
        return 0  # Mihomo 是可选的
    fi
}

check_network() {
    # 检查外网连通性
    if curl -s --max-time 5 --noproxy "*" -o /dev/null -w "%{http_code}" "http://www.google.com/generate_204" | grep -q "204"; then
        echo -e "${GREEN}✅${NC} 网络连通性正常 (可访问 Google)"
        return 0
    else
        echo -e "${YELLOW}⚠️${NC} 网络可能受限，尝试访问国内站点..."
        
        # 尝试国内站点
        if curl -s --max-time 5 -o /dev/null -w "%{http_code}" "https://www.baidu.com" | grep -q "200"; then
            echo -e "${GREEN}✅${NC} 国内网络正常"
            return 0
        else
            echo -e "${RED}❌${NC} 网络连接异常"
            return 1
        fi
    fi
}

check_disk_space() {
    local usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [ "$usage" -gt 95 ]; then
        echo -e "${RED}❌${NC} 磁盘空间严重不足 (${usage}%)"
        return 1
    elif [ "$usage" -gt 80 ]; then
        echo -e "${YELLOW}⚠️${NC} 磁盘空间不足 (${usage}%)"
        return 0
    else
        echo -e "${GREEN}✅${NC} 磁盘空间充足 (${usage}%)"
        return 0
    fi
}

check_memory() {
    local usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    
    if [ "$usage" -gt 95 ]; then
        echo -e "${RED}❌${NC} 内存使用率过高 (${usage}%)"
        return 1
    elif [ "$usage" -gt 85 ]; then
        echo -e "${YELLOW}⚠️${NC} 内存使用率偏高 (${usage}%)"
        return 0
    else
        echo -e "${GREEN}✅${NC} 内存使用正常 (${usage}%)"
        return 0
    fi
}

# ========== 修复函数 ==========

fix_gateway() {
    echo "🔧 尝试修复 Gateway..."
    
    # 先停止可能残留的进程
    pkill -f "openclaw.*gateway" 2>/dev/null
    sleep 2
    
    # 启动 Gateway
    openclaw gateway start &
    sleep 5
    
    # 检查是否成功
    if check_gateway; then
        echo -e "${GREEN}✅${NC} Gateway 修复成功"
        
        # 同时启动 Watchdog
        if [ -f "$HOME/claw_start.sh" ]; then
            nohup "$HOME/claw_start.sh" > /tmp/watchdog.log 2>&1 &
            echo "🛡️ Watchdog 已启动"
        fi
        
        return 0
    else
        echo -e "${RED}❌${NC} Gateway 修复失败"
        return 1
    fi
}

# ========== 主检查函数 ==========

run_precheck() {
    local task_name="${1:-推送任务}"
    local auto_fix="${2:-true}"
    
    echo ""
    echo "🛡️ 前置检查: $task_name"
    echo "================================"
    
    local failed_checks=()
    local can_fix=false
    
    # 1. 检查 Gateway (必需)
    echo ""
    echo "1️⃣ 检查 OpenClaw Gateway..."
    if ! check_gateway; then
        failed_checks+=("Gateway")
        can_fix=true
    fi
    
    # 2. 检查 Mihomo (可选)
    echo ""
    echo "2️⃣ 检查 Mihomo 代理..."
    check_mihomo
    # Mihomo 失败不阻止任务
    
    # 3. 检查网络
    echo ""
    echo "3️⃣ 检查网络连通性..."
    if ! check_network; then
        failed_checks+=("网络")
    fi
    
    # 4. 检查磁盘空间
    echo ""
    echo "4️⃣ 检查磁盘空间..."
    if ! check_disk_space; then
        failed_checks+=("磁盘空间")
    fi
    
    # 5. 检查内存
    echo ""
    echo "5️⃣ 检查内存使用..."
    if ! check_memory; then
        failed_checks+=("内存")
    fi
    
    # 总结
    echo ""
    echo "================================"
    
    if [ ${#failed_checks[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ 所有检查通过，可以执行 $task_name${NC}"
        return 0
    else
        echo -e "${RED}❌ 检查失败: ${failed_checks[*]}${NC}"
        
        # 尝试自动修复
        if [ "$auto_fix" = "true" ] && [ "$can_fix" = "true" ]; then
            echo ""
            echo "🔧 尝试自动修复..."
            
            if [[ " ${failed_checks[*]} " =~ " Gateway " ]]; then
                if fix_gateway; then
                    echo ""
                    echo -e "${GREEN}✅ 自动修复成功，重新检查...${NC}"
                    sleep 3
                    
                    # 重新检查
                    if check_gateway; then
                        echo -e "${GREEN}✅ 检查通过，继续执行 $task_name${NC}"
                        return 0
                    fi
                fi
            fi
        fi
        
        echo ""
        echo -e "${RED}❌ $task_name 中止执行${NC}"
        return 1
    fi
}

# ========== 快捷函数 ==========

check_and_run() {
    # 用法: check_and_run "任务名" "要执行的命令"
    local task_name="$1"
    shift
    local command="$@"
    
    if run_precheck "$task_name" "true"; then
        echo ""
        echo "🚀 执行: $task_name"
        echo "================================"
        eval "$command"
        return $?
    else
        # 记录失败
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] $task_name 因前置检查失败未执行" >> /var/log/bowlwanpi-precheck-failures.log
        return 1
    fi
}

# ========== 主入口 ==========

case "${1:-check}" in
    check)
        run_precheck "${2:-任务}" "${3:-true}"
        ;;
    gateway)
        check_gateway
        ;;
    fix)
        fix_gateway
        ;;
    run)
        check_and_run "$2" "$3"
        ;;
    *)
        echo "用法: $0 [check|gateway|fix|run]"
        echo ""
        echo "  check [任务名] [auto_fix] - 运行完整前置检查"
        echo "  gateway                    - 仅检查 Gateway"
        echo "  fix                        - 尝试修复 Gateway"
        echo "  run '任务名' '命令'       - 检查通过后执行命令"
        echo ""
        echo "示例:"
        echo "  $0 check '微博热搜推送' true"
        echo "  $0 run 'B站热门' 'python3 /scripts/bilibili_hot.py'"
        exit 1
        ;;
esac
