#!/bin/bash
#
# 自动小埋情绪发送器 - 只发送小埋风格表情包
# 检测到情绪关键词时自动发送
#

# 飞书配置
export FEISHU_APP_ID="cli_a9f5e960b8b81bb6"
export FEISHU_APP_SECRET="j9voDy9pm0q0SQaC4fMT1e1SYowDUWax"

# 目标用户
TARGET_USER="ou_a22ce6536f26dee3fec9397a9a1b87b5"
STICKER_DIR="$HOME/.openclaw/media/stickers/umaru_ai"

# 检测文本情绪并发送小埋表情包
detect_and_send() {
    local text="$1"
    local mood=""
    
    # 转小写
    text=$(echo "$text" | tr '[:upper:]' '[:lower:]')
    
    # 情绪检测（只使用小埋风格）
    if echo "$text" | grep -qE "(开心|高兴|棒|好耶|耶|哈哈|嘻嘻|谢谢|爱你|喜欢|happy|good|great|awesome|love|❤️|🎉)"; then
        mood="happy"
    elif echo "$text" | grep -qE "(难过|伤心|哭|悲|呜|泪|sad|cry|upset|😢|😭)"; then
        mood="sad"
    elif echo "$text" | grep -qE "(生气|愤怒|气|怒|哼|angry|mad|furious|😠|😡)"; then
        mood="angry"
    elif echo "$text" | grep -qE "(惊讶|震惊|哇|啊|咦|wtf|wow|shock|surprise|omg|😲|😮)"; then
        mood="shocked"
    elif echo "$text" | grep -qE "(困|累|睡|眠|sleepy|tired|sleep|exhausted|😴|💤)"; then
        mood="sleepy"
    elif echo "$text" | grep -qE "(游戏|玩|打|game|play|gaming|🎮|game)"; then
        mood="gaming"
    elif echo "$text" | grep -qE "(吃|喝|零食|薯片|可乐|cola|eat|drink|snack|🍿|🥤)"; then
        mood="snacks"
    elif echo "$text" | grep -qE "(疑惑|疑问|为什么|怎么|what|why|confused|question|🤔|❓)"; then
        mood="confused"
    elif echo "$text" | grep -qE "(得意|骄傲|嘿|哼|smug|proud|confident|😏)"; then
        mood="smug"
    elif echo "$text" | grep -qE "(酷|帅|厉害|cool|awesome|amazing|nice|😎|👍)"; then
        mood="cool"
    fi
    
    # 如果检测到情绪，发送小埋表情包
    if [ -n "$mood" ]; then
        echo "🎀 检测情绪: $mood → 发送小埋表情"
        
        # 查找对应情绪的最新小埋表情
        sticker_file=$(ls -t "$STICKER_DIR"/umaru_${mood}_*.jpg 2>/dev/null | head -1)
        
        # 如果没找到，使用随机小埋表情
        if [ -z "$sticker_file" ]; then
            sticker_file=$(ls -t "$STICKER_DIR"/umaru_*.jpg 2>/dev/null | head -1)
        fi
        
        if [ -f "$sticker_file" ]; then
            cd /root/.openclaw/workspace
            node skills/feishu-sticker/send.js \
              --target "$TARGET_USER" \
              --file "$sticker_file" >/dev/null 2>&1
            echo "✅ 已发送小埋 $mood 表情"
            return 0
        fi
    fi
    
    return 1
}

# 主入口 - 可以从外部调用
if [ $# -gt 0 ]; then
    detect_and_send "$1"
fi
