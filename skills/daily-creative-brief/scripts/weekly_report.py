#!/usr/bin/env python3
"""
周报告生成器 - 汇总一周创造成果
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict

WORKSPACE = Path("/root/.openclaw/workspace")
PKM_DIR = WORKSPACE / "pkm"
MEMORY_DIR = WORKSPACE / "memory"


def load_week_creations(weeks_ago=0):
    """加载指定周的创造记录"""
    creations = []
    
    # 计算周范围
    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday() + (weeks_ago * 7))
    week_end = week_start + timedelta(days=6)
    
    # 从daily目录加载
    daily_dir = PKM_DIR / "daily"
    if daily_dir.exists():
        for json_file in daily_dir.glob("creations-*.json"):
            try:
                # 从文件名提取日期
                date_str = json_file.stem.replace("creations-", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
                if week_start <= file_date <= week_end:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                item['date'] = date_str
                            creations.extend(data)
            except:
                pass
    
    # 从简报加载
    ideas_dir = PKM_DIR / "ideas"
    if ideas_dir.exists():
        for json_file in ideas_dir.glob("创意简报-*.json"):
            try:
                date_str = json_file.stem.replace("创意简报-", "")
                file_date = datetime.strptime(date_str, "%Y%m%d").date()
                
                if week_start <= file_date <= week_end:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            creations.append({
                                'date': date_str,
                                'task': data.get('challenge', {}).get('title', '创意简报'),
                                'exp_gained': 5,
                                'type': 'brief'
                            })
            except:
                pass
    
    return sorted(creations, key=lambda x: x.get('date', '')), week_start, week_end


def generate_weekly_report(weeks_ago=0):
    """生成周报告"""
    creations, week_start, week_end = load_week_creations(weeks_ago)
    
    if not creations:
        return None, week_start, week_end
    
    # 基础统计
    total_tasks = len(creations)
    total_exp = sum(c.get('exp_gained', 0) for c in creations)
    
    # 按天统计
    daily_stats = defaultdict(int)
    for c in creations:
        daily_stats[c.get('date', 'unknown')] += 1
    
    # 类型分布
    type_counter = Counter()
    for c in creations:
        task = c.get('task', '')
        if any(kw in task for kw in ['技能', '开发']):
            type_counter['技能开发'] += 1
        elif any(kw in task for kw in ['内容', '文章', '分享']):
            type_counter['内容创作'] += 1
        elif any(kw in task for kw in ['自动', '脚本']):
            type_counter['自动化'] += 1
        elif any(kw in task for kw in ['探索', '学习']):
            type_counter['探索学习'] += 1
        elif any(kw in task for kw in ['优化', '重构']):
            type_counter['优化改进'] += 1
        else:
            type_counter['其他创造'] += 1
    
    # 活跃天数
    active_days = len(daily_stats)
    
    # 查找亮点
    highlights = []
    
    # 最高产的一天
    if daily_stats:
        best_day = max(daily_stats.items(), key=lambda x: x[1])
        highlights.append(f"📅 最高产的一天是 {best_day[0]}，完成了 {best_day[1]} 个任务")
    
    # 成就徽章
    badges = []
    if total_tasks >= 5:
        badges.append("🏆 周创造达人 - 完成5+任务")
    if active_days >= 5:
        badges.append("🔥 全勤奖 - 5天以上活跃")
    if len(type_counter) >= 3:
        badges.append("🌈 多面手 - 涉及3+创造类型")
    if total_exp >= 50:
        badges.append("⭐ 经验收割机 - 获得50+经验")
    
    # 生成报告
    report = {
        "period": f"{week_start.strftime('%m月%d日')} - {week_end.strftime('%m月%d日')}",
        "summary": {
            "总任务数": total_tasks,
            "总经验值": total_exp,
            "活跃天数": active_days,
            "日均任务": round(total_tasks / max(active_days, 1), 1)
        },
        "type_distribution": dict(type_counter),
        "daily_activity": dict(daily_stats),
        "highlights": highlights,
        "badges": badges,
        "creations": creations
    }
    
    return report, week_start, week_end


def print_weekly_report(report, week_start, week_end):
    """打印周报告"""
    if not report:
        print("📭 本周暂无创造记录")
        print(f"   时间: {week_start.strftime('%Y-%m-%d')} - {week_end.strftime('%Y-%m-%d')}")
        return
    
    print("=" * 60)
    print(f"📊 周创造报告 | {report['period']}")
    print("=" * 60)
    
    print("\n📈 核心数据")
    print("-" * 40)
    for key, value in report['summary'].items():
        print(f"  {key}: {value}")
    
    if report.get('type_distribution'):
        print("\n📋 创造类型分布")
        print("-" * 40)
        for type_name, count in sorted(report['type_distribution'].items(), 
                                        key=lambda x: x[1], reverse=True):
            bar = "█" * count
            print(f"  {type_name:10} | {bar} {count}")
    
    if report.get('daily_activity'):
        print("\n📅 每日活跃度")
        print("-" * 40)
        for date, count in sorted(report['daily_activity'].items()):
            bar = "●" * count
            print(f"  {date} | {bar} {count}")
    
    if report.get('highlights'):
        print("\n✨ 本周亮点")
        print("-" * 40)
        for highlight in report['highlights']:
            print(f"  {highlight}")
    
    if report.get('badges'):
        print("\n🏅 获得徽章")
        print("-" * 40)
        for badge in report['badges']:
            print(f"  {badge}")
    
    print("\n📝 本周创造清单")
    print("-" * 40)
    for i, creation in enumerate(report['creations'][:10], 1):
        date = creation.get('date', '')
        task = creation.get('task', '创造任务')[:25]
        print(f"  {i}. [{date}] {task}...")
    
    if len(report['creations']) > 10:
        print(f"  ... 还有 {len(report['creations']) - 10} 项")
    
    print("\n" + "=" * 60)
    print("💪 继续创造，下周更精彩！".center(50))
    print("=" * 60)


def save_weekly_report(report, week_start):
    """保存周报告"""
    if not report:
        return
    
    reports_dir = PKM_DIR / "weekly-reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    filename = reports_dir / f"周报告-{week_start.strftime('%Y%m%d')}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 报告已保存: {filename}")


def main():
    """主函数"""
    import sys
    
    # 默认生成本周报告
    weeks_ago = 0
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "last":
            weeks_ago = 1
        else:
            try:
                weeks_ago = int(sys.argv[1])
            except:
                pass
    
    # 生成报告
    report, week_start, week_end = generate_weekly_report(weeks_ago)
    
    # 打印
    print_weekly_report(report, week_start, week_end)
    
    # 保存
    if report:
        save_weekly_report(report, week_start)


if __name__ == "__main__":
    main()
