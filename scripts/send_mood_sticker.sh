#!/bin/bash
#
# 情绪表情包发送系统
# 根据当前情绪自动选择合适的表情包
#

TARGET_USER="${1:-user:ou_a22ce6536f26dee3fec9397a9a1b87b5}"
MOOD="${2:-happy}"

# shellcheck source=/root/.openclaw/workspace/scripts/load-secrets.sh
source /root/.openclaw/workspace/scripts/load-secrets.sh
load_secret_env

if ! require_env_vars FEISHU_APP_ID FEISHU_APP_SECRET; then
    exit 1
fi

STICKER_DIR="$HOME/.openclaw/media/stickers"

# 情绪到表情包的映射
case "$MOOD" in
    "happy"|"开心"|"高兴")
        STICKER="$STICKER_DIR/ai_waifu/waifu_happy.jpg"
        TEXT="😊 开心~"
        ;;
    "sad"|"难过"|"伤心")
        STICKER="$STICKER_DIR/ai_waifu/waifu_sad.jpg"
        TEXT="😢 有点难过..."
        ;;
    "excited"|"兴奋"|"激动")
        STICKER="$STICKER_DIR/ai_waifu/waifu_excited.jpg"
        TEXT="🎉 太兴奋了！"
        ;;
    "sleepy"|"困"|"累")
        STICKER="$STICKER_DIR/ai_waifu/waifu_sleepy.jpg"
        TEXT="😴 好困啊..."
        ;;
    "angry"|"生气"|"愤怒")
        STICKER="$STICKER_DIR/ai_waifu/waifu_angry.jpg"
        TEXT="😠 有点生气！"
        ;;
    "love"|"喜欢"|"爱")
        STICKER="$STICKER_DIR/ai_waifu/waifu_love.jpg"
        TEXT="❤️ 喜欢你~"
        ;;
    "confused"|"疑惑"|"困惑")
        STICKER="$STICKER_DIR/ai_waifu/waifu_confused.jpg"
        TEXT="🤔 有点疑惑..."
        ;;
    "cool"|"酷"|"帅")
        STICKER="$STICKER_DIR/ai_waifu/waifu_cool.jpg"
        TEXT="😎 我很酷！"
        ;;
    *)
        # 随机选择
        RANDOM_MOOD=$((RANDOM % 8))
        MOODS=(happy sad excited sleepy angry love confused cool)
        SELECTED_MOOD=${MOODS[$RANDOM_MOOD]}
        STICKER="$STICKER_DIR/ai_waifu/waifu_${SELECTED_MOOD}.jpg"
        TEXT="🎭 随机表情~"
        ;;
esac

# 检查文件是否存在
if [ ! -f "$STICKER" ]; then
    echo "❌ 表情包不存在: $STICKER"
    exit 1
fi

# 发送到飞书
cd /root/.openclaw/workspace
node skills/feishu-sticker/send.js \
  --target "$TARGET_USER" \
  --file "$STICKER" 2>&1 | grep -E "(Sending|Success|Error)"

echo "✅ 情绪表情 [$MOOD] 发送完成"
