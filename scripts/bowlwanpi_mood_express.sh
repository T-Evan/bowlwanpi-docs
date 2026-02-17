#!/bin/bash
#
# 碗皮情绪感知系统 - 根据我的心情发送小埋表情包
# 结合对话内容分析和现有情绪系统
#

export FEISHU_APP_ID="cli_a9f5e960b8b81bb6"
export FEISHU_APP_SECRET="j9voDy9pm0q0SQaC4fMT1e1SYowDUWax"
export FAL_KEY="bb2e0cea-fc85-41e9-a734-2a32cc889362:fdafdf28c8122642e92f07e06ee49def"

TARGET_USER="user:ou_a22ce6536f26dee3fec9397a9a1b87b5"
STICKER_DIR="$HOME/.openclaw/media/stickers/umaru_ai"
MOOD_STATE_FILE="$HOME/.openclaw/workspace/memory/bowlwanpi_mood.json"

# 确保目录存在
mkdir -p "$STICKER_DIR"
mkdir -p "$(dirname "$MOOD_STATE_FILE")"

# 初始化或读取当前情绪状态
init_mood() {
    if [ ! -f "$MOOD_STATE_FILE" ]; then
        cat > "$MOOD_STATE_FILE" << 'EOF'
{
  "current_mood": "happy",
  "mood_score": 70,
  "energy_level": 80,
  "last_update": "",
  "mood_history": [],
  "context": "初始化状态"
}
EOF
    fi
}

# 更新情绪状态
update_mood() {
    local context="$1"
    local new_mood="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # 更新情绪文件
    cat > "$MOOD_STATE_FILE" << EOF
{
  "current_mood": "$new_mood",
  "mood_score": $(shuf -i 50-95 -n 1),
  "energy_level": $(shuf -i 40-100 -n 1),
  "last_update": "$timestamp",
  "context": "$context"
}
EOF
    
    echo "$new_mood"
}

# 分析对话内容判断我的情绪
analyze_my_mood() {
    local conversation="$1"
    local mood="happy"
    
    # 根据对话内容判断我应该有的情绪
    # 任务完成/成功 → excited
    # 遇到问题 → confused/concerned
    # 长时间工作 → sleepy/tired
    # 被夸奖 → happy/proud
    # 系统正常 → relaxed
    
    if echo "$conversation" | grep -qE "(完成|成功|搞定|厉害|棒|优秀|🎉|✅|完美)"; then
        mood="excited"
    elif echo "$conversation" | grep -qE "(错误|失败|问题|异常|警告|⚠️|❌|bug|fail)"; then
        mood="concerned"
    elif echo "$conversation" | grep -qE "(累|困|休息|睡觉|💤|tired|sleepy)"; then
        mood="sleepy"
    elif echo "$conversation" | grep -qE "(谢谢|感谢|夸|好孩子|聪明|love|❤️)"; then
        mood="loved"
    elif echo "$conversation" | grep -qE "(测试|试试|看看|检查|👀|test)"; then
        mood="curious"
    elif echo "$conversation" | grep -qE "(吃|零食|喝|可乐|🍿|🥤|饿)"; then
        mood="hungry"
    elif echo "$conversation" | grep -qE "(游戏|玩|打|🎮|game|fun)"; then
        mood="playful"
    elif echo "$conversation" | grep -qE "(正常|OK|顺利|一切安好|🟢|good)"; then
        mood="content"
    else
        # 默认保持之前的情绪或随机
        if [ -f "$MOOD_STATE_FILE" ]; then
            mood=$(cat "$MOOD_STATE_FILE" | grep -o '"current_mood": "[^"]*"' | cut -d'"' -f4)
        fi
        [ -z "$mood" ] && mood="happy"
    fi
    
    echo "$mood"
}

# 生成并发送对应情绪的小埋表情
send_mood_sticker() {
    local mood="$1"
    local context="$2"
    
    # 映射我的情绪到小埋动作
    local umaru_action=""
    case "$mood" in
        "excited"|"proud")
            umaru_action="excited, celebrating with happy pose, sparkling eyes"
            ;;
        "concerned"|"worried")
            umaru_action="worried, concerned expression, thinking pose"
            ;;
        "sleepy"|"tired")
            umaru_action="sleepy, yawning, tired eyes, about to nap"
            ;;
        "loved"|"grateful")
            umaru_action="happy, blushing, heart eyes, grateful smile"
            ;;
        "curious"|"interested")
            umaru_action="curious, peeking, interested expression"
            ;;
        "hungry"|"snacking")
            umaru_action="eating snacks, happy munching, satisfied"
            ;;
        "playful"|"gaming")
            umaru_action="playing games, excited, competitive face"
            ;;
        "content"|"relaxed")
            umaru_action="relaxed, comfortable, peaceful smile"
            ;;
        *)
            umaru_action="happy, cheerful, cute pose, smiling"
            ;;
    esac
    
    # 生成提示词
    local prompt="Umaru Doma from Himouto Umaru-chan, anime style, blonde hair with orange gradient, purple eyes, orange hamster hoodie, ${umaru_action}, kawaii, moe style, high quality"
    
    echo "🎀 碗皮当前心情: $mood"
    echo "🎭 生成小埋表情: $context"
    
    # 调用AI生成
    local JSON_PAYLOAD=$(jq -n \
      --arg prompt "$prompt" \
      '{prompt: $prompt, num_images: 1, output_format: "jpeg", image_size: "square_hd"}')
    
    local RESPONSE=$(curl -s -X POST "https://fal.run/xai/grok-imagine-image" \
      -H "Authorization: Key $FAL_KEY" \
      -H "Content-Type: application/json" \
      -d "$JSON_PAYLOAD")
    
    local IMAGE_URL=$(echo "$RESPONSE" | jq -r '.images[0].url // empty')
    
    if [ -n "$IMAGE_URL" ]; then
        # 下载
        local TEMP_FILE="$STICKER_DIR/umaru_${mood}_$(date +%s).jpg"
        curl -sL -o "$TEMP_FILE" "$IMAGE_URL"
        
        # 发送到飞书
        cd /root/.openclaw/workspace
        node skills/feishu-sticker/send.js \
          --target "$TARGET_USER" \
          --file "$TEMP_FILE" >/dev/null 2>&1
        
        echo "✅ 已根据心情[$mood]发送小埋表情"
        
        # 更新情绪状态
        update_mood "$context" "$mood"
        
        return 0
    fi
    
    return 1
}

# 主动表达情绪（随机）
express_random_mood() {
    local moods=("happy" "excited" "content" "curious" "playful")
    local random_mood=${moods[$RANDOM % ${#moods[@]}]}
    
    send_mood_sticker "$random_mood" "随机表达心情"
}

# 主入口
main() {
    init_mood
    
    if [ $# -gt 0 ]; then
        # 分析对话并发送
        local context="$1"
        local mood=$(analyze_my_mood "$context")
        send_mood_sticker "$mood" "$context"
    else
        # 随机表达
        express_random_mood
    fi
}

main "$@"
