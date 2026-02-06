const { login_qr_check } = require('NeteaseCloudMusicApi');
const fs = require('fs');

const KEY_FILE = '/tmp/netease-qr-key.txt';
const COOKIE_FILE = '/root/.openclaw/workspace/netease-music/netease-cookie.json';

async function checkLogin() {
    const unikey = fs.readFileSync(KEY_FILE, 'utf8').trim();
    console.log('检查登录状态，Key:', unikey);
    
    const result = await login_qr_check({
        key: unikey
    });
    
    console.log('返回结果:', JSON.stringify(result.body, null, 2));
    
    const { code, cookie, message } = result.body;
    
    // 800: 过期, 801: 等待扫码, 802: 等待确认, 803: 登录成功
    if (code === 803) {
        console.log('✅ 登录成功！');
        
        // 保存 cookie
        fs.writeFileSync(COOKIE_FILE, JSON.stringify({
            cookie: cookie,
            time: Date.now(),
            key: unikey
        }, null, 2));
        
        console.log('Cookie 已保存到:', COOKIE_FILE);
        process.exit(0);
    } else if (code === 800) {
        console.log('❌ 二维码已过期，需要重新生成');
        process.exit(1);
    } else if (code === 801) {
        console.log('⏳ 等待扫码...');
        process.exit(2);
    } else if (code === 802) {
        console.log('👀 已扫码，等待确认...');
        process.exit(3);
    } else {
        console.log('未知状态:', code, message);
        process.exit(4);
    }
}

checkLogin().catch(err => {
    console.error('检查出错:', err);
    process.exit(5);
});
