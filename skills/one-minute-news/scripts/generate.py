#!/usr/bin/env python3
"""
一分钟新闻 - 获取国外新闻并用 AI 翻译成中文
"""

import json
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import os
import re

# 加载 .env 文件
def load_env():
    env_file = Path('/root/.openclaw/workspace/skills/tavily-search/.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env()


def ai_translate_titles(titles: list) -> list:
    """使用 AI 翻译标题"""
    if not titles:
        return titles
    
    # 构建提示
    prompt = "请将以下英文新闻标题翻译成流畅自然的中文新闻标题。要求：\n"
    prompt += "1. 符合中文新闻阅读习惯\n"
    prompt += "2. 保留关键专有名词（公司名、人名）\n"
    prompt += "3. 简洁明了，控制在30字以内\n"
    prompt += "4. 直接返回翻译结果，每行一个，不要解释\n\n"
    
    for i, title in enumerate(titles, 1):
        prompt += f"{i}. {title}\n"
    
    try:
        # 调用 Kimi 模型进行翻译
        # 使用 OpenClaw 的模型调用方式
        result = subprocess.run(
            ['python3', '-c', f'''
import os
import json
import urllib.request

api_key = os.environ.get("KIMI_API_KEY", "")
if not api_key:
    # 如果没有 API key，返回原文
    titles = {repr(titles)}
    for t in titles:
        print(t)
    exit(0)

messages = [
    {{"role": "system", "content": "你是一个专业的新闻翻译助手，将英文新闻标题翻译成流畅的中文。"}},
    {{"role": "user", "content": """{prompt}"""}}
]

req = urllib.request.Request(
    "https://api.moonshot.cn/v1/chat/completions",
    headers={{
        "Content-Type": "application/json",
        "Authorization": f"Bearer {{api_key}}"
    }},
    data=json.dumps({{
        "model": "kimi-k2.5",
        "messages": messages,
        "temperature": 0.3
    }}).encode()
)

with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read())
    content = data["choices"][0]["message"]["content"]
    # 提取翻译结果
    for line in content.strip().split("\\n"):
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith("- ") or line.startswith("• ")):
            # 移除编号
            cleaned = line.lstrip("1234567890.-• ").strip()
            if cleaned:
                print(cleaned)
'''],
            capture_output=True,
            text=True,
            timeout=45,
            env={**os.environ, 'KIMI_API_KEY': os.environ.get('KIMI_API_KEY', '')}
        )
        
        if result.returncode == 0:
            translated = result.stdout.strip().split('\n')
            # 确保数量一致
            if len(translated) >= len(titles):
                return translated[:len(titles)]
            else:
                # 补齐
                return translated + titles[len(translated):]
        else:
            print(f"AI 翻译错误: {result.stderr}", file=sys.stderr)
    except Exception as e:
        print(f"AI 翻译失败: {e}", file=sys.stderr)
    
    # 失败返回原文
    return titles


def tavily_search(query: str, topic: str = "general", days: int = 1, max_results: int = 5):
    """使用 Tavily Node.js 脚本搜索"""
    try:
        cmd = [
            'node', '/root/.openclaw/workspace/skills/tavily-search/scripts/search.mjs',
            query,
            '-n', str(max_results),
            '--topic', topic
        ]
        if topic == 'news' and days > 0:
            cmd.extend(['--days', str(days)])
        
        env = os.environ.copy()
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd='/root/.openclaw/workspace/skills/tavily-search',
            env=env
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            items = []
            current_item = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('- **') and '**' in line[4:]:
                    title = line[4:].split('**')[0]
                    current_item = {"title": title, "url": "", "original": title}
                elif line.startswith('http') and current_item:
                    current_item["url"] = line
                    items.append(current_item)
                    current_item = None
            
            return items
        else:
            print(f"搜索错误: {result.stderr}", file=sys.stderr)
            return []
    except Exception as e:
        print(f"搜索失败: {e}", file=sys.stderr)
        return []


def fetch_and_translate_news(category: str, queries: list, max_items: int = 3) -> list:
    """获取新闻并 AI 翻译"""
    all_items = []
    for q in queries:
        items = tavily_search(q, topic="news", days=1, max_results=max_items)
        all_items.extend(items)
    
    # 去重
    seen = set()
    unique = []
    for item in all_items:
        if item["original"] not in seen:
            seen.add(item["original"])
            unique.append(item)
    
    unique = unique[:max_items]
    
    # AI 翻译
    if unique:
        titles = [item["original"] for item in unique]
        translated = ai_translate_titles(titles)
        for i, item in enumerate(unique):
            if i < len(translated):
                item["title"] = translated[i]
    
    return unique


def generate_one_minute_news():
    """生成一分钟新闻"""
    today = datetime.now().strftime("%Y-%m-%d")
    bj_time = datetime.now().strftime("%H:%M")
    
    # 获取并翻译新闻
    tech_items = fetch_and_translate_news("tech", [
        "tech news AI OpenAI Apple Nvidia today",
        "tech news Google Microsoft Meta today",
    ], 3)
    
    finance_items = fetch_and_translate_news("finance", [
        "stock market news Dow Nasdaq Fed today",
        "finance news Bitcoin crypto today",
    ], 2)
    
    general_items = fetch_and_translate_news("general", [
        "world news Trump US today",
        "world news EU Russia Ukraine today",
    ], 2)
    
    news = {
        "date": today,
        "time": bj_time,
        "source": "国际媒体聚合（AI翻译）",
        "categories": {
            "tech": {
                "name": "🚀 科技",
                "items": tech_items if tech_items else [
                    {"title": "实时科技新闻获取中..."}
                ]
            },
            "finance": {
                "name": "💰 财经",
                "items": finance_items if finance_items else [
                    {"title": "实时财经新闻获取中..."}
                ]
            },
            "general": {
                "name": "🌍 国际",
                "items": general_items if general_items else [
                    {"title": "实时国际新闻获取中..."}
                ]
            }
        }
    }
    
    return news


def format_news(news_data: dict) -> str:
    """格式化为易读文本"""
    lines = []
    lines.append(f"📰 一分钟新闻 | {news_data['date']} {news_data.get('time', '')}")
    lines.append(f"📡 来源: {news_data.get('source', '国际媒体')}")
    lines.append("")
    
    total_items = 0
    for cat_key in ["tech", "finance", "general"]:
        cat_data = news_data.get("categories", {}).get(cat_key)
        if not cat_data or not cat_data.get("items"):
            continue
        
        lines.append(f"{cat_data['name']}")
        for i, item in enumerate(cat_data.get("items", []), 1):
            title = item.get('title', '')
            # 截断过长标题
            if len(title) > 70:
                title = title[:67] + "..."
            lines.append(f"  {i}. {title}")
            total_items += 1
        lines.append("")
    
    if total_items == 0:
        lines.append("⚠️ 新闻获取失败，请稍后重试...")
    else:
        lines.append(f"⏱️ 共 {total_items} 条快讯，阅读时间约 1 分钟")
        lines.append("📝 注：内容由 AI 翻译，原文链接可点击查看")
    
    return "\n".join(lines)


def main():
    """主函数"""
    news_data = generate_one_minute_news()
    
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
    
    print(text_output)
    return text_output


if __name__ == "__main__":
    main()
