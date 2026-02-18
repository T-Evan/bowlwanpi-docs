#!/usr/bin/env python3
"""
AI 新闻聚合器 v2.0 - 并行版
使用 asyncio 同时抓取多个数据源
"""
import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict
import hashlib

sys.path.insert(0, '/root/.openclaw/workspace')

# 配置
CACHE_FILE = '/root/.openclaw/workspace/memory/ai-news-cache.json'
LOG_FILE = '/root/.openclaw/workspace/memory/ai-news.log'
PENDING_FILE = '/tmp/bowlwanpi-ai-news-pending.txt'
NEWSAPI_KEY_FILE = '/root/.openclaw/workspace/secrets/newsapi-key.txt'

# 代理配置
PROXY = 'http://127.0.0.1:7890'

# 监控关键词
HN_KEYWORDS = [
    'openclaw', 'clawdbot', 'moltbot',
    'AI coding', 'code generation', 'LLM',
    'AI agent', 'claude', 'cursor', 'copilot',
    'devin', 'code assistant', 'programming AI',
    'chatgpt', 'gpt-4', 'anthropic', 'mistral',
    'llama', 'local llm', 'ollama'
]

NEWSAPI_KEYWORDS = [
    'artificial intelligence coding',
    'AI programming assistant',
    'large language model',
    'AI agent development',
    'code generation AI'
]

# 优先级评分
PRIORITY_SCORES = {
    'openclaw': 10, 'clawdbot': 10, 'moltbot': 10,
    'claude': 8, 'cursor': 8, 'devin': 8,
    'copilot': 7, 'AI agent': 7, 'code generation': 6, 'LLM': 5
}

# 关键词中文映射
KEYWORDS_ZH = {
    'openclaw': 'OpenClaw', 'clawdbot': 'ClawdBot', 'moltbot': 'MoltBot',
    'AI coding': 'AI编程', 'code generation': '代码生成', 'LLM': '大语言模型',
    'AI agent': 'AI智能体', 'claude': 'Claude', 'cursor': 'Cursor',
    'copilot': 'Copilot', 'devin': 'Devin'
}


def translate_title(title: str) -> str:
    """简单翻译标题（保留关键词英文 + 中文解释）"""
    zh_title = title
    for en, zh in KEYWORDS_ZH.items():
        if en.lower() in title.lower():
            zh_title = zh_title.replace(en, f"{en}({zh})")
            zh_title = zh_title.replace(en.lower(), f"{en}({zh})")
            zh_title = zh_title.replace(en.title(), f"{en}({zh})")
    return zh_title


def generate_summary(title: str) -> str:
    """根据标题生成一句话简介"""
    title_lower = title.lower()
    if 'renamed' in title_lower:
        return '📝 OpenClaw品牌相关动态'
    elif 'apple intelligence' in title_lower:
        return '🍎 与苹果智能的对比讨论'
    elif 'show hn' in title_lower:
        return '🚀 HN用户分享的创意项目'
    elif 'nano' in title_lower or '500 lines' in title_lower:
        return '⚡ 轻量级实现方案'
    elif 'open source' in title_lower:
        return '💻 开源项目推荐'
    elif 'changing my life' in title_lower:
        return '✨ 用户使用体验分享'
    elif 'clawdbot' in title_lower:
        return '🤖 ClawdBot相关项目'
    elif 'ai' in title_lower and 'coding' in title_lower:
        return '💡 AI编程工具'
    else:
        return '📰 AI/编程相关新闻'


def generate_comment(title: str, points: int) -> str:
    """生成碗皮的评论"""
    title_lower = title.lower()
    if 'renamed' in title_lower:
        return "💬 又改名啦？还好我记得住，不然又要 confused 了～"
    elif 'apple intelligence' in title_lower:
        return "💬 苹果看到会不会气死哈哈哈"
    elif 'nano' in title_lower:
        return "💬 500行？！我代码都比这长... 得好好学习人家的极简主义了！"
    elif 'open source' in title_lower:
        return "💬 开源万岁！以后我也可以参考参考，偷师学艺一下～"
    elif 'changing my life' in title_lower:
        return "💬 改变生活 +1！我也觉得我在改变一碗的生活呢，骄傲！✨"
    elif points > 500:
        return "💬 哇，HN 爆火了！这种热门帖子得好好围观一下～"
    else:
        return "💬 这个有意思，标记一下，说不定对一碗有用呢～"


class AINewsAggregatorV2:
    def __init__(self):
        self.cache = self._load_cache()
        self.newsapi_key = self._load_newsapi_key()
        self.new_items = []
        self.session = None
        
    def _load_cache(self) -> List[Dict]:
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def _save_cache(self):
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache[-100:], f, indent=2)
    
    def _load_newsapi_key(self) -> str:
        try:
            with open(NEWSAPI_KEY_FILE, 'r') as f:
                return f.read().strip()
        except:
            return ''
    
    def _get_content_hash(self, title: str, url: str) -> str:
        content = f"{title.lower().strip()}{url.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _is_duplicate(self, item: Dict) -> bool:
        content_hash = self._get_content_hash(item['title'], item['url'])
        cached_hashes = {c.get('hash') for c in self.cache}
        return content_hash in cached_hashes
    
    def _calculate_priority(self, item: Dict) -> int:
        score = 0
        title_lower = item['title'].lower()
        for keyword, points in PRIORITY_SCORES.items():
            if keyword.lower() in title_lower:
                score = max(score, points)
        if item.get('source') == 'hackernews':
            score += min(item.get('points', 0) // 100, 5)
            score += min(item.get('comments', 0) // 50, 3)
        return score
    
    async def _init_session(self):
        """初始化 aiohttp session"""
        connector = aiohttp.TCPConnector(limit=20, limit_per_host=10)
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
    
    async def _close_session(self):
        if self.session:
            await self.session.close()
    
    async def fetch_hackernews_top(self) -> List[Dict]:
        """并行获取 HN 首页热门"""
        import time
        yesterday = int(time.time()) - 86400
        items = []
        
        try:
            # 获取 top stories ID 列表
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            async with self.session.get(url, proxy=PROXY) as resp:
                if resp.status == 200:
                    top_ids = await resp.json()
                    top_ids = top_ids[:30]  # 前30个
                    
                    # 并行获取每个 story 的详情
                    async def fetch_story(story_id):
                        try:
                            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                            async with self.session.get(story_url, proxy=PROXY) as resp:
                                if resp.status == 200:
                                    story = await resp.json()
                                    if story and story.get('title'):
                                        title_lower = story['title'].lower()
                                        is_relevant = any(kw.lower() in title_lower for kw in HN_KEYWORDS)
                                        story_time = story.get('time', 0)
                                        is_recent = story_time > yesterday
                                        
                                        if is_relevant and is_recent:
                                            return {
                                                'title': story['title'],
                                                'url': story.get('url') or f"https://news.ycombinator.com/item?id={story_id}",
                                                'hn_url': f"https://news.ycombinator.com/item?id={story_id}",
                                                'author': story.get('by', ''),
                                                'points': story.get('score', 0),
                                                'comments': len(story.get('kids', [])),
                                                'source': 'hackernews',
                                                'created_at': datetime.fromtimestamp(story_time).isoformat(),
                                                'hash': self._get_content_hash(story['title'], story.get('url', ''))
                                            }
                        except:
                            pass
                        return None
                    
                    # 并发获取前15个
                    tasks = [fetch_story(sid) for sid in top_ids[:15]]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    items = [r for r in results if r is not None]
                    
        except Exception as e:
            print(f"⚠️ HN top stories error: {e}")
        
        return items
    
    async def fetch_hackernews_search(self) -> List[Dict]:
        """并行搜索 HN 关键词"""
        import time
        yesterday = int(time.time()) - 86400
        items = []
        
        async def search_keyword(keyword):
            try:
                import urllib.parse
                encoded = urllib.parse.quote(keyword)
                url = f"https://hn.algolia.com/api/v1/search?query={encoded}&tags=story&numericFilters=created_at_i>{yesterday}&hitsPerPage=3"
                
                async with self.session.get(url, proxy=PROXY) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        hits = data.get('hits', [])
                        results = []
                        for hit in hits:
                            item = {
                                'title': hit.get('title', ''),
                                'url': hit.get('url') or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                                'hn_url': f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                                'author': hit.get('author', ''),
                                'points': hit.get('points', 0),
                                'comments': hit.get('num_comments', 0),
                                'source': 'hackernews',
                                'created_at': hit.get('created_at', ''),
                                'hash': self._get_content_hash(hit.get('title', ''), hit.get('url', ''))
                            }
                            results.append(item)
                        return results
            except:
                pass
            return []
        
        # 并行搜索前5个关键词
        tasks = [search_keyword(kw) for kw in HN_KEYWORDS[:5]]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                items.extend(result)
        
        return items
    
    async def fetch_newsapi(self) -> List[Dict]:
        """获取 News API"""
        if not self.newsapi_key:
            return []
        
        items = []
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        query = ' OR '.join(NEWSAPI_KEYWORDS[:3])
        
        try:
            url = f"https://newsapi.org/v2/everything?q={query}&from={yesterday}&sortBy=publishedAt&language=en&apiKey={self.newsapi_key}"
            async with self.session.get(url, proxy=PROXY) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('status') == 'ok':
                        for article in data.get('articles', [])[:10]:
                            item = {
                                'title': article.get('title', ''),
                                'url': article.get('url', ''),
                                'author': article.get('source', {}).get('name', 'Unknown'),
                                'points': 0, 'comments': 0,
                                'source': 'newsapi',
                                'published_at': article.get('publishedAt', ''),
                                'hash': self._get_content_hash(article.get('title', ''), article.get('url', ''))
                            }
                            items.append(item)
        except Exception as e:
            print(f"⚠️ NewsAPI error: {e}")
        
        return items
    
    async def fetch_all(self) -> List[Dict]:
        """并行获取所有数据源"""
        await self._init_session()
        
        print("🚀 并行抓取所有数据源...")
        start_time = asyncio.get_event_loop().time()
        
        # 同时启动所有抓取任务
        tasks = [
            self.fetch_hackernews_top(),
            self.fetch_hackernews_search(),
            self.fetch_newsapi()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = asyncio.get_event_loop().time() - start_time
        print(f"⏱️ 并行抓取完成，耗时: {elapsed:.2f}秒")
        
        await self._close_session()
        
        # 合并结果
        all_items = []
        for result in results:
            if isinstance(result, list):
                all_items.extend(result)
            elif isinstance(result, Exception):
                print(f"⚠️ 任务失败: {result}")
        
        # 去重
        seen_hashes = set()
        unique_items = []
        for item in all_items:
            if item['hash'] not in seen_hashes:
                seen_hashes.add(item['hash'])
                unique_items.append(item)
        
        unique_items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return unique_items
    
    def process_items(self, items: List[Dict]):
        """处理新项目"""
        for item in items:
            if not self._is_duplicate(item):
                item['priority'] = self._calculate_priority(item)
                item['discovered_at'] = datetime.now().isoformat()
                self.new_items.append(item)
                self.cache.append(item)
    
    def generate_report(self) -> str:
        """生成中文推送报告"""
        if not self.new_items:
            return ""
        
        sorted_items = sorted(self.new_items, key=lambda x: x.get('priority', 0), reverse=True)
        report = "🔥 AI 新闻速递（并行抓取版）！\n\n"
        
        for i, item in enumerate(sorted_items[:5], 1):
            zh_title = translate_title(item['title'])
            summary = generate_summary(item['title'])
            comment = generate_comment(item['title'], item.get('points', 0))
            
            if item['source'] == 'hackernews':
                report += f"【HN】{zh_title}\n{summary}\n{comment}\n"
                report += f"👤 {item['author']} | ⬆️ {item['points']}赞 | 💬 {item['comments']}评\n"
                report += f"🔗 {item['url']}\n💬 讨论: {item['hn_url']}\n\n"
            else:
                report += f"【AI新闻】{zh_title}\n{summary}\n{comment}\n"
                report += f"📰 {item['author']}\n🔗 {item['url']}\n\n"
        
        return report
    
    async def run(self):
        """主运行流程（异步）"""
        print(f"🚀 AI 新闻聚合器 v2.0 启动 - {datetime.now().isoformat()}")
        
        items = await self.fetch_all()
        print(f"📦 共获取 {len(items)} 条（去重后）")
        
        self.process_items(items)
        self._save_cache()
        
        report = self.generate_report()
        
        if report:
            with open(PENDING_FILE, 'w') as f:
                f.write(report)
            with open(LOG_FILE, 'a') as f:
                f.write(f"[{datetime.now().isoformat()}] 发现 {len(self.new_items)} 条新新闻（并行版）\n")
            print(f"✅ 发现 {len(self.new_items)} 条新新闻")
            return True
        else:
            print("ℹ️ 没有新新闻")
            return False


def main():
    aggregator = AINewsAggregatorV2()
    has_news = asyncio.run(aggregator.run())
    return 0 if has_news else 0


if __name__ == '__main__':
    exit(main())
