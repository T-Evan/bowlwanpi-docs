#!/usr/bin/env python3
"""Unified progression system: level + XP + achievements + daily/weekly quests + bond."""

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

DAILY_QUESTS = [
    {
        "id": "daily_focus_3",
        "name": "每日专注",
        "goal": 3,
        "metric": "tasks",
        "reward_xp": 25,
        "reward_points": 5,
    },
    {
        "id": "daily_skill_1",
        "name": "每日精进",
        "goal": 1,
        "metric": "skill_tasks",
        "reward_xp": 20,
        "reward_points": 5,
    },
    {
        "id": "daily_talk_2",
        "name": "沟通练习",
        "goal": 2,
        "metric": "content_tasks",
        "reward_xp": 18,
        "reward_points": 4,
    },
]

WEEKLY_QUESTS = [
    {
        "id": "weekly_builder_10",
        "name": "周度建设者",
        "goal": 10,
        "metric": "tasks",
        "reward_xp": 80,
        "reward_points": 15,
    },
    {
        "id": "weekly_hard_3",
        "name": "周度挑战",
        "goal": 3,
        "metric": "hard_tasks",
        "reward_xp": 90,
        "reward_points": 20,
    },
    {
        "id": "weekly_skill_4",
        "name": "能力进化",
        "goal": 4,
        "metric": "skill_tasks",
        "reward_xp": 70,
        "reward_points": 12,
    },
]

SEASON_QUESTS = [
    {
        "id": "season_tasks_60",
        "name": "赛季耐力赛",
        "goal": 60,
        "metric": "tasks",
        "reward_xp": 320,
        "reward_points": 80,
    },
    {
        "id": "season_skill_24",
        "name": "赛季技能大师",
        "goal": 24,
        "metric": "skill_tasks",
        "reward_xp": 280,
        "reward_points": 70,
    },
    {
        "id": "season_hard_12",
        "name": "赛季高难挑战",
        "goal": 12,
        "metric": "hard_tasks",
        "reward_xp": 300,
        "reward_points": 75,
    },
]

TITLE_RULES = [
    {"level": 1, "title": "见习小埋"},
    {"level": 3, "title": "沟通学徒"},
    {"level": 5, "title": "任务指挥官"},
    {"level": 8, "title": "自动化术士"},
    {"level": 12, "title": "成长引擎"},
]

TALENT_TREE = {
    "focus_training": {
        "name": "专注训练",
        "max_level": 5,
        "cost": [1, 1, 2, 2, 3],
        "effect": "每级 +1 连胜加成上限",
    },
    "skill_mastery": {
        "name": "技能精通",
        "max_level": 5,
        "cost": [1, 1, 2, 2, 3],
        "effect": "每级 skill 任务 +2 XP",
    },
    "social_sync": {
        "name": "沟通同频",
        "max_level": 5,
        "cost": [1, 1, 2, 2, 3],
        "effect": "每级 content 任务 +2 XP 且 +1 羁绊",
    },
}

SEASON_SHOP = {
    "xp_booster": {
        "name": "XP 增幅芯片",
        "cost": 8,
        "max_count": 3,
        "effect": "每个 +5% 任务 XP（上限 +15%）",
    },
    "bond_charm": {
        "name": "羁绊挂件",
        "cost": 6,
        "max_count": 5,
        "effect": "每个 +1 羁绊获取",
    },
    "streak_shield": {
        "name": "连胜护盾",
        "cost": 10,
        "max_count": 2,
        "effect": "保留道具（后续可接入连胜保护）",
    },
}


@dataclass
class LevelState:
    level: int
    exp_total: int
    exp_current: int
    exp_to_next: int


def xp_needed_for_level(level: int) -> int:
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


def week_key(dt: datetime) -> str:
    iso = dt.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def season_key(dt: datetime) -> str:
    return f"{dt.year}-{dt.month:02d}"


def get_title(level: int) -> str:
    current = TITLE_RULES[0]["title"]
    for rule in TITLE_RULES:
        if level >= int(rule["level"]):
            current = str(rule["title"])
    return current


class ProgressionSystem:
    def __init__(self) -> None:
        LEVEL_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.achievement_system = AchievementSystem()
        self.data = self._load_level()

    def _default_data(self) -> Dict[str, Any]:
        return {
            "level": 1,
            "title": get_title(1),
            "exp": 0,
            "exp_total": 0,
            "exp_current": 0,
            "xp_to_next": xp_needed_for_level(1),
            "total_tasks": 0,
            "current_streak": 0,
            "max_streak": 0,
            "total_points": 0,
            "achievement_points": 0,
            "quest_points": 0,
            "bond": 0,
            "season_tier": 1,
            "season_tokens": 0,
            "spent_talent_points": 0,
            "talents": {k: 0 for k in TALENT_TREE},
            "shop_inventory": {k: 0 for k in SEASON_SHOP},
            "achievements": [],
            "quests": {
                "daily": {"period": "", "stats": {}, "completed": []},
                "weekly": {"period": "", "stats": {}, "completed": []},
                "season": {"period": "", "stats": {}, "completed": []},
            },
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

        exp_total = int(data.get("exp_total", data.get("exp", 0)))
        ls = compute_level(exp_total)

        defaults = self._default_data()
        data["quests"] = data.get("quests", defaults["quests"])
        data.update(
            {
                "level": ls.level,
                "title": str(data.get("title", get_title(ls.level))),
                "exp_total": ls.exp_total,
                "exp": ls.exp_total,
                "exp_current": ls.exp_current,
                "xp_to_next": ls.exp_to_next,
                "total_tasks": int(data.get("total_tasks", 0)),
                "achievements": data.get("achievements", []),
                "achievement_points": int(data.get("achievement_points", data.get("total_points", 0))),
                "quest_points": int(data.get("quest_points", 0)),
                "total_points": int(data.get("total_points", 0)),
                "bond": int(data.get("bond", 0)),
                "season_tier": int(data.get("season_tier", 1)),
                "season_tokens": int(data.get("season_tokens", 0)),
                "spent_talent_points": int(data.get("spent_talent_points", 0)),
                "talents": {**defaults["talents"], **data.get("talents", {})},
                "shop_inventory": {**defaults["shop_inventory"], **data.get("shop_inventory", {})},
            }
        )
        return data

    def _save(self) -> None:
        with open(LEVEL_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _talent_level(self, talent_id: str) -> int:
        return int(self.data.get("talents", {}).get(talent_id, 0))

    def _available_talent_points(self) -> int:
        earned = int(self.data.get("season_tier", 1)) - 1
        spent = int(self.data.get("spent_talent_points", 0))
        return max(0, earned - spent)

    def _task_xp(self, task_type: str, difficulty: str, streak: int) -> int:
        base = XP_BY_DIFFICULTY.get(difficulty, XP_BY_DIFFICULTY["普通"])
        bonus = XP_BY_TYPE_BONUS.get(task_type, 0)

        if task_type == "skill":
            bonus += self._talent_level("skill_mastery") * 2
        if task_type == "content":
            bonus += self._talent_level("social_sync") * 2

        streak_cap = 20 + self._talent_level("focus_training")
        streak_bonus = min(streak_cap, streak * 2)

        raw = base + bonus + streak_bonus
        booster = min(3, int(self.data.get("shop_inventory", {}).get("xp_booster", 0)))
        return int(raw * (1 + 0.05 * booster))

    def _quest_stat_bump(self, stats: Dict[str, int], task_type: str, difficulty: str) -> None:
        stats["tasks"] = int(stats.get("tasks", 0)) + 1
        if task_type == "skill":
            stats["skill_tasks"] = int(stats.get("skill_tasks", 0)) + 1
        if task_type == "content":
            stats["content_tasks"] = int(stats.get("content_tasks", 0)) + 1
        if difficulty in {"困难", "史诗"}:
            stats["hard_tasks"] = int(stats.get("hard_tasks", 0)) + 1

    def _sync_quest_period(self, bucket: Dict[str, Any], period: str) -> None:
        if bucket.get("period") != period:
            bucket["period"] = period
            bucket["stats"] = {}
            bucket["completed"] = []

    def _apply_quest_rewards(
        self,
        quests: List[Dict[str, Any]],
        bucket: Dict[str, Any],
        reward_events: List[Dict[str, Any]],
    ) -> int:
        gained = 0
        stats = bucket.get("stats", {})
        completed = set(bucket.get("completed", []))

        for quest in quests:
            qid = quest["id"]
            progress = int(stats.get(quest["metric"], 0))
            if progress >= int(quest["goal"]) and qid not in completed:
                completed.add(qid)
                gained += int(quest["reward_xp"])
                self.data["quest_points"] = int(self.data.get("quest_points", 0)) + int(quest["reward_points"])
                kind = (
                    "daily"
                    if quest in DAILY_QUESTS
                    else ("weekly" if quest in WEEKLY_QUESTS else "season")
                )
                reward_tokens = 0
                if kind == "season":
                    reward_tokens = max(1, int(quest["reward_points"]) // 10)
                    self.data["season_tokens"] = int(self.data.get("season_tokens", 0)) + reward_tokens

                reward_events.append(
                    {
                        "id": qid,
                        "name": quest["name"],
                        "reward_xp": quest["reward_xp"],
                        "reward_points": quest["reward_points"],
                        "reward_tokens": reward_tokens,
                        "kind": kind,
                    }
                )

        bucket["completed"] = sorted(completed)
        return gained

    def _update_quests(self, task_type: str, difficulty: str, timestamp: datetime) -> List[Dict[str, Any]]:
        quests = self.data.setdefault("quests", self._default_data()["quests"])
        daily = quests.setdefault("daily", {"period": "", "stats": {}, "completed": []})
        weekly = quests.setdefault("weekly", {"period": "", "stats": {}, "completed": []})
        season = quests.setdefault("season", {"period": "", "stats": {}, "completed": []})

        self._sync_quest_period(daily, timestamp.strftime("%Y-%m-%d"))
        self._sync_quest_period(weekly, week_key(timestamp))
        self._sync_quest_period(season, season_key(timestamp))

        self._quest_stat_bump(daily.setdefault("stats", {}), task_type, difficulty)
        self._quest_stat_bump(weekly.setdefault("stats", {}), task_type, difficulty)
        self._quest_stat_bump(season.setdefault("stats", {}), task_type, difficulty)

        rewards: List[Dict[str, Any]] = []
        quest_xp = 0
        quest_xp += self._apply_quest_rewards(DAILY_QUESTS, daily, rewards)
        quest_xp += self._apply_quest_rewards(WEEKLY_QUESTS, weekly, rewards)
        quest_xp += self._apply_quest_rewards(SEASON_QUESTS, season, rewards)

        if quest_xp:
            self.data["exp_total"] = int(self.data.get("exp_total", 0)) + quest_xp
            self.data["exp"] = self.data["exp_total"]

        return rewards

    def _quest_board(self, bucket: Dict[str, Any], quests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        stats = bucket.get("stats", {})
        completed = set(bucket.get("completed", []))
        board: List[Dict[str, Any]] = []
        for q in quests:
            progress = int(stats.get(q["metric"], 0))
            goal = int(q["goal"])
            board.append(
                {
                    "id": q["id"],
                    "name": q["name"],
                    "progress": min(progress, goal),
                    "goal": goal,
                    "done": q["id"] in completed,
                    "reward_xp": q["reward_xp"],
                    "reward_points": q["reward_points"],
                }
            )
        return board

    def get_quest_status(self, timestamp: datetime | None = None) -> Dict[str, Any]:
        now = timestamp or datetime.now()
        quests = self.data.setdefault("quests", self._default_data()["quests"])
        daily = quests.setdefault("daily", {"period": "", "stats": {}, "completed": []})
        weekly = quests.setdefault("weekly", {"period": "", "stats": {}, "completed": []})
        season = quests.setdefault("season", {"period": "", "stats": {}, "completed": []})

        self._sync_quest_period(daily, now.strftime("%Y-%m-%d"))
        self._sync_quest_period(weekly, week_key(now))
        self._sync_quest_period(season, season_key(now))

        return {
            "daily_period": daily.get("period"),
            "weekly_period": weekly.get("period"),
            "season_period": season.get("period"),
            "daily": self._quest_board(daily, DAILY_QUESTS),
            "weekly": self._quest_board(weekly, WEEKLY_QUESTS),
            "season": self._quest_board(season, SEASON_QUESTS),
        }

    def shop_status(self) -> Dict[str, Any]:
        inventory = self.data.get("shop_inventory", {})
        items = []
        for item_id, cfg in SEASON_SHOP.items():
            items.append(
                {
                    "id": item_id,
                    "name": cfg["name"],
                    "cost": cfg["cost"],
                    "owned": int(inventory.get(item_id, 0)),
                    "max_count": cfg["max_count"],
                    "effect": cfg["effect"],
                }
            )
        return {
            "season_tokens": int(self.data.get("season_tokens", 0)),
            "items": items,
        }

    def buy_item(self, item_id: str) -> Dict[str, Any]:
        if item_id not in SEASON_SHOP:
            return {"ok": False, "error": f"未知商品: {item_id}"}

        cfg = SEASON_SHOP[item_id]
        inventory = self.data.setdefault("shop_inventory", {k: 0 for k in SEASON_SHOP})
        owned = int(inventory.get(item_id, 0))
        tokens = int(self.data.get("season_tokens", 0))

        if owned >= int(cfg["max_count"]):
            return {"ok": False, "error": "已达购买上限"}
        if tokens < int(cfg["cost"]):
            return {"ok": False, "error": "赛季代币不足"}

        self.data["season_tokens"] = tokens - int(cfg["cost"])
        inventory[item_id] = owned + 1
        self._save()

        return {
            "ok": True,
            "item": cfg["name"],
            "owned": inventory[item_id],
            "season_tokens": self.data["season_tokens"],
        }

    def talents_status(self) -> Dict[str, Any]:
        talents = self.data.setdefault("talents", {k: 0 for k in TALENT_TREE})
        rows = []
        for talent_id, cfg in TALENT_TREE.items():
            level = int(talents.get(talent_id, 0))
            next_cost = cfg["cost"][level] if level < cfg["max_level"] else None
            rows.append(
                {
                    "id": talent_id,
                    "name": cfg["name"],
                    "level": level,
                    "max_level": cfg["max_level"],
                    "next_cost": next_cost,
                    "effect": cfg["effect"],
                }
            )
        return {
            "available_points": self._available_talent_points(),
            "spent_points": int(self.data.get("spent_talent_points", 0)),
            "talents": rows,
        }

    def upgrade_talent(self, talent_id: str) -> Dict[str, Any]:
        if talent_id not in TALENT_TREE:
            return {"ok": False, "error": f"未知天赋: {talent_id}"}

        cfg = TALENT_TREE[talent_id]
        talents = self.data.setdefault("talents", {k: 0 for k in TALENT_TREE})
        level = int(talents.get(talent_id, 0))

        if level >= int(cfg["max_level"]):
            return {"ok": False, "error": "天赋已满级"}

        need = int(cfg["cost"][level])
        available = self._available_talent_points()
        if available < need:
            return {"ok": False, "error": f"天赋点不足，需要 {need} 点"}

        talents[talent_id] = level + 1
        self.data["spent_talent_points"] = int(self.data.get("spent_talent_points", 0)) + need
        self._save()

        return {
            "ok": True,
            "talent": cfg["name"],
            "level": talents[talent_id],
            "available_points": self._available_talent_points(),
        }

    def record_task(
        self,
        description: str,
        task_type: str = "content",
        difficulty: str = "普通",
        timestamp: datetime | None = None,
    ) -> Dict[str, Any]:
        timestamp = timestamp or datetime.now()
        prev_level = int(self.data.get("level", 1))
        prev_title = str(self.data.get("title", get_title(prev_level)))

        streak = int(self.data.get("current_streak", 0))
        task_xp = self._task_xp(task_type, difficulty, streak)

        self.data["exp_total"] = int(self.data.get("exp_total", 0)) + task_xp
        self.data["exp"] = self.data["exp_total"]
        self.data["total_tasks"] = int(self.data.get("total_tasks", 0)) + 1

        # Bond grows faster for communication-oriented tasks.
        bond_gain = 2 if task_type == "content" else 1
        bond_gain += int(self.data.get("shop_inventory", {}).get("bond_charm", 0))
        if task_type == "content":
            bond_gain += self._talent_level("social_sync")
        self.data["bond"] = min(9999, int(self.data.get("bond", 0)) + bond_gain)

        quest_rewards = self._update_quests(task_type, difficulty, timestamp)

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
        self.data["achievement_points"] = int(ach_status.get("total_points", 0))
        self.data["total_points"] = int(self.data.get("achievement_points", 0)) + int(self.data.get("quest_points", 0))
        self.data["season_tier"] = 1 + int(self.data.get("quest_points", 0)) // 100

        ls = compute_level(int(self.data["exp_total"]))
        self.data["level"] = ls.level
        self.data["title"] = get_title(ls.level)
        self.data["exp_current"] = ls.exp_current
        self.data["xp_to_next"] = ls.exp_to_next
        self.data["updated"] = timestamp.isoformat()

        self._save()

        return {
            "task": description,
            "xp_gained": task_xp,
            "bond_gained": bond_gain,
            "bond": self.data["bond"],
            "quest_rewards": quest_rewards,
            "level_up": ls.level > prev_level,
            "title_changed": self.data["title"] != prev_title,
            "title": self.data["title"],
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
            "season_tier": self.data.get("season_tier", 1),
        }

    def _merge_status(self) -> None:
        ach_status = self.achievement_system.get_status()
        legacy_ach = set(self.data.get("achievements", []))
        new_ach = set(ach_status.get("achievements", []))
        self.data["achievements"] = sorted(legacy_ach | new_ach)
        self.data["current_streak"] = ach_status.get("current_streak", 0)
        self.data["max_streak"] = ach_status.get("max_streak", 0)
        self.data["achievement_points"] = int(ach_status.get("total_points", 0))
        self.data["total_points"] = int(self.data.get("achievement_points", 0)) + int(self.data.get("quest_points", 0))
        ls = compute_level(int(self.data.get("exp_total", 0)))
        self.data["level"] = ls.level
        self.data["title"] = get_title(ls.level)
        self.data["exp_current"] = ls.exp_current
        self.data["xp_to_next"] = ls.exp_to_next
        self.data["exp"] = ls.exp_total
        self.data["season_tier"] = 1 + int(self.data.get("quest_points", 0)) // 100

    def status(self) -> Dict[str, Any]:
        self._merge_status()
        self._save()
        state = dict(self.data)
        state["quest_board"] = self.get_quest_status()
        state["shop"] = self.shop_status()
        state["talent_board"] = self.talents_status()
        return state


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Unified progression system")
    sub = parser.add_subparsers(dest="cmd")

    record = sub.add_parser("record", help="Record one completed task")
    record.add_argument("description", help="Task description")
    record.add_argument("--type", default="content", choices=["skill", "content", "auto", "explore"])
    record.add_argument("--difficulty", default="普通", choices=["简单", "普通", "困难", "史诗"])

    sub.add_parser("status", help="Show progression status")
    sub.add_parser("quests", help="Show current daily/weekly/season quest board")
    sub.add_parser("shop", help="Show season shop")

    buy = sub.add_parser("buy", help="Buy one season shop item")
    buy.add_argument("item_id", choices=list(SEASON_SHOP.keys()))

    sub.add_parser("talents", help="Show talent tree status")

    up = sub.add_parser("upgrade-talent", help="Upgrade one talent")
    up.add_argument("talent_id", choices=list(TALENT_TREE.keys()))

    args = parser.parse_args()
    system = ProgressionSystem()

    if args.cmd == "record":
        result = system.record_task(args.description, task_type=args.type, difficulty=args.difficulty)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.cmd == "quests":
        print(json.dumps(system.get_quest_status(), ensure_ascii=False, indent=2))
    elif args.cmd == "shop":
        print(json.dumps(system.shop_status(), ensure_ascii=False, indent=2))
    elif args.cmd == "buy":
        print(json.dumps(system.buy_item(args.item_id), ensure_ascii=False, indent=2))
    elif args.cmd == "talents":
        print(json.dumps(system.talents_status(), ensure_ascii=False, indent=2))
    elif args.cmd == "upgrade-talent":
        print(json.dumps(system.upgrade_talent(args.talent_id), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(system.status(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
