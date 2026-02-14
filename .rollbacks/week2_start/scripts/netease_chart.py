#!/usr/bin/env python3
"""
网易云音乐榜单推送 - 无需登录版
使用公开 API 获取热歌榜、飙升榜等
"""

import requests
import json
from datetime import datetime

# 榜单 ID
CHARTS = {
    "飙升榜": 19723756,
    "热歌榜": 3778678,
    "新歌榜": 3779629,
    "原创榜": 2884035,
    "Electro": 10520166,
    "ACG": 71384707
}

class NeteaseChart:
    """网易云榜单"""
    
    def __init__(self):
        self.base_url = "https://music.163.com/api"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
    
    def get_chart(self, chart_name="热歌榜", limit=5):
        """获取榜单"""
        chart_id = CHARTS.get(chart_name, 3778678)
        
        # 使用更简单可靠的 API
        url = f"https://music.163.com/api/playlist/detail"
        params = {
            "id": chart_id
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            
            if data.get("code") == 200 and data.get("result"):
                result = data["result"]
                tracks = result.get("tracks", [])[:limit]
                
                songs = []
                for i, track in enumerate(tracks, 1):
                    artists = ", ".join([a.get("name") for a in track.get("artists", [])])
                    songs.append({
                        "rank": i,
                        "name": track.get("name"),
                        "artist": artists,
                        "album": track.get("album", {}).get("name"),
                        "id": track.get("id")
                    })
                
                return {
                    "name": result.get("name", chart_name),
                    "description": result.get("description", ""),
                    "songs": songs
                }
        except Exception as e:
            print(f"❌ 获取失败: {e}")
        
        return None
    
    def get_daily_recommend(self):
        """获取每日推荐（匿名版 - 实际是热歌榜）"""
        return self.get_chart("热歌榜", 5)
    
    def format_message(self, chart_data):
        """格式化推送消息"""
        if not chart_data:
            return "❌ 获取榜单失败"
        
        lines = [
            f"🎵 **网易云{chart_data['name']}**",
            "",
            "碗皮锐评 💬",
            f"'{chart_data['description'][:30]}...'" if chart_data.get('description') else "",
            ""
        ]
        
        for song in chart_data['songs']:
            lines.append(f"{song['rank']}. **{song['name']}** - {song['artist']}")
            # 添加碗皮评论
            if song['rank'] == 1:
                lines.append("   💬 榜首！这首确实好听～")
            elif "周杰伦" in song['artist']:
                lines.append("   💬 杰伦的歌，经典！")
        
        lines.extend([
            "",
            f"🔗 https://music.163.com/discover/toplist",
            f"⏰ {datetime.now().strftime('%H:%M')} 更新"
        ])
        
        return "\n".join(lines)


def main():
    """测试"""
    chart = NeteaseChart()
    
    # 获取热歌榜
    data = chart.get_chart("热歌榜", 5)
    print(chart.format_message(data))


if __name__ == "__main__":
    main()
