#!/bin/bash
# 一分钟新闻定时推送脚本
# 每天早上 8:00 执行

WORKSPACE="/root/.openclaw/workspace"
SKILL_DIR="$WORKSPACE/skills/one-minute-news"
OUTPUT_DIR="$SKILL_DIR/output"
LOG_FILE="$WORKSPACE/memory/one-minute-news.log"

# 确保目录存在
mkdir -p "$OUTPUT_DIR"

# 获取今日日期
TODAY=$(date +%Y-%m-%d)

# 生成新闻
cd "$SKILL_DIR"
NEWS_OUTPUT=$(python3 scripts/generate.py 2>&1)

# 检查是否生成成功
if [ -f "$OUTPUT_DIR/news_${TODAY}.txt" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 新闻生成成功: ${TODAY}" >> "$LOG_FILE"
    
    # 读取内容并发送
    NEWS_CONTENT=$(cat "$OUTPUT_DIR/news_${TODAY}.txt")
    
    # 使用 OpenClaw message 发送（需要在 OpenClaw 环境中执行）
    # 这里只是记录，实际推送由 OpenClaw cron 调用
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 内容已生成，等待推送" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 新闻生成失败" >> "$LOG_FILE"
fi
