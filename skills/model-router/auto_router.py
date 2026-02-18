#!/usr/bin/env python3
"""
OpenClaw 智能模型路由中间件
自动根据任务类型选择最适合的模型
"""
import sys
import os
import json
import re
from typing import Optional

# 添加工作区到路径
sys.path.insert(0, '/root/.openclaw/workspace')

def analyze_task(message: str) -> tuple[str, str, str]:
    """
    分析任务类型，返回 (模型ID, 模型别名, 理由)
    """
    message_lower = message.lower()
    
    # 代码相关任务
    code_patterns = [
        r'(code|coding|program|script|debug|fix|error|bug|python|bash|shell|git|json|yaml|sql|docker|api|function|class|import|def|const|var|let)\b',
        r'(写代码|编写代码|创建脚本|调试代码|修复bug|写程序|函数|类定义|Python|PY)',
        r'(\.py|\.js|\.ts|\.sh|\.json|\.yaml|\.yml|\.sql|\.dockerfile)'
    ]
    
    # 深度分析/推理任务
    reasoning_patterns = [
        r'(analy|research|deep|complex|strategy|architecture|design|optimize|improve|plan|compare|evaluate)',
        r'(分析|研究|深度|策略|架构|设计|优化|改进|规划|评估|对比|复杂|推理)',
        r'\?.*\?.*\?'  # 多个问号表示深度问题
    ]
    
    # 中文长文本任务
    chinese_patterns = [
        r'[\u4e00-\u9fff]{50,}',  # 大量中文
        r'(总结|摘要|翻译|撰写|报告|文档|文章|长文本)'
    ]
    
    # 创意/生成任务
    creative_patterns = [
        r'(creative|write|story|poem|generate|draft|compose|imagine)',
        r'(创意|写作|故事|诗歌|生成|起草|设计|想象|创作)'
    ]
    
    code_score = sum(1 for p in code_patterns if re.search(p, message_lower))
    reasoning_score = sum(1 for p in reasoning_patterns if re.search(p, message_lower))
    chinese_score = sum(1 for p in chinese_patterns if re.search(p, message_lower))
    creative_score = sum(1 for p in creative_patterns if re.search(p, message_lower))
    
    # 决策逻辑（优先级：代码 > 推理/创意 > 中文 > 默认）
    if code_score >= 1:
        return ("kimi-code/kimi-for-coding", "kimi-code", f"检测到编程相关任务 (命中: {code_score}个模式)，使用 Kimi Code")
    
    if reasoning_score >= 1:
        return ("right/gpt-5.3-codex-xhigh", "right-gpt5.3", f"检测到复杂分析/推理任务 (命中: {reasoning_score}个模式)，使用 GPT-5.3")
    
    if creative_score >= 1:
        return ("right/gpt-5.3-codex-xhigh", "right-gpt5.3", f"检测到创意生成任务 (命中: {creative_score}个模式)，使用 GPT-5.3")
    
    if chinese_score >= 1:
        return ("kimi-coding/k2p5", "kimi-k2.5", f"检测到中文长文本任务 (命中: {chinese_score}个模式)，使用 Kimi K2.5")
    
    # 默认使用 Kimi Code（综合能力均衡）
    return ("kimi-code/kimi-for-coding", "kimi-code", "默认使用 Kimi Code")

def get_model_override(model_id: str) -> str:
    """将模型ID转换为OpenClaw可识别的格式"""
    model_map = {
        "kimi-code/kimi-for-coding": "kimi-code",
        "right/gpt-5.3-codex-xhigh": "right-gpt5.3",
        "kimi-coding/k2p5": "kimi-k2.5",
        "minimax-portal/MiniMax-M2.1": "minimax-m2.1",
        "minimax-portal/MiniMax-M2.1-lightning": "minimax-m2.1-lightning"
    }
    return model_map.get(model_id, model_id)

def main():
    # 从环境变量或参数获取消息
    message = os.environ.get('OPENCLAW_MESSAGE', '')
    
    if not message and len(sys.argv) > 1:
        message = ' '.join(sys.argv[1:])
    
    if not message:
        # 如果没有消息，输出当前模型配置
        print(json.dumps({
            "current_model": "kimi-code/kimi-for-coding",
            "available_models": [
                "kimi-code (代码/默认)",
                "right-gpt5.3 (推理/创意)",
                "kimi-k2.5 (中文长文本)",
                "minimax-m2.1 (快速响应)"
            ],
            "status": "ready"
        }, ensure_ascii=False, indent=2))
        return
    
    # 分析任务并选择模型
    model_id, model_alias, reason = analyze_task(message)
    
    # 输出结果（用于OpenClaw读取）
    result = {
        "model_id": model_id,
        "model_alias": model_alias,
        "reason": reason,
        "message_preview": message[:100] + "..." if len(message) > 100 else message
    }
    
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
