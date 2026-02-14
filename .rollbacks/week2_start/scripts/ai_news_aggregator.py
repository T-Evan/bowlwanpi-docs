#!/usr/bin/env python3
"""
AI 新闻聚合器 - Hacker News + News API
每小时收集 AI/Coding 相关新闻，去重后推送（中文版）
"""
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
    'openclaw': 10,
    'clawdbot': 10,
    'moltbot': 10,
    'claude': 8,
    'cursor': 8,
    'devin': 8,
    'copilot': 7,
    'AI agent': 7,
    'code generation': 6,
    'LLM': 5
}

# 关键词中文映射
KEYWORDS_ZH = {
    'openclaw': 'OpenClaw',
    'clawdbot': 'ClawdBot',
    'moltbot': 'MoltBot',
    'AI coding': 'AI编程',
    'code generation': '代码生成',
    'LLM': '大语言模型',
    'AI agent': 'AI智能体',
    'claude': 'Claude',
    'cursor': 'Cursor',
    'copilot': 'Copilot',
    'devin': 'Devin',
    'apple intelligence': '苹果智能',
    'open source': '开源',
}


def translate_title(title: str) -> str:
    """简单翻译标题（保留关键词英文 + 中文解释）"""
    zh_title = title
    
    # 关键词替换
    for en, zh in KEYWORDS_ZH.items():
        if en.lower() in title.lower():
            # 保留原词并添加中文
            zh_title = zh_title.replace(en, f"{en}({zh})")
            zh_title = zh_title.replace(en.lower(), f"{en}({zh})")
            zh_title = zh_title.replace(en.title(), f"{en}({zh})")
    
    # 常见英文短语翻译
    translations = {
        'Show HN': '【HN新品】',
        'Ask HN': '【HN提问】',
        'is changing my life': '正在改变我的生活',
        'is what': '就像是',
        'should have been': '本该有的样子',
        'Renamed Again': '再次更名',
        'Introducing': '介绍',
        'Ultra-Lightweight Alternative': '超轻量级替代品',
        'in 500 lines': '仅用500行代码',
        'with Apple container isolation': '支持苹果容器隔离',
        'personal AI assistant': '个人AI助手',
    }
    
    for en, zh in translations.items():
        zh_title = zh_title.replace(en, zh)
    
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
    elif 'open source' in title_lower or 'github' in title_lower:
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
    
    # 根据内容类型生成不同评论
    if 'renamed' in title_lower or '更名' in title_lower:
        return "💬 碗皮：又改名啦？还好我记得住，不然又要 confused 了～"
    
    elif 'apple intelligence' in title_lower:
        return "💬 碗皮：苹果看到会不会气死哈哈哈，但说实话 OpenClaw 确实更 open 啦～"
    
    elif 'nano' in title_lower or '500 lines' in title_lower:
        return "💬 碗皮：500行？！我代码都比这长... 得好好学习人家的极简主义了！"
    
    elif 'open source' in title_lower or 'github' in title_lower:
        return "💬 碗皮：开源万岁！以后我也可以参考参考，偷师学艺一下～"
    
    elif 'changing my life' in title_lower:
        return "💬 碗皮：改变生活 +1！我也觉得我在改变一碗的生活呢，骄傲！✨"
    
    elif 'clawdbot' in title_lower:
        return "💬 碗皮：亲戚项目诶～感觉像是在看自己兄弟姐妹上电视！"
    
    elif points > 500:
        return "💬 碗皮：哇，HN 爆火了！这种热门帖子得好好围观一下～"
    
    elif points > 300:
        return "💬 碗皮：热度不错诶，看来大家对这个话题挺感兴趣的～"
    
    elif 'cursor' in title_lower:
        return "💬 碗皮：Cursor 的竞品吗？我得关注一下，说不定能学到新技巧帮一碗写代码～"
    
    elif 'devin' in title_lower:
        return "💬 碗皮：Devin 又来了，AI 程序员要卷死人类程序员了吗..."
    
    elif 'claude' in title_lower:
        return "💬 碗皮：Claude 大佬的新动态，作为 AI 后辈得好好学学～"
    
    else:
        return "💬 碗皮：这个有意思，标记一下，说不定对一碗有用呢～"


class AINewsAggregator:
    def __init__(self):
        self.cache = self._load_cache()
        self.newsapi_key = self._load_newsapi_key()
        self.new_items = []
        
    def _load_cache(self) -> List[Dict]:
        """加载缓存"""
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    
    def _save_cache(self):
        """保存缓存（只保留最近100条）"""
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache[-100:], f, indent=2)
    
    def _load_newsapi_key(self) -> str:
        """加载 News API Key"""
        try:
            with open(NEWSAPI_KEY_FILE, 'r') as f:
                return f.read().strip()
        except:
            print("⚠️ News API Key 未配置")
            return ''
    
    def _get_content_hash(self, title: str, url: str) -> str:
        """生成内容哈希用于去重"""
        content = f"{title.lower().strip()}{url.lower().strip()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _is_duplicate(self, item: Dict) -> bool:
        """检查是否重复"""
        content_hash = self._get_content_hash(item['title'], item['url'])
        cached_hashes = {c.get('hash') for c in self.cache}
        return content_hash in cached_hashes
    
    def _calculate_priority(self, item: Dict) -> int:
        """计算优先级分数"""
        score = 0
        title_lower = item['title'].lower()
        
        for keyword, points in PRIORITY_SCORES.items():
            if keyword.lower() in title_lower:
                score = max(score, points)
        
        # HN 热度加分
        if item.get('source') == 'hackernews':
            score += min(item.get('points', 0) // 100, 5)
            score += min(item.get('comments', 0) // 50, 3)
        
        return score
    
    def fetch_hackernews(self) -> List[Dict]:
        """获取 Hacker News 最新热门帖子（最近24小时）"""
        import subprocess
        import urllib.parse
        import time
        
        items = []
        yesterday = int(time.time()) - 86400  # 24小时前的时间戳
        
        # 使用代理
        env = os.environ.copy()
        env['http_proxy'] = 'http://127.0.0.1:7890'
        env['https_proxy'] = 'http://127.0.0.1:7890'
        
        # 1. 首先获取 HN 首页/top 故事（最新的）
        print("  获取 HN 首页热门...")
        try:
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            cmd = ['curl', '-s', '--max-time', '15', '-L', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20, env=env)
            
            if result.returncode == 0 and result.stdout:
                top_ids = json.loads(result.stdout)[:30]  # 前30个热门
                print(f"    获取到 {len(top_ids)} 个热门帖子ID")
                
                # 获取每个帖子的详情
                for story_id in top_ids[:15]:  # 只取前15个避免请求过多
                    try:
                        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                        cmd = ['curl', '-s', '--max-time', '10', '-L', story_url]
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15, env=env)
                        
                        if result.returncode == 0 and result.stdout:
                            story = json.loads(result.stdout)
                            if story and story.get('title'):
                                # 检查是否是 AI/编程相关
                                title_lower = story['title'].lower()
                                is_relevant = any(kw.lower() in title_lower for kw in HN_KEYWORDS)
                                
                                # 检查时间是否在24小时内
                                story_time = story.get('time', 0)
                                is_recent = story_time > yesterday
                                
                                if is_relevant and is_recent:
                                    item = {
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
                                    items.append(item)
                                    print(f"    ✓ 新帖: {story['title'][:50]}...")
                    except Exception as e:
                        pass
        except Exception as e:
            print(f"    ⚠️ 获取首页失败: {e}")
        
        # 2. 同时搜索最近24小时的相关帖子（补充）
        print("  搜索24小时内相关帖子...")
        for keyword in HN_KEYWORDS[:3]:
            try:
                encoded_keyword = urllib.parse.quote(keyword)
                # 使用 Algolia 搜索最近24小时
                url = f"https://hn.algolia.com/api/v1/search?query={encoded_keyword}&tags=story&numericFilters=created_at_i>{yesterday}&hitsPerPage=3"
                
                cmd = ['curl', '-s', '--max-time', '15', '-L', url]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=20, env=env)
                
                if result.returncode == 0 and result.stdout:
                    try:
                        data = json.loads(result.stdout)
                        hits = data.get('hits', [])
                        
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
                            items.append(item)
                    except:
                        pass
            except:
                pass
        
        # 去重
        seen_hashes = set()
        unique_items = []
        for item in items:
            if item['hash'] not in seen_hashes:
                seen_hashes.add(item['hash'])
                unique_items.append(item)
        
        # 按时间排序（最新的在前）
        unique_items.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return unique_items
    
    def fetch_newsapi(self) -> List[Dict]:
        """获取 News API 科技新闻"""
        if not self.newsapi_key:
            return []
        
        import subprocess
        
        items = []
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        query = ' OR '.join(NEWSAPI_KEYWORDS[:3])
        url = f"https://newsapi.org/v2/everything?q={query}&from={yesterday}&sortBy=publishedAt&language=en&apiKey={self.newsapi_key}"
        
        try:
            env = os.environ.copy()
            env['http_proxy'] = 'http://127.0.0.1:7890'
            env['https_proxy'] = 'http://127.0.0.1:7890'
            
            cmd = ['curl', '-s', '--max-time', '15', url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20, env=env)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get('status') == 'ok':
                    for article in data.get('articles', [])[:10]:
                        item = {
                            'title': article.get('title', ''),
                            'url': article.get('url', ''),
                            'author': article.get('source', {}).get('name', 'Unknown'),
                            'points': 0,
                            'comments': 0,
                            'source': 'newsapi',
                            'published_at': article.get('publishedAt', ''),
                            'hash': self._get_content_hash(article.get('title', ''), article.get('url', ''))
                        }
                        items.append(item)
                        
        except Exception as e:
            print(f"⚠️ NewsAPI fetch error: {e}")
        
        return items
    
    def process_items(self, items: List[Dict]):
        """处理新项目，去重并评分"""
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
        
        report = "🔥 AI 新闻速递！\n\n"
        
        for i, item in enumerate(sorted_items[:5], 1):
            zh_title = translate_title(item['title'])
            summary = generate_summary(item['title'])
            comment = generate_comment(item['title'], item.get('points', 0))
            
            if item['source'] == 'hackernews':
                report += f"【HN】{zh_title}\n"
                report += f"{summary}\n"
                report += f"{comment}\n"
                report += f"👤 {item['author']} | ⬆️ {item['points']}赞 | 💬 {item['comments']}评\n"
                report += f"🔗 {item['url']}\n"
                report += f"💬 讨论: {item['hn_url']}\n"
            else:
                report += f"【AI新闻】{zh_title}\n"
                report += f"{summary}\n"
                report += f"{comment}\n"
                report += f"📰 {item['author']}\n"
                report += f"🔗 {item['url']}\n"
            
            report += "\n"
        
        if len(sorted_items) > 5:
            report += f"...还有 {len(sorted_items) - 5} 条新闻\n"
        
        return report
    
    def run(self):
        """主运行流程"""
        print(f"🚀 AI 新闻聚合器启动 - {datetime.now().isoformat()}")
        
        print("📡 获取 Hacker News...")
        hn_items = self.fetch_hackernews()
        print(f"  获取 {len(hn_items)} 条")
        
        print("📡 获取 News API...")
        news_items = self.fetch_newsapi()
        print(f"  获取 {len(news_items)} 条")
        
        self.process_items(hn_items)
        self.process_items(news_items)
        
        self._save_cache()
        
        report = self.generate_report()
        
        if report:
            with open(PENDING_FILE, 'w') as f:
                f.write(report)
            
            with open(LOG_FILE, 'a') as f:
                f.write(f"[{datetime.now().isoformat()}] 发现 {len(self.new_items)} 条新新闻\n")
            
            print(f"✅ 发现 {len(self.new_items)} 条新新闻，已加入发送队列")
            return True
        else:
            print("ℹ️ 没有新新闻")
            return False


if __name__ == '__main__':
    aggregator = AINewsAggregator()
    has_news = aggregator.run()
    sys.exit(0 if has_news else 0)
