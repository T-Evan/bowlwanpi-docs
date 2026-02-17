#!/usr/bin/env python3
"""
表情包下载器 v1.0
从表情包网站爬取热门表情包
"""

import os
import requests
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

STICKER_DIR = Path("/root/.openclaw/media/stickers/memes")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def download_image(url, filename):
    """下载图片"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            filepath = STICKER_DIR / filename
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"下载失败 {url}: {e}")
    return False

def fetch_fabiaoqing():
    """从发表情网站获取"""
    print("🔍 正在搜索发表情...")
    
    # 热门表情包页面
    url = "https://www.fabiaoqing.com/biaoqing/lists/page/1.html"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"访问失败: {response.status_code}")
            return []
        
        # 提取图片URL
        img_urls = re.findall(r'https?://[^\s\"]+\.(?:jpg|jpeg|png|gif)', response.text)
        
        # 去重并限制数量
        unique_urls = list(set(img_urls))[:10]
        print(f"找到 {len(unique_urls)} 个表情包")
        
        return unique_urls
    except Exception as e:
        print(f"爬取失败: {e}")
        return []

def fetch_doutula():
    """从斗图啦获取"""
    print("🔍 正在搜索斗图啦...")
    
    url = "https://www.doutula.com/article/list/"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, proxies={"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"})
        if response.status_code != 200:
            print(f"访问失败: {response.status_code}")
            return []
        
        # 提取图片URL
        img_urls = re.findall(r'https?://[^\s\"]+\.(?:jpg|jpeg|png|gif)', response.text)
        
        unique_urls = list(set(img_urls))[:10]
        print(f"找到 {len(unique_urls)} 个表情包")
        
        return unique_urls
    except Exception as e:
        print(f"爬取失败: {e}")
        return []

def fetch_sogou():
    """从搜狗表情包获取"""
    print("🔍 正在搜索搜狗表情包...")
    
    # 搜狗表情包搜索
    url = "https://pic.sogou.com/pic/emo/list.jsp?id=403406&rf=search"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, proxies={"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"})
        if response.status_code != 200:
            print(f"访问失败: {response.status_code}")
            return []
        
        # 提取图片URL
        img_urls = re.findall(r'https?://[^\s\"]+\.(?:jpg|jpeg|png|gif)', response.text)
        
        unique_urls = list(set(img_urls))[:10]
        print(f"找到 {len(unique_urls)} 个表情包")
        
        return unique_urls
    except Exception as e:
        print(f"爬取失败: {e}")
        return []

def main():
    """主函数"""
    print("🎭 表情包下载器启动...")
    print(f"📁 保存目录: {STICKER_DIR}")
    
    # 确保目录存在
    STICKER_DIR.mkdir(parents=True, exist_ok=True)
    
    all_urls = []
    
    # 从多个源获取
    all_urls.extend(fetch_fabiaoqing())
    all_urls.extend(fetch_doutula())
    all_urls.extend(fetch_sogou())
    
    if not all_urls:
        print("⚠️ 没有找到表情包，尝试备用方案...")
        # 使用一些已知的表情包URL
        backup_urls = [
            "https://i.imgur.com/8Km9tLL.jpg",  # doge
            "https://i.imgur.com/2k0l2UQ.jpg",  # 滑稽
            "https://i.imgur.com/4tUQ3qQ.jpg",  # 熊猫头
        ]
        all_urls = backup_urls
    
    print(f"\n📥 开始下载 {len(all_urls)} 个表情包...")
    
    downloaded = 0
    for i, url in enumerate(all_urls[:15]):  # 最多下载15个
        ext = url.split('.')[-1].split('?')[0][:4]  # 获取扩展名
        if ext not in ['jpg', 'jpeg', 'png', 'gif']:
            ext = 'jpg'
        
        filename = f"meme_{i+1:02d}.{ext}"
        
        if download_image(url, filename):
            print(f"✅ 已下载: {filename}")
            downloaded += 1
        else:
            print(f"❌ 失败: {url[:50]}...")
    
    print(f"\n🎉 下载完成！成功 {downloaded}/{len(all_urls)} 个")
    print(f"📂 保存位置: {STICKER_DIR}")
    
    # 列出文件
    files = list(STICKER_DIR.glob("meme_*"))
    print(f"\n📋 已下载文件:")
    for f in files:
        print(f"  - {f.name} ({f.stat().st_size/1024:.1f} KB)")

if __name__ == "__main__":
    main()
