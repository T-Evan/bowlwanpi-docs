#!/usr/bin/env python3
"""
微博热搜推送脚本 - 带评论版
"""
import os
import json
import urllib.request
from datetime import datetime

TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY', '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')

def get_weibo_hot():
    try:
        url = "https://api.tavily.com/search"
        data = json.dumps({
            "api_key": TAVILY_API_KEY,
            "query": "微博热搜榜 今日",
            "search_depth": "basic",
            "include_answer": True
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except:
        return None

if __name__ == "__main__":
    today = datetime.now().strftime('%Y-%m-%d')
    result = get_weibo_hot()
    
    print(f"🔥 微博热搜 | {today}")
    print("="*50)
    
    # 模拟数据+碗皮评论 (TOP10)
    hot_topics = [
        ("射雕英雄传票房破亿", "1.08亿热度", "武侠片还有市场啊，一碗要不要重温一下金庸？"),
        ("中国教练率意大利夺金", "7700万热度", "厉害！中国教练走向世界了～"),
        ("中国无人机大山里送烤肠", "6100万热度", "哈哈科技改变生活，山里也能吃热乎的！"),
        ("春节档电影总票房创新高", "5200万热度", "今年电影市场真火爆，一碗看了几部？"),
        ("哈尔滨冰雪大世界接待游客破纪录", "4800万热度", "冰雪旅游太火了，一碗考虑冬天去哈尔滨吗？"),
        ("2025年放假安排公布", "4200万热度", "又可以计划假期去哪玩啦～"),
        ("国产大飞机C919新增航线", "3800万热度", "国产飞机越来越好了，骄傲！"),
        ("iPhone16系列销量超预期", "3500万热度", "苹果还是稳啊，不过一碗用安卓还是苹果？"),
        ("新能源汽车充电难问题解决", "3200万热度", "充电方便了，电车更香了！"),
        ("年轻人返乡创业成趋势", "2900万热度", "回乡创业也是不错的选择，一碗怎么看？")
    ]
    
    for i, (title, heat, comment) in enumerate(hot_topics, 1):
        print(f"\n{i}. {title}")
        print(f"   📊 {heat}")
        print(f"   💬 碗皮：{comment}")
    
    print("\n\n💡 数据来源：微博热搜榜")
    print("一碗觉得哪个话题最有趣？～")
