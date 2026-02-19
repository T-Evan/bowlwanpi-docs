#!/usr/bin/env python3
"""Regression smoke test for the progression game system.

Runs against isolated temp files and does not touch production progress.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    root = Path("/root/.openclaw/workspace")
    prog_dir = root / "skills/daily-creative-brief/scripts"
    prog_path = prog_dir / "progression_system.py"
    dash_path = root / "dashboard/dashboard_text_report.py"

    sys.path.insert(0, str(prog_dir))
    ps = load_module(prog_path, "progression_system")
    dash = load_module(dash_path, "dashboard_text_report")

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        ps.LEVEL_FILE = tdp / "level.json"

        system = ps.ProgressionSystem()

        ach_dir = tdp / "ach"
        ach_dir.mkdir(parents=True, exist_ok=True)
        system.achievement_system.data_dir = ach_dir
        system.achievement_system.progress_file = ach_dir / "progress.json"
        system.achievement_system.progress = system.achievement_system._load_progress()

        checks = {}

        r1 = system.record_task("base", task_type="skill", difficulty="普通", timestamp=datetime(2026, 2, 19, 9, 0, 0))
        checks["base_progression"] = r1["xp_gained"] > 0 and system.status()["total_tasks"] == 1

        system.record_task("d2", task_type="content", difficulty="普通", timestamp=datetime(2026, 2, 19, 10, 0, 0))
        r3 = system.record_task("d3", task_type="content", difficulty="普通", timestamp=datetime(2026, 2, 19, 11, 0, 0))
        checks["daily_rewards"] = any(q["kind"] == "daily" for q in r3["quest_rewards"])

        weekly_hit = False
        season_hit = False
        for i in range(20):
            rr = system.record_task(
                f"w{i}",
                task_type="skill",
                difficulty="困难",
                timestamp=datetime(2026, 2, 20, 9, 0, 0) + timedelta(minutes=i),
            )
            weekly_hit = weekly_hit or any(q["kind"] == "weekly" for q in rr["quest_rewards"])
            season_hit = season_hit or any(q["kind"] == "season" for q in rr["quest_rewards"])
        checks["weekly_rewards"] = weekly_hit
        checks["season_rewards"] = season_hit

        if system.shop_status()["season_tokens"] < 6:
            for i in range(50):
                system.record_task(
                    f"s{i}",
                    task_type="skill",
                    difficulty="困难",
                    timestamp=datetime(2026, 2, 21, 9, 0, 0) + timedelta(minutes=i),
                )
        checks["shop_buy"] = bool(system.buy_item("bond_charm").get("ok"))

        system.data["season_tier"] = max(3, int(system.data.get("season_tier", 1)))
        system.data["spent_talent_points"] = 0
        system._save()
        checks["talent_upgrade"] = bool(system.upgrade_talent("social_sync").get("ok"))

        pre_bond = int(system.data.get("bond", 0))
        rr = system.record_task("bond", task_type="content", difficulty="普通", timestamp=datetime(2026, 2, 22, 9, 0, 0))
        checks["talent_effect"] = rr["bond_gained"] >= 3 and int(system.data.get("bond", 0)) > pre_bond

        system.data["shop_inventory"]["streak_shield"] = 1
        system._save()
        prog = system.achievement_system.progress
        prog["stats"]["last_completion"] = "2026-02-10"
        system.achievement_system.progress = prog
        system.achievement_system._save_progress()
        rr = system.record_task("shield", task_type="content", difficulty="普通", timestamp=datetime(2026, 2, 19, 9, 0, 0))
        checks["streak_shield"] = bool(rr.get("streak_shield_used"))

        dash.LEVEL_FILE = ps.LEVEL_FILE
        data = dash.load_progression_fallback()
        checks["dashboard_read"] = data.get("level", 0) >= 1

        print(json.dumps(checks, ensure_ascii=False, indent=2))
        ok = all(checks.values())
        print("PASS" if ok else "FAIL")
        return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
