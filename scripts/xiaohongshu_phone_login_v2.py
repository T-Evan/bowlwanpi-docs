#!/usr/bin/env python3
"""
小红书手机号+短信验证码登录
需要用户配合输入手机号和验证码
"""

import asyncio
from playwright.async_api import async_playwright
import os
import json

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

async def login_with_phone():
    print('📱 小红书手机号登录')
    print('=' * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # 显示浏览器窗口，方便查看
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900}
        )
        
        page = await context.new_page()
        
        # 打开小红书
        print('\n1️⃣ 打开登录页面...')
        await page.goto('https://www.xiaohongshu.com', wait_until='domcontentloaded')
        await page.wait_for_timeout(3000)
        
        # 点击登录按钮
        try:
            await page.click('text=登录', timeout=5000)
            print('✅ 已点击登录按钮')
            await page.wait_for_timeout(2000)
        except:
            print('⚠️ 未找到登录按钮，可能已经弹出登录框')
        
        # 等待登录框出现
        await page.wait_for_timeout(3000)
        
        # 切换到手机号登录（如果需要）
        try:
            phone_tab = await page.query_selector('text=手机号登录')
            if phone_tab:
                await phone_tab.click()
                print('✅ 切换到手机号登录')
                await page.wait_for_timeout(1000)
        except:
            pass
        
        # 截图显示当前状态
        await page.screenshot(path='/tmp/xhs_phone_login.png')
        print('📸 登录页面截图已保存: /tmp/xhs_phone_login.png')
        
        # 提示用户输入手机号
        print('\n2️⃣ 请输入手机号（在浏览器中输入）:')
        print('   等待 30 秒让用户操作...')
        
        # 等待用户输入手机号并点击获取验证码
        await page.wait_for_timeout(30000)  # 等待30秒
        
        # 检查是否已发送验证码
        print('\n3️⃣ 请输入短信验证码（在浏览器中输入）:')
        print('   等待 30 秒让用户输入验证码...')
        
        await page.wait_for_timeout(30000)  # 等待30秒
        
        # 检查登录状态
        print('\n4️⃣ 检查登录状态...')
        await page.wait_for_timeout(5000)
        
        # 截图确认
        await page.screenshot(path='/tmp/xhs_after_login.png')
        
        # 获取 cookies
        cookies = await context.cookies()
        with open('xiaohongshu_cookies_phone.json', 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print('💾 Cookies 已保存到 xiaohongshu_cookies_phone.json')
        
        print(f'\n✅ 登录流程完成！')
        print(f'   共获取 {len(cookies)} 个 cookies')
        
        # 保持浏览器打开，让用户确认
        print('\n⏳ 浏览器保持打开 60 秒，请确认登录状态...')
        await page.wait_for_timeout(60000)
        
        await browser.close()
        print('🔚 浏览器已关闭')

if __name__ == '__main__':
    asyncio.run(login_with_phone())
