#!/usr/bin/env python3
"""
小黑盒手机号登录脚本
流程：输入手机号 -> 获取验证码 -> 输入验证码 -> 登录成功
"""

import asyncio
from playwright.async_api import async_playwright
import json
import os

async def login_with_phone():
    """手机号登录小黑盒"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # 需要显示浏览器以便用户操作
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        
        page = await context.new_page()
        
        print("=" * 60)
        print("📱 小黑盒手机号登录")
        print("=" * 60)
        print()
        
        # 访问登录页
        print("正在打开登录页面...")
        await page.goto('https://www.xiaoheihe.cn/app/login', wait_until='networkidle')
        await asyncio.sleep(3)
        
        print("请按以下步骤操作：")
        print("1. 点击'手机号登录'")
        print("2. 输入你的手机号")
        print("3. 点击'获取验证码'")
        print("4. 输入收到的验证码")
        print("5. 点击登录")
        print()
        print("登录成功后，按回车键继续...")
        print()
        
        # 等待用户操作
        input("按回车键保存登录状态...")
        
        # 获取 cookies
        cookies = await context.cookies()
        
        # 保存到文件
        output = {
            'cookies': cookies,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        os.makedirs('secrets', exist_ok=True)
        with open('secrets/xiaoheihe_cookies.json', 'w') as f:
            json.dump(output, f, indent=2)
        
        print()
        print("✅ 登录状态已保存到 secrets/xiaoheihe_cookies.json")
        print()
        
        # 验证登录状态
        print("正在验证登录状态...")
        await page.goto('https://www.xiaoheihe.cn/app/user/me', wait_until='networkidle')
        await asyncio.sleep(3)
        
        # 截图确认
        await page.screenshot(path='screenshots/xiaoheihe_after_login.png')
        print("📸 截图已保存: screenshots/xiaoheihe_after_login.png")
        
        await browser.close()
        
        print()
        print("🎉 登录完成！")

if __name__ == '__main__':
    asyncio.run(login_with_phone())
