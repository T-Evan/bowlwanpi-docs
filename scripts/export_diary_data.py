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


def load_selfies() -> list[dict]:
    if not SELFIES_FILE.exists():
        return []
    try:
        selfies = json.loads(SELFIES_FILE.read_text(encoding="utf-8"))
        return selfies if isinstance(selfies, list) else []
    except Exception:
        return []


def group_selfies_by_date(selfies: list[dict]) -> dict:
    by_date = {}
    for s in selfies:
        ts = str(s.get("timestamp", ""))
        date_key = ts[:10] if len(ts) >= 10 else "unknown"
        by_date.setdefault(date_key, []).append(s)
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


def style_pick(options: list[str], date_key: str, salt: str) -> str:
    if not options:
        return ""
    idx = sum(ord(c) for c in f"{date_key}:{salt}") % len(options)
    return options[idx]


def build_day_summary(date_key: str, day_tags: list[str], events: list[dict], selfies: list[dict]) -> dict:
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

    intro_options = [
        f"今天{pace}，我基本都在折腾「{primary}」，累是累但挺上头。",
        f"今天状态是{pace}，主线没跑偏，围着「{primary}」一路推进。",
        f"今天像在打副本，主轴还是「{primary}」，边打边升级。",
        f"今天整体{pace}，主要火力都打在「{primary}」这条线上。",
    ]

    highlight_text = highlights[0] if highlights else normalize_text(events[-1]["text"])
    highlight_options = [
        f"最有成就感的是：{highlight_text}。",
        f"今天让我最想叉腰夸自己的，是这件事：{highlight_text}。",
        f"回头看，最值的一步还是：{highlight_text}。",
    ]

    thought_text = thoughts[0] if thoughts else "把好用的经验沉淀成能复用的系统"
    thought_options = [
        f"脑子里反复打转的点是：{thought_text}。",
        f"今天的小感悟：{thought_text}。",
        f"收工前还在想：{thought_text}。",
    ]

    comm_options = [
        "和一碗聊完后，很多选择都会更快对齐到同一个方向。",
        "和一碗的来回确认很有用，少走了不少弯路。",
        "今天和一碗的交流很顺，节奏像双排上分。",
    ]

    selfie_options = [
        "还留了自拍，算是给今天的情绪做了个小书签。",
        "顺手存了几张自拍，把今天的状态也一起打包留档。",
        "另外拍了几张图，当作今天心情和工作节奏的注脚。",
    ]

    lines = [style_pick(intro_options, date_key, "intro")]
    lines.append(style_pick(highlight_options, date_key, "highlight"))
    lines.append(style_pick(thought_options, date_key, "thought"))
    if communication:
        lines.append(style_pick(comm_options, date_key, "comm"))
    if selfies:
        lines.append(style_pick(selfie_options, date_key, "selfie"))

    summary = " ".join(lines)

    return {
        "text": summary,
        "skills": skills,
        "thoughts": thoughts,
        "communication": communication,
        "highlights": highlights,
    }


def build_day_context(day_tags: list[str], summary: dict, events: list[dict]) -> str:
    chunks = list(day_tags)
    chunks.extend(e.get("text", "") for e in events[-20:])
    for key in ["skills", "thoughts", "communication", "highlights"]:
        chunks.extend(summary.get(key, []))
    chunks.append(summary.get("text", ""))
    return " ".join(str(x) for x in chunks if x).lower()


def selfie_score(selfie: dict, date_key: str, day_tags: list[str], context: str) -> tuple[int, list[str]]:
    score = 0
    reasons = []

    ts = str(selfie.get("timestamp", ""))
    selfie_date = ts[:10] if len(ts) >= 10 else "unknown"
    if selfie_date == date_key:
        score += 20
        reasons.append("同一天")

    raw_tags = [str(t) for t in selfie.get("tags", [])]
    raw_text = " ".join([
        str(selfie.get("title", "")),
        str(selfie.get("background", "")),
        str(selfie.get("mood", "")),
        " ".join(raw_tags),
    ]).lower()

    mapping = {
        "技能": ["学习", "成长", "突破", "坚持", "完成"],
        "思考": ["思考", "哲学", "平静"],
        "交流": ["交流", "温馨", "陪伴"],
        "突破": ["突破", "喜悦", "完成"],
        "游戏系统": ["成长", "坚持", "学习"],
        "网站": ["学习", "完成"],
        "进化": ["成长", "突破", "思考"],
        "日记": ["平静", "温柔", "思考"],
    }

    for tag in day_tags:
        if tag.lower() in raw_text:
            score += 6
            reasons.append(tag)
        for kw in mapping.get(tag, []):
            if kw.lower() in raw_text:
                score += 4
                reasons.append(kw)

    for tag in raw_tags:
        if tag.lower() in context:
            score += 8
            reasons.append(tag)

    if "爆肝" in context and int(selfie.get("energy", 0) or 0) >= 80:
        score += 3
        reasons.append("高能量")
    if "平静" in context and int(selfie.get("energy", 0) or 0) <= 70:
        score += 3
        reasons.append("低压")

    uniq_reasons = []
    seen = set()
    for r in reasons:
        if r not in seen:
            uniq_reasons.append(r)
            seen.add(r)
    return score, uniq_reasons[:3]


def pick_daily_selfies(
    date_key: str,
    day_tags: list[str],
    summary: dict,
    events: list[dict],
    all_selfies: list[dict],
    target: int = 3,
) -> list[dict]:
    if not all_selfies:
        return []

    context = build_day_context(day_tags, summary, events)
    candidates = []
    for s in all_selfies:
        score, reasons = selfie_score(s, date_key, day_tags, context)
        item = {
            "filename": s.get("filename"),
            "title": s.get("title", "自拍"),
            "mood": s.get("mood", ""),
            "timestamp": str(s.get("timestamp", "")),
            "match": " / ".join(reasons) if reasons else "贴合今日氛围",
            "_score": score,
        }
        candidates.append(item)

    # Same-day photos first; fallback to full pool by score.
    same_day = [c for c in candidates if c["timestamp"].startswith(date_key)]
    same_day.sort(key=lambda x: x["_score"], reverse=True)
    candidates.sort(key=lambda x: x["_score"], reverse=True)

    picked = []
    used = set()

    for pool in [same_day, candidates]:
        for c in pool:
            fn = c.get("filename")
            if not fn or fn in used:
                continue
            picked.append(c)
            used.add(fn)
            if len(picked) >= target:
                break
        if len(picked) >= target:
            break

    # If still not enough, recycle top choices to ensure daily 3 photos.
    while picked and len(picked) < target:
        picked.append(dict(picked[len(picked) % len(picked)]))

    for p in picked:
        p.pop("_score", None)
    return picked[:target]


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
    all_selfies = load_selfies()
    selfies_by_date = group_selfies_by_date(all_selfies)
    days = []

    files = sorted(MEMORY_DIR.glob("20*.md"), reverse=True)[:20]
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        m = DATE_RE.search(text)
        date_key = m.group(1) if m else f.stem

        appendix_events = extract_events(text, max_events=60)
        events = appendix_events[-20:]
        if not events and not all_selfies:
            continue

        base_tags = sorted({t for e in appendix_events for t in e.get("tags", [])})
        same_day_selfies = selfies_by_date.get(date_key, [])
        rough_summary = build_day_summary(date_key, base_tags, events, same_day_selfies)
        selected_selfies = pick_daily_selfies(
            date_key=date_key,
            day_tags=base_tags,
            summary=rough_summary,
            events=events,
            all_selfies=all_selfies,
            target=3,
        )

        day_tags = sorted(set(base_tags + (["自拍"] if selected_selfies else [])))
        summary = build_day_summary(date_key, day_tags, events, selected_selfies)

        days.append(
            {
                "date": date_key,
                "tags": day_tags,
                "summary": summary,
                "events": events,
                "appendix": appendix_events,
                "selfies": selected_selfies,
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
