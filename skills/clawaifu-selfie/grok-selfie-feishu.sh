#!/bin/bash
# grok-selfie-feishu.sh - 生成动漫自拍并发送到飞书
# 改编自 clawaifu-selfie，适配飞书

set -euo pipefail

# 环境变量
export FAL_KEY="bb2e0cea-fc85-41e9-a734-2a32cc889362:fdafdf28c8122642e92f07e06ee49def"
export FEISHU_APP_ID="cli_a9f5e960b8b81bb6"
export FEISHU_APP_SECRET="j9voDy9pm0q0SQaC4fMT1e1SYowDUWax"

# 配置
REFERENCE_IMAGE="${REFERENCE_IMAGE:-https://i.redd.it/g4uf70te81uf1.jpeg}"
TARGET_USER="${1:-ou_a22ce6536f26dee3fec9397a9a1b87b5}"
USER_CONTEXT="${2:-taking a selfie}"
CHARACTER_STYLE="${3:-cute anime girl}"

# 构建提示词
CHARACTER="${CHARACTER_STYLE}, anime style, 2D animation, cel shading, vibrant colors"
PROMPT="${CHARACTER}, ${USER_CONTEXT}, selfie photo style, close-up shot, kawaii, moe style, sparkling eyes, soft lighting"

echo "🎨 生成动漫自拍: ${USER_CONTEXT}"

# 调用 Grok Imagine API
JSON_PAYLOAD=$(jq -n \
  --arg image_url "$REFERENCE_IMAGE" \
  --arg prompt "$PROMPT" \
  '{image_url: $image_url, prompt: $prompt, num_images: 1, output_format: "jpeg"}')

RESPONSE=$(curl -s -X POST "https://fal.run/xai/grok-imagine-image/edit" \
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

echo "✅ 图片生成成功: $IMAGE_URL"

# 下载图片
TEMP_DIR=$(mktemp -d)
TEMP_IMAGE="$TEMP_DIR/waifu_$(date +%s).jpg"
curl -sL -o "$TEMP_IMAGE" "$IMAGE_URL"

if [ ! -f "$TEMP_IMAGE" ]; then
    echo "❌ 下载图片失败"
    exit 1
fi

echo "📥 图片已下载"

# 发送到飞书
cd /root/.openclaw/workspace
node skills/feishu-sticker/send.js \
  --target "$TARGET_USER" \
  --file "$TEMP_IMAGE" 2>&1

# 清理
rm -rf "$TEMP_DIR"

echo "🎉 完成！"
