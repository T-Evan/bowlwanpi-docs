#!/usr/bin/env python3
"""
网易云音乐日推推送脚本
调用网易云 API 获取每日推荐歌曲
"""

import requests
import json
import sys
import os

# API 基础地址
BASE_URL = "https://music.163.com/api"

def get_daily_recommend(cookie=None):
    """获取每日推荐歌曲"""
    url = f"{BASE_URL}/v3/discovery/recommend/songs"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://music.163.com/",
    }
    
    try:
        if cookie:
            headers["Cookie"] = cookie
        
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        
        if data.get("code") == 200:
            songs = data.get("data", {}).get("dailySongs", [])
            return songs
        else:
            print(f"API 错误: {data.get('msg', '未知错误')}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def format_song_list(songs, limit=10):
    """格式化歌曲列表"""
    if not songs:
        return "暂无日推歌曲"
    
    result = []
    result.append("🎵 网易云音乐 - 每日推荐\n")
    result.append("=" * 30)
    
    for i, song in enumerate(songs[:limit], 1):
        name = song.get("name", "未知")
        artists = ", ".join([a.get("name", "未知") for a in song.get("artists", [])])
        album = song.get("album", {}).get("name", "未知")
        
        result.append(f"\n{i}. {name}")
        result.append(f"   歌手: {artists}")
        result.append(f"   专辑: {album}")
    
    return "\n".join(result)

if __name__ == "__main__":
    # 从环境变量读取 cookie（如果有登录）
    cookie = os.environ.get("NETEASE_COOKIE")
    
    print("正在获取网易云日推...")
    songs = get_daily_recommend(cookie)
    
    if songs:
        print(format_song_list(songs))
    else:
        print("获取失败，可能需要登录")
        sys.exit(1)
