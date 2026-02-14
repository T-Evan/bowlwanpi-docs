#!/usr/bin/env python3
"""
小黑盒 (xiaoheihe.cn) 二维码登录脚本
生成二维码，手机扫码登录
"""
import asyncio
import json
import os
from playwright.async_api import async_playwright
from datetime import datetime

async def login_xiaoheihe_qrcode():
    """小黑盒二维码登录"""
    
    # 确保目录存在
    os.makedirs('/root/.openclaw/workspace/screenshots', exist_ok=True)
    os.makedirs('/root/.openclaw/workspace/secrets', exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,  # 无头模式，服务器友好
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        
        page = await context.new_page()
        
        print("=" * 60)
        print("🔑 小黑盒二维码登录")
        print("=" * 60)
        print()
        
        # 访问登录页面
        print("🔍 正在获取登录页面...")
        await page.goto('https://www.xiaoheihe.cn/app/bbs/home', wait_until='networkidle')
        await asyncio.sleep(2)
        
        # 查找并点击登录
        login_selectors = [
            'text=登录',
            'text=注册/登录', 
            '.login-btn',
            'a[href*="login"]'
        ]
        
        for selector in login_selectors:
            try:
                if await page.is_visible(selector, timeout=3000):
                    await page.click(selector)
                    print("✅ 已打开登录界面")
                    break
            except:
                continue
        
        await asyncio.sleep(3)
        
        # 查找二维码
        print("🔍 查找二维码...")
        qr_selectors = [
            'img[src*="qr"]',
            '.qrcode img',
            '[class*="qr"] img',
            'canvas'  # 有些网站用 canvas 绘制二维码
        ]
        
        qr_found = False
        for selector in qr_selectors:
            try:
                if await page.is_visible(selector, timeout=2000):
                    # 截图二维码区域
                    element = page.locator(selector)
                    await element.screenshot(path='/root/.openclaw/workspace/screenshots/xiaoheihe_qrcode.png')
                    print("✅ 二维码已保存！")
                    qr_found = True
                    break
            except:
                continue
        
        if not qr_found:
            # 如果找不到特定二维码，截图整个登录区域
            print("⚠️ 未找到标准二维码，截图整个登录区域...")
            await page.screenshot(path='/root/.openclaw/workspace/screenshots/xiaoheihe_login.png')
        
        print()
        print("📱 请用手机扫描二维码登录")
        print("   图片位置: screenshots/xiaoheihe_qrcode.png")
        print()
        print("⏳ 等待登录中... (60秒)")
        
        # 等待登录完成（检测页面变化）
        for i in range(60):
            await asyncio.sleep(1)
            
            # 检查是否已登录（查找用户头像或退出按钮）
            try:
                if await page.is_visible('.user-avatar', timeout=1000) or \
                   await page.is_visible('[class*="profile"]', timeout=1000):
                    print("✅ 检测到登录成功！")
                    break
            except:
                pass
            
            if i % 10 == 0:
                print(f"   等待中... {i}s")
        
        # 保存 Cookie
        cookies = await context.cookies()
        cookie_data = {
            'timestamp': datetime.now().isoformat(),
            'cookies': cookies
        }
        
        with open('/root/.openclaw/workspace/secrets/xiaoheihe_cookies.json', 'w') as f:
            json.dump(cookie_data, f, indent=2)
        
        print()
        print(f"💾 Cookie 已保存 (共 {len(cookies)} 个)")
        print("   文件: secrets/xiaoheihe_cookies.json")
        
        # 截图登录后状态
        await page.screenshot(path='/root/.openclaw/workspace/screenshots/xiaoheihe_logged_in.png')
        print("💾 登录状态已截图")
        
        await browser.close()
        
        print()
        print("=" * 60)
        print("✅ 登录流程完成！")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(login_xiaoheihe_qrcode())
