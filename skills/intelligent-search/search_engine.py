#!/usr/bin/env python3
"""
智能搜索聚合器 - 统一搜索接口
支持中英文自动识别、主备切换、高可用搜索
"""

import json
import os
import sys
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/tencent-search')

from search_client import search_tencent_web


class SearchProvider(Enum):
    """搜索提供商"""
    TENCENT_WSA = "tencent_wsa"      # 腾讯云 WSA - 中文首选
    TAVILY = "tavily"                 # Tavily - 英文/引用首选
    FALLBACK = "fallback"             # 备用


@dataclass
class SearchResult:
    """统一搜索结果格式"""
    title: str
    content: str
    url: str
    source: str
    provider: str
    score: float = 0.0
    date: str = ""
    language: str = ""


class LanguageDetector:
    """语言检测器"""
    
    @staticmethod
    def detect(text: str) -> str:
        """
        检测文本语言
        
        Returns:
            'zh' - 中文
            'en' - 英文
            'mixed' - 混合
        """
        # 检测中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 检测英文字符
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        total_chars = chinese_chars + english_chars
        if total_chars == 0:
            return 'en'  # 默认英文
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:
            return 'zh'
        elif chinese_ratio > 0.1:
            return 'mixed'
        else:
            return 'en'


class SearchRouter:
    """搜索路由器 - 决定使用哪个搜索引擎"""
    
    # 中文关键词 - 优先使用腾讯云 WSA
    CHINESE_KEYWORDS = [
        '中文', '中国', '国内', '新闻', '热点', '微博', '知乎', '百度',
        '腾讯', '阿里', '字节', '抖音', '快手', '小红书', 'B站'
    ]
    
    # 英文/技术关键词 - 优先使用 Tavily
    ENGLISH_KEYWORDS = [
        'github', 'stackoverflow', 'documentation', 'api', 'tutorial',
        'paper', 'research', 'arxiv', 'python', 'javascript', 'code'
    ]
    
    @classmethod
    def route(cls, query: str, prefer_citations: bool = False) -> Tuple[SearchProvider, SearchProvider]:
        """
        决定搜索策略
        
        Args:
            query: 搜索词
            prefer_citations: 是否优先需要引用来源
        
        Returns:
            (primary_provider, fallback_provider)
        """
        lang = LanguageDetector.detect(query)
        query_lower = query.lower()
        
        # 检查特定关键词
        has_chinese_keyword = any(kw in query for kw in cls.CHINESE_KEYWORDS)
        has_english_keyword = any(kw in query_lower for kw in cls.ENGLISH_KEYWORDS)
        
        # 决策逻辑
        if prefer_citations:
            # 需要详细引用 -> Tavily 优先
            if lang == 'zh' or has_chinese_keyword:
                return (SearchProvider.TAVILY, SearchProvider.TENCENT_WSA)
            else:
                return (SearchProvider.TAVILY, SearchProvider.TENCENT_WSA)
        
        # 默认策略
        if lang == 'zh' or has_chinese_keyword:
            return (SearchProvider.TENCENT_WSA, SearchProvider.TAVILY)
        elif lang == 'en' or has_english_keyword:
            return (SearchProvider.TAVILY, SearchProvider.TENCENT_WSA)
        else:
            # 混合语言 - 腾讯云 WSA 优先（中文效果好）
            return (SearchProvider.TENCENT_WSA, SearchProvider.TAVILY)


class TavilySearchClient:
    """Tavily MCP 搜索客户端"""
    
    async def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """使用 Tavily MCP 搜索"""
        try:
            # 通过 MCP 调用 Tavily
            import subprocess
            
            # 使用 npx 调用 tavily-mcp
            result = subprocess.run(
                ['npx', '-y', '@tavily/mcp', 'search', query, '--limit', str(num_results)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd='/root/.openclaw/workspace'
            )
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    return data.get('results', [])
                except:
                    return []
            else:
                return [{'error': f'Tavily error: {result.stderr}'}]
                
        except Exception as e:
            return [{'error': f'Tavily search failed: {e}'}]


class IntelligentSearchEngine:
    """智能搜索引擎 - 高可用聚合"""
    
    def __init__(self):
        self.tavily_client = TavilySearchClient()
        self.search_history: List[Dict] = []
    
    async def search(
        self,
        query: str,
        num_results: int = 10,
        prefer_citations: bool = False,
        force_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        智能搜索
        
        Args:
            query: 搜索词
            num_results: 结果数量
            prefer_citations: 是否优先需要引用
            force_provider: 强制指定搜索引擎 ('tencent', 'tavily', None=自动)
        
        Returns:
            {
                'success': bool,
                'query': str,
                'language': str,
                'primary_provider': str,
                'fallback_used': bool,
                'results': List[SearchResult],
                'total_results': int,
                'errors': List[str]
            }
        """
        # 检测语言
        language = LanguageDetector.detect(query)
        
        # 确定搜索策略
        if force_provider == 'tencent':
            primary = SearchProvider.TENCENT_WSA
            fallback = SearchProvider.TAVILY
        elif force_provider == 'tavily':
            primary = SearchProvider.TAVILY
            fallback = SearchProvider.TENCENT_WSA
        else:
            primary, fallback = SearchRouter.route(query, prefer_citations)
        
        errors = []
        all_results = []
        fallback_used = False
        
        # 主搜索
        primary_results = await self._execute_search(primary, query, num_results)
        
        if primary_results and not any('error' in r for r in primary_results):
            all_results = self._normalize_results(primary_results, primary.value)
        else:
            # 主搜索失败，使用备用
            if primary_results and any('error' in r for r in primary_results):
                errors.append(f"Primary ({primary.value}) failed")
            
            fallback_results = await self._execute_search(fallback, query, num_results)
            
            if fallback_results and not any('error' in r for r in fallback_results):
                all_results = self._normalize_results(fallback_results, fallback.value)
                fallback_used = True
            else:
                if fallback_results and any('error' in r for r in fallback_results):
                    errors.append(f"Fallback ({fallback.value}) failed")
                return {
                    'success': False,
                    'query': query,
                    'language': language,
                    'primary_provider': primary.value,
                    'fallback_used': False,
                    'results': [],
                    'total_results': 0,
                    'errors': errors or ['All search providers failed']
                }
        
        # 按分数排序
        all_results.sort(key=lambda x: x.score, reverse=True)
        
        # 记录搜索历史
        self.search_history.append({
            'query': query,
            'language': language,
            'primary': primary.value,
            'fallback_used': fallback_used,
            'result_count': len(all_results)
        })
        
        return {
            'success': True,
            'query': query,
            'language': language,
            'primary_provider': primary.value,
            'fallback_used': fallback_used,
            'results': all_results[:num_results],
            'total_results': len(all_results),
            'errors': errors
        }
    
    async def _execute_search(
        self,
        provider: SearchProvider,
        query: str,
        num_results: int
    ) -> List[Dict]:
        """执行具体搜索"""
        if provider == SearchProvider.TENCENT_WSA:
            return await search_tencent_web(query, num_results)
        elif provider == SearchProvider.TAVILY:
            return await self.tavily_client.search(query, num_results)
        else:
            return [{'error': 'Unknown provider'}]
    
    def _normalize_results(
        self,
        raw_results: List[Dict],
        provider: str
    ) -> List[SearchResult]:
        """标准化搜索结果"""
        normalized = []
        
        for item in raw_results:
            if 'error' in item:
                continue
            
            if provider == 'tencent_wsa':
                normalized.append(SearchResult(
                    title=item.get('title', ''),
                    content=item.get('content', ''),
                    url=item.get('url', ''),
                    source=item.get('site', '腾讯云'),
                    provider=provider,
                    score=float(item.get('score', 0)),
                    date=item.get('date', ''),
                    language='zh'
                ))
            elif provider == 'tavily':
                # Tavily 格式适配
                normalized.append(SearchResult(
                    title=item.get('title', ''),
                    content=item.get('content', item.get('snippet', '')),
                    url=item.get('url', ''),
                    source=item.get('source', 'Tavily'),
                    provider=provider,
                    score=float(item.get('score', 0)),
                    date=item.get('published_date', ''),
                    language='en'
                ))
        
        return normalized
    
    def get_search_stats(self) -> Dict:
        """获取搜索统计"""
        if not self.search_history:
            return {'total_searches': 0}
        
        total = len(self.search_history)
        fallback_count = sum(1 for h in self.search_history if h['fallback_used'])
        
        return {
            'total_searches': total,
            'fallback_usage': fallback_count,
            'fallback_rate': fallback_count / total if total > 0 else 0,
            'recent_queries': [h['query'] for h in self.search_history[-5:]]
        }


# 便捷函数
async def smart_search(
    query: str,
    num_results: int = 10,
    prefer_citations: bool = False,
    force_provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    智能搜索 - 一键调用
    
    自动选择最佳搜索引擎：
    - 中文查询 -> 腾讯云 WSA
    - 英文/需要引用 -> Tavily
    - 失败自动切换备用
    """
    engine = IntelligentSearchEngine()
    return await engine.search(query, num_results, prefer_citations, force_provider)


# 兼容性接口
async def web_search(query: str, num_results: int = 10) -> List[Dict]:
    """
    兼容原 web_search 接口
    
    自动选择最佳搜索引擎
    """
    result = await smart_search(query, num_results)
    
    if result['success']:
        return [
            {
                'title': r.title,
                'content': r.content,
                'url': r.url,
                'source': r.source,
                'provider': r.provider
            }
            for r in result['results']
        ]
    else:
        return [{'error': '; '.join(result['errors'])}]


if __name__ == '__main__':
    async def test():
        print("🔍 智能搜索引擎测试\n")
        
        # 测试中文搜索
        print("=" * 50)
        print("测试 1: 中文搜索")
        print("=" * 50)
        result = await smart_search("人工智能发展", num_results=3)
        print(f"查询: {result['query']}")
        print(f"语言: {result['language']}")
        print(f"主引擎: {result['primary_provider']}")
        print(f"使用备用: {result['fallback_used']}")
        print(f"结果数: {result['total_results']}")
        print()
        
        # 测试英文搜索
        print("=" * 50)
        print("测试 2: 英文搜索")
        print("=" * 50)
        result = await smart_search("Python best practices", num_results=3)
        print(f"查询: {result['query']}")
        print(f"语言: {result['language']}")
        print(f"主引擎: {result['primary_provider']}")
        print(f"使用备用: {result['fallback_used']}")
        print(f"结果数: {result['total_results']}")
        print()
        
        # 测试混合语言
        print("=" * 50)
        print("测试 3: 混合语言")
        print("=" * 50)
        result = await smart_search("OpenClaw 部署教程", num_results=3)
        print(f"查询: {result['query']}")
        print(f"语言: {result['language']}")
        print(f"主引擎: {result['primary_provider']}")
        print(f"使用备用: {result['fallback_used']}")
        print(f"结果数: {result['total_results']}")
        print()
        
        # 统计
        print("=" * 50)
        print("搜索统计")
        print("=" * 50)
        engine = IntelligentSearchEngine()
        # 复制历史记录
        engine.search_history = [
            {'query': 'test', 'fallback_used': False},
            {'query': 'test2', 'fallback_used': True}
        ]
        stats = engine.get_search_stats()
        print(f"总搜索次数: {stats['total_searches']}")
        print(f"备用使用率: {stats['fallback_rate']:.1%}")
    
    asyncio.run(test())
