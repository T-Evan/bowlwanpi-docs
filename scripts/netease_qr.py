#!/usr/bin/env python3
"""
网易云音乐 - 二维码登录 (纯文本版本)
"""
import requests
import json
import base64
import os
import time
import urllib.parse
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

class NeteaseCrypto:
    MODULUS = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
    NONCE = '0CoJUm6Qyw8W8jud'
    PUBKEY = '010001'
    IV = '0102030405060708'
    
    @staticmethod
    def aes_encrypt(text, key):
        pad_len = 16 - len(text) % 16
        text = text + chr(pad_len) * pad_len
        cipher = Cipher(algorithms.AES(key.encode('utf-8')), modes.CBC(NeteaseCrypto.IV.encode('utf-8')), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(text.encode('utf-8')) + encryptor.finalize()
        return base64.b64encode(ciphertext).decode('utf-8')
    
    @staticmethod
    def rsa_encrypt(text, pubkey, modulus):
        text = text[::-1]
        text_bytes = text.encode('utf-8')
        text_int = int.from_bytes(text_bytes, 'big')
        pubkey_int = int(pubkey, 16)
        modulus_int = int(modulus, 16)
        result = pow(text_int, pubkey_int, modulus_int)
        return format(result, 'x').zfill(256)
    
    @staticmethod
    def encrypt(params):
        sec_key = ''.join([chr(ord('a') + (os.urandom(1)[0] % 26)) for _ in range(16)])
        text = json.dumps(params)
        enc_text = NeteaseCrypto.aes_encrypt(text, NeteaseCrypto.NONCE)
        enc_text = NeteaseCrypto.aes_encrypt(enc_text, sec_key)
        enc_sec_key = NeteaseCrypto.rsa_encrypt(sec_key, NeteaseCrypto.PUBKEY, NeteaseCrypto.MODULUS)
        return {'params': enc_text, 'encSecKey': enc_sec_key}

class NeteaseQRLogin:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://music.163.com/',
            'Origin': 'https://music.163.com',
        })
        self.crypto = NeteaseCrypto()
        self.cookies_file = '/root/.openclaw/workspace/secrets/netease_cookies.json'
        
    def weapi_request(self, endpoint, params=None):
        url = f'https://music.163.com/weapi{endpoint}'
        params = params or {}
        cookies = self.session.cookies.get_dict()
        params['csrf_token'] = cookies.get('__csrf', '')
        data = self.crypto.encrypt(params)
        try:
            response = self.session.post(url, data=data, timeout=15)
            return response.json()
        except Exception as e:
            return {'code': -1, 'msg': str(e)}
    
    def get_qr_key(self):
        result = self.weapi_request('/login/qrcode/unikey', {'type': '1'})
        if result.get('code') == 200:
            return result.get('unikey')
        return None
    
    def get_qr_url(self, key):
        """获取二维码图片URL"""
        return f'https://music.163.com/login?codekey={key}'
    
    def get_qr_base64(self, key):
        """获取base64编码的二维码图片"""
        # 使用网易云的二维码生成接口
        qr_url = f'https://music.163.com/weapi/login/qrcode/create?key={key}'
        result = self.weapi_request('/login/qrcode/create', {'key': key, 'qrimg': 'true'})
        if result.get('code') == 200:
            return result.get('data', {}).get('qrimg')  # base64图片
        return None
    
    def check_qr_status(self, key):
        result = self.weapi_request('/login/qrcode/client/login', {'key': key, 'type': '1'})
        return result
    
    def save_cookies(self):
        os.makedirs(os.path.dirname(self.cookies_file), exist_ok=True)
        with open(self.cookies_file, 'w') as f:
            json.dump(dict(self.session.cookies), f)
        print("💾 登录状态已保存")
    
    def load_cookies(self):
        try:
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
                self.session.cookies.update(cookies)
                return True
        except:
            return False

def generate_qr():
    """生成二维码并等待登录"""
    client = NeteaseQRLogin()
    
    key = client.get_qr_key()
    if not key:
        print("❌ 获取二维码失败")
        return False
    
    # 获取二维码base64图片
    qr_base64 = client.get_qr_base64(key)
    
    print("🎵 网易云音乐二维码登录")
    print("=" * 50)
    print("📱 请使用网易云音乐App扫描下方二维码")
    print("=" * 50)
    
    if qr_base64:
        # 保存二维码图片
        qr_path = '/tmp/netease_qr.png'
        with open(qr_path, 'wb') as f:
            f.write(base64.b64decode(qr_base64.split(',')[1] if ',' in qr_base64 else qr_base64))
        print(f"\n📍 二维码图片已保存: {qr_path}")
        print(f"🔑 Key: {key}")
    else:
        # 备用：显示URL
        qr_url = client.get_qr_url(key)
        print(f"\n🔗 登录URL: {qr_url}")
        print(f"🔑 Key: {key}")
        print("\n⚠️ 请手动复制URL到浏览器，或使用二维码生成工具")
    
    print("\n⏳ 等待扫码... (120秒超时)")
    print("-" * 50)
    
    # 轮询检查状态
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < 120:
        result = client.check_qr_status(key)
        code = result.get('code')
        
        if code != last_status:
            if code == 800:
                print("⏳ 等待扫码...")
            elif code == 801:
                print("📱 已扫码，请在App中确认登录")
            elif code == 802:
                print("✅ 已确认，正在登录...")
            elif code == 803:
                print("🎉 登录成功！")
                client.save_cookies()
                return True
            else:
                msg = result.get('message', result.get('msg', f'状态码: {code}'))
                print(f"⚠️ {msg}")
            last_status = code
        
        time.sleep(3)
    
    print("\n❌ 登录超时")
    return False

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 netease_qr.py login   - 生成二维码并登录")
        print("  python3 netease_qr.py status  - 检查登录状态")
        return
    
    cmd = sys.argv[1]
    
    if cmd == 'login':
        if generate_qr():
            print("\n✅ 登录完成！可以获取日推了")
        else:
            print("\n❌ 登录失败")
    
    elif cmd == 'status':
        client = NeteaseQRLogin()
        if client.load_cookies():
            print("✅ 已保存登录状态")
        else:
            print("❌ 未登录")

if __name__ == '__main__':
    main()
