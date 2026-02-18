#!/usr/bin/env python3
"""Fetch Chinese platform hot topics from local DailyHotApi and print a compact report."""

from __future__ import annotations

import datetime as dt
import json
import os
import urllib.error
import urllib.request

API_BASE = os.environ.get("DAILY_HOT_API_URL", "http://localhost:6688")
SOURCES = [
    ("weibo", "微博热搜"),
    ("zhihu", "知乎热榜"),
    ("bilibili", "B站热门"),
]


def fetch_source(path: str) -> dict:
    url = f"{API_BASE.rstrip('/')}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "BowlWanpi-CNHot/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def normalize_items(payload: dict) -> list[dict]:
    data = payload.get("data") or payload.get("list") or []
    out: list[dict] = []
    for i, item in enumerate(data[:5], start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or item.get("name") or item.get("word") or "").strip()
        if not title:
            continue
        hot = str(item.get("hot") or item.get("score") or item.get("heat") or "-")
        url = str(item.get("url") or item.get("link") or "").strip()
        out.append({"rank": i, "title": title, "hot": hot, "url": url})
    return out


def main() -> int:
    bj_now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    lines = [
        f"🔥 中文平台热榜速览 | {bj_now:%m月%d日 %H:%M}（北京时间）",
        "",
    ]

    any_ok = False
    for key, label in SOURCES:
        try:
            payload = fetch_source(key)
            items = normalize_items(payload)
            if not items:
                lines.append(f"【{label}】暂无可用数据")
                lines.append("")
                continue
            any_ok = True
            lines.append(f"【{label}】")
            for it in items:
                line = f"{it['rank']}. {it['title']}"
                if it["hot"] and it["hot"] != "-":
                    line += f"（热度: {it['hot']}）"
                lines.append(line)
                if it["url"]:
                    lines.append(it["url"])
            lines.append("")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            lines.append(f"【{label}】抓取失败（源服务可能未启动）")
            lines.append("")

    if not any_ok:
        print("NO_REPLY")
        return 0

    lines.append("🥣 碗皮备注：这条是中文平台专栏，和 GitHub / X 热点分开发，避免信息打架。")
    print("\n".join(lines).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
