#!/bin/bash
# umaru-mood.sh - 小埋情绪表情包系统（含本地兜底）

set -u -o pipefail

# shellcheck source=/root/.openclaw/workspace/scripts/load-secrets.sh
source /root/.openclaw/workspace/scripts/load-secrets.sh
load_secret_env

if ! require_env_vars FEISHU_APP_ID FEISHU_APP_SECRET; then
    exit 1
fi

TARGET_USER="${1:-user:ou_a22ce6536f26dee3fec9397a9a1b87b5}"
MOOD="${2:-happy}"
SAVE_DIR="$HOME/.openclaw/media/stickers/umaru_ai"

mkdir -p "$SAVE_DIR"

send_local_fallback() {
    local mood="$1"
    local preferred
    preferred=$(ls -t "$SAVE_DIR"/umaru_${mood}_*.jpg 2>/dev/null | head -1)

    if [ -z "$preferred" ]; then
        preferred=$(ls -t "$SAVE_DIR"/umaru_*.jpg 2>/dev/null | head -1)
    fi

    if [ -z "$preferred" ] || [ ! -f "$preferred" ]; then
        echo "❌ 本地库存为空，无法兜底"
        return 1
    fi

    cd /root/.openclaw/workspace
    if node skills/feishu-sticker/send.js --target "$TARGET_USER" --file "$preferred" 2>&1 | grep -E "(Sending|Success)" >/dev/null; then
        echo "🧩 使用本地兜底发送: $(basename "$preferred")"
        return 0
    fi

    echo "❌ 本地兜底发送失败"
    return 1
}

# 小埋角色特征
UMARU_BASE="Umaru Doma from Himouto Umaru-chan, anime style, blonde hair with orange gradient, purple eyes, orange hamster hoodie with ears, kawaii, moe style"

# 情绪到动作的映射
case "$MOOD" in
    "gaming"|"游戏"|"打游戏")
        ACTION="playing video games with game controller, excited, competitive face"
        FILE_KEY="gaming"
        ;;
    "cola"|"可乐"|"喝可乐")
        ACTION="drinking cola with straw, happy smile, holding bottle"
        FILE_KEY="cola"
        ;;
    "snacks"|"零食"|"吃薯片")
        ACTION="eating chips and snacks, lazy lying on floor, satisfied expression"
        FILE_KEY="snacks"
        ;;
    "sleepy"|"困"|"睡觉")
        ACTION="sleepy, yawning, about to sleep on floor, tired eyes"
        FILE_KEY="sleepy"
        ;;
    "happy"|"开心"|"高兴")
        ACTION="happy smile, peace sign pose, sparkling eyes, cheerful"
        FILE_KEY="happy"
        ;;
    "smug"|"得意"|"骄傲")
        ACTION="smug face, confident pose, slightly arrogant smile"
        FILE_KEY="smug"
        ;;
    "shocked"|"震惊"|"惊讶")
        ACTION="shocked expression, wide eyes, surprised pose"
        FILE_KEY="shocked"
        ;;
    "lazy"|"懒"|"废")
        ACTION="lazy lying down, unmotivated, relaxed, comfortable"
        FILE_KEY="lazy"
        ;;
    *)
        ACTION="cute pose, happy expression"
        FILE_KEY="cute"
        ;;
esac

PROMPT="${UMARU_BASE}, ${ACTION}, high quality anime art"

echo "🎀 生成小埋表情: $MOOD"

JSON_PAYLOAD=$(jq -n \
  --arg prompt "$PROMPT" \
  '{prompt: $prompt, num_images: 1, output_format: "jpeg", image_size: "square_hd"}')

if [ -z "${FAL_KEY:-}" ]; then
    echo "ℹ️ 未配置 FAL_KEY，直接走本地兜底"
    send_local_fallback "$FILE_KEY"
    exit $?
fi

RESPONSE=$(curl -sS --max-time 25 -X POST "https://fal.run/xai/grok-imagine-image" \
  -H "Authorization: Key ${FAL_KEY}" \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD" 2>/dev/null || true)

IMAGE_URL=$(echo "$RESPONSE" | jq -r '.images[0].url // empty' 2>/dev/null)

if [ -z "$IMAGE_URL" ]; then
    REASON=$(echo "$RESPONSE" | jq -r '.detail // .error // .message // empty' 2>/dev/null)
    [ -z "$REASON" ] && REASON="fal unavailable or quota/rate limited"
    echo "⚠️ FAL 生成失败: $REASON"
    send_local_fallback "$FILE_KEY"
    exit $?
fi

TEMP_IMAGE="$SAVE_DIR/umaru_${FILE_KEY}_$(date +%s).jpg"
if ! curl -sSL --max-time 20 -o "$TEMP_IMAGE" "$IMAGE_URL" || [ ! -s "$TEMP_IMAGE" ]; then
    echo "⚠️ 下载失败，走本地兜底"
    send_local_fallback "$FILE_KEY"
    exit $?
fi

cd /root/.openclaw/workspace
if node skills/feishu-sticker/send.js --target "$TARGET_USER" --file "$TEMP_IMAGE" 2>&1 | grep -E "(Sending|Success)" >/dev/null; then
    echo "🎀 小埋表情 [$MOOD] 完成！"
    exit 0
fi

echo "⚠️ 飞书发送失败，走本地兜底"
send_local_fallback "$FILE_KEY"
