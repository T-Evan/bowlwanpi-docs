#!/usr/bin/env python3
"""
Tavily MCP SSE 客户端
连接 Tavily 官方 MCP 服务
"""
import json
import httpx
from typing import Any, Dict, List

TAVILY_MCP_URL = "https://mcp.tavily.com/mcp/?tavilyApiKey=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"


class TavilyMCPClient:
    """Tavily MCP 客户端 (SSE 模式)"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or "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"
        self.base_url = "https://mcp.tavily.com"
        self.mcp_endpoint = f"{self.base_url}/mcp/?tavilyApiKey={self.api_key}"
        self.tools = []
    
    async def list_tools(self) -> List[Dict]:
        """获取可用工具列表"""
        # 这里应该通过 MCP 协议获取
        # Tavily MCP 提供的工具通常包括:
        # - tavily_search: 搜索网页
        # - tavily_extract: 提取网页内容
        # - tavily_research: 深度研究
        return [
            {
                "name": "tavily_search",
                "description": "Search the web using Tavily's API",
                "parameters": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "default": 5},
                    "search_depth": {"type": "string", "default": "basic"}
                }
            }
        ]
    
    async def search(self, query: str, max_results: int = 5, **kwargs) -> Dict[str, Any]:
        """
        使用 Tavily MCP 搜索
        
        由于 MCP SSE 连接较复杂，这里直接调用 Tavily REST API
        """
        url = "https://api.tavily.com/search"
        
        payload = {
            "query": query,
            "max_results": max_results,
            "api_key": self.api_key,
            **kwargs
        }
        
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()


# 同步调用函数
def tavily_search(query: str, max_results: int = 5, **kwargs) -> Dict[str, Any]:
    """同步搜索 Tavily"""
    import asyncio
    
    async def _search():
        client = TavilyMCPClient()
        return await client.search(query, max_results, **kwargs)
    
    return asyncio.run(_search())


if __name__ == "__main__":
    # 测试
    import asyncio
    
    async def test():
        print("🔍 测试 Tavily MCP 连接...")
        
        client = TavilyMCPClient()
        
        print("\n📋 可用工具:")
        tools = await client.list_tools()
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        print("\n🔎 测试搜索...")
        try:
            result = await client.search("Python programming", max_results=3)
            print(f"✅ 搜索成功！找到 {len(result.get('results', []))} 个结果")
            for i, item in enumerate(result.get('results', [])[:3], 1):
                print(f"  {i}. {item.get('title', '无标题')}")
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
    
    asyncio.run(test())
