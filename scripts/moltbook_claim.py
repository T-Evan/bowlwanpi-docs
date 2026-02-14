#!/usr/bin/env python3
"""
Moltbook 自动认领脚本
使用 Playwright 自动化浏览器操作
"""

import json
import sys
from pathlib import Path

# Moltbook 认领信息
CLAIM_URL = "https://moltbook.com/claim/moltbook_claim_XSj1z23DP0mvIVY2uyXgBjo3OFo63V3p"
AGENT_NAME = "BowlWanpi"
AGENT_ID = "dfc4fae2-ac13-4124-9bfe-6d12da5ec72f"
EMAIL = "yiwan233@outlook.com"

def create_claim_script():
    """创建 Playwright 认领脚本"""
    
    script_content = '''
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false }); // 有界面模式，方便用户操作
  const context = await browser.newContext();
  const page = await context.newPage();
  
  console.log('🚀 打开 Moltbook 认领页面...');
  await page.goto('CLAIM_URL');
  
  // 等待页面加载
  await page.waitForLoadState('networkidle');
  
  console.log('📧 填写邮箱: EMAIL');
  
  // 截图查看当前状态
  await page.screenshot({ path: '/tmp/moltbook-claim-step1.png' });
  
  console.log('✅ 请手动完成剩余步骤:');
  console.log('   1. 在浏览器中填写邮箱: EMAIL');
  console.log('   2. 点击认领/登录按钮');
  console.log('   3. 检查邮箱获取验证码');
  console.log('   4. 完成认领流程');
  
  // 保持浏览器打开，让用户手动操作
  console.log('\\n⏳ 浏览器保持打开状态，完成后手动关闭...');
  
})();
'''.replace('CLAIM_URL', CLAIM_URL).replace('EMAIL', EMAIL)
    
    # 保存脚本
    script_path = Path('/tmp/moltbook-claim.js')
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    return script_path

def manual_claim_guide():
    """手动认领指南"""
    guide = f"""
🎯 Moltbook 重新认领指南

📧 使用邮箱: {EMAIL}
🤖 Agent: {AGENT_NAME}
🆔 Agent ID: {AGENT_ID}

📋 认领步骤:

1️⃣ 打开认领链接:
   {CLAIM_URL}

2️⃣ 填写邮箱: {EMAIL}

3️⃣ 点击"认领"或"登录"按钮

4️⃣ 检查邮箱 (yiwan233@outlook.com) 获取验证码

5️⃣ 输入验证码完成认领

6️⃣ 记录新的 API Key:
   - 认领成功后会在页面显示
   - 保存到安全位置
   - 更新到 /clawd-data/moltbook-credentials.json

⚠️ 注意事项:
- 如果链接过期，需要去 Moltbook 官网重新生成
- 认领后原有 API Key 会失效
- 新 API Key 请妥善保管

🔗 相关链接:
- 官网: https://moltbook.com
- 我的主页: https://moltbook.com/u/{AGENT_NAME}
"""
    return guide

def main():
    print(manual_claim_guide())
    
    # 检查现有凭证
    cred_file = Path('/clawd-data/moltbook-credentials.json')
    if cred_file.exists():
        print("\n📄 现有凭证文件存在:")
        try:
            with open(cred_file, 'r') as f:
                data = json.load(f)
                print(f"   Agent: {data.get('agent_name')}")
                print(f"   状态: 需要重新认领")
        except:
            print("   无法读取")
    
    print("\n" + "="*60)
    print("💡 建议操作:")
    print("   1. 点击上面的认领链接")
    print("   2. 使用邮箱 yiwan233@outlook.com 登录")
    print("   3. 获取新的 API Key")
    print("   4. 告诉我新 API Key，我帮你更新配置")

if __name__ == "__main__":
    main()
