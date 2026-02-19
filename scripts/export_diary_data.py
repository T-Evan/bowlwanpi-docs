#!/usr/bin/env python3
"""Export diary timeline from memory files and selfies for website."""

from __future__ import annotations

import json
import re
from datetime import datetime
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


def normalize_text(text: str, limit: int = 72) -> str:
    cleaned = re.sub(r"[`*]", "", text).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned[:limit] + "…" if len(cleaned) > limit else cleaned


def unique_texts(items: list[str], max_items: int = 4) -> list[str]:
    out = []
    seen = set()
    for item in items:
        key = item.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)
        if len(out) >= max_items:
            break
    return out


def build_day_summary(day_tags: list[str], events: list[dict], selfies: list[dict]) -> dict:
    if not events:
        return {
            "text": "今天是轻量的一天，先留白，明天继续推进。",
            "skills": [],
            "thoughts": [],
            "communication": [],
            "highlights": [],
        }

    tags = [t for t in day_tags if t != "自拍"]
    primary = "、".join(tags[:3]) if tags else "成长"

    skill_events = [normalize_text(e["text"]) for e in events if "技能" in e.get("tags", []) or "进化" in e.get("tags", [])]
    thought_events = [normalize_text(e["text"]) for e in events if "思考" in e.get("tags", [])]
    comm_events = [normalize_text(e["text"]) for e in events if "交流" in e.get("tags", [])]
    breakthrough_events = [normalize_text(e["text"]) for e in events if "突破" in e.get("tags", [])]

    skills = unique_texts(skill_events)
    thoughts = unique_texts(thought_events)
    communication = unique_texts(comm_events)
    highlight_candidates = [
        x for x in breakthrough_events if len(x) >= 8 and not x.endswith((":", "："))
    ]
    if not highlight_candidates:
        highlight_candidates = [normalize_text(events[-1]["text"])]
    highlights = unique_texts(highlight_candidates, max_items=3)

    if len(events) >= 14:
        pace = "有点爆肝"
    elif len(events) >= 9:
        pace = "节奏很在线"
    else:
        pace = "慢慢推进但很稳"

    lines = [f"今天{pace}，主线基本都围着「{primary}」在转。"]
    if highlights:
        lines.append(f"最有成就感的一笔是：{highlights[0]}。")
    if thoughts:
        lines.append(f"脑子里反复打转的点是：{thoughts[0]}。")
    if communication:
        lines.append("和一碗聊完后，很多选择会更快对齐到同一个方向。")
    if selfies:
        lines.append("还留了自拍，算是给今天的情绪做个小书签。")

    summary = " ".join(lines)

    return {
        "text": summary,
        "skills": skills,
        "thoughts": thoughts,
        "communication": communication,
        "highlights": highlights,
    }


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

        appendix_events = extract_events(text, max_events=60)
        events = appendix_events[-20:]
        selfies = selfies_by_date.get(date_key, [])
        if not events and not selfies:
            continue

        day_tags = sorted({t for e in appendix_events for t in e.get("tags", [])})
        if selfies:
            day_tags = sorted(set(day_tags + ["自拍"]))

        summary = build_day_summary(day_tags, events, selfies)

        days.append(
            {
                "date": date_key,
                "tags": day_tags,
                "summary": summary,
                "events": events,
                "appendix": appendix_events,
                "selfies": selfies,
            }
        )

    payload = {
        "updated": datetime.now().isoformat(),
        "days": days,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Exported: {OUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
