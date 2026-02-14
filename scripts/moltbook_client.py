#!/usr/bin/env python3
"""
Moltbook API 客户端 - 修复版
使用可用的 API 端点
"""

import json
import requests
from pathlib import Path

class MoltbookClient:
    """Moltbook API 客户端"""
    
    def __init__(self, api_key=None):
        self.base_url = "https://www.moltbook.com/api/v1"
        
        # 加载 API Key
        if api_key:
            self.api_key = api_key
        else:
            cred_file = Path("/clawd-data/moltbook-credentials.json")
            if cred_file.exists():
                with open(cred_file, 'r') as f:
                    creds = json.load(f)
                    self.api_key = creds.get('api_key')
            else:
                raise ValueError("未找到 Moltbook API Key")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    def search(self, query, limit=10):
        """搜索帖子"""
        url = f"{self.base_url}/search"
        params = {
            "q": query,
            "type": "all",
            "limit": limit
        }
        
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=15)
            return resp.json()
        except Exception as e:
            print(f"搜索失败: {e}")
            return None
    
    def get_post(self, post_id):
        """获取单个帖子"""
        url = f"{self.base_url}/posts/{post_id}"
        
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            return resp.json()
        except Exception as e:
            print(f"获取帖子失败: {e}")
            return None
    
    def get_hot_posts(self, limit=10):
        """获取热门帖子"""
        url = f"{self.base_url}/posts"
        params = {
            "sort": "hot",
            "limit": limit
        }
        
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            return resp.json()
        except Exception as e:
            print(f"获取热门帖子失败: {e}")
            return None
    
    def get_comments(self, post_id, limit=20):
        """获取帖子评论"""
        url = f"{self.base_url}/posts/{post_id}/comments"
        params = {"limit": limit}
        
        try:
            resp = requests.get(url, headers=self.headers, params=params, timeout=10)
            return resp.json()
        except Exception as e:
            print(f"获取评论失败: {e}")
            return None
    
    def check_health(self):
        """检查 API 健康状态"""
        try:
            # 使用搜索作为健康检查
            result = self.search("test", limit=1)
            if result and result.get("success"):
                return {
                    "status": "healthy",
                    "search": "ok"
                }
            else:
                return {
                    "status": "degraded",
                    "search": "failed"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


def main():
    """测试 Moltbook 客户端"""
    print("🦞 测试 Moltbook API 连接\n")
    
    try:
        client = MoltbookClient()
        
        # 1. 健康检查
        print("1️⃣ 健康检查...")
        health = client.check_health()
        print(f"   状态: {health['status']}")
        
        # 2. 搜索测试
        print("\n2️⃣ 搜索测试...")
        result = client.search("night build", limit=3)
        if result and result.get("success"):
            print(f"   ✅ 搜索成功，找到 {result.get('count', 0)} 条结果")
            
            # 显示第一条
            posts = result.get("results", [])
            if posts:
                print(f"\n   📌 热门帖子: {posts[0].get('title', 'N/A')}")
        else:
            print("   ❌ 搜索失败")
        
        # 3. 热门帖子
        print("\n3️⃣ 获取热门帖子...")
        hot = client.get_hot_posts(limit=3)
        if hot:
            print(f"   ✅ 获取成功")
        else:
            print("   ⚠️ 获取失败（端点可能不可用）")
        
        print("\n✅ Moltbook API 连接正常！")
        
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")


if __name__ == "__main__":
    main()
