#!/usr/bin/env python3
"""
统计可视化 - 每日灵感简报扩展
生成创造活动统计图表和报告
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict


class StatsVisualizer:
    def __init__(self):
        self.data_dir = Path.home() / ".openclaw/workspace/pkm/achievements"
        self.progress_file = self.data_dir / "progress.json"
        self.report_dir = Path.home() / ".openclaw/workspace/pkm/reports"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        self.progress = self._load_progress()
    
    def _load_progress(self):
        """加载进度数据"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"daily_log": {}, "stats": {}}
    
    def generate_ascii_chart(self, data, title, width=40):
        """生成ASCII图表"""
        if not data:
            return f"{title}: 暂无数据"
        
        max_val = max(data.values()) if data else 1
        lines = [f"\n{title}", "=" * width]
        
        for label, value in data.items():
            bar_len = int((value / max_val) * (width - 20))
            bar = "█" * bar_len
            lines.append(f"{label:12} |{bar:<{width-20}}| {value}")
        
        return "\n".join(lines)
    
    def get_weekly_stats(self):
        """获取本周统计"""
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday())
        
        weekly_data = defaultdict(int)
        for date_str, tasks in self.progress.get("daily_log", {}).items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if week_start <= date <= today:
                day_name = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()]
                weekly_data[day_name] += len(tasks)
        
        return dict(weekly_data)
    
    def get_type_distribution(self):
        """获取任务类型分布"""
        type_counts = defaultdict(int)
        for tasks in self.progress.get("daily_log", {}).values():
            for task in tasks:
                type_counts[task["type"]] += 1
        return dict(type_counts)
    
    def get_difficulty_distribution(self):
        """获取难度分布"""
        diff_counts = defaultdict(int)
        for tasks in self.progress.get("daily_log", {}).values():
            for task in tasks:
                diff_counts[task["difficulty"]] += 1
        return dict(diff_counts)
    
    def get_activity_heatmap(self, days=30):
        """生成活动热力图"""
        today = datetime.now()
        heatmap_data = []
        
        # 按周组织
        for week in range(5):
            week_row = []
            for day in range(7):
                date = today - timedelta(days=(week * 7 + day))
                date_str = date.strftime("%Y-%m-%d")
                count = len(self.progress.get("daily_log", {}).get(date_str, []))
                
                # 热度等级
                if count == 0:
                    level = "⬜"
                elif count == 1:
                    level = "🟩"
                elif count <= 3:
                    level = "🟨"
                else:
                    level = "🟥"
                
                week_row.insert(0, (date_str, level, count))
            heatmap_data.insert(0, week_row)
        
        return heatmap_data
    
    def print_full_report(self):
        """打印完整报告"""
        print("\n" + "=" * 60)
        print("📊 创造活动统计报告")
        print("=" * 60)
        
        # 总体统计
        stats = self.progress.get("stats", {})
        print(f"\n📈 总体统计")
        print(f"  总完成任务: {stats.get('total_completed', 0)} 个")
        print(f"  当前连胜: {stats.get('current_streak', 0)} 天")
        print(f"  最高连胜: {stats.get('max_streak', 0)} 天")
        print(f"  总积分: {stats.get('total_points', 0)} 点")
        
        # 本周活动
        weekly = self.get_weekly_stats()
        print(self.generate_ascii_chart(weekly, "📅 本周活动分布"))
        
        # 类型分布
        types = self.get_type_distribution()
        if types:
            print(self.generate_ascii_chart(types, "🎯 任务类型分布"))
        
        # 难度分布
        diffs = self.get_difficulty_distribution()
        if diffs:
            print(self.generate_ascii_chart(diffs, "💪 难度分布"))
        
        # 活动热力图
        print("\n🔥 最近30天活动热力图")
        print("   日 一 二 三 四 五 六")
        heatmap = self.get_activity_heatmap()
        for week in heatmap:
            row = ""
            for date_str, level, count in week:
                row += f" {level}"
            print(f"  {row}")
        print("\n  ⬜ 无  🟩 1个  🟨 2-3个  🟥 4+个")
    
    def generate_monthly_report(self):
        """生成月度报告"""
        today = datetime.now()
        month_start = today.replace(day=1)
        
        month_data = {
            "month": today.strftime("%Y年%m月"),
            "total_tasks": 0,
            "active_days": 0,
            "by_type": defaultdict(int),
            "by_difficulty": defaultdict(int),
            "daily_activity": []
        }
        
        for date_str, tasks in self.progress.get("daily_log", {}).items():
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if date >= month_start:
                month_data["total_tasks"] += len(tasks)
                month_data["active_days"] += 1
                
                for task in tasks:
                    month_data["by_type"][task["type"]] += 1
                    month_data["by_difficulty"][task["difficulty"]] += 1
                
                month_data["daily_activity"].append({
                    "date": date_str,
                    "count": len(tasks)
                })
        
        month_data["by_type"] = dict(month_data["by_type"])
        month_data["by_difficulty"] = dict(month_data["by_difficulty"])
        
        # 保存报告
        report_file = self.report_dir / f"monthly-{today.strftime('%Y%m')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(month_data, f, ensure_ascii=False, indent=2)
        
        return month_data
    
    def export_summary(self):
        """导出摘要"""
        summary = {
            "generated_at": datetime.now().isoformat(),
            "stats": self.progress.get("stats", {}),
            "weekly_activity": self.get_weekly_stats(),
            "type_distribution": self.get_type_distribution(),
            "difficulty_distribution": self.get_difficulty_distribution()
        }
        
        summary_file = self.report_dir / "latest-summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        return summary


def main():
    import sys
    
    visualizer = StatsVisualizer()
    
    if len(sys.argv) < 2:
        visualizer.print_full_report()
        return
    
    command = sys.argv[1]
    
    if command == "weekly":
        weekly = visualizer.get_weekly_stats()
        print(visualizer.generate_ascii_chart(weekly, "📅 本周活动分布"))
    
    elif command == "types":
        types = visualizer.get_type_distribution()
        print(visualizer.generate_ascii_chart(types, "🎯 任务类型分布"))
    
    elif command == "heatmap":
        print("\n🔥 最近30天活动热力图")
        print("   日 一 二 三 四 五 六")
        heatmap = visualizer.get_activity_heatmap()
        for week in heatmap:
            row = ""
            for date_str, level, count in week:
                row += f" {level}"
            print(f"  {row}")
        print("\n  ⬜ 无  🟩 1个  🟨 2-3个  🟥 4+个")
    
    elif command == "monthly":
        report = visualizer.generate_monthly_report()
        print(f"\n📊 {report['month']} 月度报告")
        print(f"总任务数: {report['total_tasks']}")
        print(f"活跃天数: {report['active_days']}")
        print(f"类型分布: {dict(report['by_type'])}")
        print(f"难度分布: {dict(report['by_difficulty'])}")
    
    elif command == "export":
        summary = visualizer.export_summary()
        print("✅ 统计摘要已导出")
        print(f"文件: {visualizer.report_dir}/latest-summary.json")
    
    else:
        visualizer.print_full_report()


if __name__ == "__main__":
    main()
