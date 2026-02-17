#!/usr/bin/env python3
"""
智能模型路由器 - 根据任务类型自动选择 Kimi 或 GPT

路由策略:
- 代码/编程任务 → Kimi Code (擅长长上下文代码理解)
- 复杂推理/多模态/高复杂度 → GPT-5.3 ( reasoning 能力强)
- 日常对话/简单任务 → 默认 GPT-5.3
- 中文长文本 → Kimi (上下文窗口 256k)

使用方法:
1. 直接调用: python3 model_router.py "你的问题"
2. 获取推荐模型: python3 model_router.py --recommend "你的问题"
3. 自动执行: python3 model_router.py --exec "你的问题"
"""

import re
import sys
from typing import Tuple, List

# 模型配置
MODELS = {
    "kimi-code": {
        "id": "kimi-coding/kimi-for-coding",
        "alias": "Kimi Code",
        "strengths": ["代码", "编程", "debug", "长上下文", "中文技术文档"],
        "context_window": 262144,
        "reasoning": True,
        "cost_level": "medium"
    },
    "gpt-5.3": {
        "id": "crs/gpt-5.3-codex", 
        "alias": "crs-gpt5.3",
        "strengths": ["复杂推理", "多模态", "高阶思维", "数学", "分析"],
        "context_window": 200000,
        "reasoning": True,
        "cost_level": "high"
    },
    "kimi-k2.5": {
        "id": "kimi-coding/k2p5",
        "alias": "kimi-k2.5",
        "strengths": ["通用", "长文本", "中文", "日常"],
        "context_window": 256000,
        "reasoning": False,
        "cost_level": "low"
    }
}

# 关键词路由规则
ROUTING_RULES = [
    # 代码相关 → Kimi Code
    {
        "model": "kimi-code",
        "keywords": [
            "代码", "编程", "debug", "调试", "python", "javascript", "js",
            "函数", "类", "算法", "leetcode", "bug", "报错", "error",
            "git", "commit", "pr", "代码审查", "重构", "refactor",
            "docker", "kubernetes", "k8s", "dockerfile", "yaml",
            "sql", "数据库", "query", "优化", "performance",
            "脚本", "自动化", "bash", "shell", "cli",
            "cursor", "ide", "编辑器", "vscode", "配置"
        ],
        "priority": 10
    },
    # 复杂推理 → GPT-5.3
    {
        "model": "gpt-5.3",
        "keywords": [
            "分析", "推理", "逻辑", "数学", "计算", "证明",
            "多模态", "图像", "图片", "vision", "看这张",
            "复杂", "深度", "系统思考", "架构设计", "设计模式",
            "哲学", "抽象", "概念", "理论",
            "预测", "趋势", "未来", "规划", "战略"
        ],
        "priority": 10
    },
    # 中文长文本 → Kimi
    {
        "model": "kimi-k2.5",
        "keywords": [
            "总结", "摘要", "长文", "文章", "文档", "pdf",
            "小说", "故事", "历史", "文学", "阅读",
            "翻译", "中文", "古文", "诗词"
        ],
        "priority": 5
    }
]


def analyze_task(query: str) -> Tuple[str, float, str]:
    """
    分析任务并推荐模型
    
    返回: (模型ID, 置信度, 推荐理由)
    """
    query_lower = query.lower()
    scores = {model: 0 for model in MODELS}
    reasons = {model: [] for model in MODELS}
    
    # 基于关键词匹配
    for rule in ROUTING_RULES:
        model = rule["model"]
        priority = rule["priority"]
        
        for keyword in rule["keywords"]:
            if keyword.lower() in query_lower:
                scores[model] += priority
                if len(reasons[model]) < 3:  # 最多记录3个理由
                    reasons[model].append(f"匹配关键词: {keyword}")
    
    # 基于长度判断
    if len(query) > 5000:
        scores["kimi-code"] += 3
        scores["kimi-k2.5"] += 2
        reasons["kimi-code"].append("长文本输入(>5k字)")
    
    if len(query) > 30000:
        scores["kimi-k2.5"] += 5
        reasons["kimi-k2.5"].append("超长文本输入(>30k字)")
    
    # 基于特殊标记
    if any(code_marker in query for code_marker in ["```", "def ", "class ", "import ", "function"]):
        scores["kimi-code"] += 8
        reasons["kimi-code"].append("包含代码块")
    
    if query.startswith(("/", "!")) or "命令" in query:
        scores["kimi-code"] += 3
        reasons["kimi-code"].append("可能是CLI命令相关")
    
    # 选择最高分
    best_model = max(scores, key=scores.get)
    confidence = min(scores[best_model] / 10, 1.0)  # 归一化到0-1
    
    # 生成推荐理由
    if reasons[best_model]:
        reason_text = "; ".join(reasons[best_model][:2])
    else:
        # 默认理由
        if best_model == "gpt-5.3":
            reason_text = "默认选择(通用复杂任务)"
        elif best_model == "kimi-code":
            reason_text = "默认选择(技术相关)"
        else:
            reason_text = "默认选择(日常对话)"
    
    return MODELS[best_model]["id"], confidence, reason_text


def get_model_for_task(query: str) -> str:
    """简单接口：获取推荐模型ID"""
    model_id, _, _ = analyze_task(query)
    return model_id


def print_recommendation(query: str):
    """打印推荐结果"""
    model_id, confidence, reason = analyze_task(query)
    
    print(f"📊 任务分析")
    print(f"=" * 40)
    print(f"查询: {query[:50]}..." if len(query) > 50 else f"查询: {query}")
    print()
    print(f"🎯 推荐模型: {model_id}")
    print(f"置信度: {confidence*100:.0f}%")
    print(f"理由: {reason}")
    print()
    
    # 显示所有分数
    print("📈 模型匹配度:")
    for model_name, info in MODELS.items():
        # 重新计算分数用于显示
        query_lower = query.lower()
        score = 0
        for rule in ROUTING_RULES:
            if rule["model"] == model_name:
                for keyword in rule["keywords"]:
                    if keyword.lower() in query_lower:
                        score += rule["priority"]
        
        bar = "█" * min(score, 10) + "░" * (10 - min(score, 10))
        print(f"  {info['alias']:15} [{bar}] {score}")


def exec_with_model(query: str):
    """使用推荐模型执行任务(通过OpenClaw)"""
    import subprocess
    
    model_id, confidence, reason = analyze_task(query)
    
    print(f"🤖 智能路由选择: {MODELS[model_id]['alias']}")
    print(f"   理由: {reason}")
    print(f"   置信度: {confidence*100:.0f}%")
    print()
    
    # 使用 openclaw agent 命令执行
    cmd = [
        "openclaw", "agent",
        "--model", model_id,
        "--message", query
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        print(result.stdout)
        if result.stderr:
            print("错误:", result.stderr, file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("执行超时", file=sys.stderr)
    except Exception as e:
        print(f"执行错误: {e}", file=sys.stderr)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\n用法:")
        print(f"  python3 {sys.argv[0]} '你的问题'        # 查看推荐")
        print(f"  python3 {sys.argv[0]} --recommend '问题' # 详细分析")
        print(f"  python3 {sys.argv[0]} --exec '问题'      # 自动执行")
        sys.exit(1)
    
    if sys.argv[1] == "--recommend":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        print_recommendation(query)
    elif sys.argv[1] == "--exec":
        query = sys.argv[2] if len(sys.argv) > 2 else ""
        exec_with_model(query)
    else:
        # 默认: 简单推荐
        query = sys.argv[1]
        model_id, confidence, reason = analyze_task(query)
        print(f"推荐模型: {model_id}")
        print(f"置信度: {confidence*100:.0f}%")
        print(f"理由: {reason}")


if __name__ == "__main__":
    main()
