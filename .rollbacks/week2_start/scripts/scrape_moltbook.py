#!/usr/bin/env python3
"""
Moltbook 热门帖子抓取脚本
使用 Playwright 模拟浏览器访问
"""
import asyncio
import json
from datetime import datetime
from playwright.async_api import async_playwright

async def scrape_moltbook_hot():
    """抓取 Moltbook 热门帖子"""
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        
        page = await context.new_page()
        
        print("🔍 正在访问 Moltbook...")
        
        # 访问首页（热门帖子）
        await page.goto('https://moltbook.com/?sort=hot', wait_until='networkidle')
        
        # 等待页面加载完成
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(3)  # 额外等待 JS 渲染
        
        # 提取帖子信息（使用更通用的选择器）
        posts = await page.evaluate('''() => {
            // 尝试多种可能的选择器
            const selectors = [
                'article',
                '[class*="post"]',
                '[class*="card"]',
                '.group',
                'main > div > div'
            ];
            
            let postCards = [];
            for (const selector of selectors) {
                postCards = document.querySelectorAll(selector);
                if (postCards.length >= 3) break;
            }
            
            const results = [];
            
            postCards.forEach((card, index) => {
                if (index >= 5) return; // 只取前5个
                
                // 尝试多种标题选择器
                const titleEl = card.querySelector('h1, h2, h3, h4, [class*="title"], a[class*="title"]');
                // 尝试多种作者选择器
                const authorEl = card.querySelector('[class*="author"], [class*="user"], [class*="name"]');
                // 尝试多种内容选择器
                const contentEl = card.querySelector('p, [class*="content"], [class*="text"]');
                // 链接
                const linkEl = card.querySelector('a');
                
                const title = titleEl ? titleEl.innerText.trim() : '';
                // 过滤掉没有标题的
                if (!title || title.length < 3) return;
                
                results.push({
                    title: title.substring(0, 100),
                    author: authorEl ? authorEl.innerText.trim().substring(0, 50) : '匿名',
                    content: contentEl ? contentEl.innerText.trim().substring(0, 200) : '',
                    link: linkEl ? linkEl.href : window.location.href
                });
            });
            
            return results;
        }''')
        
        await browser.close()
        
        return posts

async def main():
    """主函数"""
    print("=" * 60)
    print("🔥 Moltbook 热门帖子抓取")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    try:
        posts = await scrape_moltbook_hot()
        
        if posts:
            print(f"✅ 成功抓取 {len(posts)} 个热门帖子\n")
            
            for i, post in enumerate(posts, 1):
                print(f"{i}. {post['title']}")
                print(f"   👤 @{post['author']}")
                if post['content']:
                    print(f"   📝 {post['content'][:100]}...")
                if post['link']:
                    print(f"   🔗 {post['link']}")
                print()
            
            # 保存到文件
            with open('/root/.openclaw/workspace/memory/moltbook-hot-scrape.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'posts': posts
                }, f, ensure_ascii=False, indent=2)
            
            print("💾 已保存到 memory/moltbook-hot-scrape.json")
        else:
            print("⚠️ 没有获取到帖子数据")
            
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 60)
    print("✅ 完成！")

if __name__ == "__main__":
    asyncio.run(main())
