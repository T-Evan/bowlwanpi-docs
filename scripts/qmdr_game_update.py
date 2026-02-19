#!/usr/bin/env python3
"""
QMDR 游戏进度自动更新
分析会话内容和系统活动，自动记录游戏任务
"""

import json
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")

def load_game_system():
    """加载游戏系统模块"""
    sys.path.insert(0, "/root/.openclaw/workspace-tasks/skills/daily-creative-brief/scripts")
    try:
        import progression_system as ps
        return ps.ProgressionSystem()
    except Exception as e:
        print(f"⚠️ 游戏系统加载失败: {e}")
        return None

def analyze_activity():
    """分析今日活动量"""
    activities = []
    
    # 1. QMDR 索引更新 (必定执行)
    activities.append({
        "type": "auto",
        "difficulty": "普通",
        "desc": "QMDR索引更新",
        "xp": 20
    })
    
    return activities

def update_game_progress():
    """更新游戏进度"""
    system = load_game_system()
    if not system:
        return {"success": False, "error": "游戏系统不可用"}
    
    activities = analyze_activity()
    results = []
    total_xp = 0
    
    for activity in activities:
        try:
            result = system.record_task(
                description=activity["desc"],
                task_type=activity["type"],
                difficulty=activity["difficulty"]
            )
            results.append({
                "activity": activity["desc"],
                "xp": result.get("xp_gained", activity["xp"]),
                "type": activity["type"]
            })
            total_xp += result.get("xp_gained", activity["xp"])
        except Exception as e:
            print(f"⚠️ 记录任务失败: {e}")
    
    # 获取最新状态
    status = system.status()
    
    return {
        "success": True,
        "activities": len(results),
        "total_xp": total_xp,
        "level": status.get("level", 1),
        "exp": status.get("exp_current", 0),
        "streak": status.get("current_streak", 0),
        "details": results
    }

def main():
    print("🎮 QMDR 游戏进度更新")
    print("=" * 40)
    
    result = update_game_progress()
    
    if result["success"]:
        print(f"✅ 记录 {result['activities']} 个活动")
        print(f"💰 获得 XP: {result['total_xp']}")
        print(f"📊 Lv.{result['level']} ({result['exp']} XP)")
        print(f"🔥 连击: {result['streak']} 天")
        print("\n活动详情:")
        for d in result["details"]:
            print(f"  • {d['activity']}: +{d['xp']} XP")
    else:
        print(f"❌ {result.get('error', '更新失败')}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
