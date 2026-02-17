#!/usr/bin/env python3
"""
知乎热榜推送脚本。
优先尝试知乎官方接口；若受限，自动降级到公开聚合源。
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

OFFICIAL_API = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
FALLBACK_API = "https://hot.baiwumm.com/api/zhihu"
TIMEOUT_SECONDS = 20
MAX_ITEMS = max(1, int(os.getenv("ZHIHU_MAX_ITEMS", "20")))


def log(msg: str) -> None:
    """Write runtime details to stderr so user-facing push stays clean."""
    print(msg, file=sys.stderr)


def build_env() -> Dict[str, str]:
    """Use local proxy by default when upstream proxy vars are not set."""
    env = os.environ.copy()
    env.setdefault("http_proxy", "http://127.0.0.1:7890")
    env.setdefault("https_proxy", "http://127.0.0.1:7890")
    return env


def request_json(url: str, extra_headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[Any], Optional[str]]:
    """Fetch and decode JSON from URL, returning (data, error_message)."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    if extra_headers:
        headers.update(extra_headers)

    cmd = ["curl", "-sL", "--max-time", str(TIMEOUT_SECONDS)]
    for key, value in headers.items():
        cmd.extend(["-H", f"{key}: {value}"])
    cmd.append(url)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS + 5, env=build_env())
    if result.returncode != 0:
        return None, f"curl returncode={result.returncode}"

    if not result.stdout:
        return None, "empty response"

    try:
        return json.loads(result.stdout), None
    except json.JSONDecodeError as exc:
        return None, f"json decode error: {exc}"


def extract_hot_value(raw: Any) -> Optional[int]:
    """Extract numeric hot value from int/string fields."""
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw)
    if isinstance(raw, str):
        digits = re.findall(r"\d+", raw.replace(",", ""))
        if digits:
            return int(digits[0])
    return None


def format_hot(hot: Optional[int]) -> str:
    if hot is None:
        return ""
    if hot >= 100000000:
        return f"{hot / 100000000:.2f}亿"
    if hot >= 10000:
        return f"{hot / 10000:.1f}万"
    return str(hot)


def parse_official(data: Any) -> List[Dict[str, Any]]:
    """Parse official zhihu API payload."""
    if not isinstance(data, dict):
        return []

    error = data.get("error")
    if isinstance(error, dict):
        log(f"官方接口受限: {error.get('name')} - {error.get('message')}")
        return []

    items = data.get("data")
    if not isinstance(items, list):
        return []

    parsed: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        target = item.get("target") if isinstance(item.get("target"), dict) else {}
        title = str(target.get("title", "")).strip()
        qid = target.get("id")
        url = ""
        if qid:
            url = f"https://www.zhihu.com/question/{qid}"
        else:
            url = str(target.get("url") or "").strip()

        if not title or not url:
            continue

        hot_raw = item.get("detail_text")
        if not hot_raw and isinstance(item.get("metrics_area"), dict):
            hot_raw = item["metrics_area"].get("text")

        parsed.append(
            {
                "title": title,
                "url": url,
                "hot": extract_hot_value(hot_raw),
                "source": "official",
            }
        )

    return parsed


def parse_fallback(data: Any) -> List[Dict[str, Any]]:
    """Parse backup hotlist API payload."""
    if not isinstance(data, dict):
        return []

    items = data.get("data")
    if not isinstance(items, list):
        return []

    parsed: List[Dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title") or "").strip()
        url = str(item.get("url") or item.get("mobileUrl") or "").strip()
        if not title or not url:
            continue

        parsed.append(
            {
                "title": title,
                "url": url,
                "hot": extract_hot_value(item.get("hot")),
                "source": "fallback",
            }
        )

    return parsed


def default_fallback_items() -> List[Dict[str, Any]]:
    """Last-resort static items to avoid empty pushes."""
    return [
        {"title": "如何看待 2026 年 AI Agent 的落地趋势？", "url": "https://www.zhihu.com/search?q=AI%20Agent", "hot": None, "source": "static"},
        {"title": "哪些编程习惯能长期提升代码质量？", "url": "https://www.zhihu.com/search?q=代码质量", "hot": None, "source": "static"},
        {"title": "长期熬夜会带来哪些不可逆影响？", "url": "https://www.zhihu.com/search?q=熬夜", "hot": None, "source": "static"},
        {"title": "你最常用的效率工具有哪些？", "url": "https://www.zhihu.com/search?q=效率工具", "hot": None, "source": "static"},
        {"title": "新手如何系统提升技术深度？", "url": "https://www.zhihu.com/search?q=技术成长", "hot": None, "source": "static"},
    ]


def fetch_zhihu_hot() -> Tuple[List[Dict[str, Any]], str]:
    """Fetch from source chain: official -> fallback -> static."""
    data, err = request_json(OFFICIAL_API, {"Referer": "https://www.zhihu.com/hot"})
    if not err:
        items = parse_official(data)
        if items:
            log(f"官方接口成功，获取 {len(items)} 条")
            return items, "知乎官方"
    else:
        log(f"官方接口失败: {err}")

    data, err = request_json(FALLBACK_API)
    if not err:
        items = parse_fallback(data)
        if items:
            log(f"备用接口成功，获取 {len(items)} 条")
            return items, "聚合热榜"
    else:
        log(f"备用接口失败: {err}")

    log("所有在线源失败，使用静态兜底数据")
    return default_fallback_items(), "静态兜底"


def build_message(items: List[Dict[str, Any]], source_name: str) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    picked = items[:MAX_ITEMS]

    message_lines = [
        f"📚 知乎热榜 | {now}",
        "=" * 40,
        f"数据源：{source_name} | 共 {len(items)} 条，推送前 {len(picked)} 条",
    ]

    for idx, item in enumerate(picked, 1):
        title = item.get("title", "")
        url = item.get("url", "")
        hot = format_hot(item.get("hot"))

        message_lines.append(f"\n{idx}. {title}")
        if hot:
            message_lines.append(f"   🔥 热度：{hot}")
        message_lines.append(f"   🔗 {url}")

    message_lines.append("\n💡 想看某条的详细解读，我可以继续深挖～")
    return "\n".join(message_lines)


def main() -> None:
    hot_items, source_name = fetch_zhihu_hot()
    message = build_message(hot_items, source_name)

    # stdout 会被 backup-cron.sh 捕获并发送到飞书
    print(message)

    with open("/tmp/bowlwanpi-zhihu-hot.txt", "w", encoding="utf-8") as f:
        f.write(message)


if __name__ == "__main__":
    main()
