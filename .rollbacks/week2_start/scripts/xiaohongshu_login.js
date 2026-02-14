const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

// 小红书登录脚本
async function loginXiaohongshu() {
    console.log('🚀 启动浏览器...');
    
    const browser = await chromium.launch({
        headless: true,  // 无头模式
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const context = await browser.newContext({
        viewport: { width: 1280, height: 720 },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    });
    
    const page = await context.newPage();
    
    try {
        console.log('📱 打开小红书登录页面...');
        await page.goto('https://www.xiaohongshu.com/sign_in', {
            waitUntil: 'networkidle',
            timeout: 30000
        });
        
        // 等待页面加载
        await page.waitForTimeout(3000);
        
        // 截图查看当前页面
        const screenshotPath = '/tmp/xiaohongshu_login.png';
        await page.screenshot({ path: screenshotPath, fullPage: true });
        console.log(`📸 截图已保存: ${screenshotPath}`);
        
        // 查找二维码
        const qrSelectors = [
            'img[src*="qr"]',
            '.qrcode img',
            '[class*="qr"] img',
            'canvas'  // 有些二维码是 canvas 绘制的
        ];
        
        let qrFound = false;
        for (const selector of qrSelectors) {
            try {
                const element = await page.$(selector);
                if (element) {
                    await element.screenshot({ path: '/tmp/xiaohongshu_qrcode.png' });
                    console.log('✅ 找到二维码并截图');
                    qrFound = true;
                    break;
                }
            } catch (e) {
                // 继续尝试下一个选择器
            }
        }
        
        if (!qrFound) {
            console.log('⚠️ 未找到二维码，保存完整页面截图');
        }
        
        // 保存页面 HTML 供分析
        const html = await page.content();
        fs.writeFileSync('/tmp/xiaohongshu_page.html', html);
        
        // 保存 cookies（登录后可用）
        const cookies = await context.cookies();
        fs.writeFileSync('/tmp/xiaohongshu_cookies.json', JSON.stringify(cookies, null, 2));
        
        console.log('⏳ 等待扫码登录...');
        console.log('请查看截图 /tmp/xiaohongshu_login.png');
        
        // 等待一段时间，让用户扫码
        await page.waitForTimeout(30000);  // 等待30秒
        
        // 检查是否登录成功（通过检查页面元素）
        const isLoggedIn = await page.evaluate(() => {
            // 检查是否有登录后的特征元素
            return document.querySelector('.user-info') !== null ||
                   document.querySelector('.avatar') !== null ||
                   document.querySelector('[class*="user"]') !== null;
        });
        
        if (isLoggedIn) {
            console.log('✅ 登录成功！');
            // 保存登录后的 cookies
            const loggedInCookies = await context.cookies();
            fs.writeFileSync('/root/.openclaw/workspace/xiaohongshu_cookies.json', JSON.stringify(loggedInCookies, null, 2));
            console.log('💾 Cookies 已保存');
        } else {
            console.log('⏰ 等待扫码超时，请手动运行脚本完成登录');
        }
        
    } catch (error) {
        console.error('❌ 错误:', error.message);
        // 出错时也保存截图
        await page.screenshot({ path: '/tmp/xiaohongshu_error.png' });
    } finally {
        await browser.close();
        console.log('🔚 浏览器已关闭');
    }
}

// 运行
loginXiaohongshu().catch(console.error);
