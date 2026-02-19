#!/usr/bin/env python3
"""Record one completed creation task and sync progression state."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path

from progression_system import ProgressionSystem

WORKSPACE = Path("/root/.openclaw/workspace")
BRAIN_FILE = WORKSPACE / "memory/bowlwanpi-brain.json"
DEFAULT_FEISHU_TARGET = "user:ou_a22ce6536f26dee3fec9397a9a1b87b5"


def send_progression_notification(message: str) -> None:
    """Push progression milestone to Feishu via OpenClaw CLI."""
    if not message.strip():
        return
    try:
        subprocess.run(
            [
                "openclaw",
                "message",
                "send",
                "--channel",
                "feishu",
                "--target",
                DEFAULT_FEISHU_TARGET,
                "--message",
                "-",
            ],
            input=message,
            text=True,
            cwd=str(WORKSPACE),
            check=False,
            timeout=15,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError):
        # Notification failure should never block progression recording.
        pass


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

    if result.get("quest_rewards"):
        print("🎯 任务完成奖励：")
        for quest in result["quest_rewards"]:
            scope = {"daily": "日常", "weekly": "周常", "season": "赛季"}.get(quest.get("kind"), "任务")
            token_text = f", +{quest.get('reward_tokens', 0)}代币" if quest.get('reward_tokens', 0) else ""
            print(f"  ✅ [{scope}] {quest['name']} (+{quest['reward_xp']} XP, +{quest['reward_points']}点{token_text})")

    if result.get("streak_shield_used"):
        print("🛡️ 连胜护盾生效：本次已自动保住连胜")

    print(
        f"🎮 当前状态: Lv.{result['level']} {result['title']} | XP: {result['exp_current']}/{result['xp_to_next']} | 连胜: {result['streak']}天"
    )
    print(f"🛡️ 赛季阶位: T{result.get('season_tier', 1)} | 代币: {result.get('season_tokens', 0)}")
    print(f"🤝 羁绊值: {result['bond']} (+{result['bond_gained']})")
    print(f"🔥 动力值: {drive:.1%}")

    notify_lines = []
    if result["level_up"]:
        notify_lines.append(f"🎉 升级啦！现在是 Lv.{result['level']}！")
    if result.get("title_changed"):
        notify_lines.append(f"👑 新称号：{result['title']}")
    for ach in result.get("new_achievements", []):
        notify_lines.append(f"🏆 解锁成就：{ach['icon']} {ach['name']} (+{ach['points']}点)")
    for quest in result.get("quest_rewards", []):
        notify_lines.append(f"🎯 完成任务：{quest['name']} (+{quest['reward_xp']} XP)")
    if result.get("streak_shield_used"):
        notify_lines.append("🛡️ 连胜护盾生效：已自动保住连胜")

    if notify_lines:
        notify_lines.append(
            f"\n当前进度：Lv.{result['level']} {result['title']} | XP {result['exp_current']}/{result['xp_to_next']} | 连胜 {result['streak']} 天 | 赛季T{result.get('season_tier', 1)} | 羁绊 {result['bond']}"
        )
        send_progression_notification("\n".join(notify_lines))


if __name__ == "__main__":
    main()
