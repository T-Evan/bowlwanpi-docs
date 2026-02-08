#!/usr/bin/env python3
"""
小黑盒深度数据抓取脚本
获取热门帖子、点赞数、评论数等详细信息
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime

async def fetch_xiaoheihe_deep():
    """深度抓取小黑盒数据"""
    
    # 读取 cookies
    with open('/root/.openclaw/workspace/secrets/xiaoheihe_cookies.json', 'r') as f:
        cookie_data = json.load(f)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        
        # 添加 cookies
        await context.add_cookies(cookie_data['cookies'])
        
        page = await context.new_page()
        
        print("=" * 60)
        print("🔥 小黑盒热门数据抓取")
        print("=" * 60)
        print()
        
        # 访问首页
        print("📱 正在加载首页...")
        await page.goto('https://www.xiaoheihe.cn/app/bbs/home', wait_until='networkidle')
        await asyncio.sleep(5)  # 等待动态内容加载
        
        # 尝试多种选择器来获取帖子数据
        posts_data = []
        
        # 方法1: 尝试获取帖子卡片数据
        try:
            cards = await page.query_selector_all('[class*="post"], [class*="topic"], [class*="card"]')
            print(f"找到 {len(cards)} 个卡片元素")
            
            for i, card in enumerate(cards[:10]):
                try:
                    # 获取标题
                    title_elem = await card.query_selector('h1, h2, h3, .title, [class*="title"]')
                    title = await title_elem.inner_text() if title_elem else '无标题'
                    
                    # 获取作者
                    author_elem = await card.query_selector('.author, [class*="author"], [class*="user"]')
                    author = await author_elem.inner_text() if author_elem else '未知作者'
                    
                    # 获取点赞数
                    like_elem = await card.query_selector('.like, [class*="like"], [class*="vote"]')
                    likes = await like_elem.inner_text() if like_elem else '0'
                    
                    # 获取评论数
                    comment_elem = await card.query_selector('.comment, [class*="comment"], [class*="reply"]')
                    comments = await comment_elem.inner_text() if comment_elem else '0'
                    
                    posts_data.append({
                        'title': title.strip()[:50],
                        'author': author.strip()[:20],
                        'likes': likes.strip(),
                        'comments': comments.strip()
                    })
                except:
                    continue
        except Exception as e:
            print(f"方法1失败: {e}")
        
        # 方法2: 通过 JavaScript 提取页面数据
        if not posts_data:
            print("\n尝试通过 JavaScript 提取数据...")
            try:
                # 尝试读取页面上的数据
                page_data = await page.evaluate('''() => {
                    // 尝试找到包含帖子数据的全局变量
                    const data = window.__INITIAL_STATE__ || window.__DATA__ || {};
                    return data;
                }''')
                
                if page_data:
                    print(f"找到页面数据: {str(page_data)[:200]}...")
            except:
                pass
        
        # 方法3: 直接提取可见文本
        if not posts_data:
            print("\n尝试提取可见文本...")
            try:
                # 获取所有可见的文本内容
                text_content = await page.inner_text('body')
                lines = [l.strip() for l in text_content.split('\n') if l.strip()]
                
                # 过滤出可能是帖子的内容（长度适中）
                potential_posts = [l for l in lines if 10 < len(l) < 100][:15]
                
                for line in potential_posts:
                    posts_data.append({
                        'title': line,
                        'author': '未知',
                        'likes': '-',
                        'comments': '-'
                    })
            except Exception as e:
                print(f"方法3失败: {e}")
        
        # 输出结果
        print("\n" + "=" * 60)
        print("📊 抓取结果")
        print("=" * 60)
        
        if posts_data:
            for i, post in enumerate(posts_data[:10], 1):
                print(f"\n{i}. {post['title']}")
                if post['author'] != '未知':
                    print(f"   👤 {post['author']}")
                if post['likes'] != '-':
                    print(f"   👍 {post['likes']}  💬 {post['comments']}")
        else:
            print("\n⚠️ 未能抓取到详细帖子数据")
            print("\n可能原因:")
            print("- 小黑盒使用复杂的动态加载机制")
            print("- 需要特定的 API 签名或 Token")
            print("- 页面结构可能已更新")
        
        # 保存截图供分析
        await page.screenshot(path='/root/.openclaw/workspace/screenshots/xiaoheihe_debug.png')
        print(f"\n📸 截图已保存: screenshots/xiaoheihe_debug.png")
        
        await browser.close()
        
        return posts_data

if __name__ == '__main__':
    result = asyncio.run(fetch_xiaoheihe_deep())
    
    # 保存结果
    if result:
        output = {
            'timestamp': datetime.now().isoformat(),
            'count': len(result),
            'posts': result
        }
        with open('/root/.openclaw/workspace/data/xiaoheihe_posts.json', 'w') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n💾 数据已保存: data/xiaoheihe_posts.json")
