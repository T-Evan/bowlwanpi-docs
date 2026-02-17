#!/usr/bin/env python3
"""
网页抓取工具 - Playwright 实现
作为 Crawl4AI 的临时替代方案
"""

import asyncio
import sys
import json
from urllib.parse import urlparse

async def crawl_page(url: str):
    """使用 Playwright 抓取页面内容"""
    try:
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080},
                locale='zh-CN'
            )
            
            # 注入脚本隐藏自动化特征
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                window.chrome = { runtime: {} };
            """)
            
            page = await context.new_page()
            
            # 设置超时
            page.set_default_timeout(30000)
            
            # 导航到页面
            await page.goto(url, wait_until="domcontentloaded")
            
            # 等待内容加载
            await asyncio.sleep(2)
            
            # 提取信息
            title = await page.title()
            
            # 尝试获取 main 或 article 内容，回退到 body
            content = await page.evaluate("""
                () => {
                    const selectors = ['main', 'article', '[role="main"]', '.content', '#content', 'body'];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el && el.innerText.trim().length > 100) {
                            return el.innerText.trim();
                        }
                    }
                    return document.body?.innerText?.trim() || '';
                }
            """)
            
            # 获取所有链接
            links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]'))
                    .map(a => ({text: a.innerText.trim(), href: a.href}))
                    .filter(l => l.text && l.href.startsWith('http'))
                    .slice(0, 50)
            """)
            
            # 获取图片
            images = await page.evaluate("""
                () => Array.from(document.querySelectorAll('img[src]'))
                    .map(img => ({
                        src: img.src,
                        alt: img.alt || '',
                        width: img.naturalWidth,
                        height: img.naturalHeight
                    }))
                    .filter(img => img.width > 100 && img.height > 100)
                    .slice(0, 20)
            """)
            
            await browser.close()
            
            return {
                "success": True,
                "url": url,
                "title": title,
                "content": content,
                "links": links,
                "images": images,
                "markdown": f"# {title}\n\n{content[:5000]}"  # 简化版 markdown
            }
            
    except ImportError:
        return {"success": False, "error": "Playwright not installed. Run: pip install playwright"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        print("网页抓取工具 - Playwright 实现")
        print("")
        print("Usage: python3 crawl.py <url> [--json]")
        print("")
        print("Options:")
        print("  --json    输出完整 JSON")
        sys.exit(0)
    
    url = sys.argv[1]
    json_output = '--json' in sys.argv
    
    result = await crawl_page(url)
    
    if json_output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result.get("success"):
            print(result.get("markdown", result.get("content", "")))
        else:
            print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
