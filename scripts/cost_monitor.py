#!/usr/bin/env python3
"""
成本优化监控系统 v1.0
- Token 使用追踪
- 模型成本分析
- 预算预警
- 成本优化建议
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

WORKSPACE = Path("/root/.openclaw/workspace")
COST_DIR = WORKSPACE / "cost"
COST_STATE = COST_DIR / "cost-state.json"

# 模型成本配置 (每 1K tokens)
MODEL_COSTS = {
    "kimi-code/kimi-for-coding": {"input": 0.0015, "output": 0.002, "currency": "USD"},
    "crs/gpt-5.2-codex": {"input": 0.002, "output": 0.006, "currency": "USD"},
    "kimi-coding/k2p5": {"input": 0.001, "output": 0.0015, "currency": "USD"},
    "minimax-portal/MiniMax-M2.1": {"input": 0.001, "output": 0.001, "currency": "USD"}
}

# 预算配置
BUDGET_CONFIG = {
    "daily_usd": 10.0,
    "monthly_usd": 200.0,
    "warning_threshold": 0.8,  # 80% 预警
    "critical_threshold": 0.95  # 95% 严重预警
}

class CostMonitor:
    """成本监控器"""
    
    def __init__(self):
        os.makedirs(COST_DIR, exist_ok=True)
        self.data = self._load_data()
    
    def _load_data(self) -> Dict:
        """加载成本数据"""
        if COST_STATE.exists():
            with open(COST_STATE, 'r') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "daily_usage": {},
            "model_usage": {},
            "task_usage": {},
            "total_spent_usd": 0.0
        }
    
    def _save_data(self):
        """保存成本数据"""
        with open(COST_STATE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    # ========== 1. Token 记录 ==========
    def record_usage(self, model: str, input_tokens: int, output_tokens: int, task: str = "unknown"):
        """记录模型使用"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 计算成本
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        
        # 记录到每日使用
        if today not in self.data["daily_usage"]:
            self.data["daily_usage"][today] = {
                "total_tokens": 0,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": 0.0,
                "models": {},
                "tasks": {}
            }
        
        daily = self.data["daily_usage"][today]
        daily["total_tokens"] += input_tokens + output_tokens
        daily["input_tokens"] += input_tokens
        daily["output_tokens"] += output_tokens
        daily["cost_usd"] += cost
        
        # 按模型统计
        if model not in daily["models"]:
            daily["models"][model] = {"tokens": 0, "cost": 0.0}
        daily["models"][model]["tokens"] += input_tokens + output_tokens
        daily["models"][model]["cost"] += cost
        
        # 按任务统计
        if task not in daily["tasks"]:
            daily["tasks"][task] = {"tokens": 0, "cost": 0.0}
        daily["tasks"][task]["tokens"] += input_tokens + output_tokens
        daily["tasks"][task]["cost"] += cost
        
        # 更新总计
        self.data["total_spent_usd"] += cost
        
        # 保存
        self._save_data()
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """计算成本"""
        if model not in MODEL_COSTS:
            # 默认成本
            return (input_tokens + output_tokens) / 1000 * 0.002
        
        costs = MODEL_COSTS[model]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    # ========== 2. 预算检查 ==========
    def check_budget(self) -> Dict:
        """检查预算状态"""
        today = datetime.now().strftime('%Y-%m-%d')
        current_month = today[:7]  # YYYY-MM
        
        # 今日花费
        daily_cost = self.data["daily_usage"].get(today, {}).get("cost_usd", 0)
        
        # 本月花费
        monthly_cost = sum(
            day_data.get("cost_usd", 0)
            for date, day_data in self.data["daily_usage"].items()
            if date.startswith(current_month)
        )
        
        # 检查阈值
        daily_ratio = daily_cost / BUDGET_CONFIG["daily_usd"]
        monthly_ratio = monthly_cost / BUDGET_CONFIG["monthly_usd"]
        
        alerts = []
        
        if daily_ratio > BUDGET_CONFIG["critical_threshold"]:
            alerts.append({
                "level": "critical",
                "type": "daily_budget",
                "message": f"今日花费 ${daily_cost:.2f}，超过日预算 95%"
            })
        elif daily_ratio > BUDGET_CONFIG["warning_threshold"]:
            alerts.append({
                "level": "warning",
                "type": "daily_budget",
                "message": f"今日花费 ${daily_cost:.2f}，超过日预算 80%"
            })
        
        if monthly_ratio > BUDGET_CONFIG["critical_threshold"]:
            alerts.append({
                "level": "critical",
                "type": "monthly_budget",
                "message": f"本月花费 ${monthly_cost:.2f}，超过月预算 95%"
            })
        elif monthly_ratio > BUDGET_CONFIG["warning_threshold"]:
            alerts.append({
                "level": "warning",
                "type": "monthly_budget",
                "message": f"本月花费 ${monthly_cost:.2f}，超过月预算 80%"
            })
        
        return {
            "daily_cost": daily_cost,
            "daily_budget": BUDGET_CONFIG["daily_usd"],
            "daily_ratio": daily_ratio,
            "monthly_cost": monthly_cost,
            "monthly_budget": BUDGET_CONFIG["monthly_usd"],
            "monthly_ratio": monthly_ratio,
            "alerts": alerts
        }
    
    # ========== 3. 成本分析 ==========
    def analyze_costs(self, days: int = 7) -> Dict:
        """分析成本趋势"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        analysis = {
            "period_days": days,
            "total_cost": 0.0,
            "total_tokens": 0,
            "by_model": {},
            "by_task": {},
            "daily_breakdown": [],
            "recommendations": []
        }
        
        for i in range(days):
            date = (end_date - timedelta(days=i)).strftime('%Y-%m-%d')
            day_data = self.data["daily_usage"].get(date, {})
            
            cost = day_data.get("cost_usd", 0)
            tokens = day_data.get("total_tokens", 0)
            
            analysis["total_cost"] += cost
            analysis["total_tokens"] += tokens
            
            analysis["daily_breakdown"].append({
                "date": date,
                "cost": cost,
                "tokens": tokens
            })
            
            # 按模型汇总
            for model, model_data in day_data.get("models", {}).items():
                if model not in analysis["by_model"]:
                    analysis["by_model"][model] = {"cost": 0.0, "tokens": 0}
                analysis["by_model"][model]["cost"] += model_data.get("cost", 0)
                analysis["by_model"][model]["tokens"] += model_data.get("tokens", 0)
            
            # 按任务汇总
            for task, task_data in day_data.get("tasks", {}).items():
                if task not in analysis["by_task"]:
                    analysis["by_task"][task] = {"cost": 0.0, "tokens": 0}
                analysis["by_task"][task]["cost"] += task_data.get("cost", 0)
                analysis["by_task"][task]["tokens"] += task_data.get("tokens", 0)
        
        # 生成建议
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """生成成本优化建议"""
        recommendations = []
        
        # 检查高成本模型
        for model, data in analysis["by_model"].items():
            cost = data.get("cost", 0)
            if cost > analysis["total_cost"] * 0.5:  # 占总成本50%以上
                recommendations.append(
                    f"模型 {model} 占总成本 {cost/analysis['total_cost']*100:.1f}%，"
                    f"考虑使用更便宜的替代模型"
                )
        
        # 检查高成本任务
        for task, data in analysis["by_task"].items():
            cost = data.get("cost", 0)
            if cost > 1.0:  # 单次任务超过$1
                recommendations.append(
                    f"任务 {task} 平均成本 ${cost:.2f}，考虑优化或缓存结果"
                )
        
        # 检查成本趋势
        daily_costs = [d["cost"] for d in analysis["daily_breakdown"]]
        if len(daily_costs) >= 3:
            avg_recent = sum(daily_costs[:3]) / 3
            avg_older = sum(daily_costs[-3:]) / 3 if len(daily_costs) >= 6 else avg_recent
            
            if avg_recent > avg_older * 1.5:
                recommendations.append(
                    "近期成本上升趋势明显，建议审查最近的任务和模型使用"
                )
        
        return recommendations
    
    # ========== 4. 报告生成 ==========
    def generate_report(self) -> str:
        """生成成本报告"""
        budget = self.check_budget()
        analysis = self.analyze_costs(7)
        
        report = f"""# 💰 成本监控报告

*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

## 📊 预算状态

### 今日
- 花费: ${budget['daily_cost']:.2f} / ${budget['daily_budget']:.2f}
- 使用率: {budget['daily_ratio']*100:.1f}%

### 本月
- 花费: ${budget['monthly_cost']:.2f} / ${budget['monthly_budget']:.2f}
- 使用率: {budget['monthly_ratio']*100:.1f}%

"""
        
        if budget['alerts']:
            report += "### 🚨 预算告警\n\n"
            for alert in budget['alerts']:
                emoji = "🔴" if alert['level'] == 'critical' else "🟡"
                report += f"{emoji} {alert['message']}\n"
            report += "\n"
        
        report += f"""## 📈 过去7天分析

- 总成本: ${analysis['total_cost']:.2f}
- 总Token: {analysis['total_tokens']:,}
- 平均每日: ${analysis['total_cost']/7:.2f}

### 按模型统计

"""
        
        for model, data in sorted(analysis['by_model'].items(), key=lambda x: x[1]['cost'], reverse=True):
            report += f"- **{model}**: ${data['cost']:.2f} ({data['tokens']:,} tokens)\n"
        
        if analysis['recommendations']:
            report += "\n### 💡 优化建议\n\n"
            for rec in analysis['recommendations']:
                report += f"- {rec}\n"
        
        return report

def main():
    """CLI 入口"""
    import sys
    
    monitor = CostMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "record" and len(sys.argv) >= 5:
            # record <model> <input_tokens> <output_tokens> [task]
            model = sys.argv[2]
            input_tokens = int(sys.argv[3])
            output_tokens = int(sys.argv[4])
            task = sys.argv[5] if len(sys.argv) > 5 else "unknown"
            
            monitor.record_usage(model, input_tokens, output_tokens, task)
            cost = monitor._calculate_cost(model, input_tokens, output_tokens)
            print(f"✅ 记录: {model}, ${cost:.4f}, task={task}")
        
        elif command == "budget":
            budget = monitor.check_budget()
            print(f"今日: ${budget['daily_cost']:.2f} / ${budget['daily_budget']:.2f}")
            print(f"本月: ${budget['monthly_cost']:.2f} / ${budget['monthly_budget']:.2f}")
            if budget['alerts']:
                print("\n⚠️ 预算告警:")
                for alert in budget['alerts']:
                    print(f"  {alert['message']}")
        
        elif command == "report":
            print(monitor.generate_report())
    else:
        print(monitor.generate_report())

if __name__ == "__main__":
    main()
