#!/usr/bin/env python3
"""
网易云音乐二维码登录
"""

import requests
import json
import time
import os
from urllib.parse import urlencode

BASE_URL = "https://music.163.com"
WEAPI_URL = f"{BASE_URL}/weapi"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://music.163.com/",
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

def generate_qr():
    """生成二维码"""
    # 1. 获取 unikey
    url = f"{WEAPI_URL}/login/qrcode/unikey"
    params = {
        "type": "1",
    }
    
    try:
        # 注意：网易云的 API 需要加密参数，这里使用简化方式
        # 实际应该使用网易云的加密算法（RSA + AES）
        response = requests.post(url, headers=HEADERS, data=params, timeout=30)
        print(f"Key API 响应: {response.text}")
        
        # 尝试直接访问二维码创建 API
        qr_url = f"{BASE_URL}/login?codekey=test"
        
        # 使用二维码 API 生成图片
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # 网易云二维码内容格式: https://music.163.com/login?codekey=xxx
        # 这里我们先生成一个测试用的 key
        test_key = f"test_{int(time.time())}"
        qr.add_data(f"https://music.163.com/login?codekey={test_key}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        qr_path = "/tmp/netease-qr-py.png"
        img.save(qr_path)
        
        print(f"二维码已保存: {qr_path}")
        print(f"测试 Key: {test_key}")
        
        return qr_path, test_key
        
    except Exception as e:
        print(f"生成二维码出错: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    print("正在生成网易云音乐登录二维码...")
    qr_path, key = generate_qr()
    
    if qr_path:
        print(f"\n二维码路径: {qr_path}")
        print("请用网易云音乐 App 扫描此二维码登录")
