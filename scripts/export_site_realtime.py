#!/usr/bin/env python3
"""Export near-realtime site data: game state + live logs."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

WORKSPACE = Path("/root/.openclaw/workspace")
SCRIPTS_DIR = WORKSPACE / "skills/daily-creative-brief/scripts"
DOCS_DATA = WORKSPACE / "docs/data"
GAME_FILE = DOCS_DATA / "game-system.json"
LOG_FILE = DOCS_DATA / "live-logs.json"

LOG_SOURCES: List[Tuple[Path, str]] = [
    (Path("/var/log/bowlwanpi-heartbeat.log"), "heartbeat"),
    (WORKSPACE / "memory/nightly-build.log", "nightly"),
    (WORKSPACE / "memory/ai-news.log", "news"),
]


def export_game() -> None:
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
    GAME_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def classify_level(text: str) -> str:
    t = text.lower()
    if "error" in t or "failed" in t or "异常" in text:
        return "ERROR"
    if "warn" in t or "warning" in t or "⚠" in text:
        return "WARN"
    return "INFO"


def tail_lines(path: Path, n: int = 20) -> List[str]:
    if not path.exists():
        return []
    try:
        out = subprocess.check_output(["tail", "-n", str(n), str(path)], text=True, stderr=subprocess.DEVNULL)
        return [ln for ln in out.splitlines() if ln.strip()]
    except Exception:
        return []


def normalize_log_line(line: str, source: str) -> dict:
    ts = datetime.now().strftime("%H:%M:%S")
    m = re.search(r"\[(\d{4}-\d{2}-\d{2}[^\]]*)\]", line)
    if m:
        raw = m.group(1)
        ts = raw[-8:] if len(raw) >= 8 else raw
    msg = re.sub(r"^\[[^\]]+\]\s*", "", line).strip()
    return {
        "time": ts,
        "level": classify_level(msg),
        "source": source,
        "message": msg[:220],
    }


def export_logs() -> None:
    entries = []
    for path, source in LOG_SOURCES:
        for ln in tail_lines(path, n=15):
            entries.append(normalize_log_line(ln, source))

    entries = entries[-40:]
    payload = {
        "updated": datetime.now().isoformat(),
        "entries": entries,
    }
    LOG_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    export_game()
    export_logs()
    print(f"Exported {GAME_FILE.name} and {LOG_FILE.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
