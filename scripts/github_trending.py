#!/usr/bin/env python3
"""
GitHub Trending 检查脚本
获取今日热门仓库
"""
import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace')

# 简单的 trending 数据（实际实现会抓取网页）
def get_trending_repos(languages=None):
    """获取 trending 仓库"""
    # 这里应该是实际抓取逻辑
    # 简化版返回示例数据
    repos = []
    
    # 读取缓存或抓取
    cache_file = Path('/root/.openclaw/workspace/memory/github-trending-cache.json')
    if cache_file.exists():
        try:
            with open(cache_file) as f:
                data = json.load(f)
                if data.get('date') == datetime.now().strftime('%Y-%m-%d'):
                    repos = data.get('repos', [])
        except:
            pass
    
    if not repos:
        # 模拟抓取（实际应使用 requests/scrapy）
        repos = [
            {'name': 'example/repo1', 'stars': 1000, 'language': 'Python'},
            {'name': 'example/repo2', 'stars': 800, 'language': 'JavaScript'}
        ]
    
    return repos


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--lang', default='')
    args = parser.parse_args()
    
    langs = args.lang.split(',') if args.lang else []
    repos = get_trending_repos(langs)
    
    if repos:
        print(f"🔥 GitHub Trending ({datetime.now().strftime('%Y-%m-%d')})")
        for repo in repos[:5]:
            print(f"  • {repo['name']} ({repo['language']}) ⭐ {repo['stars']}")
        return 0
    else:
        print("ℹ️ 暂无 trending 数据")
        return 0


if __name__ == '__main__':
    exit(main())
