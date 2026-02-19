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
SIMPLE_TIME_RE = re.compile(r"^(\d{1,2}:\d{2})\s+")
SIGNIFICANT_VERBS = [
    "完成",
    "修复",
    "新增",
    "整合",
    "上线",
    "发布",
    "通过",
    "解锁",
    "升级",
    "进化",
    "安装",
    "部署",
    "测试",
]

NOISE_PATTERNS = [
    "优先事项",
    "定时任务",
    "微博热搜",
    "知乎热榜",
    "b站热门",
    "热榜速览",
    "中文平台热榜",
    "版本快照",
    "爆发项目精选",
    "heartbeat_ok",
    "heartbeat 简报",
    "监控频率",
    "更新时间",
    "system:",
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
    "偏好",
    "技能",
    "经验",
    "突破",
    "整合",
    "部署",
    "测试",
    "发布",
    "上线",
    "升级",
    "解锁",
    "赛季",
    "天赋",
    "商店",
    "羁绊",
    "进化",
    "evolver",
]

TAG_RULES = [
    ("进化", ["进化", "evolver", "gep", "gene", "capsule"]),
    (
        "游戏系统",
        [
            "等级",
            "成就",
            "赛季",
            "天赋",
            "商店",
            "羁绊",
            "xp",
            "quest",
            "tier",
            "代币",
        ],
    ),
    (
        "技能",
        [
            "实现",
            "新增",
            "重构",
            "修复",
            "集成",
            "脚本",
            "部署",
            "测试",
            "编译",
            "安装",
            "配置",
            "发布",
            "提交",
            "commit",
            "feat:",
            "fix:",
            "refactor:",
        ],
    ),
    ("思考", ["思考", "反思", "感受", "想法", "洞察", "收获", "学到", "理解"]),
    ("交流", ["一碗", "沟通", "交流", "对话", "反馈", "偏好", "约定", "讨论"]),
    ("突破", ["搞定", "完成", "通过", "上线", "发布", "整合", "落地", "解决", "pass"]),
    ("网站", ["github pages", "gh-pages", "网站", "页面", "diary.html", "index.html", "docs/"]),
    ("日记", ["日记", "diary", "记录"]),
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
    if "http://" in low or "https://" in low or "🔗" in line:
        return True
    if SIMPLE_TIME_RE.match(line) and not any(v in low for v in SIGNIFICANT_VERBS):
        return True
    if any(p in low for p in NOISE_PATTERNS):
        return True
    return False


def is_meaningful(line: str) -> bool:
    low = line.lower()
    return any(k in low for k in MEANINGFUL_HINTS)


def compute_tags(text: str) -> list:
    low = text.lower()
    tags = []
    for tag, keywords in TAG_RULES:
        for kw in keywords:
            if kw.lower() in low:
                tags.append(tag)
                break
    return tags


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
            cleaned = re.sub(r"\*\*", "", line).strip()
            tags = compute_tags(cleaned)
            if not tags and is_meaningful(cleaned):
                tags = ["成长"]
            if not tags:
                continue
            if cleaned not in seen:
                events.append({"time": t.group(1), "text": cleaned, "tags": tags})
                seen.add(cleaned)
            continue

        if line.startswith("- ") or line.startswith("### "):
            cleaned = re.sub(r"^[-#\s]+", "", line).strip()
            if cleaned and is_meaningful(cleaned):
                tags = compute_tags(cleaned)
                if not tags:
                    tags = ["成长"]
                if cleaned not in seen:
                    events.append({"time": "", "text": cleaned, "tags": tags})
                    seen.add(cleaned)

    return events[-max_events:]


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

        selfies = selfies_by_date.get(date_key, [])
        day_tags = sorted({t for e in events for t in e.get("tags", [])})
        if selfies:
            day_tags = sorted(set(day_tags + ["自拍"]))

        days.append(
            {
                "date": date_key,
                "tags": day_tags,
                "events": events,
                "selfies": selfies,
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
