#!/usr/bin/env python3
"""
智能模型路由器 v1.0
根据任务特征自动选择最适合的模型
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 模型配置
MODELS = {
    "kimi-code": {
        "id": "kimi-code/kimi-for-coding",
        "name": "Kimi Code",
        "strengths": ["code", "debug", "chinese", "long_context"],
        "context_window": 262144,
        "cost_level": "low",
        "latency": "fast"
    },
    "gpt-5.2": {
        "id": "crs/gpt-5.2-codex",
        "name": "GPT-5.2",
        "strengths": ["reasoning", "analysis", "multimodal", "creative", "complex"],
        "context_window": 200000,
        "cost_level": "medium",
        "latency": "medium"
    },
    "kimi-k2.5": {
        "id": "kimi-coding/k2p5",
        "name": "Kimi K2.5",
        "strengths": ["chinese", "long_context", "summarization"],
        "context_window": 256000,
        "cost_level": "low",
        "latency": "fast"
    }
}

# 任务分类关键词
TASK_PATTERNS = {
    "code": {
        "keywords": ["code", "debug", "error", "fix", "script", "python", "bash", "shell", "git", "programming", "function", "class", "api", "json", "yaml"],
        "recommended": "kimi-code",
        "reason": "Kimi Code 有 256K 上下文，代码理解能力最强"
    },
    "reasoning": {
        "keywords": ["analyze", "analysis", "research", "deep", "complex", "why", "how to", "strategy", "architecture", "design", "optimize", "improve"],
        "recommended": "gpt-5.2",
        "reason": "GPT-5.2 推理能力最强，适合深度分析"
    },
    "chinese_long": {
        "keywords": ["中文", "总结", "摘要", "长文", "document", "summary", "translate chinese"],
        "recommended": "kimi-k2.5",
        "reason": "Kimi K2.5 中文处理能力优秀，成本低"
    },
    "creative": {
        "keywords": ["creative", "write", "story", "poem", "imagine", "design", "innovation", "idea"],
        "recommended": "gpt-5.2",
        "reason": "GPT-5.2 创造力更强"
    },
    "quick_qa": {
        "keywords": ["what is", "how do", "explain", "simple", "brief", "quick"],
        "recommended": "gpt-5.2",
        "reason": "GPT-5.2 响应快，综合能力均衡"
    },
    "multimodal": {
        "keywords": ["image", "picture", "photo", "diagram", "chart", "visual", "describe"],
        "recommended": "gpt-5.2",
        "reason": "GPT-5.2 支持多模态（图像理解）"
    }
}

class ModelRouter:
    """智能模型路由器"""
    
    def __init__(self):
        self.usage_log = Path("/root/.openclaw/workspace/memory/model-usage.json")
        self.load_usage()
    
    def load_usage(self):
        """加载使用统计"""
        if self.usage_log.exists():
            with open(self.usage_log, 'r') as f:
                self.usage_data = json.load(f)
        else:
            self.usage_data = {
                "total_requests": 0,
                "by_model": {},
                "by_task_type": {},
                "history": []
            }
    
    def save_usage(self):
        """保存使用统计"""
        os.makedirs(self.usage_log.parent, exist_ok=True)
        with open(self.usage_log, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def analyze_task(self, task_description: str) -> Tuple[str, float, str]:
        """
        分析任务并推荐模型
        
        Returns:
            (model_key, confidence, reason)
        """
        task_lower = task_description.lower()
        scores = {}
        
        # 计算每个任务类型的匹配分数
        for task_type, config in TASK_PATTERNS.items():
            score = 0
            for keyword in config["keywords"]:
                if keyword in task_lower:
                    score += 1
            if score > 0:
                scores[task_type] = score
        
        if not scores:
            # 默认使用 GPT-5.2
            return "gpt-5.2", 0.5, "默认推荐，综合能力均衡"
        
        # 找出最高分的任务类型
        best_task = max(scores, key=scores.get)
        confidence = min(scores[best_task] / 3, 1.0)  # 归一化到 0-1
        
        config = TASK_PATTERNS[best_task]
        return config["recommended"], confidence, config["reason"]
    
    def route(self, task_description: str, force_model: Optional[str] = None) -> Dict:
        """
        路由到合适的模型
        
        Args:
            task_description: 任务描述
            force_model: 强制使用特定模型（可选）
        
        Returns:
            路由结果
        """
        if force_model and force_model in MODELS:
            model_key = force_model
            confidence = 1.0
            reason = f"强制指定: {MODELS[model_key]['name']}"
        else:
            model_key, confidence, reason = self.analyze_task(task_description)
        
        model_config = MODELS[model_key]
        
        result = {
            "model_id": model_config["id"],
            "model_name": model_config["name"],
            "model_key": model_key,
            "confidence": confidence,
            "reason": reason,
            "task_analyzed": task_description[:100],
            "timestamp": datetime.now().isoformat()
        }
        
        # 记录使用
        self._record_usage(model_key, task_description)
        
        return result
    
    def _record_usage(self, model_key: str, task: str):
        """记录使用情况"""
        self.usage_data["total_requests"] += 1
        
        # 按模型统计
        if model_key not in self.usage_data["by_model"]:
            self.usage_data["by_model"][model_key] = 0
        self.usage_data["by_model"][model_key] += 1
        
        # 历史记录（保留最近100条）
        self.usage_data["history"].append({
            "model": model_key,
            "task": task[:100],
            "timestamp": datetime.now().isoformat()
        })
        self.usage_data["history"] = self.usage_data["history"][-100:]
        
        self.save_usage()
    
    def get_stats(self) -> Dict:
        """获取使用统计"""
        return self.usage_data
    
    def print_recommendation(self, task: str):
        """打印推荐结果"""
        result = self.route(task)
        
        print(f"\n🎯 任务分析: {task[:60]}...")
        print(f"📊 推荐模型: {result['model_name']}")
        print(f"🆔 模型ID: {result['model_id']}")
        print(f"📈 置信度: {result['confidence']:.0%}")
        print(f"💡 推荐理由: {result['reason']}")
        print()
        
        return result

def main():
    """CLI 入口"""
    if len(sys.argv) < 2:
        print("Usage: python3 model_router.py '<task description>'")
        print("\nExamples:")
        print('  python3 model_router.py "debug this python error"')
        print('  python3 model_router.py "analyze system architecture"')
        print('  python3 model_router.py "write a creative story"')
        print()
        print("Available models:")
        for key, config in MODELS.items():
            print(f"  - {key}: {config['name']}")
        sys.exit(1)
    
    task = " ".join(sys.argv[1:])
    router = ModelRouter()
    result = router.print_recommendation(task)
    
    # 输出模型ID（用于脚本调用）
    print(f"RECOMMENDED_MODEL={result['model_id']}")

if __name__ == "__main__":
    main()
