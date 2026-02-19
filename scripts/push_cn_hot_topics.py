#!/usr/bin/env python3
"""
中文热榜推送 - 详细版
包含摘要描述和碗皮点评
"""

from __future__ import annotations

import datetime as dt
import json
import os
import urllib.error
import urllib.request
import random

API_BASE = os.environ.get("DAILY_HOT_API_URL", "http://localhost:6688")
SOURCES = [
    ("weibo", "微博热搜", "🔥"),
    ("zhihu", "知乎热榜", "💡"),
    ("bilibili", "B站热门", "📺"),
]

# 碗皮评论模板
WANPI_COMMENTS = {
    "weibo": [
        "这个话题有点意思～",
        "又上热搜了，看来大家很关注啊",
        "吃瓜吃瓜 🍉",
        "这波热度可以的",
        "网友讨论挺激烈的",
        "有点好奇后续发展",
        "这个我也有点感触",
        "哈哈，有点意思",
    ],
    "zhihu": [
        "这个问题挺有深度的",
        "知乎上的讨论质量通常不错",
        "值得思考一下",
        "这个观点有意思",
        "我也想听听大家的看法",
        "这个问题确实值得关注",
        "长回答预警 📖",
        "可以去看看高赞回答",
    ],
    "bilibili": [
        "B站用户整活有一手的",
        "这个播放量很顶啊",
        "弹幕一定很有趣",
        "我去看看是什么内容",
        "这个标题就很有吸引力",
        "B站热门越来越多元了",
        "看来挺受欢迎的",
        "这个我也想看看",
    ],
}


def fetch_source(path: str) -> dict:
    url = f"{API_BASE.rstrip('/')}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "BowlWanpi-CNHot/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def format_number(num) -> str:
    """格式化数字"""
    try:
        n = int(num)
        if n >= 100000000:
            return f"{n/100000000:.1f}亿"
        elif n >= 10000:
            return f"{n/10000:.0f}万"
        return str(n)
    except:
        return str(num)


def normalize_items(payload: dict, source: str) -> list[dict]:
    data = payload.get("data") or payload.get("list") or []
    out = []
    for i, item in enumerate(data[:5], start=1):
        if not isinstance(item, dict):
            continue
        
        title = str(item.get("title") or item.get("name") or item.get("word") or "").strip()
        if not title:
            continue
        
        # 获取描述
        desc = str(item.get("desc") or "").strip()
        # 微博的 desc 通常是话题标签重复，过滤掉
        if source == "weibo" and (desc == title or desc.startswith("#")):
            desc = ""
        
        hot = item.get("hot") or item.get("score") or item.get("heat") or "-"
        url = str(item.get("url") or item.get("link") or "").strip()
        
        # 生成碗皮评论
        comment = random.choice(WANPI_COMMENTS.get(source, ["值得关注～"]))
        
        out.append({
            "rank": i,
            "title": title,
            "desc": desc,
            "hot": hot,
            "url": url,
            "comment": comment,
        })
    return out


def main() -> int:
    bj_now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8)))
    lines = [
        f"🔥 中文平台热榜速览 | {bj_now:%m月%d日 %H:%M}（北京时间）",
        "",
        "以下是今日中文平台热门话题精选，带碗皮简评～",
        "",
    ]

    any_ok = False
    for key, label, emoji in SOURCES:
        try:
            payload = fetch_source(key)
            items = normalize_items(payload, key)
            if not items:
                lines.append(f"{emoji} 【{label}】暂无可用数据")
                lines.append("")
                continue
            
            any_ok = True
            lines.append(f"{emoji} 【{label}】")
            lines.append("")
            
            for it in items:
                # 标题 + 热度
                hot_str = format_number(it["hot"]) if it["hot"] != "-" else ""
                if hot_str:
                    lines.append(f"{it['rank']}. **{it['title']}** （热度: {hot_str}）")
                else:
                    lines.append(f"{it['rank']}. **{it['title']}**")
                
                # 描述（如果有）
                if it["desc"] and len(it["desc"]) > 5:
                    # 截断过长的描述
                    desc = it["desc"][:80] + "..." if len(it["desc"]) > 80 else it["desc"]
                    lines.append(f"   📝 {desc}")
                
                # 碗皮评论
                lines.append(f"   🥣 {it['comment']}")
                
                # 链接
                if it["url"]:
                    lines.append(f"   🔗 {it['url']}")
                
                lines.append("")
            
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            lines.append(f"{emoji} 【{label}】抓取失败: {str(e)[:30]}")
            lines.append("")

    if not any_ok:
        print("NO_REPLY")
        return 0

    lines.append("---")
    lines.append("💡 这是中文平台专栏，和 GitHub / X / 技术深度分开发送，避免信息过载～")
    lines.append("⏰ 每6小时更新一次")
    
    print("\n".join(lines).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
