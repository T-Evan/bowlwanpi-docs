#!/usr/bin/env python3
"""
小红书登录 - 使用代理IP完成完整登录
"""

import asyncio
from playwright.async_api import async_playwright
import os
import json

PROXY_SERVER = "http://127.0.0.1:7890"
PHONE_NUMBER = "17671776855"

async def full_login():
    print('📱 小红书登录 - 使用代理IP')
    print(f'手机号: {PHONE_NUMBER[:3]}****{PHONE_NUMBER[-4:]}')
    print('=' * 50)
    
    async with async_playwright() as p:
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
        
        # 1. 打开小红书
        print('\n1️⃣ 打开小红书...')
        await page.goto('https://www.xiaohongshu.com', wait_until='domcontentloaded')
        await page.wait_for_timeout(3000)
        
        # 2. 点击登录
        print('2️⃣ 点击登录按钮...')
        await page.click('text=登录')
        await page.wait_for_timeout(2000)
        
        # 3. 切换到手机号登录
        print('3️⃣ 切换到手机号登录...')
        await page.click('text=手机号登录')
        await page.wait_for_timeout(2000)
        
        # 4. 输入手机号
        print('4️⃣ 输入手机号...')
        await page.fill('input[placeholder*="手机号"]', PHONE_NUMBER)
        print(f'   ✅ 已输入: {PHONE_NUMBER[:3]}****{PHONE_NUMBER[-4:]}')
        await page.wait_for_timeout(1000)
        
        # 截图查看
        await page.screenshot(path='/tmp/xhs_proxy_phone.png')
        
        # 5. 点击获取验证码
        print('5️⃣ 点击获取验证码...')
        await page.click('text=获取验证码')
        print('   ✅ 已点击')
        await page.wait_for_timeout(3000)
        
        # 截图等待验证码输入
        await page.screenshot(path='/tmp/xhs_proxy_waiting.png')
        print('📸 截图已保存')
        
        print('\n' + '=' * 50)
        print('⏳ 验证码已发送！')
        print('请查看手机短信，告诉我验证码～')
        print('等待 60 秒...')
        print('=' * 50)
        
        # 等待用户输入验证码（实际场景中需要用户交互）
        await page.wait_for_timeout(60000)
        
        # 保存当前状态
        cookies = await context.cookies()
        with open('xiaohongshu_proxy_progress.json', 'w') as f:
            json.dump({
                'phone': PHONE_NUMBER,
                'cookies': cookies,
                'status': 'waiting_for_code'
            }, f)
        
        await browser.close()
        print('\n💾 进度已保存，等待验证码...')

if __name__ == '__main__':
    asyncio.run(full_login())
