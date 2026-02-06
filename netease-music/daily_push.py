#!/usr/bin/env python3
"""
网易云音乐日推推送
每天早上自动获取并推送日推
"""

import requests
import json
import os
import sys

COOKIE_FILE = '/root/.openclaw/workspace/netease-music/netease-cookie.json'

def load_cookie():
    """加载保存的 cookie"""
    try:
        with open(COOKIE_FILE, 'r') as f:
            data = json.load(f)
            return data.get('cookie')
    except:
        return None

def get_daily_recommend(cookie):
    """获取每日推荐"""
    url = "https://music.163.com/api/v3/discovery/recommend/songs"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://music.163.com/",
        "Cookie": cookie
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        data = response.json()
        
        if data.get("code") == 200:
            return data.get("data", {}).get("dailySongs", [])
        else:
            print(f"API 错误: {data}")
            return None
    except Exception as e:
        print(f"请求失败: {e}")
        return None

def format_songs(songs, limit=10):
    """格式化歌曲列表"""
    if not songs:
        return "暂无日推歌曲，请检查登录状态"
    
    lines = []
    lines.append("🎵 网易云音乐 - 每日推荐")
    lines.append("=" * 40)
    lines.append("")
    
    for i, song in enumerate(songs[:limit], 1):
        name = song.get("name", "未知")
        
        # 获取歌手信息（可能有多个字段）
        artists = song.get("artists", [])
        if not artists:
            artists = song.get("ar", [])
        
        artist_names = []
        for a in artists:
            if isinstance(a, dict):
                artist_names.append(a.get("name", "未知"))
        
        artist_str = ", ".join(artist_names) if artist_names else "未知歌手"
        
        # 获取专辑信息
        album = ""
        if song.get("album"):
            album = song.get("album", {}).get("name", "")
        elif song.get("al"):
            album = song.get("al", {}).get("name", "")
        
        # 获取歌曲链接
        song_id = song.get("id", "")
        song_url = f"https://music.163.com/song?id={song_id}" if song_id else ""
        
        lines.append(f"{i}. {name}")
        lines.append(f"   🎤 {artist_str}")
        if album:
            lines.append(f"   💿 {album}")
        if song_url:
            lines.append(f"   🔗 {song_url}")
        lines.append("")
    
    return "\n".join(lines)

def main():
    cookie = load_cookie()
    if not cookie:
        print("错误：未找到登录信息，请先完成二维码登录")
        sys.exit(1)
    
    print("正在获取网易云日推...")
    songs = get_daily_recommend(cookie)
    
    if songs:
        message = format_songs(songs)
        print(message)
    else:
        print("获取日推失败，可能需要重新登录")
        sys.exit(1)

if __name__ == "__main__":
    main()
