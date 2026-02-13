#!/usr/bin/env python3
"""
AI Brain 集成器 - 根据大脑状态调整创造系统
"""

import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
SKILL_DIR = WORKSPACE / "skills/daily-creative-brief"


def load_brain_state():
    """加载AI Brain状态"""
    brain_file = MEMORY_DIR / "bowlwanpi-brain.json"
    level_file = MEMORY_DIR / "bowlwanpi-level.json"
    emotions_file = MEMORY_DIR / "bowlwanpi-emotions.json"
    
    state = {
        "level": 1,
        "exp": 0,
        "drive": 0.5,
        "memories": 0,
        "emotions": {},
        "habits": {}
    }
    
    # 加载大脑核心数据
    if brain_file.exists():
        try:
            with open(brain_file, 'r') as f:
                brain = json.load(f)
                state["drive"] = brain.get("drive", {}).get("drive", 0.5)
                state["memories"] = brain.get("memory", {}).get("total_memories", 0)
                state["drive_seeking"] = brain.get("drive", {}).get("seeking", [])
                state["drive_anticipating"] = brain.get("drive", {}).get("anticipating", [])
        except:
            pass
    
    # 加载等级数据
    if level_file.exists():
        try:
            with open(level_file, 'r') as f:
                level = json.load(f)
                state["level"] = level.get("level", 1)
                state["exp"] = level.get("exp", 0)
                state["achievements"] = level.get("achievements", [])
        except:
            pass
    
    # 加载情感状态
    if emotions_file.exists():
        try:
            with open(emotions_file, 'r') as f:
                emotions = json.load(f)
                state["emotions"] = emotions.get("current_state", {})
        except:
            pass
    
    return state


def analyze_brain_for_creativity(brain_state):
    """分析大脑状态，给出创造建议"""
    
    suggestions = {
        "difficulty_adjustment": "normal",  # easy, normal, hard
        "challenge_type": None,
        "motivation_message": "",
        "special_actions": []
    }
    
    drive = brain_state.get("drive", 0.5)
    level = brain_state.get("level", 1)
    exp = brain_state.get("exp", 0)
    
    # 根据动力值调整
    if drive >= 0.8:
        suggestions["difficulty_adjustment"] = "hard"
        suggestions["motivation_message"] = "🔥 动力满格！这是挑战高难度任务的最佳时机！"
        suggestions["special_actions"].append("推荐尝试进阶挑战类型")
        
    elif drive >= 0.5:
        suggestions["difficulty_adjustment"] = "normal"
        suggestions["motivation_message"] = "💪 状态不错，保持这个节奏！"
        
    elif drive >= 0.3:
        suggestions["difficulty_adjustment"] = "easy"
        suggestions["motivation_message"] = "🌱 从简单任务开始，逐步建立创造节奏"
        suggestions["special_actions"].append("推荐15分钟以内的快速任务")
        
    else:
        suggestions["difficulty_adjustment"] = "easy"
        suggestions["motivation_message"] = "💤 动力较低，需要外部刺激。试试这些："
        suggestions["special_actions"].extend([
            "回顾过去的成功创造",
            "从最喜欢的创造类型开始",
            "完成一个5分钟的超简单任务"
        ])
    
    # 根据等级调整
    if level == 1 and exp < 50:
        suggestions["special_actions"].append("🎯 距离升级还差 {} 经验，再完成几个任务！".format(100 - exp))
    
    # 检查是否有未完成的挑战类型
    seeking = brain_state.get("drive_seeking", [])
    if seeking:
        suggestions["challenge_type_hint"] = seeking[0]
    
    # 分析情感状态
    emotions = brain_state.get("emotions", {})
    valence = emotions.get("valence", 0)
    energy = emotions.get("energy", 0.5)
    
    if valence < -0.3:
        suggestions["special_actions"].append("😊 检测到低情绪，建议先做一些能带来成就感的小任务")
    
    if energy < 0.3:
        suggestions["special_actions"].append("⚡ 能量较低，选择轻松有趣的任务")
    
    return suggestions


def sync_with_brain():
    """同步创造系统与AI Brain"""
    print("🧠 正在同步 AI Brain 状态...\n")
    
    # 加载大脑状态
    brain = load_brain_state()
    
    print(f"📊 当前状态:")
    print(f"  等级: Lv.{brain['level']} ({brain['exp']}/100 EXP)")
    print(f"  动力: {brain['drive']:.0%}")
    print(f"  记忆: {brain['memories']} 条")
    print()
    
    # 分析建议
    suggestions = analyze_brain_for_creativity(brain)
    
    print(f"💡 创造建议:")
    print(f"  {suggestions['motivation_message']}")
    print(f"  难度调整: {suggestions['difficulty_adjustment']}")
    print()
    
    if suggestions.get("special_actions"):
        print(f"🎯 特别行动:")
        for action in suggestions["special_actions"]:
            print(f"  • {action}")
        print()
    
    # 保存建议到文件（供其他脚本使用）
    config_file = SKILL_DIR / "config/brain-sync.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    sync_data = {
        "timestamp": datetime.now().isoformat(),
        "brain_state": {
            "level": brain["level"],
            "exp": brain["exp"],
            "drive": brain["drive"],
            "memories": brain["memories"]
        },
        "suggestions": suggestions
    }
    
    with open(config_file, 'w') as f:
        json.dump(sync_data, f, indent=2)
    
    print(f"💾 建议已保存到: {config_file}")
    
    return suggestions


def update_brain_after_creation(task_type, difficulty, success=True):
    """完成任务后更新大脑状态"""
    
    brain_file = MEMORY_DIR / "bowlwanpi-brain.json"
    
    if not brain_file.exists():
        return
    
    try:
        with open(brain_file, 'r') as f:
            brain = json.load(f)
        
        # 增加动力
        current_drive = brain.get("drive", {}).get("drive", 0.5)
        reward = 0.1  # 基础奖励
        
        # 根据难度额外奖励
        if difficulty == "hard":
            reward += 0.05
        
        # 成功奖励，失败小幅提升（尝试也值得奖励）
        if success:
            new_drive = min(1.0, current_drive + reward)
        else:
            new_drive = min(1.0, current_drive + 0.03)
        
        if "drive" not in brain:
            brain["drive"] = {}
        
        brain["drive"]["drive"] = new_drive
        brain["drive"]["baseline"] = 0.5
        brain["drive"]["anticipating"] = ["下一个创造项目", "能力提升"]
        brain["updated"] = datetime.now().isoformat()
        
        # 添加记忆
        recent_topics = brain.get("memory", {}).get("recent_topics", [])
        if task_type not in recent_topics:
            recent_topics.append(task_type)
            recent_topics = recent_topics[-5:]  # 保持最近5个
        
        if "memory" not in brain:
            brain["memory"] = {}
        brain["memory"]["recent_topics"] = recent_topics
        
        # 保存
        with open(brain_file, 'w') as f:
            json.dump(brain, f, indent=2)
        
        print(f"🧠 AI Brain 已更新:")
        print(f"  动力值: {current_drive:.0%} → {new_drive:.0%}")
        print(f"  最近话题: {', '.join(recent_topics)}")
        
    except Exception as e:
        print(f"⚠️ 更新Brain失败: {e}")


def get_smart_challenge():
    """获取智能推荐的挑战"""
    
    # 同步大脑状态
    suggestions = sync_with_brain()
    
    # 根据建议调整
    difficulty = suggestions.get("difficulty_adjustment", "normal")
    
    print(f"\n🎯 基于AI Brain分析，推荐 {difficulty} 难度挑战\n")
    
    # 调用推荐器
    import sys
    sys.path.insert(0, str(SKILL_DIR / "scripts"))
    from recommender import recommend_challenge, get_drive_state
    
    drive = get_drive_state()
    challenge = recommend_challenge(drive=drive)
    
    # 应用难度调整
    if difficulty == "easy" and challenge.get("diff") in ["中等", "进阶"]:
        challenge["original_diff"] = challenge["diff"]
        challenge["diff"] = "简单"
        challenge["note"] = "🧠 根据当前状态调整为简单难度"
    
    return challenge


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "update":
        # 更新模式
        if len(sys.argv) >= 4:
            update_brain_after_creation(sys.argv[2], sys.argv[3])
        else:
            print("用法: python3 brain_sync.py update [任务类型] [难度]")
    else:
        # 同步模式
        sync_with_brain()
