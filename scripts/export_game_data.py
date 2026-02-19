#!/usr/bin/env python3
"""Export live progression data for website consumption."""

from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
SCRIPTS_DIR = WORKSPACE / "skills/daily-creative-brief/scripts"
OUT_FILE = WORKSPACE / "docs/data/game-system.json"


def main() -> int:
    sys.path.insert(0, str(SCRIPTS_DIR))
    import progression_system as ps  # pylint: disable=import-error

    system = ps.ProgressionSystem()
    state = system.status()

    quest = state.get("quest_board", {})
    payload = {
        "updated": state.get("updated"),
        "level": state.get("level", 1),
        "title": state.get("title", "见习小埋"),
        "xp_current": state.get("exp_current", 0),
        "xp_to_next": state.get("xp_to_next", 100),
        "season_tier": state.get("season_tier", 1),
        "season_tokens": state.get("season_tokens", 0),
        "bond": state.get("bond", 0),
        "streak": state.get("current_streak", 0),
        "achievements": len(state.get("achievements", [])),
        "daily_done": len(state.get("quests", {}).get("daily", {}).get("completed", [])),
        "weekly_done": len(state.get("quests", {}).get("weekly", {}).get("completed", [])),
        "season_done": len(state.get("quests", {}).get("season", {}).get("completed", [])),
        "daily_total": len(quest.get("daily", [])) or 3,
        "weekly_total": len(quest.get("weekly", [])) or 3,
        "season_total": len(quest.get("season", [])) or 3,
        "shop_theme": state.get("shop_theme", ""),
        "talent_points": max(0, state.get("season_tier", 1) - 1 - state.get("spent_talent_points", 0)),
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported: {OUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
