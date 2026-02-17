#!/bin/bash
# umaru-selfie.sh - 生成真正的小埋风格表情包
# 干物妹小埋 - Umaru Doma

set -euo pipefail

export FAL_KEY="bb2e0cea-fc85-41e9-a734-2a32cc889362:fdafdf28c8122642e92f07e06ee49def"
export FEISHU_APP_ID="cli_a9f5e960b8b81bb6"
export FEISHU_APP_SECRET="j9voDy9pm0q0SQaC4fMT1e1SYowDUWax"

TARGET_USER="${1:-ou_a22ce6536f26dee3fec9397a9a1b87b5}"
ACTION="${2:-playing games}"

# 小埋角色特征
CHARACTER="Umaru Doma from Himouto Umaru-chan"
STYLE="anime style, 2D animation, cel shading, vibrant colors, moe style"
APPEARANCE="blonde hair with orange gradient, purple eyes, cute face, petite girl"
OUTFIT="orange hamster hoodie with ears, white fluffy trim, hood up with hamster ears"
EXPRESSION="cute expression, sparkling eyes, kawaii"

echo "🎀 生成小埋表情包: ${ACTION}"

# 构建提示词 - 突出小埋特征
PROMPT="${CHARACTER}, ${STYLE}, ${APPEARANCE}, ${EXPRESSION}, wearing ${OUTFIT}, ${ACTION}, cute pose, chibi proportions possible, anime screenshot style, high quality"

# 使用文本生成图片（不使用参考图，直接生成）
JSON_PAYLOAD=$(jq -n \
  --arg prompt "$PROMPT" \
  '{prompt: $prompt, num_images: 1, output_format: "jpeg", image_size: "square_hd"}')

RESPONSE=$(curl -s -X POST "https://fal.run/xai/grok-imagine-image" \
  -H "Authorization: Key $FAL_KEY" \
  -H "Content-Type: application/json" \
  -d "$JSON_PAYLOAD")

# 提取图片 URL
IMAGE_URL=$(echo "$RESPONSE" | jq -r '.images[0].url // empty')

if [ -z "$IMAGE_URL" ]; then
    echo "❌ 生成失败"
    echo "响应: $RESPONSE"
    exit 1
fi

echo "✅ 图片生成成功"

# 下载图片
TEMP_DIR=$(mktemp -d)
TEMP_IMAGE="$TEMP_DIR/umaru_$(date +%s).jpg"
curl -sL -o "$TEMP_IMAGE" "$IMAGE_URL"

if [ ! -f "$TEMP_IMAGE" ]; then
    echo "❌ 下载图片失败"
    exit 1
fi

# 发送到飞书
cd /root/.openclaw/workspace
node skills/feishu-sticker/send.js \
  --target "$TARGET_USER" \
  --file "$TEMP_IMAGE" 2>&1 | grep -E "(Sending|Success|Error)"

# 清理
rm -rf "$TEMP_DIR"

echo "🎀 小埋表情发送完成！"
