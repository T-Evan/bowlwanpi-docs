#!/usr/bin/env python3
"""Generate 3 new daily selfies and sync website data."""

from __future__ import annotations

import argparse
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


def build_recipes(date_key: str, context: dict) -> list[dict]:
    tags = context.get("tags", [])
    summary = context.get("summary", "")

    mood_core = "focused" if "爆肝" in summary or "推进" in summary else "warm"
    if "思考" in tags:
        mood_core = "reflective"
    if "交流" in tags:
        mood_core = "friendly"

    work_scene = "a modern coding desk with dashboards on screen"
    if "游戏系统" in tags:
        work_scene = "a creative desk with game UI sketches and progress charts"
    elif "网站" in tags:
        work_scene = "a web design workspace with browser previews and code editor"

    recipes = [
        {
            "key": "work",
            "scene": work_scene,
            "mood": "confident",
            "action": "typing while reviewing daily progress",
            "title": "今日主线推进",
            "background": "把当天工作的主线沉淀成可复用成果。",
            "mood_zh": "专注又踏实，节奏在线。",
            "energy": 82,
            "tags": ["工作", "成长", "技能"],
        },
        {
            "key": "mood",
            "scene": "a cozy room with soft light and sticky notes",
            "mood": mood_core,
            "action": "taking a short break and smiling at completed tasks",
            "title": "今日心情切片",
            "background": "把今天的情绪状态也认真记录下来。",
            "mood_zh": "轻松一点，心里有数。" if mood_core != "reflective" else "有点安静，脑子在转。",
            "energy": 74,
            "tags": ["心情", "记录", "自拍"],
        },
        {
            "key": "reflection",
            "scene": "a night desk with notebook, tea and subtle city lights",
            "mood": "thoughtful",
            "action": "writing daily reflection notes",
            "title": "收工反思时刻",
            "background": "复盘今天学到的经验和和一碗的沟通收获。",
            "mood_zh": "收一收线，把经验留下来。",
            "energy": 66,
            "tags": ["反思", "交流", "总结"],
        },
    ]

    for r in recipes:
        # Keep day tags as weak context for downstream matching.
        r["tags"] = sorted(set(r["tags"] + tags[:3]))
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


def sync_selfies(date_key: str, generated_files: list[Path], recipes: list[dict]) -> int:
    SELFIE_DIR.mkdir(parents=True, exist_ok=True)
    data = load_json(SELFIES_JSON, [])

    # Remove existing entries from the same day to keep exactly 3 fresh photos.
    data = [x for x in data if str(x.get("timestamp", ""))[:10] != date_key]

    ts_base = now_bjt().strftime("%Y-%m-%dT%H:%M:%S")
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="regenerate even if today's photos already exist")
    parser.add_argument("--deploy-pages", action="store_true", help="push docs to gh-pages after generation")
    args = parser.parse_args()

    date_key = now_bjt().strftime("%Y-%m-%d")
    existing = load_json(SELFIES_JSON, [])
    today_count = sum(1 for x in existing if str(x.get("timestamp", ""))[:10] == date_key)
    if today_count >= 3 and not args.force:
        print(f"Already has {today_count} photos for {date_key}, skip.")
        return 0

    context = infer_day_context(date_key)
    recipes = build_recipes(date_key, context)

    generated = []
    for recipe in recipes:
        print(f"Generating: {recipe['key']}...")
        generated.append(run_recipe(recipe))

    count = sync_selfies(date_key, generated, recipes)
    run_post_exports()

    if args.deploy_pages:
        deploy_pages()

    print(f"Done. Added {count} daily photos for {date_key}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
