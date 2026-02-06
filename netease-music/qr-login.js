const { login_qr_create, login_qr_check } = require('NeteaseCloudMusicApi')
const QRCode = require('qrcode')
const fs = require('fs')
const path = require('path')

// 保存 cookie 的文件
const COOKIE_FILE = path.join(__dirname, 'netease-cookie.json')

// 生成二维码
async function generateQRCode() {
    try {
        console.log('正在获取登录二维码...')
        const result = await login_qr_create({
            cookie: '',
        })
        
        if (result.status !== 200) {
            console.error('获取二维码失败:', result)
            process.exit(1)
        }
        
        console.log('API返回:', JSON.stringify(result.body, null, 2))
        
        const data = result.body.data
        const qrurl = data.qrurl || data.url
        const key = data.key || data.unikey
        
        // 生成二维码图片
        const qrPath = '/tmp/netease-qr.png'
        await QRCode.toFile(qrPath, qrurl, {
            width: 300,
            margin: 2,
            color: {
                dark: '#000000',
                light: '#ffffff'
            }
        })
        
        console.log('二维码已生成:', qrPath)
        console.log('QR Key:', key)
        console.log('QR URL:', qrurl)
        
        // 保存 key 用于后续检查
        fs.writeFileSync('/tmp/netease-qr-key.json', JSON.stringify({ key, time: Date.now() }))
        
        return { key, qrPath }
    } catch (error) {
        console.error('生成二维码出错:', error)
        process.exit(1)
    }
}

// 检查登录状态
async function checkLogin(key) {
    try {
        const result = await login_qr_check({
            key: key,
            cookie: '',
        })
        
        const { code, cookie, message } = result.body
        
        // 800: 二维码过期, 801: 等待扫码, 802: 等待确认, 803: 授权成功
        if (code === 803) {
            console.log('登录成功！')
            console.log('Cookie:', cookie)
            
            // 保存 cookie
            fs.writeFileSync(COOKIE_FILE, JSON.stringify({
                cookie,
                time: Date.now()
            }))
            
            return { success: true, cookie }
        } else if (code === 800) {
            console.log('二维码已过期，请重新生成')
            return { success: false, expired: true }
        } else if (code === 801) {
            console.log('等待扫码...')
            return { success: false, waiting: true }
        } else if (code === 802) {
            console.log('已扫码，等待确认...')
            return { success: false, confirming: true }
        } else {
            console.log('状态:', code, message)
            return { success: false, message }
        }
    } catch (error) {
        console.error('检查登录出错:', error)
        return { success: false, error }
    }
}

// 主函数
async function main() {
    const action = process.argv[2]
    
    if (action === 'generate') {
        await generateQRCode()
    } else if (action === 'check') {
        const keyData = JSON.parse(fs.readFileSync('/tmp/netease-qr-key.json', 'utf8'))
        await checkLogin(keyData.key)
    } else {
        console.log('Usage: node qr-login.js [generate|check]')
    }
}

main()
