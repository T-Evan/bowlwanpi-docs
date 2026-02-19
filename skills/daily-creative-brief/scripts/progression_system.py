#!/usr/bin/env python3
"""Unified progression system: level + XP + achievements."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from achievements_v2 import AchievementSystem, Achievement

WORKSPACE = Path("/root/.openclaw/workspace")
LEVEL_FILE = WORKSPACE / "memory/bowlwanpi-level.json"

XP_BY_DIFFICULTY = {
    "简单": 10,
    "普通": 20,
    "困难": 35,
    "史诗": 60,
}

XP_BY_TYPE_BONUS = {
    "skill": 8,
    "auto": 6,
    "content": 4,
    "explore": 3,
}


@dataclass
class LevelState:
    level: int
    exp_total: int
    exp_current: int
    exp_to_next: int


def xp_needed_for_level(level: int) -> int:
    """XP required to advance from `level` to `level+1`."""
    return 100 + (level - 1) * 50


def compute_level(exp_total: int) -> LevelState:
    level = 1
    remain = max(0, exp_total)

    while remain >= xp_needed_for_level(level):
        remain -= xp_needed_for_level(level)
        level += 1

    return LevelState(
        level=level,
        exp_total=exp_total,
        exp_current=remain,
        exp_to_next=xp_needed_for_level(level),
    )


class ProgressionSystem:
    def __init__(self) -> None:
        LEVEL_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.achievement_system = AchievementSystem()
        self.data = self._load_level()

    def _default_data(self) -> Dict[str, Any]:
        return {
            "level": 1,
            "exp": 0,
            "exp_total": 0,
            "exp_current": 0,
            "xp_to_next": xp_needed_for_level(1),
            "total_tasks": 0,
            "current_streak": 0,
            "max_streak": 0,
            "total_points": 0,
            "achievements": [],
            "updated": datetime.now().isoformat(),
        }

    def _load_level(self) -> Dict[str, Any]:
        if not LEVEL_FILE.exists():
            return self._default_data()
        try:
            with open(LEVEL_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            data = self._default_data()

        # Backward compatibility: old file may only have exp.
        exp_total = int(data.get("exp_total", data.get("exp", 0)))
        ls = compute_level(exp_total)
        data.update(
            {
                "level": ls.level,
                "exp_total": ls.exp_total,
                "exp": ls.exp_total,
                "exp_current": ls.exp_current,
                "xp_to_next": ls.exp_to_next,
                "total_tasks": int(data.get("total_tasks", 0)),
                "achievements": data.get("achievements", []),
            }
        )
        return data

    def _save(self) -> None:
        with open(LEVEL_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _task_xp(self, task_type: str, difficulty: str) -> int:
        base = XP_BY_DIFFICULTY.get(difficulty, XP_BY_DIFFICULTY["普通"])
        bonus = XP_BY_TYPE_BONUS.get(task_type, 0)
        return base + bonus

    def record_task(
        self,
        description: str,
        task_type: str = "content",
        difficulty: str = "普通",
        timestamp: datetime | None = None,
    ) -> Dict[str, Any]:
        timestamp = timestamp or datetime.now()
        gained_xp = self._task_xp(task_type, difficulty)

        prev_level = int(self.data.get("level", 1))
        self.data["exp_total"] = int(self.data.get("exp_total", 0)) + gained_xp
        self.data["exp"] = self.data["exp_total"]
        self.data["total_tasks"] = int(self.data.get("total_tasks", 0)) + 1

        # Sync achievements first (streak/points/unlocks)
        new_achievements: List[Achievement] = self.achievement_system.record_completion(
            task_type=task_type,
            difficulty=difficulty,
            timestamp=timestamp,
        )
        ach_status = self.achievement_system.get_status()

        legacy_ach = set(self.data.get("achievements", []))
        new_ach = set(ach_status.get("achievements", []))
        self.data["achievements"] = sorted(legacy_ach | new_ach)
        self.data["current_streak"] = ach_status.get("current_streak", 0)
        self.data["max_streak"] = ach_status.get("max_streak", 0)
        self.data["total_points"] = ach_status.get("total_points", 0)

        # Recompute level progress.
        ls = compute_level(int(self.data["exp_total"]))
        self.data["level"] = ls.level
        self.data["exp_current"] = ls.exp_current
        self.data["xp_to_next"] = ls.exp_to_next
        self.data["updated"] = timestamp.isoformat()

        self._save()

        return {
            "task": description,
            "xp_gained": gained_xp,
            "level_up": ls.level > prev_level,
            "level": ls.level,
            "exp_current": ls.exp_current,
            "xp_to_next": ls.exp_to_next,
            "new_achievements": [
                {
                    "id": a.id,
                    "name": a.name,
                    "icon": a.icon,
                    "points": a.points,
                }
                for a in new_achievements
            ],
            "streak": ach_status.get("current_streak", 0),
        }

    def status(self) -> Dict[str, Any]:
        # Refresh with achievements status to avoid drift.
        ach_status = self.achievement_system.get_status()
        legacy_ach = set(self.data.get("achievements", []))
        new_ach = set(ach_status.get("achievements", []))
        self.data["achievements"] = sorted(legacy_ach | new_ach)
        self.data["current_streak"] = ach_status.get("current_streak", 0)
        self.data["max_streak"] = ach_status.get("max_streak", 0)
        self.data["total_points"] = ach_status.get("total_points", 0)
        ls = compute_level(int(self.data.get("exp_total", 0)))
        self.data["level"] = ls.level
        self.data["exp_current"] = ls.exp_current
        self.data["xp_to_next"] = ls.exp_to_next
        self.data["exp"] = ls.exp_total
        self._save()
        return dict(self.data)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Unified progression system")
    sub = parser.add_subparsers(dest="cmd")

    record = sub.add_parser("record", help="Record one completed task")
    record.add_argument("description", help="Task description")
    record.add_argument("--type", default="content", choices=["skill", "content", "auto", "explore"])
    record.add_argument("--difficulty", default="普通", choices=["简单", "普通", "困难", "史诗"])

    sub.add_parser("status", help="Show progression status")

    args = parser.parse_args()
    system = ProgressionSystem()

    if args.cmd == "record":
        result = system.record_task(args.description, task_type=args.type, difficulty=args.difficulty)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(system.status(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
