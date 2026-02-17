#!/bin/bash
# umaru-mood.sh - 小埋情绪表情包系统
# 干物妹小埋专用

set -euo pipefail

export FAL_KEY="bb2e0cea-fc85-41e9-a734-2a32cc889362:fdafdf28c8122642e92f07e06ee49def"
export FEISHU_APP_ID="cli_a9f5e960b8b81bb6"
export FEISHU_APP_SECRET="j9voDy9pm0q0SQaC4fMT1e1SYowDUWax"

TARGET_USER="${1:-ou_a22ce6536f26dee3fec9397a9a1b87b5}"
MOOD="${2:-happy}"
SAVE_DIR="$HOME/.openclaw/media/stickers/umaru_ai"

mkdir -p "$SAVE_DIR"

# 小埋角色特征
UMARU_BASE="Umaru Doma from Himouto Umaru-chan, anime style, blonde hair with orange gradient, purple eyes, orange hamster hoodie with ears, kawaii, moe style"

# 情绪到动作的映射
case "$MOOD" in
    "gaming"|"游戏"|"打游戏")
        ACTION="playing video games with game controller, excited, competitive face"
        FILENAME="umaru_gaming"
        ;;
    "cola"|"可乐"|"喝可乐")
        ACTION="drinking cola with straw, happy smile, holding bottle"
        FILENAME="umaru_cola"
        ;;
    "snacks"|"零食"|"吃薯片")
        ACTION="eating chips and snacks, lazy lying on floor, satisfied expression"
        FILENAME="umaru_snacks"
        ;;
    "sleepy"|"困"|"睡觉")
        ACTION="sleepy, yawning, about to sleep on floor, tired eyes"
        FILENAME="umaru_sleepy"
        ;;
    "happy"|"开心"|"高兴")
        ACTION="happy smile, peace sign pose, sparkling eyes, cheerful"
        FILENAME="umaru_happy"
        ;;
    "smug"|"得意"|"骄傲")
        ACTION="smug face, confident pose, slightly arrogant smile"
        FILENAME="umaru_smug"
        ;;
    "shocked"|"震惊"|"惊讶")
        ACTION="shocked expression, wide eyes, surprised pose"
        FILENAME="umaru_shocked"
        ;;
    "lazy"|"懒"|"废")
        ACTION="lazy lying down, unmotivated, relaxed, comfortable"
        FILENAME="umaru_lazy"
        ;;
    *)
        ACTION="cute pose, happy expression"
        FILENAME="umaru_cute"
        ;;
esac

PROMPT="${UMARU_BASE}, ${ACTION}, high quality anime art"

echo "🎀 生成小埋表情: $MOOD"

# 生成图片
JSON_PAYLOAD=$(jq -n \
  --arg prompt "$PROMPT" \
  '{prompt: $prompt, num_images: 1, output_format: "jpeg", image_size: "square_hd"}')

RESPONSE=$(curl -s -X POST "https://fal.run/xai/grok-imagine-image" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD")

IMAGE_URL=$(echo "$RESPONSE" | jq -r '.images[0].url // empty')

if [ -z "$IMAGE_URL" ]; then
    echo "❌ 生成失败: $RESPONSE"
    exit 1
fi

# 下载并保存
TEMP_IMAGE="$SAVE_DIR/${FILENAME}_$(date +%s).jpg"
curl -sL -o "$TEMP_IMAGE" "$IMAGE_URL"

# 发送到飞书
cd /root/.openclaw/workspace
node skills/feishu-sticker/send.js \
  --target "$TARGET_USER" \
  --file "$TEMP_IMAGE" 2>&1 | grep -E "(Sending|Success)"

echo "🎀 小埋表情 [$MOOD] 完成！"
