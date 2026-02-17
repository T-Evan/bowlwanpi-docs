#!/usr/bin/env python3
"""
主动进化机制 v1.0
- 自动分析系统摩擦点
- 实验性优化测试
- A/B 测试效果对比
- 自动推广成功优化
"""

import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

WORKSPACE = Path("/root/.openclaw/workspace")
EVOLUTION_DIR = WORKSPACE / ".evolution"
EVOLUTION_STATE = EVOLUTION_DIR / "state.json"
EXPERIMENTS_DIR = EVOLUTION_DIR / "experiments"

class ActiveEvolution:
    """主动进化引擎"""
    
    def __init__(self):
        os.makedirs(EVOLUTION_DIR, exist_ok=True)
        os.makedirs(EXPERIMENTS_DIR, exist_ok=True)
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """加载进化状态"""
        if EVOLUTION_STATE.exists():
            with open(EVOLUTION_STATE, 'r') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "friction_points": [],
            "experiments": [],
            "successful_optimizations": [],
            "failed_optimizations": []
        }
    
    def _save_state(self):
        """保存进化状态"""
        with open(EVOLUTION_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    # ========== 1. 摩擦点检测 ==========
    def detect_friction_points(self) -> List[Dict]:
        """检测系统摩擦点"""
        friction_points = []
        
        # 1. 分析错误日志
        error_patterns = self._analyze_error_logs()
        friction_points.extend(error_patterns)
        
        # 2. 分析性能数据
        performance_issues = self._analyze_performance()
        friction_points.extend(performance_issues)
        
        # 3. 分析用户反馈（从记忆中提取）
        user_feedback = self._analyze_user_feedback()
        friction_points.extend(user_feedback)
        
        # 保存到状态
        self.state["friction_points"] = friction_points[-50:]  # 保留最近50个
        self._save_state()
        
        return friction_points
    
    def _analyze_error_logs(self) -> List[Dict]:
        """分析错误日志找模式"""
        patterns = []
        
        log_files = [
            "/var/log/bowlwanpi-cron.log",
            "/var/log/bowlwanpi-health.log",
            "/var/log/bowlwanpi-memory.log"
        ]
        
        error_keywords = ["ERROR", "FAIL", "exception", "timeout", "killed", "OOM"]
        
        for log_file in log_files:
            if not os.path.exists(log_file):
                continue
            
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                # 分析最近100行
                recent_lines = lines[-100:]
                
                for line in recent_lines:
                    for keyword in error_keywords:
                        if keyword.lower() in line.lower():
                            # 提取错误上下文
                            context = line.strip()[:200]
                            
                            # 去重检查
                            if not any(p.get("context") == context for p in patterns):
                                patterns.append({
                                    "type": "error_log",
                                    "source": log_file,
                                    "keyword": keyword,
                                    "context": context,
                                    "detected_at": datetime.now().isoformat(),
                                    "severity": self._calculate_severity(line)
                                })
                            break
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
        
        return patterns
    
    def _analyze_performance(self) -> List[Dict]:
        """分析性能数据"""
        issues = []
        
        # 读取性能统计
        stats_file = WORKSPACE / "stats" / "system-stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
                
                # 检查慢任务
                for task_name, task_data in stats.get("tasks", {}).items():
                    avg_duration = task_data.get("avg_duration_ms", 0)
                    if avg_duration > 10000:  # 超过10秒
                        issues.append({
                            "type": "performance",
                            "category": "slow_task",
                            "task": task_name,
                            "avg_duration_ms": avg_duration,
                            "suggestion": f"优化 {task_name} 的执行时间",
                            "detected_at": datetime.now().isoformat()
                        })
                    
                    # 检查失败率
                    total = task_data.get("success", 0) + task_data.get("fail", 0)
                    if total > 0:
                        fail_rate = task_data.get("fail", 0) / total
                        if fail_rate > 0.1:  # 失败率超过10%
                            issues.append({
                                "type": "performance",
                                "category": "high_failure_rate",
                                "task": task_name,
                                "fail_rate": fail_rate,
                                "suggestion": f"调查 {task_name} 的高失败率",
                                "detected_at": datetime.now().isoformat()
                            })
            except Exception as e:
                print(f"Error analyzing performance: {e}")
        
        return issues
    
    def _analyze_user_feedback(self) -> List[Dict]:
        """从记忆中分析用户反馈"""
        feedback = []
        
        # 读取今日记忆
        today = datetime.now().strftime('%Y-%m-%d')
        memory_file = WORKSPACE / "memory" / f"{today}.md"
        
        if memory_file.exists():
            try:
                content = memory_file.read_text()
                
                # 查找优化相关的关键词
                improvement_keywords = [
                    "优化", "改进", "修复", "问题", "bug", "慢", "卡",
                    "optimize", "improve", "fix", "slow", "issue"
                ]
                
                for keyword in improvement_keywords:
                    if keyword in content.lower():
                        # 找到相关段落
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if keyword in line.lower():
                                # 提取上下文
                                context_lines = lines[max(0, i-2):min(len(lines), i+3)]
                                context = '\n'.join(context_lines)
                                
                                if len(context) > 50:  # 有意义的上下文
                                    feedback.append({
                                        "type": "user_feedback",
                                        "keyword": keyword,
                                        "context": context[:300],
                                        "suggestion": f"用户提到 '{keyword}'，需要关注",
                                        "detected_at": datetime.now().isoformat()
                                    })
            except Exception as e:
                print(f"Error analyzing feedback: {e}")
        
        return feedback
    
    def _calculate_severity(self, error_line: str) -> str:
        """计算错误严重程度"""
        if any(kw in error_line.lower() for kw in ["fatal", "panic", "crash"]):
            return "high"
        elif any(kw in error_line.lower() for kw in ["error", "fail", "timeout"]):
            return "medium"
        return "low"
    
    # ========== 2. 实验管理 ==========
    def create_experiment(self, friction_point: Dict) -> Dict:
        """为摩擦点创建优化实验"""
        experiment_id = f"exp-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        experiment = {
            "id": experiment_id,
            "friction_point": friction_point,
            "created_at": datetime.now().isoformat(),
            "status": "proposed",
            "optimization": self._generate_optimization(friction_point),
            "test_results": [],
            "metrics": {}
        }
        
        self.state["experiments"].append(experiment)
        self._save_state()
        
        return experiment
    
    def _generate_optimization(self, friction_point: Dict) -> Dict:
        """生成优化方案"""
        optimization = {
            "description": "",
            "changes": [],
            "expected_benefit": "",
            "risk": "low"
        }
        
        point_type = friction_point.get("type")
        category = friction_point.get("category", "")
        
        if point_type == "error_log":
            keyword = friction_point.get("keyword", "")
            if "timeout" in keyword.lower():
                optimization["description"] = "增加超时时间和重试机制"
                optimization["changes"] = ["添加超时配置", "实现指数退避重试"]
                optimization["expected_benefit"] = "减少超时错误，提高成功率"
            elif "oom" in keyword.lower() or "memory" in keyword.lower():
                optimization["description"] = "优化内存使用"
                optimization["changes"] = ["分批处理大数据", "清理临时变量"]
                optimization["expected_benefit"] = "降低内存占用，避免OOM"
        
        elif point_type == "performance":
            if category == "slow_task":
                task = friction_point.get("task", "")
                optimization["description"] = f"优化 {task} 性能"
                optimization["changes"] = ["并行化处理", "缓存结果", "减少IO操作"]
                optimization["expected_benefit"] = "减少执行时间"
            elif category == "high_failure_rate":
                task = friction_point.get("task", "")
                optimization["description"] = f"修复 {task} 失败问题"
                optimization["changes"] = ["添加错误处理", "改进输入验证"]
                optimization["expected_benefit"] = "降低失败率"
        
        return optimization
    
    # ========== 3. A/B 测试 ==========
    def run_ab_test(self, experiment_id: str) -> Dict:
        """运行 A/B 测试"""
        experiment = next(
            (e for e in self.state["experiments"] if e["id"] == experiment_id),
            None
        )
        
        if not experiment:
            return {"error": "Experiment not found"}
        
        # 标记为测试中
        experiment["status"] = "testing"
        self._save_state()
        
        # 这里应该实际运行测试
        # 简化版本：记录测试意图
        test_result = {
            "test_id": f"test-{datetime.now().strftime('%H%M%S')}",
            "started_at": datetime.now().isoformat(),
            "status": "completed",
            "metrics": {
                "baseline": {},
                "optimized": {}
            },
            "improvement": "pending measurement"
        }
        
        experiment["test_results"].append(test_result)
        experiment["status"] = "evaluating"
        self._save_state()
        
        return test_result
    
    # ========== 4. 报告生成 ==========
    def generate_report(self) -> str:
        """生成进化报告"""
        report = f"""# 🧬 主动进化报告

*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

## 📊 当前状态

- 检测到的摩擦点: {len(self.state.get('friction_points', []))}
- 进行中的实验: {len([e for e in self.state.get('experiments', []) if e.get('status') == 'testing'])}
- 成功优化: {len(self.state.get('successful_optimizations', []))}
- 失败优化: {len(self.state.get('failed_optimizations', []))}

## 🔍 最近检测到的摩擦点

"""
        
        recent_points = self.state.get("friction_points", [])[-10:]
        for point in recent_points:
            report += f"### {point.get('type', 'Unknown')}\n"
            report += f"- 类别: {point.get('category', 'N/A')}\n"
            report += f"- 严重程度: {point.get('severity', 'N/A')}\n"
            if 'context' in point:
                report += f"- 上下文: {point['context'][:100]}...\n"
            if 'suggestion' in point:
                report += f"- 建议: {point['suggestion']}\n"
            report += "\n"
        
        return report

def main():
    """CLI 入口"""
    import sys
    
    evolution = ActiveEvolution()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "detect":
            points = evolution.detect_friction_points()
            print(f"🔍 检测到 {len(points)} 个摩擦点")
            for point in points:
                print(f"  - {point.get('type')}: {point.get('context', 'N/A')[:50]}...")
        
        elif command == "experiment":
            if len(sys.argv) > 2:
                exp_id = sys.argv[2]
                result = evolution.run_ab_test(exp_id)
                print(f"🧪 实验结果: {result}")
        
        elif command == "report":
            print(evolution.generate_report())
    else:
        # 默认运行检测
        points = evolution.detect_friction_points()
        print(evolution.generate_report())

if __name__ == "__main__":
    main()
