#!/usr/bin/env python3
"""Record one completed creation task and sync progression state."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from progression_system import ProgressionSystem

WORKSPACE = Path("/root/.openclaw/workspace")
BRAIN_FILE = WORKSPACE / "memory/bowlwanpi-brain.json"


def update_brain_drive(task_description: str) -> float:
    """Update drive state after completing a task."""
    if BRAIN_FILE.exists():
        with open(BRAIN_FILE, "r", encoding="utf-8") as f:
            brain = json.load(f)
    else:
        brain = {"memory": {}, "drive": {}}

    current_drive = brain.get("drive", {}).get("drive", 0.5)
    new_drive = min(1.0, current_drive + 0.08)

    brain.setdefault("drive", {})
    brain["drive"]["drive"] = new_drive
    brain["drive"]["baseline"] = 0.5
    brain["drive"]["seeking"] = brain["drive"].get("seeking", []) + [task_description]
    brain["drive"]["anticipating"] = ["下一个创作项目", "能力提升"]
    brain["updated"] = datetime.now().isoformat()

    with open(BRAIN_FILE, "w", encoding="utf-8") as f:
        json.dump(brain, f, ensure_ascii=False, indent=2)

    return new_drive


def append_daily_log(task_description: str, xp_gained: int, task_type: str, difficulty: str) -> None:
    pkm_dir = WORKSPACE / "pkm/daily"
    pkm_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = pkm_dir / f"creations-{today}.json"

    creations = []
    if log_file.exists():
        with open(log_file, "r", encoding="utf-8") as f:
            creations = json.load(f)

    creations.append(
        {
            "time": datetime.now().isoformat(),
            "task": task_description,
            "type": task_type,
            "difficulty": difficulty,
            "exp_gained": xp_gained,
        }
    )

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(creations, f, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Record completion and reward progression")
    parser.add_argument("task", nargs="?", default="完成了今日创造挑战", help="Task description")
    parser.add_argument("--type", default="content", choices=["skill", "content", "auto", "explore"])
    parser.add_argument("--difficulty", default="普通", choices=["简单", "普通", "困难", "史诗"])
    args = parser.parse_args()

    system = ProgressionSystem()
    result = system.record_task(args.task, task_type=args.type, difficulty=args.difficulty)
    drive = update_brain_drive(args.task)
    append_daily_log(args.task, result["xp_gained"], args.type, args.difficulty)

    print("✅ 完成记录已保存！")
    if result["level_up"]:
        print(f"🎉 升级！达到 Lv.{result['level']}！")

    if result["new_achievements"]:
        print("🏆 新成就解锁：")
        for ach in result["new_achievements"]:
            print(f"  {ach['icon']} {ach['name']} (+{ach['points']}点)")

    print(
        f"🎮 当前状态: Lv.{result['level']} | XP: {result['exp_current']}/{result['xp_to_next']} | 连胜: {result['streak']}天"
    )
    print(f"🔥 动力值: {drive:.1%}")


if __name__ == "__main__":
    main()
