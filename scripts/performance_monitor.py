#!/usr/bin/env python3
"""
系统性能监控与使用统计
- 任务执行时间追踪
- 模型使用统计
- Token消耗估算
- 性能趋势分析
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

WORKSPACE = Path("/root/.openclaw/workspace")
STATS_DIR = WORKSPACE / "stats"
STATS_FILE = STATS_DIR / "system-stats.json"

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        os.makedirs(STATS_DIR, exist_ok=True)
        self.data = self._load_stats()
    
    def _load_stats(self) -> Dict:
        """加载统计数据"""
        if STATS_FILE.exists():
            with open(STATS_FILE, 'r') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "tasks": {},
            "models": {},
            "daily": {},
            "hourly_tokens": []
        }
    
    def _save_stats(self):
        """保存统计数据"""
        with open(STATS_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def record_task(self, task_name: str, duration_ms: int, model: str, success: bool = True):
        """记录任务执行"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if task_name not in self.data["tasks"]:
            self.data["tasks"][task_name] = {
                "count": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "success": 0,
                "fail": 0,
                "models_used": {}
            }
        
        task = self.data["tasks"][task_name]
        task["count"] += 1
        task["total_duration_ms"] += duration_ms
        task["avg_duration_ms"] = task["total_duration_ms"] // task["count"]
        
        if success:
            task["success"] += 1
        else:
            task["fail"] += 1
        
        if model not in task["models_used"]:
            task["models_used"][model] = 0
        task["models_used"][model] += 1
        
        # 记录到每日统计
        if today not in self.data["daily"]:
            self.data["daily"][today] = {"tasks": 0, "tokens": 0, "duration_ms": 0}
        
        self.data["daily"][today]["tasks"] += 1
        self.data["daily"][today]["duration_ms"] += duration_ms
        
        self._save_stats()
    
    def record_model_usage(self, model: str, input_tokens: int, output_tokens: int):
        """记录模型使用"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        if model not in self.data["models"]:
            self.data["models"][model] = {
                "total_calls": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "daily_usage": {}
            }
        
        model_data = self.data["models"][model]
        model_data["total_calls"] += 1
        model_data["total_input_tokens"] += input_tokens
        model_data["total_output_tokens"] += output_tokens
        
        if today not in model_data["daily_usage"]:
            model_data["daily_usage"][today] = {
                "calls": 0,
                "input_tokens": 0,
                "output_tokens": 0
            }
        
        model_data["daily_usage"][today]["calls"] += 1
        model_data["daily_usage"][today]["input_tokens"] += input_tokens
        model_data["daily_usage"][today]["output_tokens"] += output_tokens
        
        # 记录到每日统计
        if today not in self.data["daily"]:
            self.data["daily"][today] = {"tasks": 0, "tokens": 0, "duration_ms": 0}
        
        self.data["daily"][today]["tokens"] += input_tokens + output_tokens
        
        self._save_stats()
    
    def get_task_stats(self, days: int = 7) -> Dict:
        """获取任务统计"""
        cutoff = datetime.now() - timedelta(days=days)
        
        result = {
            "period_days": days,
            "total_tasks": 0,
            "avg_duration_ms": 0,
            "top_tasks": [],
            "success_rate": 0
        }
        
        total_duration = 0
        total_success = 0
        total_fail = 0
        
        for task_name, task in self.data["tasks"].items():
            result["total_tasks"] += task["count"]
            total_duration += task["total_duration_ms"]
            total_success += task["success"]
            total_fail += task["fail"]
        
        if result["total_tasks"] > 0:
            result["avg_duration_ms"] = total_duration // result["total_tasks"]
            result["success_rate"] = total_success / (total_success + total_fail)
        
        # 排序获取 Top 任务
        sorted_tasks = sorted(
            self.data["tasks"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:5]
        
        result["top_tasks"] = [
            {"name": name, "count": data["count"], "avg_duration_ms": data["avg_duration_ms"]}
            for name, data in sorted_tasks
        ]
        
        return result
    
    def get_model_stats(self, days: int = 7) -> Dict:
        """获取模型使用统计"""
        result = {
            "period_days": days,
            "models": {}
        }
        
        for model, data in self.data["models"].items():
            # 计算最近 N 天的使用
            recent_calls = 0
            recent_input = 0
            recent_output = 0
            
            for i in range(days):
                day = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
                if day in data["daily_usage"]:
                    recent_calls += data["daily_usage"][day]["calls"]
                    recent_input += data["daily_usage"][day]["input_tokens"]
                    recent_output += data["daily_usage"][day]["output_tokens"]
            
            result["models"][model] = {
                "recent_calls": recent_calls,
                "recent_input_tokens": recent_input,
                "recent_output_tokens": recent_output,
                "total_calls": data["total_calls"]
            }
        
        return result
    
    def generate_report(self) -> str:
        """生成性能报告"""
        task_stats = self.get_task_stats(7)
        model_stats = self.get_model_stats(7)
        
        report = f"""# 系统性能报告

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 📊 任务统计 (过去7天)

- 总任务数: {task_stats['total_tasks']}
- 平均执行时间: {task_stats['avg_duration_ms']}ms
- 成功率: {task_stats['success_rate']:.1%}

### Top 5 任务
"""
        
        for i, task in enumerate(task_stats['top_tasks'], 1):
            report += f"{i}. **{task['name']}**: {task['count']} 次, 平均 {task['avg_duration_ms']}ms\n"
        
        report += "\n## 🤖 模型使用统计 (过去7天)\n\n"
        
        for model, data in model_stats['models'].items():
            report += f"### {model}\n"
            report += f"- 调用次数: {data['recent_calls']}\n"
            report += f"- Input tokens: {data['recent_input_tokens']:,}\n"
            report += f"- Output tokens: {data['recent_output_tokens']:,}\n"
            report += f"- 总计: {data['total_calls']} 次\n\n"
        
        # 今日统计
        today = datetime.now().strftime('%Y-%m-%d')
        if today in self.data["daily"]:
            daily = self.data["daily"][today]
            report += f"## 📅 今日统计 ({today})\n\n"
            report += f"- 任务数: {daily['tasks']}\n"
            report += f"- Token消耗: {daily['tokens']:,}\n"
            report += f"- 总执行时间: {daily['duration_ms']}ms\n"
        
        return report

def main():
    """CLI入口"""
    import sys
    
    monitor = PerformanceMonitor()
    
    # 支持 record 命令
    if len(sys.argv) > 1 and sys.argv[1] == "record":
        # monitor-wrapper.sh 调用: record <task-name> <duration> <success>
        if len(sys.argv) >= 4:
            task_name = sys.argv[2]
            duration = int(sys.argv[3])
            success = sys.argv[4] == "true" if len(sys.argv) > 4 else True
            model = "unknown"
            
            monitor.record_task(task_name, duration, model, success)
            print(f"✅ 记录: {task_name}, {duration}ms, success={success}")
            return
    
    # 默认生成报告
    print(monitor.generate_report())
    
    # 也保存到文件
    report_file = STATS_DIR / f"report-{datetime.now().strftime('%Y%m%d')}.md"
    with open(report_file, 'w') as f:
        f.write(monitor.generate_report())
    
    print(f"\n📄 报告已保存: {report_file}")

if __name__ == "__main__":
    main()
