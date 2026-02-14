const { chromium } = require('playwright');
const fs = require('fs');
const readline = require('readline');

// 手机号验证码登录脚本
async function loginWithPhone() {
    console.log('🚀 启动浏览器...');
    
    const browser = await chromium.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const context = await browser.newContext({
        viewport: { width: 1280, height: 720 },
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    });
    
    const page = await context.newPage();
    
    try {
        console.log('📱 打开小红书登录页面...');
        await page.goto('https://www.xiaohongshu.com/sign_in', {
            waitUntil: 'networkidle',
            timeout: 30000
        });
        
        await page.waitForTimeout(3000);
        
        // 切换到手机号登录
        console.log('🔍 查找手机号登录选项...');
        
        // 截图查看页面结构
        await page.screenshot({ path: '/tmp/xiaohongshu_phone_login.png' });
        console.log('📸 页面截图已保存');
        
        // 查找手机号输入框
        const phoneSelectors = [
            'input[type="tel"]',
            'input[placeholder*="手机号"]',
            'input[placeholder*="电话"]',
            'input[name="phone"]',
            'input[name="mobile"]',
            '[class*="phone"] input',
            '[class*="login"] input[type="text"]'
        ];
        
        let phoneInput = null;
        for (const selector of phoneSelectors) {
            try {
                phoneInput = await page.$(selector);
                if (phoneInput) {
                    console.log(`✅ 找到手机号输入框: ${selector}`);
                    break;
                }
            } catch (e) {}
        }
        
        if (!phoneInput) {
            console.log('⚠️ 未找到手机号输入框，保存页面源码供分析');
            const html = await page.content();
            fs.writeFileSync('/tmp/xiaohongshu_login_html.txt', html);
            console.log('💾 页面HTML已保存到 /tmp/xiaohongshu_login_html.txt');
            
            // 尝试点击"手机号登录"按钮
            const phoneLoginButtons = [
                'text=手机号登录',
                'text=手机登录',
                'button:has-text("手机")',
                '[class*="phone"]'
            ];
            
            for (const btnSelector of phoneLoginButtons) {
                try {
                    const btn = await page.$(btnSelector);
                    if (btn) {
                        await btn.click();
                        console.log(`🖱️ 点击了: ${btnSelector}`);
                        await page.waitForTimeout(2000);
                        break;
                    }
                } catch (e) {}
            }
        }
        
        // 等待用户输入手机号
        const phoneNumber = process.env.XIAOHONGSHU_PHONE;
        if (!phoneNumber) {
            console.log('❌ 请设置环境变量 XIAOHONGSHU_PHONE');
            console.log('例如: export XIAOHONGSHU_PHONE=13800138000');
            await browser.close();
            return;
        }
        
        // 重新查找手机号输入框（可能切换后出现了）
        for (const selector of phoneSelectors) {
            try {
                phoneInput = await page.$(selector);
                if (phoneInput) break;
            } catch (e) {}
        }
        
        if (phoneInput) {
            await phoneInput.fill(phoneNumber);
            console.log(`✅ 已填入手机号: ${phoneNumber}`);
            
            // 点击获取验证码按钮
            const codeBtnSelectors = [
                'text=获取验证码',
                'text=发送验证码',
                'button:has-text("验证码")',
                '[class*="code"]',
                '[class*="verify"]'
            ];
            
            for (const btnSelector of codeBtnSelectors) {
                try {
                    const btn = await page.$(btnSelector);
                    if (btn) {
                        await btn.click();
                        console.log('🖱️ 点击获取验证码');
                        break;
                    }
                } catch (e) {}
            }
            
            console.log('⏳ 等待验证码...');
            console.log('请在手机上查看验证码，然后设置环境变量 XIAOHONGSHU_CODE');
            console.log('例如: export XIAOHONGSHU_CODE=123456');
            console.log('等待 60 秒...');
            
            // 等待验证码输入
            await page.waitForTimeout(60000);
            
            const verifyCode = process.env.XIAOHONGSHU_CODE;
            if (verifyCode) {
                // 查找验证码输入框
                const codeSelectors = [
                    'input[placeholder*="验证码"]',
                    'input[type="number"]',
                    'input[maxlength="6"]'
                ];
                
                let codeInput = null;
                for (const selector of codeSelectors) {
                    try {
                        codeInput = await page.$(selector);
                        if (codeInput) break;
                    } catch (e) {}
                }
                
                if (codeInput) {
                    await codeInput.fill(verifyCode);
                    console.log('✅ 已填入验证码');
                    
                    // 点击登录按钮
                    const loginBtnSelectors = [
                        'text=登录',
                        'text=确认',
                        'button[type="submit"]'
                    ];
                    
                    for (const btnSelector of loginBtnSelectors) {
                        try {
                            const btn = await page.$(btnSelector);
                            if (btn) {
                                await btn.click();
                                console.log('🖱️ 点击登录');
                                break;
                            }
                        } catch (e) {}
                    }
                    
                    // 等待登录完成
                    await page.waitForTimeout(5000);
                    
                    // 检查是否登录成功
                    const isLoggedIn = await page.evaluate(() => {
                        return document.querySelector('.user-info') !== null ||
                               document.querySelector('.avatar') !== null ||
                               document.querySelector('[class*="user"]') !== null;
                    });
                    
                    if (isLoggedIn) {
                        console.log('✅ 登录成功！');
                        const cookies = await context.cookies();
                        fs.writeFileSync('/root/.openclaw/workspace/xiaohongshu_cookies.json', JSON.stringify(cookies, null, 2));
                        console.log('💾 Cookies 已保存');
                    } else {
                        console.log('❌ 登录可能失败，请检查');
                    }
                }
            } else {
                console.log('⏰ 未收到验证码，请重新运行脚本');
            }
        } else {
            console.log('❌ 无法找到手机号输入框');
        }
        
    } catch (error) {
        console.error('❌ 错误:', error.message);
        await page.screenshot({ path: '/tmp/xiaohongshu_error.png' });
    } finally {
        await browser.close();
        console.log('🔚 浏览器已关闭');
    }
}

// 运行
loginWithPhone().catch(console.error);
