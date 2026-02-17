#!/usr/bin/env python3
"""
Agent News 监控脚本
替代旧的 HN 定向检索：每小时从 HN 热门里筛选 Agent/AI Coding 相关新闻。
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

WORKSPACE = Path("/root/.openclaw/workspace")
CACHE_FILE = WORKSPACE / "memory" / "agent-news-cache.json"
PENDING_FILE = Path("/tmp/bowlwanpi-agent-news-pending.txt")
LOG_FILE = Path("/var/log/bowlwanpi-agent-news.log")

TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
ITEM_URL_TMPL = "https://hacker-news.firebaseio.com/v0/item/{id}.json"

LOOKBACK_SECONDS = 24 * 3600
MAX_TOP_IDS = 80
MAX_CACHE_ITEMS = 300

KEYWORDS = [
    "openclaw",
    "clawdbot",
    "moltbot",
    "agent",
    "ai agent",
    "coding agent",
    "code assistant",
    "cursor",
    "claude code",
    "codex",
    "devin",
    "llm",
    "mcp",
    "function calling",
]


def log(message: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")


def fetch_json(url: str, timeout: int = 12) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "bowlwanpi-agent-news/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
        return json.loads(resp.read().decode("utf-8"))


def strip_html(text: str) -> str:
    text = html.unescape(text)
    return re.sub(r"<[^>]+>", " ", text)


def load_cache() -> List[Dict[str, Any]]:
    if not CACHE_FILE.exists():
        return []
    try:
        with CACHE_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def save_cache(items: List[Dict[str, Any]]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE_FILE.open("w", encoding="utf-8") as f:
        json.dump(items[-MAX_CACHE_ITEMS:], f, ensure_ascii=False, indent=2)


def matches_keywords(item: Dict[str, Any]) -> bool:
    title = str(item.get("title") or "")
    text = str(item.get("text") or "")
    combined = f"{title} {strip_html(text)}".lower()
    return any(k in combined for k in KEYWORDS)


def format_pending(items: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for item in items:
        story_id = item.get("id")
        title = str(item.get("title") or "(no title)")
        author = str(item.get("by") or "unknown")
        score = int(item.get("score") or 0)
        comments = int(item.get("descendants") or 0)
        source_url = str(item.get("url") or "").strip()
        hn_url = f"https://news.ycombinator.com/item?id={story_id}"

        lines.append(f"📰 Agent News: {title}")
        lines.append(f"👤 {author} | ⬆️ {score} | 💬 {comments}")
        if source_url:
            lines.append(f"🔗 {source_url}")
        lines.append(f"🧵 {hn_url}")
        lines.append("---")
    return "\n".join(lines) + ("\n" if lines else "")


def main() -> int:
    now = int(time.time())
    cutoff = now - LOOKBACK_SECONDS

    log("Checking Hacker News top stories for agent news...")

    try:
        top_ids = fetch_json(TOP_STORIES_URL)
        if not isinstance(top_ids, list):
            raise ValueError("topstories response is not a list")
    except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as e:
        log(f"ERROR: failed to fetch top stories: {e}")
        return 1

    cache = load_cache()
    cached_ids = {int(x.get("id")) for x in cache if isinstance(x, dict) and str(x.get("id", "")).isdigit()}

    checked = 0
    matched: List[Dict[str, Any]] = []
    new_items: List[Dict[str, Any]] = []

    for story_id in top_ids[:MAX_TOP_IDS]:
        try:
            story = fetch_json(ITEM_URL_TMPL.format(id=story_id), timeout=10)
        except Exception:
            continue

        if not isinstance(story, dict):
            continue
        if story.get("type") != "story":
            continue
        if story.get("deleted") or story.get("dead"):
            continue

        checked += 1

        story_time = int(story.get("time") or 0)
        if story_time < cutoff:
            continue
        if not matches_keywords(story):
            continue

        matched.append(story)

        sid = int(story.get("id") or 0)
        if sid and sid not in cached_ids:
            new_items.append(story)
            cache.append(
                {
                    "id": sid,
                    "title": story.get("title", ""),
                    "time": story_time,
                    "score": int(story.get("score") or 0),
                    "comments": int(story.get("descendants") or 0),
                    "by": story.get("by", ""),
                    "url": story.get("url", ""),
                }
            )
            cached_ids.add(sid)

    save_cache(cache)

    if new_items:
        PENDING_FILE.write_text(format_pending(new_items), encoding="utf-8")
        log(f"FOUND_NEW: {len(new_items)}")
    else:
        if PENDING_FILE.exists():
            PENDING_FILE.unlink()
        log("NO_NEW")

    log(f"SUMMARY: checked={checked}, matched={len(matched)}, new={len(new_items)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
