#!/usr/bin/env python3
"""
网易云音乐日推 + 评论区风格/情绪分析
"""

import requests
import json
import os
import subprocess

COOKIE_FILE = '/root/.openclaw/workspace/netease-music/netease-cookie.json'

def load_cookie():
    """加载 cookie"""
    try:
        with open(COOKIE_FILE, 'r') as f:
            data = json.load(f)
            return data.get('cookie')
    except:
        return None

def get_daily_recommend(cookie):
    """获取日推"""
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
    except Exception as e:
        print(f"获取日推失败: {e}")
    return None

def get_comments(song_id, cookie):
    """获取歌曲热门评论"""
    url = f"https://music.163.com/api/v1/resource/comments/R_SO_4_{song_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://music.163.com/",
        "Cookie": cookie
    }
    params = {"limit": 15}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        data = response.json()
        comments = data.get("hotComments", []) or data.get("comments", [])
        return [c.get("content", "") for c in comments[:10]]
    except Exception as e:
        print(f"获取评论失败: {e}")
        return []

def analyze_comments(comments):
    """分析评论的风格和情绪"""
    if not comments:
        return None, None
    
    # 简单的关键词匹配分析
    text = " ".join(comments).lower()
    
    # 情绪关键词
    emotions = {
        "治愈": ["温暖", "治愈", "温柔", "安慰", "暖心", "感动", "泪目"],
        "伤感": ["难过", "悲伤", "遗憾", "失恋", "孤独", "寂寞", "哭"],
        "快乐": ["开心", "快乐", "欢乐", "愉快", "嗨", "爽", "棒"],
        "怀旧": ["回忆", "青春", "过去", "曾经", "以前", "时光", " nostalgic"],
        "浪漫": ["浪漫", "爱情", "甜蜜", "心动", "喜欢", "爱"],
        "励志": ["加油", "努力", "奋斗", "坚持", "梦想", "希望"],
        "放松": ["放松", "舒服", "惬意", "安静", "平静", "轻松"]
    }
    
    # 风格关键词
    styles = {
        "流行": ["好听", "洗脑", "上头", "单曲循环"],
        "民谣": ["故事", "民谣", "吉他", "诗意", "远方", "家乡"],
        "摇滚": ["燃", "炸", "燥", "激情", "力量"],
        "电子": ["节奏", "电子", "dj", "蹦迪", "律动"],
        "说唱": ["说唱", "rap", "flow", "押韵", "炸"],
        "R&B": ["r&b", "soul", "慵懒", "性感"]
    }
    
    # 统计
    emotion_scores = {}
    for emotion, keywords in emotions.items():
        score = sum(1 for k in keywords if k in text)
        if score > 0:
            emotion_scores[emotion] = score
    
    style_scores = {}
    for style, keywords in styles.items():
        score = sum(1 for k in keywords if k in text)
        if score > 0:
            style_scores[style] = score
    
    # 返回最高分的
    top_emotion = max(emotion_scores, key=emotion_scores.get) if emotion_scores else None
    top_style = max(style_scores, key=style_scores.get) if style_scores else None
    
    return top_emotion, top_style

def format_song(song, emotion=None, style=None):
    """格式化单首歌曲信息"""
    name = song.get("name", "未知")
    
    # 歌手
    artists = song.get("ar", song.get("artists", []))
    artist_names = [a.get("name", "") for a in artists if isinstance(a, dict)]
    artist_str = ", ".join(artist_names) if artist_names else "未知歌手"
    
    # 专辑
    album = ""
    if song.get("al"):
        album = song.get("al", {}).get("name", "")
    elif song.get("album"):
        album = song.get("album", {}).get("name", "")
    
    # 链接
    song_id = song.get("id", "")
    song_url = f"https://music.163.com/song?id={song_id}" if song_id else ""
    
    # 构建输出
    lines = [f"🎵 {name}"]
    lines.append(f"   🎤 {artist_str}")
    if album:
        lines.append(f"   💿 {album}")
    if song_url:
        lines.append(f"   🔗 {song_url}")
    
    # 添加风格和情绪标签
    tags = []
    if style:
        tags.append(style)
    if emotion:
        tags.append(emotion)
    if tags:
        lines.append(f"   🏷️ {' | '.join(tags)}")
    
    return "\n".join(lines)

def main():
    cookie = load_cookie()
    if not cookie:
        print("错误：未找到登录信息")
        return
    
    print("🎵 网易云音乐 - 每日推荐")
    print("=" * 50)
    print("💡 从评论区分析歌曲风格与情绪\n")
    
    songs = get_daily_recommend(cookie)
    if not songs:
        print("获取日推失败")
        return
    
    # 只分析前5首，避免太慢
    for i, song in enumerate(songs[:5], 1):
        print(f"\n【{i}】", end="")
        
        # 获取评论
        song_id = song.get("id")
        if song_id:
            comments = get_comments(song_id, cookie)
            emotion, style = analyze_comments(comments)
            print(format_song(song, emotion, style))
        else:
            print(format_song(song))

if __name__ == "__main__":
    main()
