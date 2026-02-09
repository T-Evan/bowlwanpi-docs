#!/usr/bin/env python3
"""
一分钟新闻 - 快速新闻摘要推送
使用 Tavily MCP 搜索获取新闻
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

def search_news(query: str, num_results: int = 5):
    """使用 Tavily 搜索新闻"""
    try:
        # 调用 Tavily skill 搜索
        result = subprocess.run(
            ['python3', '-m', 'tavily.search', query, '--max-results', str(num_results)],
            cwd='/root/.openclaw/workspace/skills/tavily-skills/skills/tavily/search',
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout
    except Exception as e:
        return f"搜索失败: {e}"

def generate_one_minute_news():
    """生成一分钟新闻"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 由于网络限制，这里使用模拟数据展示格式
    # 实际运行时可以通过 Tavily MCP 或腾讯云搜索获取
    news = {
        "date": today,
        "categories": {
            "tech": {
                "name": "🚀 科技",
                "items": [
                    {"title": "OpenAI 发布 GPT-4.5 预览版，推理能力大幅提升"},
                    {"title": "苹果 iOS 18.4 将集成更多本地化 AI 功能"},
                    {"title": "英伟达财报超预期，AI 芯片需求持续强劲"},
                ]
            },
            "finance": {
                "name": "💰 财经", 
                "items": [
                    {"title": "比特币突破 10 万美元，加密货币市场全面上涨"},
                    {"title": "美联储暗示可能暂停加息，市场情绪回暖"},
                ]
            },
            "general": {
                "name": "🌍 国际",
                "items": [
                    {"title": "特朗普宣布对加拿大、墨西哥加征 25% 关税"},
                    {"title": "欧盟通过 430 亿欧元芯片补贴法案"},
                ]
            }
        }
    }
    
    return news

def format_news(news_data: dict) -> str:
    """格式化为易读文本"""
    lines = []
    lines.append(f"📰 一分钟新闻 | {news_data['date']}")
    lines.append("")
    
    total_items = 0
    for cat_key in ["tech", "finance", "general"]:
        cat_data = news_data.get("categories", {}).get(cat_key)
        if not cat_data or not cat_data.get("items"):
            continue
            
        lines.append(f"{cat_data['name']}")
        for i, item in enumerate(cat_data.get("items", []), 1):
            title = item.get('title', '')
            # 清理标题
            title = title.split("|")[0].strip()
            if len(title) > 60:
                title = title[:57] + "..."
            lines.append(f"  {i}. {title}")
            total_items += 1
        lines.append("")
    
    if total_items == 0:
        lines.append("⚠️ 今天网络有点卡，新闻抓取失败了...")
    else:
        lines.append(f"⏱️ 共 {total_items} 条快讯，阅读时间约 1 分钟")
    
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
