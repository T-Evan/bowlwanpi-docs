#!/bin/bash
# 智能模型路由配置脚本
# 为不同场景配置最优模型选择

set -e

echo "🤖 配置智能模型路由..."

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 配置模型别名和路由规则
cat << 'EOF'

📋 智能路由策略:

┌─────────────────┬──────────────────────┬────────────────────────┐
│ 场景类型        │ 推荐模型             │ 理由                   │
├─────────────────┼──────────────────────┼────────────────────────┤
│ 代码/编程/Debug │ kimi-coding/k2p5     │ 256K上下文,代码理解强  │
│ 复杂推理/分析   │ crs/gpt-5.3-codex    │ reasoning能力强        │
│ 长文本/摘要     │ kimi-coding/k2p5     │ 中文长文本处理优秀     │
│ 日常对话        │ crs/gpt-5.3-codex    │ 默认,综合能力均衡      │
└─────────────────┴──────────────────────┴────────────────────────┘

EOF

# 更新 OpenClaw 配置 - 设置智能 fallback 顺序
echo "📝 更新模型 fallback 配置..."

# 使用 CLI 更新 fallback 列表
# 顺序: GPT-5.3 (主) -> Kimi K2.5 (fallback) -> MiniMax (备选)

openclaw models fallbacks clear 2>/dev/null || true

# 添加 fallback 链
openclaw models fallbacks add kimi-coding/k2p5 2>/dev/null || echo "⚠️ 添加 k2p5 fallback 失败"
openclaw models fallbacks add minimax-portal/MiniMax-M2.1-lightning 2>/dev/null || echo "⚠️ 添加 MiniMax fallback 失败"

echo "✅ Fallback 链配置完成"

# 创建快捷命令
cat << 'EOF'

🛠️ 使用方式:

1. 代码任务 (自动路由):
   /model kimi-code
   
2. 复杂推理 (默认):
   /model default
   
3. 使用路由脚本分析:
   python3 scripts/model_router.py --recommend "你的任务"

4. 查看当前配置:
   openclaw models fallbacks list

💡 提示:
- 代码相关任务建议手动切换到 Kimi Code
- 日常对话保持 GPT-5.3 即可
- 长文本处理用 Kimi (256K 上下文)

EOF

echo "✨ 智能路由配置完成!"
