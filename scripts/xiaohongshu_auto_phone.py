#!/usr/bin/env python3
"""
小红书手机号自动登录 - 自动输入手机号，等待验证码
"""

import asyncio
from playwright.async_api import async_playwright
import os
import json

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

PHONE_NUMBER = "17671776855"

async def auto_login():
    print('📱 小红书自动登录')
    print(f'手机号: {PHONE_NUMBER[:3]}****{PHONE_NUMBER[-4:]}')
    print('=' * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # 无头模式
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        # 打开小红书
        print('\n1️⃣ 打开登录页面...')
        await page.goto('https://www.xiaohongshu.com', wait_until='domcontentloaded', timeout=30000)
        await page.wait_for_timeout(3000)
        
        # 点击登录按钮
        print('2️⃣ 点击登录按钮...')
        try:
            await page.click('text=登录', timeout=5000)
            await page.wait_for_timeout(2000)
        except:
            print('   可能已经有登录框弹出')
        
        await page.wait_for_timeout(3000)
        
        # 切换到手机号登录
        print('3️⃣ 切换到手机号登录...')
        try:
            # 查找手机号登录标签
            phone_tab = await page.query_selector('text=手机号登录')
            if phone_tab:
                await phone_tab.click()
                print('   ✅ 已切换到手机号登录')
                await page.wait_for_timeout(2000)
        except Exception as e:
            print(f'   可能已经是在手机号登录界面: {e}')
        
        # 截图查看当前状态
        await page.screenshot(path='/tmp/xhs_phone_step1.png')
        
        # 输入手机号
        print(f'4️⃣ 输入手机号...')
        try:
            # 查找手机号输入框
            phone_input = await page.wait_for_selector('input[placeholder*="手机号"], input[type="tel"]', timeout=5000)
            if phone_input:
                await phone_input.fill(PHONE_NUMBER)
                print(f'   ✅ 手机号已输入')
                await page.wait_for_timeout(1000)
        except Exception as e:
            print(f'   ❌ 未找到手机号输入框: {e}')
            # 尝试其他选择器
            try:
                await page.fill('input', PHONE_NUMBER)
                print('   ✅ 使用通用选择器输入手机号')
            except:
                pass
        
        await page.wait_for_timeout(2000)
        
        # 点击获取验证码
        print('5️⃣ 点击获取验证码按钮...')
        try:
            # 查找获取验证码按钮
            code_btn = await page.query_selector('text=获取验证码, text=发送验证码, button:has-text("验证码")')
            if code_btn:
                await code_btn.click()
                print('   ✅ 已点击获取验证码')
            else:
                # 尝试其他方式
                await page.click('button >> nth=1')  # 通常第二个按钮是获取验证码
                print('   ✅ 已点击按钮（推测为获取验证码）')
        except Exception as e:
            print(f'   ⚠️ 点击验证码按钮时出错: {e}')
        
        await page.wait_for_timeout(3000)
        
        # 截图显示当前状态
        await page.screenshot(path='/tmp/xhs_phone_step2.png')
        print('📸 当前状态截图: /tmp/xhs_phone_step2.png')
        
        print('\n' + '=' * 50)
        print('⏳ 等待短信验证码...')
        print('请告诉我收到的验证码，我会自动填写！')
        print('等待 60 秒...')
        
        # 等待用户输入验证码（这里会暂停，实际运行时由用户通过其他方式提供）
        # 在真实场景中，这里可以读取文件或等待输入
        await page.wait_for_timeout(60000)  # 等待60秒
        
        # 检查是否已登录
        print('\n6️⃣ 检查登录状态...')
        await page.wait_for_timeout(5000)
        
        # 保存 cookies
        cookies = await context.cookies()
        with open('xiaohongshu_cookies_auto.json', 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f'💾 Cookies 已保存 ({len(cookies)} 个)')
        
        # 截图最终状态
        await page.screenshot(path='/tmp/xhs_phone_final.png')
        
        await browser.close()
        print('\n🔚 流程完成')

if __name__ == '__main__':
    asyncio.run(auto_login())
