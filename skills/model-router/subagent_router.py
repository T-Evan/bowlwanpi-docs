#!/usr/bin/env python3
"""
智能模型路由 - 子代理模式
根据任务类型自动创建对应模型的子会话来处理
"""
import subprocess
import json
import sys
import re
from typing import Optional, Tuple

# 模型配置
MODELS = {
    "kimi-code": {
        "id": "kimi-code/kimi-for-coding",
        "name": "Kimi Code",
        "strengths": ["code", "debug", "chinese", "long_context"],
        "description": "代码编程专家"
    },
    "gpt-5.3": {
        "id": "right/gpt-5.3-codex-xhigh", 
        "name": "GPT-5.3",
        "strengths": ["reasoning", "analysis", "multimodal", "creative", "complex"],
        "description": "深度推理专家"
    },
    "kimi-k2.5": {
        "id": "kimi-coding/k2p5",
        "name": "Kimi K2.5",
        "strengths": ["chinese", "long_context", "summarization"],
        "description": "中文处理专家"
    }
}

def analyze_task(message: str) -> Tuple[str, str, float]:
    """
    分析任务类型，返回 (模型key, 理由, 置信度)
    """
    message_lower = message.lower()
    
    # 代码相关
    code_patterns = [
        r'(code|coding|program|script|debug|fix|error|bug|python|bash|shell|git|json|yaml|sql|docker|api|function|class|import|def)\b',
        r'(写代码|编写代码|创建脚本|调试代码|修复bug|写程序|Python|代码|编程|脚本)'
    ]
    
    # 推理分析
    reasoning_patterns = [
        r'(analy|research|deep|complex|strategy|architecture|design|optimize|improve|plan|evaluate)\b',
        r'(分析|研究|深度|策略|架构|设计|优化|改进|规划|评估|复杂|推理)'
    ]
    
    # 创意写作
    creative_patterns = [
        r'(creative|write|story|poem|imagine|design|innovation|idea)\b',
        r'(创意|写作|故事|诗歌|生成|起草|设计|想象|创作)'
    ]
    
    # 中文长文本
    chinese_patterns = [
        r'[\u4e00-\u9fff]{100,}',  # 大量中文
        r'(总结|摘要|翻译|撰写|报告|文档|文章|长文本)'
    ]
    
    code_score = sum(1 for p in code_patterns if re.search(p, message_lower))
    reasoning_score = sum(1 for p in reasoning_patterns if re.search(p, message_lower))
    creative_score = sum(1 for p in creative_patterns if re.search(p, message_lower))
    chinese_score = sum(1 for p in chinese_patterns if re.search(p, message_lower))
    
    # 决策逻辑
    if code_score >= 1:
        return ("kimi-code", f"检测到编程相关任务 (命中{code_score}个模式)", 0.9)
    
    if reasoning_score >= 1:
        return ("gpt-5.3", f"检测到复杂分析/推理任务 (命中{reasoning_score}个模式)", 0.85)
    
    if creative_score >= 1:
        return ("gpt-5.3", f"检测到创意生成任务 (命中{creative_score}个模式)", 0.8)
    
    if chinese_score >= 1:
        return ("kimi-k2.5", f"检测到中文长文本任务 (命中{chinese_score}个模式)", 0.85)
    
    # 默认
    return ("kimi-code", "默认使用 Kimi Code（综合能力均衡）", 0.6)

def route_to_subagent(message: str, timeout: int = 300) -> dict:
    """
    将任务路由到对应的子代理
    
    Args:
        message: 用户消息
        timeout: 子代理超时时间（秒）
    
    Returns:
        {
            "model": "使用的模型",
            "reason": "选择理由",
            "result": "子代理返回结果",
            "success": True/False
        }
    """
    # 分析任务
    model_key, reason, confidence = analyze_task(message)
    model_config = MODELS[model_key]
    model_id = model_config["id"]
    
    print(f"🎯 任务分析完成")
    print(f"📊 推荐模型: {model_config['name']}")
    print(f"💡 选择理由: {reason}")
    print(f"📈 置信度: {confidence:.0%}")
    print(f"⏳ 正在创建子代理...")
    
    try:
        # 使用 sessions_spawn 创建子代理
        # 注意：这里通过构造一个特殊的提示来让子代理使用指定模型
        # 实际实现需要在 session_status 中设置模型
        
        # 先设置当前会话的模型（如果可能）
        # 然后通过 sessions_send 发送任务
        
        # 由于 sessions_spawn 不支持直接指定模型，
        # 我们使用 workaround：创建一个特定的任务消息，包含模型选择指令
        
        enhanced_message = f"""[MODEL_OVERRIDE: {model_id}]

你需要使用以下模型来完成任务：{model_config['name']}

用户任务：
{message}

请直接开始处理任务，返回完整结果。
"""
        
        # 创建子代理任务
        result = spawn_subagent(enhanced_message, model_id, timeout)
        
        return {
            "model": model_config['name'],
            "model_id": model_id,
            "reason": reason,
            "confidence": confidence,
            "result": result.get("output", ""),
            "success": result.get("success", False),
            "error": result.get("error", None)
        }
        
    except Exception as e:
        return {
            "model": model_config['name'],
            "reason": reason,
            "confidence": confidence,
            "result": "",
            "success": False,
            "error": str(e)
        }

def spawn_subagent(task: str, model_id: str, timeout: int = 300) -> dict:
    """
    创建子代理并执行任务
    
    由于当前 OpenClaw 的 sessions_spawn 限制，
    这里提供一个基于文件通信的 workaround
    """
    import uuid
    import time
    import os
    
    task_id = str(uuid.uuid4())[:8]
    task_file = f"/tmp/model_router_task_{task_id}.json"
    result_file = f"/tmp/model_router_result_{task_id}.json"
    
    # 写入任务
    task_data = {
        "task": task,
        "model": model_id,
        "task_id": task_id,
        "created_at": time.time()
    }
    
    with open(task_file, 'w') as f:
        json.dump(task_data, f)
    
    print(f"📝 任务已创建: {task_id}")
    print(f"⏳ 等待子代理处理 (超时: {timeout}s)...")
    
    # 由于无法真正创建带特定模型的子代理，
    # 这里返回一个提示，建议手动使用 /model 命令
    
    return {
        "success": False,
        "output": "",
        "error": f"子代理模式需要手动配合。建议：\n1. 使用 /model {model_id} 切换模型\n2. 然后直接发送任务",
        "model": model_id
    }

def main():
    """CLI入口"""
    if len(sys.argv) < 2:
        print("智能模型路由 - 子代理模式")
        print()
        print("Usage: python3 subagent_router.py '<message>'")
        print()
        print("示例:")
        print('  python3 subagent_router.py "帮我写一段Python代码"')
        print('  python3 subagent_router.py "分析这个业务架构"')
        print()
        print("可用模型:")
        for key, config in MODELS.items():
            print(f"  - {key}: {config['name']} - {config['description']}")
        sys.exit(1)
    
    message = " ".join(sys.argv[1:])
    
    # 分析并显示推荐
    model_key, reason, confidence = analyze_task(message)
    model_config = MODELS[model_key]
    
    print(f"\n🎯 任务分析")
    print(f"=" * 50)
    print(f"📝 任务: {message[:80]}...")
    print(f"📊 推荐模型: {model_config['name']}")
    print(f"🆔 模型ID: {model_config['id']}")
    print(f"📈 置信度: {confidence:.0%}")
    print(f"💡 选择理由: {reason}")
    print(f"=" * 50)
    print()
    print("💡 使用建议:")
    print(f"  1. 执行: /model {model_config['id']}")
    print(f"  2. 然后发送你的任务")
    print()

if __name__ == "__main__":
    main()
