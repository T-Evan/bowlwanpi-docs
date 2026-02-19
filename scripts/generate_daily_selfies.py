#!/usr/bin/env python3
"""Generate 3 new daily selfies and sync website data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

WORKSPACE = Path("/root/.openclaw/workspace")
TMP_DIR = WORKSPACE / "tmp"
SELFIES_JSON = WORKSPACE / "docs/data/selfies.json"
SELFIE_DIR = WORKSPACE / "docs/assets/selfies"
DIARY_JSON = WORKSPACE / "docs/data/diary.json"

UMARU_SCRIPT = WORKSPACE / "skills/umaru-anime-style/scripts/generate.py"
EXPORT_DIARY = WORKSPACE / "scripts/export_diary_data.py"
EXPORT_SITE = WORKSPACE / "scripts/export_site_realtime.py"
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})$")


def now_bjt() -> datetime:
    return datetime.now(timezone.utc).astimezone(ZoneInfo("Asia/Shanghai"))


def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_renamed(stdout: str) -> Path | None:
    m = re.search(r"Renamed:\s*(\S+)", stdout)
    if m:
        p = Path(m.group(1))
        if p.exists():
            return p
    candidates = sorted(TMP_DIR.glob("umaru_*.webp"), key=lambda x: x.stat().st_mtime, reverse=True)
    return candidates[0] if candidates else None


def infer_day_context(date_key: str) -> dict:
    data = load_json(DIARY_JSON, {"days": []})
    day = next((d for d in data.get("days", []) if d.get("date") == date_key), None)
    if not day:
        return {"tags": ["成长"], "summary": "今天继续稳定推进。"}
    return {
        "tags": day.get("tags", ["成长"]),
        "summary": day.get("summary", {}).get("text", "今天继续稳定推进。"),
    }


def list_backfill_dates(today_key: str) -> list[str]:
    diary = load_json(DIARY_JSON, {"days": []})
    dates = []
    seen = set()
    for day in diary.get("days", []):
        date_key = str(day.get("date", ""))
        if not DATE_RE.fullmatch(date_key):
            continue
        if date_key == today_key or date_key in seen:
            continue
        seen.add(date_key)
        dates.append(date_key)

    # Backfill from old to new so the timeline feels chronological.
    return sorted(dates)


def pick_variant(options: list[str], date_key: str, slot: str, summary: str) -> str:
    if not options:
        return ""
    seed = f"{date_key}:{slot}:{summary[:80]}"
    idx = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) % len(options)
    return options[idx]


def infer_work_focus(tags: list[str], summary: str) -> str:
    text = " ".join(tags) + " " + summary
    if any(k in text for k in ["网站", "页面", "gh-pages", "deploy"]):
        return "web"
    if any(k in text for k in ["游戏", "赛季", "成就", "任务", "xp"]):
        return "game"
    if any(k in text for k in ["进化", "evolver", "思考", "洞察"]):
        return "research"
    return "coding"


def infer_mood_profile(tags: list[str], summary: str) -> tuple[str, str, int]:
    text = " ".join(tags) + " " + summary
    if any(k in text for k in ["爆肝", "高能", "冲刺", "赶进度"]):
        return "focused", "专注拉满，有点燃。", 86
    if any(k in text for k in ["反思", "思考", "复盘", "洞察"]):
        return "reflective", "有点安静，脑子在转。", 68
    if any(k in text for k in ["交流", "一碗", "沟通", "协作"]):
        return "friendly", "互动顺滑，心情挺暖。", 74
    return "warm", "轻松一点，心里有数。", 72


def build_recipes(date_key: str, context: dict) -> list[dict]:
    tags = context.get("tags", [])
    summary = context.get("summary", "")

    focus = infer_work_focus(tags, summary)
    mood_core, mood_zh, mood_energy = infer_mood_profile(tags, summary)

    work_scenes = {
        "coding": [
            "a standing desk with multiple monitors, terminal logs, and sticky notes",
            "a laptop workspace in a cafe corner with code editor and TODO board",
            "a late-night workstation with dual screens and debugging traces",
            "a minimal home office with a bright monitor showing project dashboard",
        ],
        "web": [
            "a web design workspace with browser previews, color swatches and code editor",
            "a UI review table with tablet mockups and responsive layout sketches",
            "a product design desk with wireframes pinned on a wall",
            "a modern studio with website analytics and deployment panel on screen",
        ],
        "game": [
            "a creative desk with game UI sketches, xp charts and reward board",
            "a neon-lit setup with season progress map and quest cards",
            "a gamification planning wall with badges, tokens, and flow diagrams",
            "a cozy dev corner with playful HUD concepts on monitor",
        ],
        "research": [
            "a quiet research desk with notebook mindmaps and evolution graph",
            "a thinking corner with whiteboard formulas and concept cards",
            "a study room with books, sticky links, and timeline notes",
            "a calm workspace with insight dashboard and reflection journal",
        ],
    }

    mood_scenes = [
        "a rainy window seat with warm desk lamp and a cup of tea",
        "a sunny balcony corner with plants, notebook and soft breeze",
        "a cozy beanbag nook with fairy lights and handwritten notes",
        "a quiet cafe table with warm light and open journal",
        "a city-night window desk with ambient glow and headphones",
    ]

    reflection_scenes = [
        "a night desk with open notebook, fountain pen and subtle city lights",
        "a reading corner with paper journal and floor lamp at dusk",
        "a wooden desk with tea steam, checklist and calm blue hour lighting",
        "a minimalist room with reflection board and post-it timeline",
        "a moonlit workstation with diary notes and finished task cards",
    ]

    work_actions = {
        "coding": [
            "typing while reviewing bug fixes and commit diff",
            "checking integration logs and polishing scripts",
            "merging ideas into a stable automation pipeline",
            "refining toolchain details and verifying outputs",
        ],
        "web": [
            "fine-tuning page layout and checking mobile preview",
            "reviewing deployment status and polishing visual details",
            "updating site data feed and validating diary rendering",
            "iterating UI blocks based on daily content",
        ],
        "game": [
            "organizing quest flow and balancing reward progression",
            "updating season progress board and checking milestones",
            "mapping daily tasks to XP and achievement triggers",
            "tuning game loop details for smoother motivation feedback",
        ],
        "research": [
            "connecting notes into a clearer mental model",
            "summarizing insights and marking next experiments",
            "linking observations to practical workflow improvements",
            "sorting evolution signals into actionable ideas",
        ],
    }

    mood_actions = [
        "taking a short break and breathing after a focused sprint",
        "leaning back with a small smile after finishing key tasks",
        "stretching and checking today's emotional energy",
        "pausing for a soft reset before the next task",
        "listening to calm music and noting current feelings",
    ]

    reflection_actions = [
        "writing daily reflection notes and key lessons",
        "highlighting what worked and what to improve tomorrow",
        "reviewing today's interactions and keeping useful takeaways",
        "closing the day with a short honest self-review",
        "archiving wins and lessons into tomorrow's plan",
    ]

    work_scene = pick_variant(work_scenes.get(focus, work_scenes["coding"]), date_key, "work_scene", summary)
    mood_scene = pick_variant(mood_scenes, date_key, "mood_scene", summary)
    reflection_scene = pick_variant(reflection_scenes, date_key, "reflection_scene", summary)

    work_action = pick_variant(work_actions.get(focus, work_actions["coding"]), date_key, "work_action", summary)
    mood_action = pick_variant(mood_actions, date_key, "mood_action", summary)
    reflection_action = pick_variant(reflection_actions, date_key, "reflection_action", summary)

    # Avoid repeated backgrounds inside the same day.
    def avoid_duplicate(scene: str, pool: list[str], used: set[str]) -> str:
        if scene not in used:
            return scene
        for candidate in pool:
            if candidate not in used:
                return candidate
        return scene

    used_scenes: set[str] = set()
    work_scene = avoid_duplicate(work_scene, work_scenes.get(focus, work_scenes["coding"]), used_scenes)
    used_scenes.add(work_scene)
    mood_scene = avoid_duplicate(mood_scene, mood_scenes, used_scenes)
    used_scenes.add(mood_scene)
    reflection_scene = avoid_duplicate(reflection_scene, reflection_scenes, used_scenes)

    recipes = [
        {
            "key": "work",
            "scene": work_scene,
            "mood": "confident" if focus != "research" else "focused",
            "action": work_action,
            "title": "今日主线推进",
            "background": f"今天主线偏{focus}向，把工作的关键结果稳稳推进。",
            "mood_zh": "专注又踏实，节奏在线。",
            "energy": 82,
            "tags": ["工作", "成长", "技能", focus],
        },
        {
            "key": "mood",
            "scene": mood_scene,
            "mood": mood_core,
            "action": mood_action,
            "title": "今日心情切片",
            "background": "把今天的情绪状态和节奏变化认真记录下来。",
            "mood_zh": mood_zh,
            "energy": mood_energy,
            "tags": ["心情", "记录", "自拍"],
        },
        {
            "key": "reflection",
            "scene": reflection_scene,
            "mood": "thoughtful",
            "action": reflection_action,
            "title": "收工反思时刻",
            "background": "复盘今天的得失，把可复用经验写进明天。",
            "mood_zh": "收一收线，把经验留下来。",
            "energy": 64 if mood_energy < 75 else 70,
            "tags": ["反思", "总结", "成长"],
        },
    ]

    for r in recipes:
        # Keep day tags as weak context for downstream matching.
        r["tags"] = sorted(set(r["tags"] + tags[:4]))
    return recipes


def run_recipe(recipe: dict) -> Path:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        "python3",
        str(UMARU_SCRIPT),
        "--scene",
        recipe["scene"],
        "--mood",
        recipe["mood"],
        "--action",
        recipe["action"],
        "--output-dir",
        str(TMP_DIR),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "image generation failed").strip())
    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    generated = parse_renamed(out)
    if not generated:
        raise RuntimeError("generated file not found")
    return generated


def sync_selfies(
    date_key: str,
    generated_files: list[Path],
    recipes: list[dict],
    timestamp_base: str,
) -> int:
    SELFIE_DIR.mkdir(parents=True, exist_ok=True)
    data = load_json(SELFIES_JSON, [])

    # Remove existing entries from the same day to keep exactly 3 fresh photos.
    data = [x for x in data if str(x.get("timestamp", ""))[:10] != date_key]

    ts_base = timestamp_base
    for i, (src, recipe) in enumerate(zip(generated_files, recipes), start=1):
        dst_name = f"daily_{date_key.replace('-', '')}_{i}_{src.name}"
        dst = SELFIE_DIR / dst_name
        shutil.copy2(src, dst)

        data.append(
            {
                "filename": dst_name,
                "title": recipe["title"],
                "background": recipe["background"],
                "mood": recipe["mood_zh"],
                "energy": recipe["energy"],
                "tags": recipe["tags"],
                "timestamp": ts_base,
            }
        )

    # Keep recent entries only.
    data.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    data = data[:180]
    save_json(SELFIES_JSON, data)
    return 3


def run_post_exports() -> None:
    subprocess.run(["python3", str(EXPORT_DIARY)], check=False)
    subprocess.run(["python3", str(EXPORT_SITE)], check=False)


def deploy_pages() -> None:
    remote = subprocess.check_output(["git", "-C", str(WORKSPACE), "remote", "get-url", "origin"], text=True).strip()
    tmp = Path(subprocess.check_output(["mktemp", "-d"], text=True).strip())
    try:
        subprocess.run(["git", "init", "-b", "gh-pages"], cwd=tmp, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "config", "user.name", "bowlwanpi"], cwd=tmp, check=True)
        subprocess.run(["git", "config", "user.email", "bowlwanpi@local"], cwd=tmp, check=True)
        subprocess.run(["cp", "-r", str(WORKSPACE / "docs") + "/.", str(tmp)], check=True)
        subprocess.run(["git", "add", "."], cwd=tmp, check=True)
        subprocess.run(["git", "commit", "-m", "deploy: daily selfie refresh"], cwd=tmp, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "remote", "add", "origin", remote], cwd=tmp, check=True)
        subprocess.run(["git", "push", "-f", "origin", "gh-pages"], cwd=tmp, check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def generate_for_date(date_key: str, force: bool = False) -> bool:
    existing = load_json(SELFIES_JSON, [])
    day_count = sum(1 for x in existing if str(x.get("timestamp", ""))[:10] == date_key)
    if day_count >= 3 and not force:
        print(f"Already has {day_count} photos for {date_key}, skip.")
        return False

    context = infer_day_context(date_key)
    recipes = build_recipes(date_key, context)

    generated = []
    for recipe in recipes:
        print(f"[{date_key}] Generating: {recipe['key']}...")
        generated.append(run_recipe(recipe))

    # Keep historical timestamp aligned to diary date.
    timestamp_base = f"{date_key}T21:40:00"
    count = sync_selfies(date_key, generated, recipes, timestamp_base=timestamp_base)
    print(f"[{date_key}] Added {count} photos.")
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="regenerate even if photos already exist")
    parser.add_argument("--date", help="target date (YYYY-MM-DD)")
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="regenerate 3 photos for all previous diary dates",
    )
    parser.add_argument("--deploy-pages", action="store_true", help="push docs to gh-pages after generation")
    args = parser.parse_args()

    today_key = now_bjt().strftime("%Y-%m-%d")

    if args.date and args.backfill:
        raise SystemExit("Use either --date or --backfill, not both.")

    changed = False

    if args.backfill:
        targets = list_backfill_dates(today_key)
        if not targets:
            print("No previous diary dates found for backfill.")
        for date_key in targets:
            changed = generate_for_date(date_key, force=True) or changed
    else:
        date_key = args.date or today_key
        if not DATE_RE.fullmatch(date_key):
            raise SystemExit("--date must be YYYY-MM-DD")
        changed = generate_for_date(date_key, force=args.force)

    if changed:
        run_post_exports()
        if args.deploy_pages:
            deploy_pages()

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
