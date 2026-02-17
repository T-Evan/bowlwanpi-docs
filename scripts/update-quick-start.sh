#!/bin/bash
# 更新快速启动文件
# 合并 SOUL.md + IDENTITY.md + USER.md + AMYGDALA_STATE.md + HIPPOCAMPUS_CORE.md

WORKSPACE="/root/.openclaw/workspace"
OUTPUT="$WORKSPACE/QUICK_START.md"

echo "# QUICK_START.md - 碗皮快速启动档案" > "$OUTPUT"
echo "" >> "$OUTPUT"

# 提取情感状态
if [ -f "$WORKSPACE/AMYGDALA_STATE.md" ]; then
    echo "## 🎭 当前状态" >> "$OUTPUT"
    grep -A 5 "Overall mood" "$WORKSPACE/AMYGDALA_STATE.md" | head -6 >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

# 提取身份信息
if [ -f "$WORKSPACE/IDENTITY.md" ]; then
    echo "## 👤 我是谁" >> "$OUTPUT"
    grep "Name:\|Creature:\|Mode:\|Emoji:" "$WORKSPACE/IDENTITY.md" >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

# 提取核心特质 (SOUL.md)
if [ -f "$WORKSPACE/SOUL.md" ]; then
    echo "## 🧠 核心特质" >> "$OUTPUT"
    grep -A 1 "Core Truths" "$WORKSPACE/SOUL.md" | tail -1 >> "$OUTPUT"
    echo "" >> "$OUTPUT"
    
    echo "## 💝 当前能力" >> "$OUTPUT"
    grep -A 5 "现在的我" "$WORKSPACE/SOUL.md" | tail -4 >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

# 提取用户信息
if [ -f "$WORKSPACE/USER.md" ]; then
    echo "## 👥 一碗是谁" >> "$OUTPUT"
    grep -v "^#" "$WORKSPACE/USER.md" | head -3 >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

# 今日记忆
TODAY=$(date +%Y-%m-%d)
if [ -f "$WORKSPACE/memory/$TODAY.md" ]; then
    echo "## 📝 今日要点" >> "$OUTPUT"
    grep -E "^(-|\*)" "$WORKSPACE/memory/$TODAY.md" | head -5 >> "$OUTPUT"
    echo "" >> "$OUTPUT"
fi

echo "---" >> "$OUTPUT"
echo "*快速启动文件 - 自动生成于 $(date '+%Y-%m-%d %H:%M')*" >> "$OUTPUT"

echo "✅ QUICK_START.md 已更新"
