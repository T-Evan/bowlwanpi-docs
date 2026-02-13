#!/usr/bin/env python3
"""
智能挑战推荐器 - 基于历史数据个性化推荐
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

WORKSPACE = Path("/root/.openclaw/workspace")
PKM_DIR = WORKSPACE / "pkm"
MEMORY_DIR = WORKSPACE / "memory"

# 扩展挑战库，增加更多类型
CHALLENGES_DB = {
    "skill-dev": {
        "weight": 1.0,
        "items": [
            {"title": "开发一个CLI工具", "desc": "解决命令行的小问题", "time": "1小时", "diff": "中等"},
            {"title": "创建一个MCP技能", "desc": "让AI能调用你的工具", "time": "2小时", "diff": "进阶"},
            {"title": "写一个自动化脚本", "desc": "自动化重复工作", "time": "30分钟", "diff": "简单"},
            {"title": "开发API接口", "desc": "创建简单的REST API", "time": "1.5小时", "diff": "中等"},
        ]
    },
    "content-creation": {
        "weight": 1.0,
        "items": [
            {"title": "写一篇技术博客", "desc": "分享你的学习经验", "time": "45分钟", "diff": "简单"},
            {"title": "制作教程视频脚本", "desc": "规划一个教学视频", "time": "1小时", "diff": "中等"},
            {"title": "写技术推特线程", "desc": "5-10条连贯的技术分享", "time": "20分钟", "diff": "简单"},
            {"title": "创作技术漫画脚本", "desc": "用漫画讲技术概念", "time": "1.5小时", "diff": "中等"},
        ]
    },
    "automation": {
        "weight": 1.0,
        "items": [
            {"title": "自动化数据整理", "desc": "让数据处理自动完成", "time": "30分钟", "diff": "简单"},
            {"title": "创建定时任务", "desc": "设置自动执行的流程", "time": "20分钟", "diff": "简单"},
            {"title": "开发监控告警", "desc": "异常情况自动通知", "time": "1小时", "diff": "中等"},
        ]
    },
    "exploration": {
        "weight": 1.0,
        "items": [
            {"title": "学习新框架", "desc": "尝试一个没用过的工具", "time": "2小时", "diff": "中等"},
            {"title": "研究开源项目", "desc": "深入分析一个优秀项目", "time": "1.5小时", "diff": "中等"},
            {"title": "体验新AI工具", "desc": "试用最新的AI产品", "time": "45分钟", "diff": "简单"},
        ]
    },
    "optimization": {
        "weight": 1.0,
        "items": [
            {"title": "性能优化", "desc": "让现有代码快一倍", "time": "1小时", "diff": "中等"},
            {"title": "重构代码", "desc": "提升代码质量", "time": "1.5小时", "diff": "中等"},
            {"title": "简化流程", "desc": "减少不必要的步骤", "time": "30分钟", "diff": "简单"},
        ]
    },
    "creative-writing": {
        "weight": 1.0,
        "items": [
            {"title": "写技术寓言", "desc": "用故事讲技术概念", "time": "45分钟", "diff": "中等"},
            {"title": "创作类比", "desc": "找到技术的形象比喻", "time": "20分钟", "diff": "简单"},
            {"title": "写科幻短篇", "desc": "设想AI未来场景", "time": "1.5小时", "diff": "中等"},
        ]
    },
    "community": {
        "weight": 0.8,
        "items": [
            {"title": "回复社区帖子", "desc": "在Moltbook分享见解", "time": "30分钟", "diff": "简单"},
            {"title": "帮助他人", "desc": "解答一个技术问题", "time": "45分钟", "diff": "中等"},
            {"title": "发起讨论", "desc": "提出有意思的话题", "time": "20分钟", "diff": "简单"},
        ]
    }
}


def load_creation_history():
    """加载创造历史"""
    history = []
    
    # 从daily目录加载
    daily_dir = PKM_DIR / "daily"
    if daily_dir.exists():
        for json_file in daily_dir.glob("creations-*.json"):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        history.extend(data)
            except:
                pass
    
    return history


def analyze_preferences(history):
    """分析用户偏好"""
    if not history:
        return None
    
    # 统计任务类型
    type_counter = Counter()
    difficulty_counter = Counter()
    
    for item in history:
        task = item.get('task', '')
        # 推断类型
        if any(kw in task for kw in ['技能', '开发', 'CLI', 'API']):
            type_counter['skill-dev'] += 1
        elif any(kw in task for kw in ['内容', '文章', '分享', '博客']):
            type_counter['content-creation'] += 1
        elif any(kw in task for kw in ['自动', '脚本', '定时']):
            type_counter['automation'] += 1
        elif any(kw in task for kw in ['探索', '学习', '研究']):
            type_counter['exploration'] += 1
        elif any(kw in task for kw in ['优化', '重构', '简化']):
            type_counter['optimization'] += 1
        else:
            type_counter['creative-writing'] += 1
    
    # 找出最喜欢的类型
    favorite_type = type_counter.most_common(1)[0][0] if type_counter else None
    
    # 计算多样性
    total = sum(type_counter.values())
    diversity = len(type_counter) / len(CHALLENGES_DB) if total > 0 else 0
    
    return {
        "favorite_type": favorite_type,
        "type_distribution": dict(type_counter),
        "total_creations": total,
        "diversity": diversity,
        "suggestion": "expand" if diversity < 0.5 else "deepen"
    }


def get_drive_state():
    """获取当前动力状态"""
    brain_file = MEMORY_DIR / "bowlwanpi-brain.json"
    
    if brain_file.exists():
        try:
            with open(brain_file, 'r') as f:
                brain = json.load(f)
                return brain.get("drive", {}).get("drive", 0.5)
        except:
            pass
    
    return 0.5


def recommend_challenge(history=None, drive=None):
    """智能推荐挑战"""
    
    # 加载历史
    if history is None:
        history = load_creation_history()
    
    # 分析偏好
    prefs = analyze_preferences(history)
    
    # 获取动力状态
    if drive is None:
        drive = get_drive_state()
    
    # 根据偏好和动力调整权重
    weights = {}
    for challenge_type, data in CHALLENGES_DB.items():
        weight = data["weight"]
        
        # 如果是喜欢的类型，增加权重
        if prefs and prefs["favorite_type"] == challenge_type:
            weight *= 1.5
        
        # 如果多样性低，增加未尝试类型的权重
        if prefs and prefs["suggestion"] == "expand":
            if challenge_type not in prefs.get("type_distribution", {}):
                weight *= 2.0
        
        # 根据动力调整难度偏好
        # 高动力：更喜欢有挑战性的
        # 低动力：更喜欢简单快速的
        
        weights[challenge_type] = weight
    
    # 加权随机选择类型
    types = list(weights.keys())
    type_weights = [weights[t] for t in types]
    selected_type = random.choices(types, weights=type_weights, k=1)[0]
    
    # 从选中的类型中随机选择具体挑战
    challenges = CHALLENGES_DB[selected_type]["items"]
    
    # 根据动力筛选难度
    if drive > 0.7:
        # 高动力，可以选中等或进阶
        candidates = [c for c in challenges if c["diff"] in ["中等", "进阶"]]
    elif drive < 0.3:
        # 低动力，只选简单的
        candidates = [c for c in challenges if c["diff"] == "简单"]
    else:
        # 正常状态，都可以
        candidates = challenges
    
    if not candidates:
        candidates = challenges
    
    selected = random.choice(candidates)
    
    # 添加推荐理由
    reasons = []
    if prefs:
        if selected_type == prefs.get("favorite_type"):
            reasons.append("基于你喜欢的类型推荐")
        elif prefs["suggestion"] == "expand":
            reasons.append("尝试新类型，扩展创造力边界")
    
    if drive > 0.7:
        reasons.append("你动力满满，适合有挑战性的任务")
    elif drive < 0.3:
        reasons.append("从简单任务开始，重建创造节奏")
    
    selected["type"] = selected_type
    selected["reasons"] = reasons
    selected["personalization"] = prefs
    
    return selected


def generate_personalized_brief():
    """生成个性化简报"""
    print("🎯 正在生成个性化挑战推荐...\n")
    
    # 加载历史
    history = load_creation_history()
    print(f"📊 分析了 {len(history)} 条历史记录")
    
    # 分析偏好
    prefs = analyze_preferences(history)
    if prefs:
        print(f"🧠 发现你最喜欢的创造类型: {prefs['favorite_type']}")
        print(f"📈 创造多样性: {prefs['diversity']:.0%}")
    
    # 获取动力
    drive = get_drive_state()
    print(f"🔥 当前动力值: {drive:.0%}")
    
    # 推荐挑战
    challenge = recommend_challenge(history, drive)
    
    print(f"\n🎯 今日个性化挑战")
    print("-" * 40)
    print(f"类型: {challenge['type']}")
    print(f"标题: {challenge['title']}")
    print(f"难度: {challenge['diff']}")
    print(f"预计时间: {challenge['time']}")
    print(f"\n描述: {challenge['desc']}")
    
    if challenge.get('reasons'):
        print(f"\n💡 推荐理由:")
        for reason in challenge['reasons']:
            print(f"  • {reason}")
    
    return challenge


if __name__ == "__main__":
    challenge = generate_personalized_brief()
