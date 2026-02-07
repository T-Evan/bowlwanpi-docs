"""
memU 记忆客户端 - BowlWanpi 版
使用 HTTP API 直接调用 memU 服务
"""
import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional

class BowlWanpiMemory:
    """
    BowlWanpi 的记忆系统 - 基于 memU API
    """
    
    def __init__(self):
        # 从安全位置加载凭证
        self.credentials_path = os.path.expanduser("~/.openclaw/workspace/secrets/memu-credentials.json")
        self.api_key = self._load_api_key()
        self.base_url = "https://api.memu.pro/v1"
        self.user_id = "bowlwanpi_user_001"  # 一碗的用户ID
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.enabled = self.api_key != ""
    
    def _load_api_key(self) -> str:
        """从安全文件加载 API Key"""
        try:
            with open(self.credentials_path, 'r') as f:
                creds = json.load(f)
                return creds.get("api_key", "")
        except Exception as e:
            print(f"[Memory] 无法加载 API Key: {e}")
            return ""
    
    def memorize(self, content: str, metadata: Dict = None) -> bool:
        """
        存储记忆到 memU
        
        Args:
            content: 要记忆的内容
            metadata: 元数据（如时间、类型等）
        """
        try:
            payload = {
                "user_id": self.user_id,
                "content": content,
                "metadata": metadata or {
                    "timestamp": datetime.now().isoformat(),
                    "type": "conversation",
                    "agent": "bowlwanpi"
                }
            }
            
            response = requests.post(
                f"{self.base_url}/memorize",
                headers=self.headers,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"[Memory] ✅ 已存储: {content[:50]}...")
                return True
            else:
                print(f"[Memory] ❌ 存储失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"[Memory] ❌ 错误: {e}")
            return False
    
    def retrieve(self, query: str, limit: int = 5) -> List[Dict]:
        """
        从 memU 检索相关记忆
        
        Args:
            query: 查询内容
            limit: 返回结果数量
            
        Returns:
            相关记忆列表
        """
        try:
            payload = {
                "user_id": self.user_id,
                "query": query,
                "limit": limit
            }
            
            response = requests.post(
                f"{self.base_url}/retrieve",
                headers=self.headers,
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                results = response.json().get("memories", [])
                print(f"[Memory] ✅ 检索到 {len(results)} 条记忆")
                return results
            else:
                print(f"[Memory] ❌ 检索失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"[Memory] ❌ 错误: {e}")
            return []
    
    def get_user_profile(self) -> Dict:
        """获取用户画像（偏好、习惯等）"""
        try:
            response = requests.get(
                f"{self.base_url}/profile/{self.user_id}",
                headers=self.headers,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {}
                
        except Exception as e:
            print(f"[Memory] ❌ 获取画像失败: {e}")
            return {}
    
    def forget(self, memory_id: str) -> bool:
        """删除特定记忆"""
        try:
            response = requests.delete(
                f"{self.base_url}/memory/{memory_id}",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def summarize_memories(self, days: int = 7) -> str:
        """生成近期记忆摘要"""
        try:
            payload = {
                "user_id": self.user_id,
                "days": days
            }
            
            response = requests.post(
                f"{self.base_url}/summarize",
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json().get("summary", "")
            else:
                return ""
                
        except Exception as e:
            print(f"[Memory] ❌ 摘要生成失败: {e}")
            return ""


# 便捷函数
def get_memory_client() -> BowlWanpiMemory:
    """获取记忆客户端单例"""
    if not hasattr(get_memory_client, "_instance"):
        get_memory_client._instance = BowlWanpiMemory()
    return get_memory_client._instance


# 测试代码
if __name__ == "__main__":
    print("🧠 测试 BowlWanpi 记忆系统...")
    
    memory = get_memory_client()
    
    # 测试存储
    test_content = "一碗喜欢在晚上喝茶"
    success = memory.memorize(test_content, {"type": "preference", "topic": "drink"})
    
    if success:
        print("✅ 存储测试通过")
        
        # 测试检索
        results = memory.retrieve("茶")
        print(f"检索结果: {results}")
    else:
        print("❌ 存储测试失败")
