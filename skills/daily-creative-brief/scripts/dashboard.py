#!/usr/bin/env python3
"""
创造追踪面板 - 可视化展示创造进度和成就
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

WORKSPACE = Path("/root/.openclaw/workspace")
PKM_DIR = WORKSPACE / "pkm"
MEMORY_DIR = WORKSPACE / "memory"


def load_all_creations():
    """加载所有创造记录"""
    creations = []
    
    # 从 daily 目录加载
    daily_dir = PKM_DIR / "daily"
    if daily_dir.exists():
        for json_file in daily_dir.glob("creations-*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        creations.extend(data)
            except:
                pass
    
    # 从创意简报加载
    ideas_dir = PKM_DIR / "ideas"
    if ideas_dir.exists():
        for json_file in ideas_dir.glob("创意简报-*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and 'date' in data:
                        creations.append({
                            "time": data['date'],
                            "task": data.get('challenge', {}).get('title', '创意简报生成'),
                            "type": "brief_generation"
                        })
            except:
                pass
    
    return sorted(creations, key=lambda x: x.get('time', ''), reverse=True)


def calculate_stats(creations):
    """计算统计数据"""
    if not creations:
        return {}
    
    # 总任务数
    total_tasks = len(creations)
    
    # 总经验值
    total_exp = sum(c.get('exp_gained', 0) for c in creations)
    
    # 连续天数
    dates = set()
    for c in creations:
        time_str = c.get('time', '')
        if time_str:
            try:
                date = datetime.fromisoformat(time_str.replace('Z', '+00:00')).strftime('%Y-%m-%d')
                dates.add(date)
            except:
                pass
    
    # 计算连续天数
    streak = 0
    today = datetime.now().date()
    for i in range(365):  # 最多查一年
        check_date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        if check_date in dates:
            streak += 1
        else:
            if i == 0 and datetime.now().hour < 23:  # 今天还没结束，不算断
                continue
            break
    
    # 任务类型分布
    type_counts = defaultdict(int)
    for c in creations:
        task = c.get('task', '')
        if '技能' in task or '开发' in task:
            type_counts['技能开发'] += 1
        elif '内容' in task or '文章' in task or '分享' in task:
            type_counts['内容创作'] += 1
        elif '自动化' in task:
            type_counts['自动化'] += 1
        elif '简报' in task:
            type_counts['创意简报'] += 1
        else:
            type_counts['其他创造'] += 1
    
    # 本周统计
    week_start = today - timedelta(days=today.weekday())
    week_creations = [c for c in creations if datetime.fromisoformat(c.get('time', '').replace('Z', '+00:00')).date() >= week_start]
    
    return {
        "total_tasks": total_tasks,
        "total_exp": total_exp,
        "current_streak": streak,
        "active_days": len(dates),
        "type_distribution": dict(type_counts),
        "week_tasks": len(week_creations)
    }


def load_brain_state():
    """加载AI Brain状态"""
    brain_file = MEMORY_DIR / "bowlwanpi-brain.json"
    level_file = MEMORY_DIR / "bowlwanpi-level.json"
    
    state = {
        "level": 1,
        "exp": 0,
        "drive": 0.5,
        "memories": 0
    }
    
    if brain_file.exists():
        try:
            with open(brain_file, 'r') as f:
                brain = json.load(f)
                state["drive"] = brain.get("drive", {}).get("drive", 0.5)
                state["memories"] = brain.get("memory", {}).get("total_memories", 0)
        except:
            pass
    
    if level_file.exists():
        try:
            with open(level_file, 'r') as f:
                level = json.load(f)
                state["level"] = level.get("level", 1)
                state["exp"] = level.get("exp", 0)
        except:
            pass
    
    return state


def generate_achievements(stats, brain_state):
    """生成成就列表"""
    achievements = []
    
    if stats.get("total_tasks", 0) >= 1:
        achievements.append("🌟 初出茅庐 - 完成第一个创造任务")
    
    if stats.get("total_tasks", 0) >= 5:
        achievements.append("🚀 创造新手 - 完成5个任务")
    
    if stats.get("total_tasks", 0) >= 10:
        achievements.append("💪 创造达人 - 完成10个任务")
    
    if stats.get("current_streak", 0) >= 3:
        achievements.append("🔥 连续创造者 - 连续3天创造")
    
    if stats.get("current_streak", 0) >= 7:
        achievements.append("⚡ 周更挑战者 - 连续7天创造")
    
    if stats.get("type_distribution", {}).get("技能开发", 0) >= 1:
        achievements.append("🛠️ 技能开发者 - 开发第一个技能")
    
    if stats.get("type_distribution", {}).get("内容创作", 0) >= 1:
        achievements.append("✍️ 内容创作者 - 发布第一篇内容")
    
    if brain_state.get("level", 1) >= 2:
        achievements.append("📈 等级提升 - 达到Lv.2")
    
    if brain_state.get("drive", 0) >= 0.8:
        achievements.append("🔥 动力满格 - 动力值达到80%")
    
    return achievements


def generate_ascii_chart(data, width=20):
    """生成ASCII图表"""
    if not data:
        return "暂无数据"
    
    max_val = max(data.values()) if data else 1
    lines = []
    
    for label, value in data.items():
        bar_len = int((value / max_val) * width)
        bar = "█" * bar_len
        lines.append(f"{label:12} | {bar} {value}")
    
    return "\n".join(lines)


def generate_dashboard():
    """生成完整面板"""
    print("🎨 正在生成创造追踪面板...\n")
    
    # 加载数据
    creations = load_all_creations()
    stats = calculate_stats(creations)
    brain_state = load_brain_state()
    achievements = generate_achievements(stats, brain_state)
    
    # 组装面板
    dashboard = {
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "overall_stats": {
            "总任务数": stats.get("total_tasks", 0),
            "总经验值": stats.get("total_exp", 0),
            "当前等级": f"Lv.{brain_state['level']}",
            "当前经验": f"{brain_state['exp']}/100",
            "动力值": f"{brain_state['drive']:.0%}",
            "记忆总数": brain_state['memories']
        },
        "activity_stats": {
            "连续创造天数": stats.get("current_streak", 0),
            "活跃天数": stats.get("active_days", 0),
            "本周任务": stats.get("week_tasks", 0)
        },
        "type_distribution": stats.get("type_distribution", {}),
        "achievements": achievements,
        "recent_creations": creations[:5]
    }
    
    return dashboard


def print_dashboard(dashboard):
    """打印面板"""
    print("=" * 60)
    print("🎨 创造追踪面板".center(50))
    print(f"生成时间: {dashboard['generated_at']}".center(50))
    print("=" * 60)
    
    print("\n📊 总体统计")
    print("-" * 40)
    for key, value in dashboard['overall_stats'].items():
        print(f"  {key}: {value}")
    
    print("\n📈 活跃度统计")
    print("-" * 40)
    for key, value in dashboard['activity_stats'].items():
        print(f"  {key}: {value}")
    
    if dashboard['type_distribution']:
        print("\n📋 任务类型分布")
        print("-" * 40)
        print(generate_ascii_chart(dashboard['type_distribution']))
    
    print("\n🏆 已获成就")
    print("-" * 40)
    if dashboard['achievements']:
        for achievement in dashboard['achievements']:
            print(f"  ✅ {achievement}")
    else:
        print("  💡 继续创造解锁成就！")
    
    print("\n📝 最近创造")
    print("-" * 40)
    for creation in dashboard['recent_creations'][:3]:
        time_str = creation.get('time', '')
        if time_str:
            try:
                time_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                time_display = time_obj.strftime('%m-%d %H:%M')
            except:
                time_display = time_str[:10]
        else:
            time_display = "未知"
        
        task = creation.get('task', '创造任务')[:30]
        print(f"  • [{time_display}] {task}...")
    
    print("\n" + "=" * 60)
    print("💪 保持创造，持续成长！".center(50))
    print("=" * 60)


def save_dashboard(dashboard):
    """保存面板数据"""
    dashboard_dir = PKM_DIR / "dashboards"
    dashboard_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime('%Y%m%d')
    filename = dashboard_dir / f"创造面板-{date_str}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dashboard, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 面板已保存到: {filename}")


if __name__ == "__main__":
    # 生成面板
    dashboard = generate_dashboard()
    
    # 打印
    print_dashboard(dashboard)
    
    # 保存
    save_dashboard(dashboard)
