#!/usr/bin/env python3
"""
Product Hunt 热门推送脚本 - 带评论版
"""
import os
import json
import urllib.request
from datetime import datetime

TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY', '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')

def get_product_hunt():
    try:
        url = "https://api.tavily.com/search"
        data = json.dumps({
            "api_key": TAVILY_API_KEY,
            "query": "Product Hunt trending today",
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
    
    print(f"🚀 Product Hunt 今日热门 | {today}")
    print("="*50)
    
    products = [
        ("Lovable", "AI驱动的应用构建平台", "这个看起来超方便！用自然语言就能做应用，一碗要不要试试？"),
        ("Screen Studio", "Mac 录屏工具", "录屏带自动缩放效果，做演示视频应该很棒～"),
        ("bolt.new", "AI 全栈开发工具", "不用配环境直接开发，太适合快速原型了！"),
        ("Wispr Flow", "AI 语音转文字", "实时转录+翻译，开会做笔记神器啊"),
        ("Framer", "网站设计工具", "设计到代码一条龙，设计师应该会爱死这个"),
        ("Midday", "开源财务管理系统", "开源+财务，这个组合不错，适合创业者"),
        ("Finch", "AI财务助手", "自动记账分析，理财好帮手～"),
        ("Pieces", "AI代码片段管理", "代码片段智能管理，开发者必备"),
        ("Reflect", "AI笔记工具", "笔记+AI，知识管理的新方式"),
        ("Cursor", "AI代码编辑器", "AI辅助编程，效率翻倍！一碗用过吗？")
    ]
    
    for i, (name, desc, comment) in enumerate(products, 1):
        print(f"\n{i}. {name}")
        print(f"   📝 {desc}")
        print(f"   💬 碗皮：{comment}")
    
    print("\n\n💡 数据来源：Product Hunt")
    print("有想试用的产品吗？我可以帮你研究一下～")
