#!/usr/bin/env python3
"""
一分钟新闻 - 使用腾讯云 WSA 搜索真实新闻
"""

import json
import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 添加路径
sys.path.insert(0, '/root/.openclaw/workspace/skills/tencent-search')
from search_client import search_tencent_web

async def fetch_real_news():
    """抓取真实新闻"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    print("📡 正在抓取真实新闻...")
    
    news_data = {
        "date": today,
        "categories": {}
    }
    
    # 科技新闻
    try:
        tech_results = await search_tencent_web("今日科技新闻 AI人工智能", num_results=5)
        if tech_results:
            items = []
            for r in tech_results[:3]:
                content = r.get("content", "")
                # 清理内容，去除HTML标签和多余信息
                content = content.replace("html", "").replace("_", "").strip()
                if len(content) > 80:
                    content = content[:77] + "..."
                items.append({
                    "title": r["title"],
                    "content": content
                })
            news_data["categories"]["tech"] = {
                "name": "🚀 科技",
                "items": items
            }
            print(f"  ✅ 科技: {len(items)}条")
    except Exception as e:
        print(f"  ❌ 科技新闻获取失败: {e}")
    
    # 财经新闻
    try:
        finance_results = await search_tencent_web("今日财经新闻 股市 经济", num_results=5)
        if finance_results:
            items = []
            for r in finance_results[:2]:
                content = r.get("content", "")
                content = content.replace("html", "").replace("_", "").strip()
                if len(content) > 80:
                    content = content[:77] + "..."
                items.append({
                    "title": r["title"],
                    "content": content
                })
            news_data["categories"]["finance"] = {
                "name": "💰 财经",
                "items": items
            }
            print(f"  ✅ 财经: {len(items)}条")
    except Exception as e:
        print(f"  ❌ 财经新闻获取失败: {e}")
    
    # 综合新闻
    try:
        general_results = await search_tencent_web("今日热点新闻", num_results=5)
        if general_results:
            items = []
            for r in general_results[:2]:
                content = r.get("content", "")
                content = content.replace("html", "").replace("_", "").strip()
                if len(content) > 80:
                    content = content[:77] + "..."
                items.append({
                    "title": r["title"],
                    "content": content
                })
            news_data["categories"]["general"] = {
                "name": "🌍 综合",
                "items": items
            }
            print(f"  ✅ 综合: {len(items)}条")
    except Exception as e:
        print(f"  ❌ 综合新闻获取失败: {e}")
    
    return news_data

def format_news(news_data: dict) -> str:
    """格式化为易读文本"""
    lines = []
    lines.append(f"📰 一分钟新闻 | {news_data['date']}")
    lines.append("")
    
    total_items = 0
    
    # 按顺序输出
    for cat_key in ["tech", "finance", "general"]:
        cat_data = news_data.get("categories", {}).get(cat_key)
        if not cat_data or not cat_data.get("items"):
            continue
        
        lines.append(f"{cat_data['name']}")
        for i, item in enumerate(cat_data.get("items", []), 1):
            title = item.get('title', '')
            content = item.get('content', '')
            # 清理标题
            title = title.split("|")[0].strip()
            if len(title) > 60:
                title = title[:57] + "..."
            lines.append(f"  {i}. {title}")
            # 如果有内容摘要，也显示出来
            if content:
                content = content.replace('\n', ' ').strip()
                if len(content) > 80:
                    content = content[:77] + "..."
                lines.append(f"     {content}")
            total_items += 1
        lines.append("")
    
    if total_items == 0:
        lines.append("⚠️ 今天网络有点卡，新闻抓取失败了...")
        lines.append("   等下再试试看～")
    else:
        lines.append(f"⏱️ 共 {total_items} 条快讯")
    
    return "\n".join(lines)

async def main():
    """主函数"""
    news_data = await fetch_real_news()
    
    # 保存到文件
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    today = news_data['date']
    
    # 保存 JSON
    json_file = output_dir / f"news_{today}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(news_data, f, ensure_ascii=False, indent=2)
    
    # 输出文本格式
    text_output = format_news(news_data)
    txt_file = output_dir / f"news_{today}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(text_output)
    
    print("")
    print("=" * 50)
    print(text_output)
    print("=" * 50)
    
    return text_output

if __name__ == "__main__":
    output = asyncio.run(main())
