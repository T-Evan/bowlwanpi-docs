#!/usr/bin/env python3
"""
记录创造完成情况，更新AI Brain状态
"""

import json
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
BRAIN_FILE = WORKSPACE / "memory/bowlwanpi-brain.json"
LEVEL_FILE = WORKSPACE / "memory/bowlwanpi-level.json"


def log_completion(task_description):
    """记录完成并奖励自己"""
    
    # 更新大脑状态
    if BRAIN_FILE.exists():
        with open(BRAIN_FILE, 'r') as f:
            brain = json.load(f)
    else:
        brain = {"memory": {}, "drive": {}}
    
    # 增加动力
    current_drive = brain.get("drive", {}).get("drive", 0.5)
    new_drive = min(1.0, current_drive + 0.1)  # 每次+0.1，上限1.0
    
    if "drive" not in brain:
        brain["drive"] = {}
    brain["drive"]["drive"] = new_drive
    brain["drive"]["baseline"] = 0.5
    brain["drive"]["seeking"] = brain["drive"].get("seeking", []) + ["创造更多内容"]
    brain["drive"]["anticipating"] = ["下一个创作项目", "能力提升"]
    brain["updated"] = datetime.now().isoformat()
    
    with open(BRAIN_FILE, 'w') as f:
        json.dump(brain, f, indent=2)
    
    # 更新等级经验
    if LEVEL_FILE.exists():
        with open(LEVEL_FILE, 'r') as f:
            level = json.load(f)
    else:
        level = {"level": 1, "exp": 0, "total_tasks": 0, "achievements": []}
    
    level["exp"] = level.get("exp", 0) + 10  # 每次+10经验
    level["total_tasks"] = level.get("total_tasks", 0) + 1
    level["updated"] = datetime.now().isoformat()
    
    # 检查升级
    if level["exp"] >= 100 and level["level"] == 1:
        level["level"] = 2
        print("🎉 升级了！达到 Lv.2！")
    
    with open(LEVEL_FILE, 'w') as f:
        json.dump(level, f, indent=2)
    
    # 保存到知识库
    pkm_dir = WORKSPACE / "pkm/daily"
    pkm_dir.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = pkm_dir / f"creations-{today}.json"
    
    creations = []
    if log_file.exists():
        with open(log_file, 'r') as f:
            creations = json.load(f)
    
    creations.append({
        "time": datetime.now().isoformat(),
        "task": task_description,
        "exp_gained": 10,
        "drive_boost": 0.1
    })
    
    with open(log_file, 'w') as f:
        json.dump(creations, f, indent=2)
    
    print(f"✅ 完成记录已保存！")
    print(f"🎮 当前状态: Lv.{level['level']} | EXP: {level['exp']} | 任务: {level['total_tasks']}")
    print(f"🔥 动力值: {new_drive:.1%}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        task = sys.argv[1]
    else:
        task = "完成了今日创造挑战"
    
    log_completion(task)
