#!/usr/bin/env python3
"""
网易云音乐扫码登录 - Python 版本
"""
import requests
import json
import os
import time

COOKIE_FILE = "/root/.openclaw/workspace/netease-music/netease-cookie.json"

def generate_qr():
    """生成二维码"""
    url = "https://music.163.com/weapi/login/qrcode/unikey"
    params = {
        "type": "1"
    }
    
    try:
        response = requests.post(url, data=params, timeout=10)
        data = response.json()
        
        if data.get('code') == 200:
            unikey = data.get('unikey')
            qrurl = f"https://music.163.com/login?codekey={unikey}"
            
            print("🎵 网易云音乐登录")
            print("="*50)
            print(f"\n请用网易云音乐APP扫描以下二维码：")
            print(f"\n{qrurl}")
            print(f"\nKey: {unikey}")
            
            # 保存 key
            with open('/tmp/netease-qr-key.txt', 'w') as f:
                f.write(unikey)
            
            return unikey
        else:
            print(f"生成二维码失败: {data}")
            return None
    except Exception as e:
        print(f"错误: {e}")
        return None

def check_login(unikey):
    """检查登录状态"""
    url = "https://music.163.com/weapi/login/qrcode/client/login"
    params = {
        "key": unikey,
        "type": "1"
    }
    
    try:
        response = requests.post(url, data=params, timeout=10)
        data = response.json()
        
        code = data.get('code')
        
        if code == 803:
            print("✅ 登录成功！")
            cookie = response.headers.get('Set-Cookie', '')
            
            # 保存 cookie
            with open(COOKIE_FILE, 'w') as f:
                json.dump({
                    'cookie': cookie,
                    'time': int(time.time() * 1000)
                }, f, indent=2)
            
            print(f"Cookie 已保存")
            return True
        elif code == 800:
            print("❌ 二维码已过期")
            return False
        elif code == 801:
            print("⏳ 等待扫码...")
            return None
        elif code == 802:
            print("👀 已扫码，等待确认...")
            return None
        else:
            print(f"状态: {code}, {data.get('message', '')}")
            return None
    except Exception as e:
        print(f"检查出错: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2 or sys.argv[1] == 'generate':
        key = generate_qr()
        if key:
            print("\n二维码已生成，请用网易云APP扫描")
            print("扫描后运行: python3 qr_login.py check")
    elif sys.argv[1] == 'check':
        if os.path.exists('/tmp/netease-qr-key.txt'):
            with open('/tmp/netease-qr-key.txt', 'r') as f:
                key = f.read().strip()
            check_login(key)
        else:
            print("请先运行 generate 生成二维码")
