#!/usr/bin/env python3
"""Export diary timeline from memory files and selfies for website."""

from __future__ import annotations

import json
import re
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
SELFIES_FILE = WORKSPACE / "docs/data/selfies.json"
OUT_FILE = WORKSPACE / "docs/data/diary.json"

DATE_RE = re.compile(r"^#\s*(\d{4}-\d{2}-\d{2})")
TIME_LINE_RE = re.compile(r"\*\*(\d{1,2}:\d{2})")

NOISE_PATTERNS = [
    "优先事项",
    "定时任务",
    "微博热搜",
    "知乎热榜",
    "B站热门",
    "github",
    "cron",
    "heartbeat",
    "提醒",
    "咨询",
]

MEANINGFUL_HINTS = [
    "完成",
    "修复",
    "新增",
    "学习",
    "思考",
    "感受",
    "反思",
    "成长",
    "交流",
    "一碗",
    "技能",
    "经验",
    "突破",
]


def load_selfies_by_date() -> dict:
    if not SELFIES_FILE.exists():
        return {}
    try:
        selfies = json.loads(SELFIES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

    by_date = {}
    for s in selfies:
        ts = str(s.get("timestamp", ""))
        date_key = ts[:10] if len(ts) >= 10 else "unknown"
        by_date.setdefault(date_key, []).append(
            {
                "filename": s.get("filename"),
                "title": s.get("title", "自拍"),
                "mood": s.get("mood", ""),
                "timestamp": ts,
            }
        )
    return by_date


def is_noise(line: str) -> bool:
    low = line.lower()
    if line.startswith("- ["):
        return True
    if any(p in low for p in NOISE_PATTERNS):
        return True
    return False


def is_meaningful(line: str) -> bool:
    low = line.lower()
    return any(k in low for k in MEANINGFUL_HINTS)


def extract_events(text: str, max_events: int = 20) -> list:
    events = []
    seen = set()

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("<!--") or line.startswith("---"):
            continue
        if is_noise(line):
            continue

        t = TIME_LINE_RE.search(line)
        if t:
            cleaned = re.sub(r"\*\*", "", line)
            if cleaned not in seen:
                events.append({"time": t.group(1), "text": cleaned})
                seen.add(cleaned)
            continue

        if line.startswith("- ") or line.startswith("### "):
            cleaned = re.sub(r"^[-#\s]+", "", line)
            if cleaned and is_meaningful(cleaned) and cleaned not in seen:
                events.append({"time": "", "text": cleaned})
                seen.add(cleaned)

        if len(events) >= max_events:
            break
    return events


def main() -> int:
    selfies_by_date = load_selfies_by_date()
    days = []

    files = sorted(MEMORY_DIR.glob("20*.md"), reverse=True)[:20]
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        m = DATE_RE.search(text)
        date_key = m.group(1) if m else f.stem
        events = extract_events(text)
        if not events and not selfies_by_date.get(date_key):
            continue

        days.append(
            {
                "date": date_key,
                "events": events,
                "selfies": selfies_by_date.get(date_key, []),
            }
        )

    payload = {
        "updated": __import__("datetime").datetime.now().isoformat(),
        "days": days,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported: {OUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
