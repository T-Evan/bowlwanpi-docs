#!/bin/bash
# 智能模型选择钩子
# 在OpenClaw处理消息前自动选择最适合的模型

# 模型别名映射
alias_kimi_code="kimi-code/kimi-for-coding"
alias_gpt53="right/gpt-5.3-codex-xhigh"
alias_kimi_k25="kimi-coding/k2p5"

# 根据消息内容选择模型
select_model() {
    local message="$1"
    local message_lower=$(echo "$message" | tr '[:upper:]' '[:lower:]')
    
    # 代码相关任务 → Kimi Code
    if echo "$message_lower" | grep -qE "(code|debug|error|fix|script|python|bash|shell|git|编程|代码|调试|错误|修复|脚本)"; then
        echo "$alias_kimi_code"
        return
    fi
    
    # 深度推理/分析 → GPT-5.3
    if echo "$message_lower" | grep -qE "(analyze|analysis|research|deep|complex|reasoning|分析|研究|深度|推理|复杂|架构|设计)"; then
        echo "$alias_gpt53"
        return
    fi
    
    # 中文长文本/总结 → Kimi K2.5
    if echo "$message_lower" | grep -qE "(summary|summarize|translate|中文|总结|摘要|翻译|长文)"; then
        echo "$alias_kimi_k25"
        return
    fi
    
    # 多模态/图像 → GPT-5.3
    if echo "$message_lower" | grep -qE "(image|picture|photo|diagram|chart|visual|图像|图片|照片|图表)"; then
        echo "$alias_gpt53"
        return
    fi
    
    # 默认使用 Kimi Code（平衡成本和性能）
    echo "$alias_kimi_code"
}

# 主要逻辑
if [ -n "$1" ]; then
    MODEL=$(select_model "$1")
    echo "$MODEL"
else
    # 没有输入时返回默认模型
    echo "$alias_kimi_code"
fi
