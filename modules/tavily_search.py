#!/usr/bin/env python3
"""
Tavily Search Skill for BowlWanpi
使用 Tavily 的 LLM 优化搜索 API
"""
import os
import json
import httpx
from typing import Optional, List, Dict, Any

# Tavily API 配置
TAVILY_API_BASE = "https://api.tavily.com"
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")


def search(
    query: str,
    max_results: int = 5,
    search_depth: str = "advanced",
    topic: str = "general",
    time_range: Optional[str] = None,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    include_answer: bool = False,
    include_raw_content: bool = False,
    include_images: bool = False,
    chunks_per_source: int = 3
) -> Dict[str, Any]:
    """
    使用 Tavily 搜索网页
    
    Args:
        query: 搜索查询（建议少于400字符）
        max_results: 最大结果数 (0-20)
        search_depth: 搜索深度 (ultra-fast/fast/basic/advanced)
        topic: 主题 (general/news/finance)
        time_range: 时间范围 (day/week/month/year)
        include_domains: 包含的域名列表
        exclude_domains: 排除的域名列表
        include_answer: 是否包含 AI 生成的答案
        include_raw_content: 是否包含完整页面内容
        include_images: 是否包含图片结果
        chunks_per_source: 每个来源的片段数
    
    Returns:
        搜索结果字典
    
    示例:
        result = search("Python async patterns", max_results=10)
        for item in result['results']:
            print(f"{item['title']}: {item['url']}")
    """
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY 环境变量未设置")
    
    url = f"{TAVILY_API_BASE}/search"
    
    payload = {
        "query": query,
        "max_results": max_results,
        "search_depth": search_depth,
        "topic": topic,
        "chunks_per_source": chunks_per_source,
        "include_answer": include_answer,
        "include_raw_content": include_raw_content,
        "include_images": include_images
    }
    
    # 添加可选参数
    if time_range:
        payload["time_range"] = time_range
    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains
    
    headers = {
        "Authorization": f"Bearer {TAVILY_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # 直接访问（不通过代理）
        with httpx.Client(timeout=30) as client:
            response = client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "query": query}


def search_news(
    query: str,
    time_range: str = "day",
    max_results: int = 10
) -> Dict[str, Any]:
    """
    搜索新闻
    
    示例:
        result = search_news("AI 新闻", time_range="week")
    """
    return search(
        query=query,
        max_results=max_results,
        topic="news",
        time_range=time_range,
        search_depth="advanced"
    )


def search_finance(
    query: str,
    max_results: int = 10
) -> Dict[str, Any]:
    """
    搜索财经信息
    
    示例:
        result = search_finance("AAPL earnings Q4 2024")
    """
    return search(
        query=query,
        max_results=max_results,
        topic="finance",
        search_depth="advanced"
    )


def format_search_results(result: Dict[str, Any]) -> str:
    """
    格式化搜索结果为可读文本
    
    Args:
        result: search() 返回的结果
    
    Returns:
        格式化的文本
    """
    if "error" in result:
        return f"❌ 搜索失败: {result['error']}"
    
    query = result.get('query', '')
    results = result.get('results', [])
    answer = result.get('answer', '')
    
    lines = [f"🔍 **Tavily 搜索结果**: {query}\n"]
    
    # AI 生成的答案
    if answer:
        lines.append(f"💡 **AI 回答**:\n{answer}\n")
    
    # 搜索结果
    lines.append(f"📚 **找到 {len(results)} 个结果**:\n")
    
    for i, item in enumerate(results, 1):
        title = item.get('title', '无标题')
        url = item.get('url', '')
        content = item.get('content', '')
        score = item.get('score', 0)
        
        lines.append(f"{i}. **{title}** (相关度: {score:.2f})")
        lines.append(f"   🔗 {url}")
        if content:
            # 截取前200字符
            content_preview = content[:200].replace('\n', ' ')
            lines.append(f"   📝 {content_preview}...")
        lines.append("")
    
    return "\n".join(lines)


# 便捷函数
def quick_search(query: str) -> str:
    """快速搜索并返回格式化结果"""
    result = search(query)
    return format_search_results(result)


if __name__ == "__main__":
    # 测试
    if not TAVILY_API_KEY:
        print("⚠️ 请设置 TAVILY_API_KEY 环境变量")
        print("获取 API Key: https://tavily.com")
    else:
        print("🔍 测试 Tavily 搜索...")
        result = search("Python async best practices", max_results=3)
        print(format_search_results(result))
