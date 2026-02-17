#!/bin/bash
# auto_mood_sender.sh - 自动检测情绪并发送表情
# 检测文本情绪，自动发送对应的小埋表情包

set -euo pipefail

# shellcheck source=/root/.openclaw/workspace/scripts/load-secrets.sh
source /root/.openclaw/workspace/scripts/load-secrets.sh
load_secret_env

if ! require_env_vars FEISHU_APP_ID FEISHU_APP_SECRET; then
    exit 1
fi

TARGET_USER="${1:-user:ou_a22ce6536f26dee3fec9397a9a1b87b5}"
INPUT_TEXT="${2:-}"
STICKER_DIR="$HOME/.openclaw/media/stickers/umaru_ai"

# 确保目录存在
mkdir -p "$STICKER_DIR"

# 情绪检测函数
detect_mood() {
    local text="$1"
    local mood="default"
    
    # 转换小写便于匹配
    text=$(echo "$text" | tr '[:upper:]' '[:lower:]')
    
    # 检测各种情绪关键词
    if echo "$text" | grep -qE "(开心|高兴|棒|好耶|耶|哈哈|嘻嘻|谢谢|爱你|喜欢|happy|good|great|awesome|love)"; then
        mood="happy"
    elif echo "$text" | grep -qE "(难过|伤心|哭|悲|呜|泪|sad|cry|upset|sorry)"; then
        mood="sad"
    elif echo "$text" | grep -qE "(生气|愤怒|气|怒|哼|angry|mad|furious)"; then
        mood="angry"
    elif echo "$text" | grep -qE "(惊讶|震惊|哇|啊|咦|wtf|wow|shock|surprise|omg)"; then
        mood="shocked"
    elif echo "$text" | grep -qE "(困|累|睡|眠|sleepy|tired|sleep|exhausted)"; then
        mood="sleepy"
    elif echo "$text" | grep -qE "(游戏|玩|打|game|play|gaming)"; then
        mood="gaming"
    elif echo "$text" | grep -qE "(吃|喝|零食|薯片|可乐|cola|eat|drink|snack)"; then
        mood="snacks"
    elif echo "$text" | grep -qE "(疑惑|疑问|为什么|怎么|what|why|confused|question)"; then
        mood="confused"
    elif echo "$text" | grep -qE "(得意|骄傲|嘿|哼|smug|proud|confident)"; then
        mood="smug"
    elif echo "$text" | grep -qE "(酷|帅|厉害|cool|awesome|amazing|nice)"; then
        mood="cool"
    else
        # 默认随机选择
        MOODS=(happy sleepy snacks gaming)
        RANDOM_INDEX=$((RANDOM % ${#MOODS[@]}))
        mood=${MOODS[$RANDOM_INDEX]}
    fi
    
    echo "$mood"
}

# 获取最新生成的对应情绪的表情
get_sticker() {
    local mood="$1"
    local sticker_file
    
    # 查找对应情绪的最新表情
    sticker_file=$(ls -t "$STICKER_DIR"/umaru_${mood}_*.jpg 2>/dev/null | head -1)
    
    if [ -z "$sticker_file" ] || [ ! -f "$sticker_file" ]; then
        # 如果没有找到，生成一个
        echo "生成新的表情: $mood"
        bash /root/.openclaw/workspace/scripts/umaru_mood.sh "$TARGET_USER" "$mood" >/dev/null 2>&1
        sticker_file=$(ls -t "$STICKER_DIR"/umaru_${mood}_*.jpg 2>/dev/null | head -1)
    fi
    
    echo "$sticker_file"
}

# 主逻辑
echo "🎭 检测文本情绪..."
DETECTED_MOOD=$(detect_mood "$INPUT_TEXT")
echo "🎀 检测到情绪: $DETECTED_MOOD"

# 获取表情文件
STICKER_FILE=$(get_sticker "$DETECTED_MOOD")

if [ -f "$STICKER_FILE" ]; then
    echo "📤 发送表情: $(basename "$STICKER_FILE")"
    
    # 发送到飞书
    cd /root/.openclaw/workspace
    node skills/feishu-sticker/send.js \
      --target "$TARGET_USER" \
      --file "$STICKER_FILE" 2>&1 | grep -E "(Sending|Success|Error)"
    
    echo "✅ 情绪表情发送完成！"
else
    echo "❌ 未找到表情文件"
    exit 1
fi
