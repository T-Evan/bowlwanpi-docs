#!/usr/bin/env python3
"""
网易云音乐API客户端 - 简化版
使用网易云公开API获取数据
"""
import requests
import json
import hashlib
import base64
from datetime import datetime

class NeteaseMusicAPI:
    """网易云音乐API客户端"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0',
            'Referer': 'https://music.163.com/',
            'Accept': 'application/json, text/plain, */*'
        })
        self.base_url = 'https://music.163.com/api'
        self.phone = None
        
    def send_captcha(self, phone):
        """发送验证码"""
        url = 'https://music.163.com/weapi/sms/captcha/sent'
        params = {
            'cellphone': phone,
            'ctcode': '86'
        }
        try:
            response = self.session.post(url, data=params)
            result = response.json()
            if result.get('code') == 200:
                print(f"✅ 验证码已发送到 {phone}")
                self.phone = phone
                return True
            else:
                print(f"❌ 发送失败: {result.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 请求错误: {e}")
            return False
    
    def login_with_captcha(self, phone, captcha):
        """使用验证码登录"""
        url = 'https://music.163.com/weapi/login/cellphone'
        params = {
            'phone': phone,
            'captcha': captcha,
            'countrycode': '86',
            'rememberLogin': 'true'
        }
        try:
            response = self.session.post(url, data=params)
            result = response.json()
            if result.get('code') == 200:
                print(f"✅ 登录成功! 用户: {result.get('profile', {}).get('nickname', '未知')}")
                # 保存cookies
                self.save_cookies()
                return True
            else:
                print(f"❌ 登录失败: {result.get('message', '未知错误')}")
                return False
        except Exception as e:
            print(f"❌ 请求错误: {e}")
            return False
    
    def save_cookies(self):
        """保存登录状态"""
        with open('/root/.openclaw/workspace/secrets/netease_cookies.json', 'w') as f:
            json.dump(dict(self.session.cookies), f)
        print("💾 Cookies已保存")
    
    def load_cookies(self):
        """加载登录状态"""
        try:
            with open('/root/.openclaw/workspace/secrets/netease_cookies.json', 'r') as f:
                cookies = json.load(f)
                self.session.cookies.update(cookies)
                print("💾 Cookies已加载")
                return True
        except FileNotFoundError:
            return False
    
    def get_recommend_songs(self):
        """获取每日推荐歌曲"""
        url = 'https://music.163.com/weapi/v1/discovery/recommend/songs'
        try:
            response = self.session.post(url)
            result = response.json()
            if result.get('code') == 200:
                songs = result.get('data', {}).get('dailySongs', [])
                return songs[:10]  # 返回前10首
            else:
                print(f"❌ 获取失败: {result.get('message', '未知错误')}")
                return []
        except Exception as e:
            print(f"❌ 请求错误: {e}")
            return []
    
    def get_toplist(self, idx=0):
        """获取榜单 (无需登录)"""
        # 0: 飙升榜, 1: 新歌榜, 2: 原创榜, 3: 热歌榜
        toplist_ids = [19723756, 3779629, 2884035, 3778678]
        url = f'https://music.163.com/api/playlist/detail?id={toplist_ids[idx]}'
        try:
            response = self.session.get(url)
            result = response.json()
            if result.get('code') == 200:
                tracks = result.get('result', {}).get('tracks', [])
                return tracks[:10]
            return []
        except Exception as e:
            print(f"❌ 请求错误: {e}")
            return []

def format_song_list(songs, title="🎵 今日推荐"):
    """格式化歌曲列表"""
    output = [f"{title}", "=" * 40]
    for i, song in enumerate(songs, 1):
        name = song.get('name', '未知')
        artists = ', '.join([a.get('name', '未知') for a in song.get('artists', [])])
        album = song.get('album', {}).get('name', '未知专辑')
        output.append(f"{i}. {name} - {artists}")
        output.append(f"   💿 {album}")
    return '\n'.join(output)

if __name__ == '__main__':
    import sys
    api = NeteaseMusicAPI()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == 'send_captcha' and len(sys.argv) > 2:
            phone = sys.argv[2]
            api.send_captcha(phone)
            
        elif cmd == 'login' and len(sys.argv) > 3:
            phone = sys.argv[2]
            captcha = sys.argv[3]
            api.login_with_captcha(phone, captcha)
            
        elif cmd == 'daily':
            if api.load_cookies():
                songs = api.get_recommend_songs()
                if songs:
                    print(format_song_list(songs, "🎵 网易云日推"))
                else:
                    print("❌ 获取日推失败，可能需要重新登录")
            else:
                print("❌ 未登录，请先登录")
                
        elif cmd == 'toplist':
            songs = api.get_toplist(0)
            if songs:
                print(format_song_list(songs, "🎵 网易云飙升榜"))
            else:
                print("❌ 获取榜单失败")
    else:
        print("用法:")
        print("  python3 netease_api.py send_captcha <手机号>")
        print("  python3 netease_api.py login <手机号> <验证码>")
        print("  python3 netease_api.py daily")
        print("  python3 netease_api.py toplist")
