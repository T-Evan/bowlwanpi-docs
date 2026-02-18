#!/usr/bin/env python3
"""GitHub 监控推送脚本（版本更新 + 本周新爆发项目）。"""

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

REPOS = [
    ("openclaw/openclaw", "OpenClaw"),
    ("code-yeongyu/oh-my-opencode", "Oh My OpenCode"),
    ("anomalyco/opencode", "OpenCode 桌面版"),
    ("NevaMind-AI/memU", "memU 记忆系统"),
]

CACHE_FILE = "/root/.openclaw/workspace/memory/github-release-cache.json"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def gh_request(url: str):
    headers = {
        "User-Agent": "BowlWanpi-GitHub-Monitor",
        "Accept": "application/vnd.github+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def get_latest_release(repo):
    try:
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        data = gh_request(url)
        body = data.get("body", "")

        changes = []
        for line in body.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* ") or line.startswith("###"):
                clean = line.replace("- ", "").replace("* ", "").replace("### ", "").strip()
                if clean:
                    changes.append(clean)

        # 去重并保留原顺序
        deduped = []
        seen = set()
        for item in changes:
            if item in seen:
                continue
            seen.add(item)
            deduped.append(item)

        return {
            "version": data.get("tag_name", "unknown"),
            "changes": deduped if deduped else ["暂无详细更新内容"],
            "published": (data.get("published_at") or "")[:10],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception:
        return None


def fmt_num(n: int) -> str:
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def fetch_weekly_breakouts(limit=5):
    now = datetime.now(timezone.utc)
    pushed_since = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    created_since = (now - timedelta(days=120)).strftime("%Y-%m-%d")

    queries = [
        f"(ai OR llm OR agent OR rag OR diffusion) in:name,description pushed:>={pushed_since} created:>={created_since} stars:>=80",
        f"topic:generative-ai pushed:>={pushed_since} created:>={created_since} stars:>=80",
        f"topic:llm pushed:>={pushed_since} created:>={created_since} stars:>=80",
    ]

    merged = {}
    for q in queries:
        params = urllib.parse.urlencode(
            {
                "q": q,
                "sort": "stars",
                "order": "desc",
                "per_page": 30,
            }
        )
        url = f"https://api.github.com/search/repositories?{params}"
        try:
            data = gh_request(url)
            for item in data.get("items", []):
                full_name = item.get("full_name")
                if not full_name:
                    continue
                if full_name not in merged:
                    merged[full_name] = item
        except Exception:
            continue

    repos = sorted(merged.values(), key=lambda x: x.get("stargazers_count", 0), reverse=True)

    output = []
    for r in repos:
        full_name = r.get("full_name", "")
        # 排除过于成熟的超级项目，尽量保留“新爆发”
        if full_name in {"openclaw/openclaw", "langchain-ai/langchain", "n8n-io/n8n", "Significant-Gravitas/AutoGPT"}:
            continue

        desc = (r.get("description") or "暂无简介").strip()
        if len(desc) > 120:
            desc = desc[:117] + "..."

        stars = r.get("stargazers_count", 0)
        forks = r.get("forks_count", 0)
        lang = r.get("language") or "N/A"
        html = r.get("html_url")

        # 简短点评模板
        if stars >= 50000:
            comment = "热度已经破圈，值得重点跟踪。"
        elif stars >= 10000:
            comment = "增长势头很猛，适合尽快试用评估。"
        else:
            comment = "还在快速爬坡，建议先收藏观察。"

        output.append(
            {
                "name": full_name,
                "url": html,
                "stars": stars,
                "forks": forks,
                "language": lang,
                "description": desc,
                "comment": comment,
            }
        )

        if len(output) >= limit:
            break

    return output


def print_release_snapshot(cache):
    print("🐙 GitHub 版本快照（用于稳定追踪）")
    print("-")
    for repo, name in REPOS:
        release = get_latest_release(repo)
        if not release:
            release = cache.get(repo)
        if not release:
            print(f"• {name}: 暂无数据")
            continue
        cache[repo] = release
        print(f"• {name}: {release.get('version', 'unknown')}（{release.get('published', 'unknown')}）")
    print("")


def print_weekly_breakouts():
    projects = fetch_weekly_breakouts(limit=5)
    print("🔥 本周新爆发 AI 项目（精选 5 个）")
    print("")

    if not projects:
        print("本周暂未检索到符合条件的新爆发项目，建议下轮再看～")
        return

    for idx, p in enumerate(projects, 1):
        print(f"{idx}. {p['name']}")
        print(f"   链接：{p['url']}")
        print(f"   数据：⭐ {fmt_num(p['stars'])} · 🍴 {fmt_num(p['forks'])} · {p['language']}")
        print(f"   简介：{p['description']}")
        print(f"   碗皮评价：{p['comment']}")
        print("")


if __name__ == "__main__":
    cache = load_cache()

    print_release_snapshot(cache)
    print_weekly_breakouts()

    save_cache(cache)

    print("⏰ 每6小时自动更新")
