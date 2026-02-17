#!/usr/bin/env python3
"""
批量下载B站表情包 - 目标100个
"""

import requests
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

STICKERS_DIR = Path("/root/.openclaw/media/stickers/real_memes")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://t.bilibili.com/"
}

def download_emote(emote, index):
    """下载单个表情包"""
    try:
        resp = requests.get(emote["url"], headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            ext = emote["url"].split(".")[-1].split("?")[0]
            if ext not in ["png", "jpg", "gif", "webp"]:
                ext = "png"
            
            # 清理文件名
            safe_name = "".join(c for c in emote["name"] if c.isalnum() or c in "_-").strip("_")[:15]
            filename = f"bili_{index:03d}_{safe_name}.{ext}"
            filepath = STICKERS_DIR / filename
            
            with open(filepath, "wb") as f:
                f.write(resp.content)
            
            return True, filename, len(resp.content)
    except Exception as e:
        pass
    return False, emote.get("name", "unknown"), 0

def fetch_all_emotes():
    """获取所有表情包"""
    url = "https://api.bilibili.com/x/emote/user/panel/web?business=reply"
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        data = resp.json()
        
        if data.get("code") == 0:
            packages = data["data"]["packages"]
            
            all_emotes = []
            for pkg in packages:
                pkg_name = pkg.get("text", "")
                for emote in pkg.get("emote", []):
                    all_emotes.append({
                        "name": emote["text"].strip("[]"),
                        "url": emote["url"],
                        "package": pkg_name
                    })
            
            return all_emotes
    except Exception as e:
        print(f"获取失败: {e}")
    
    return []

def main():
    print("🎭 批量下载B站表情包...")
    print(f"📁 保存目录: {STICKERS_DIR}")
    
    STICKERS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 获取所有表情包
    print("\n🔍 正在获取表情包列表...")
    all_emotes = fetch_all_emotes()
    print(f"✅ 找到 {len(all_emotes)} 个表情包")
    
    if len(all_emotes) < 100:
        print(f"⚠️ 只有 {len(all_emotes)} 个，尝试获取其他来源...")
    
    # 批量下载
    target = min(100, len(all_emotes))
    print(f"\n📥 开始下载 {target} 个表情包...")
    
    downloaded = 0
    failed = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(download_emote, emote, i): emote 
            for i, emote in enumerate(all_emotes[:target])
        }
        
        for future in as_completed(futures):
            success, name, size = future.result()
            if success:
                downloaded += 1
                if downloaded % 10 == 0:
                    print(f"  ✅ 已下载 {downloaded}/{target}")
            else:
                failed += 1
    
    print(f"\n🎉 下载完成！")
    print(f"  ✅ 成功: {downloaded}")
    print(f"  ❌ 失败: {failed}")
    
    # 统计
    files = list(STICKERS_DIR.glob("bili_*.png")) + list(STICKERS_DIR.glob("bili_*.jpg"))
    print(f"\n📊 当前共有 {len(files)} 个表情包")
    
    # 显示前10个
    print(f"\n📋 部分表情包:")
    for f in sorted(files)[:10]:
        print(f"  - {f.name}")

if __name__ == "__main__":
    main()
