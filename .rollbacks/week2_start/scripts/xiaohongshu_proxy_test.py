#!/usr/bin/env python3
"""
小红书登录 - 使用代理IP绕过风控
"""

import asyncio
from playwright.async_api import async_playwright
import os

# 使用代理IP（从备用订阅中选取）
PROXY_SERVER = "http://127.0.0.1:7890"  # Mihomo本地代理

async def login_with_proxy():
    print('🌐 小红书登录 - 使用代理IP')
    print('=' * 50)
    
    async with async_playwright() as p:
        # 使用代理启动浏览器
        browser = await p.chromium.launch(
            headless=True,
            proxy={'server': PROXY_SERVER},
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        print('1️⃣ 通过代理打开小红书...')
        try:
            await page.goto('https://www.xiaohongshu.com', wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(3000)
            
            # 截图查看
            await page.screenshot(path='/tmp/xhs_proxy_step1.png')
            print('✅ 页面已打开，截图保存')
            
            # 检查是否有安全限制
            content = await page.content()
            if '安全限制' in content or 'IP存在风险' in content:
                print('❌ 仍然遇到安全限制，代理IP也被拦截了')
                await browser.close()
                return False
            
            print('✅ 没有安全限制，继续登录流程')
            
            # 尝试点击登录
            try:
                await page.click('text=登录', timeout=5000)
                print('✅ 已点击登录')
                await page.wait_for_timeout(2000)
            except:
                print('⚠️ 可能已经有登录框或无需点击')
            
            # 截图当前状态
            await page.screenshot(path='/tmp/xhs_proxy_step2.png')
            print('📸 登录页面截图已保存')
            
            await browser.close()
            print('\n🔚 测试完成')
            return True
            
        except Exception as e:
            print(f'❌ 出错: {e}')
            await page.screenshot(path='/tmp/xhs_proxy_error.png')
            await browser.close()
            return False

if __name__ == '__main__':
    result = asyncio.run(login_with_proxy())
    print(f'\n结果: {"✅ 成功" if result else "❌ 失败"}')
