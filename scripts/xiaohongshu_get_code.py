#!/usr/bin/env python3
"""
小红书登录 - 继续流程：点击获取验证码并等待输入
"""

import asyncio
from playwright.async_api import async_playwright
import os
import json

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

PHONE_NUMBER = "17671776855"

async def continue_login():
    print('📱 小红书登录 - 获取验证码')
    print('=' * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900}
        )
        
        page = await context.new_page()
        
        # 打开小红书并进入登录页面
        print('1️⃣ 打开登录页面...')
        await page.goto('https://www.xiaohongshu.com', wait_until='domcontentloaded')
        await page.wait_for_timeout(2000)
        
        # 点击登录
        await page.click('text=登录', timeout=5000)
        await page.wait_for_timeout(2000)
        
        # 切换到手机号登录
        await page.click('text=手机号登录')
        await page.wait_for_timeout(2000)
        
        # 输入手机号
        print('2️⃣ 输入手机号...')
        await page.fill('input[type="tel"]', PHONE_NUMBER)
        await page.wait_for_timeout(1000)
        print(f'   ✅ 手机号 {PHONE_NUMBER[:3]}****{PHONE_NUMBER[-4:]} 已输入')
        
        # 点击获取验证码
        print('3️⃣ 点击获取验证码...')
        try:
            # 查找获取验证码按钮
            code_btn = await page.wait_for_selector('text=获取验证码', timeout=5000)
            if code_btn:
                await code_btn.click()
                print('   ✅ 已点击"获取验证码"')
        except:
            print('   ⚠️ 未找到按钮，可能已点击过')
        
        await page.wait_for_timeout(3000)
        
        # 截图当前状态
        await page.screenshot(path='/tmp/xhs_waiting_code.png')
        
        print('\n' + '=' * 50)
        print('📱 验证码已发送！')
        print('请查看手机短信，告诉我收到的验证码')
        print('等待 60 秒...')
        print('=' * 50)
        
        # 等待60秒让用户提供验证码
        await page.wait_for_timeout(60000)
        
        # 这里需要用户输入验证码，暂时保存状态
        print('\n⏳ 等待验证码输入...')
        
        # 保存当前页面状态以便后续继续
        cookies = await context.cookies()
        with open('xiaohongshu_login_progress.json', 'w') as f:
            json.dump({
                'phone': PHONE_NUMBER,
                'cookies': cookies,
                'status': 'waiting_for_code'
            }, f)
        
        await browser.close()
        print('\n🔚 流程暂停，等待验证码')

if __name__ == '__main__':
    asyncio.run(continue_login())
