#!/bin/bash
# BowlWanpi 社交媒体监控脚本 v1.0
# 监控平台: 小红书、抖音、知乎
# 执行频率: 每小时检查小红书，每2小时检查抖音，每天检查知乎

set -e

# 配置
WORKSPACE="/root/.openclaw/workspace"
LOG_DIR="/var/log"
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M:%S)
LOG_FILE="${LOG_DIR}/bowlwanpi-social-media.log"
REPORT_FILE="${WORKSPACE}/memory/social-media-${DATE}.md"

# 环境变量
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
export PATH="/root/.nvm/versions/node/v22.22.0/bin:$PATH"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 初始化报告
init_report() {
    cat > "$REPORT_FILE" << EOF
# 社交媒体监控报告

**日期**: ${DATE}  
**时间**: ${TIME}  
**监控平台**: 小红书、抖音、知乎

---

EOF
}

# 监控小红书
monitor_xiaohongshu() {
    log "[小红书] 开始监控..."
    
    local xhs_log="${WORKSPACE}/memory/xiaohongshu-${DATE}-${TIME}.json"
    
    # 检查小红书MCP服务器是否运行
    if ! pgrep -f "xiaohongshu-mcp" > /dev/null; then
        log "[小红书] ⚠️  MCP服务器未运行，跳过监控"
        echo "- **小红书**: ⚠️ 服务器未运行" >> "$REPORT_FILE"
        return
    fi
    
    # 搜索热门关键词
    local keywords=("AI" "科技" "数码" "生活" "美食")
    local all_results=""
    
    for keyword in "${keywords[@]}"; do
        log "[小红书] 搜索关键词: $keyword"
        
        # 使用 xhs_client.py 搜索
        local result=$(python3 "${WORKSPACE}/skills/xiaohongshu-mcp/scripts/xhs_client.py" search "$keyword" 2>/dev/null || echo "")
        
        if [ -n "$result" ]; then
            all_results="${all_results}\n## 关键词: ${keyword}\n\n${result}\n"
            log "[小红书] ✅ 获取到 ${keyword} 的搜索结果"
        else
            log "[小红书] ⚠️  ${keyword} 搜索无结果"
        fi
        
        sleep 2  # 避免请求过快
    done
    
    # 获取推荐feed
    log "[小红书] 获取推荐feed..."
    local feeds=$(python3 "${WORKSPACE}/skills/xiaohongshu-mcp/scripts/xhs_client.py" feeds 2>/dev/null || echo "")
    
    if [ -n "$feeds" ]; then
        all_results="${all_results}\n## 推荐Feed\n\n${feeds}\n"
        log "[小红书] ✅ 获取到推荐feed"
    fi
    
    # 保存结果
    if [ -n "$all_results" ]; then
        echo -e "$all_results" > "$xhs_log"
        
        # 提取热门笔记数量
        local note_count=$(echo -e "$all_results" | grep -c "note_id" || echo "0")
        
        echo "- **小红书**: ✅ 监控完成，获取 ${note_count} 条热门笔记" >> "$REPORT_FILE"
        log "[小红书] ✅ 监控完成，获取 ${note_count} 条笔记"
        
        # 发送到Feishu (可选)
        # openclaw message send --channel feishu --target "your-id" --message "📕 小红书监控完成: ${note_count}条热门笔记"
    else
        echo "- **小红书**: ⚠️ 无数据" >> "$REPORT_FILE"
        log "[小红书] ⚠️ 未获取到数据"
    fi
}

# 监控抖音
monitor_douyin() {
    log "[抖音] 开始监控..."
    
    # 获取抖音热门视频ID列表 (从外部API或配置读取)
    # 这里使用示例ID
    local hot_videos=("7599980362898427178" "7601234567890123456")
    local douyin_log="${WORKSPACE}/memory/douyin-${DATE}-${TIME}.log"
    local download_count=0
    
    for video_id in "${hot_videos[@]}"; do
        log "[抖音] 下载视频: $video_id"
        
        # 使用 douyin-video-fetch 下载视频
        if python3 "${WORKSPACE}/skills/douyin-video-fetch/scripts/fetch_video.py" "$video_id" --output-dir "${WORKSPACE}/downloads/douyin" >> "$douyin_log" 2>&1; then
            ((download_count++))
            log "[抖音] ✅ 视频 ${video_id} 下载成功"
        else
            log "[抖音] ⚠️  视频 ${video_id} 下载失败"
        fi
        
        sleep 3  # 避免请求过快
    done
    
    if [ $download_count -gt 0 ]; then
        echo "- **抖音**: ✅ 下载 ${download_count} 个热门视频" >> "$REPORT_FILE"
        log "[抖音] ✅ 监控完成，下载 ${download_count} 个视频"
    else
        echo "- **抖音**: ⚠️ 无新视频" >> "$REPORT_FILE"
        log "[抖音] ⚠️ 未下载到新视频"
    fi
}

# 监控知乎
monitor_zhihu() {
    log "[知乎] 开始监控..."
    
    # 检查知乎API配置
    if [ -z "$ZHIHU_APP_KEY" ] || [ -z "$ZHIHU_APP_SECRET" ]; then
        # 尝试从环境文件加载
        if [ -f "${WORKSPACE}/skills/zhihu/.env" ]; then
            export $(cat "${WORKSPACE}/skills/zhihu/.env" | xargs)
        fi
    fi
    
    if [ -z "$ZHIHU_APP_KEY" ]; then
        log "[知乎] ⚠️  未配置API密钥，跳过监控"
        echo "- **知乎**: ⚠️ 未配置API" >> "$REPORT_FILE"
        return
    fi
    
    local zhihu_log="${WORKSPACE}/memory/zhihu-${DATE}-${TIME}.json"
    local ring_id="2001009660925334090"  # AI圈子
    
    log "[知乎] 获取圈子内容..."
    
    # 获取圈子详情
    local ring_detail=$(python3 "${WORKSPACE}/skills/zhihu/scripts/zhihu_bot.py" ring detail "$ring_id" 1 20 2>/dev/null || echo "")
    
    if [ -n "$ring_detail" ]; then
        echo "$ring_detail" > "$zhihu_log"
        
        # 统计想法数量
        local pin_count=$(echo "$ring_detail" | grep -c "pin" || echo "0")
        
        echo "- **知乎**: ✅ 获取 ${pin_count} 条想法" >> "$REPORT_FILE"
        log "[知乎] ✅ 监控完成，获取 ${pin_count} 条想法"
    else
        echo "- **知乎**: ⚠️ 获取失败" >> "$REPORT_FILE"
        log "[知乎] ⚠️ 获取圈子内容失败"
    fi
}

# 生成汇总报告
generate_summary() {
    log "[汇总] 生成报告..."
    
    cat >> "$REPORT_FILE" << EOF

---

**监控时间**: $(date '+%Y-%m-%d %H:%M:%S')  
**日志文件**: ${LOG_FILE}

## 详细数据位置

- 小红书数据: \`memory/xiaohongshu-${DATE}-*.json\`
- 抖音数据: \`memory/douyin-${DATE}-*.log\`
- 知乎数据: \`memory/zhihu-${DATE}-*.json\`

## 下一步行动建议

1. 查看各平台的热门内容
2. 分析趋势话题
3. 准备相关内容创作
4. 定时发布到对应平台

EOF

    log "[汇总] 报告已保存: $REPORT_FILE"
}

# 主函数
main() {
    log "=== 社交媒体监控开始 ==="
    
    # 初始化报告
    init_report
    
    # 根据参数执行不同平台的监控
    case "$1" in
        xiaohongshu|xhs)
            monitor_xiaohongshu
            ;;
        douyin|dy)
            monitor_douyin
            ;;
        zhihu|zh)
            monitor_zhihu
            ;;
        all|*)
            monitor_xiaohongshu
            monitor_douyin
            monitor_zhihu
            ;;
    esac
    
    # 生成汇总
    generate_summary
    
    log "=== 社交媒体监控完成 ==="
}

# 执行主函数
main "$@"

exit 0
