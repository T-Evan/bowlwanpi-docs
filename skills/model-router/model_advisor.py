#!/usr/bin/env python3
"""
智能模型助手 - 实时分析和提示
在每次处理任务前，自动分析并提示最佳模型
"""
import sys
import json
import re

# 模型配置
MODELS = {
    "kimi-code": {
        "id": "kimi-code/kimi-for-coding",
        "name": "Kimi Code",
        "emoji": "💻",
        "strengths": ["代码", "调试", "脚本", "技术实现"],
        "switch_cmd": "/model kimi-code"
    },
    "gpt-5.3": {
        "id": "right/gpt-5.3-codex-xhigh",
        "name": "GPT-5.3", 
        "emoji": "🧠",
        "strengths": ["推理", "分析", "创意", "复杂问题"],
        "switch_cmd": "/model right-gpt5.3"
    },
    "kimi-k2.5": {
        "id": "kimi-coding/k2p5",
        "name": "Kimi K2.5",
        "emoji": "🇨🇳",
        "strengths": ["中文", "长文本", "总结", "翻译"],
        "switch_cmd": "/model kimi-k2.5"
    }
}

def analyze_task(message: str) -> tuple:
    """分析任务类型"""
    msg = message.lower()
    
    # 代码任务
    if any(k in msg for k in ['code', 'python', 'debug', 'script', 'program', '函数', '代码', '编程', '调试', '.py', '.js']):
        return "kimi-code", "代码相关任务", 0.9
    
    # 分析推理
    if any(k in msg for k in ['analyze', 'analysis', '研究', '分析', '策略', '架构', '设计', '优化', '复杂']):
        return "gpt-5.3", "分析推理任务", 0.85
    
    # 创意写作
    if any(k in msg for k in ['creative', 'write', 'story', '创意', '写作', '故事', '生成']):
        return "gpt-5.3", "创意生成任务", 0.8
    
    # 中文长文本
    if len([c for c in message if '\u4e00' <= c <= '\u9fff']) > 50:
        return "kimi-k2.5", "中文长文本任务", 0.85
    
    # 默认
    return "kimi-code", "综合任务", 0.6

def get_model_advice(message: str) -> str:
    """获取模型建议（小埋风格）"""
    model_key, reason, confidence = analyze_task(message)
    model = MODELS[model_key]
    
    # 如果当前已经是推荐模型，不提示
    # 这里假设一碗会使用这个脚本来检查
    
    lines = [
        f"{model['emoji']} 碗皮觉得用 **{model['name']}** 更好哦～",
        f"",
        f"💡 理由: {reason}",
        f"📈 匹配度: {confidence:.0%}",
        f"",
        f"🎯 快速切换:",
        f"   {model['switch_cmd']}",
        f"",
        f"✨ {model['name']} 擅长: {', '.join(model['strengths'][:3])}",
    ]
    
    if confidence < 0.8:
        lines.append(f"")
        lines.append(f"🤔 或者保持当前模型也可以～")
    
    return '\n'.join(lines)

def should_switch(message: str, current_model: str = "kimi-code") -> tuple:
    """
    判断是否应该切换模型
    
    Returns: (should_switch, target_model, reason)
    """
    recommended, reason, confidence = analyze_task(message)
    
    # 如果当前模型就是推荐的，不需要切换
    if current_model == recommended:
        return False, recommended, "当前模型已是最优"
    
    # 如果置信度很高，建议切换
    if confidence >= 0.85:
        return True, recommended, reason
    
    # 置信度中等，可选切换
    if confidence >= 0.7:
        return False, recommended, f"{reason}（可选切换）"
    
    # 置信度低，保持当前
    return False, current_model, "保持当前模型"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 model_advisor.py '<message>'")
        sys.exit(1)
    
    message = " ".join(sys.argv[1:])
    print(get_model_advice(message))
