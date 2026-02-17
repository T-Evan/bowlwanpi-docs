#!/usr/bin/env python3
"""
Crawl4AI Web Scraper - Python 版本
直接使用 crawl4ai 库进行网页抓取
"""

import asyncio
import sys
import json
from crawl4ai import AsyncWebCrawler

async def crawl(url: str, verbose: bool = False):
    """使用 Crawl4AI 抓取页面内容"""
    try:
        async with AsyncWebCrawler(verbose=verbose) as crawler:
            result = await crawler.arun(url=url)
            
            return {
                "success": True,
                "url": url,
                "title": result.metadata.get('title', '') if isinstance(result.metadata, dict) else '',
                "content": result.markdown if hasattr(result, 'markdown') else "",
                "links": [],
                "media": {
                    "images": [],
                    "videos": []
                },
                "markdown": result.markdown if hasattr(result, 'markdown') else ""
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

async def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        print("Crawl4AI Web Scraper")
        print("")
        print("Usage: python3 crawl4ai.py <url> [--json] [--verbose]")
        print("")
        print("Options:")
        print("  --json      输出完整 JSON")
        print("  --verbose   显示详细日志")
        sys.exit(0)
    
    url = sys.argv[1]
    json_output = '--json' in sys.argv
    verbose = '--verbose' in sys.argv
    
    result = await crawl(url, verbose=verbose)
    
    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("success"):
            md = result.get("markdown", "")
            title = result.get("title", "")
            if title:
                print(f"# {title}\n")
            print(md)
        else:
            print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
