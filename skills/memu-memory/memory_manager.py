#!/usr/bin/env python3
"""
memU Memory Manager - 自动记忆存储和检索
在每次对话后自动存储重要信息到 memU
"""

import json
import os
import sys
from typing import List, Dict, Any, Optional

# 添加 workspace 到路径
sys.path.insert(0, '/root/.openclaw/workspace')

try:
    from memu_sdk import MemUClient
except ImportError:
    print("❌ memu_sdk 未安装")
    sys.exit(1)

# 配置
CREDENTIALS_PATH = '/root/.openclaw/workspace/secrets/memu-credentials.json'
USER_ID = 'yiwan'
AGENT_ID = 'bowlwanpi'

class MemoryManager:
    """记忆管理器 - 处理记忆的存储和检索"""
    
    def __init__(self):
        self.api_key = self._load_api_key()
        self.client = None
    
    def _load_api_key(self) -> str:
        """加载 API Key"""
        try:
            with open(CREDENTIALS_PATH, 'r') as f:
                creds = json.load(f)
                return creds.get('api_key', '')
        except Exception as e:
            print(f"❌ 加载 credentials 失败: {e}")
            return ''
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        if not self.api_key:
            raise ValueError("API Key 未配置")
        self.client = MemUClient(api_key=self.api_key)
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    def _is_important_conversation(self, user_message: str, assistant_message: str) -> bool:
        """
        判断对话是否重要，需要存储
        
        重要标准：
        1. 用户明确说"记住"
        2. 包含个人偏好、习惯
        3. 包含重要决策或信息
        4. 技术选型、工具配置
        5. 约定或规则
        """
        important_keywords = [
            '记住', '提醒', '约定', '规则',
            '我喜欢', '我习惯', '我偏好',
            '配置', '设置', '方案',
            '选择', '决定', '计划',
            '重要', '关键', '核心'
        ]
        
        combined = (user_message + ' ' + assistant_message).lower()
        
        for keyword in important_keywords:
            if keyword in combined:
                return True
        
        # 技术相关长对话也存储
        if len(assistant_message) > 500 and any(tech in combined for tech in ['代码', '编程', '工具', '配置', '方案']):
            return True
        
        return False
    
    async def store_conversation(self, user_message: str, assistant_message: str) -> bool:
        """
        存储单条对话到 memU
        
        Args:
            user_message: 用户消息
            assistant_message: 助手回复
        
        Returns:
            bool: 是否成功存储
        """
        # 检查是否重要
        if not self._is_important_conversation(user_message, assistant_message):
            return False
        
        # 构建对话格式
        conversation = [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_message}
        ]
        
        try:
            result = await self.client.memorize(
                conversation=conversation,
                user_id=USER_ID,
                agent_id=AGENT_ID
            )
            print(f"✅ 记忆已存储: {user_message[:30]}...")
            return True
        except Exception as e:
            print(f"❌ 存储失败: {e}")
            return False
    
    async def retrieve_relevant_memories(self, query: str, limit: int = 5) -> List[Dict]:
        """
        检索相关记忆
        
        Args:
            query: 查询内容
            limit: 返回条数
        
        Returns:
            List[Dict]: 相关记忆列表
        """
        try:
            result = await self.client.retrieve(
                query=query,
                user_id=USER_ID,
                agent_id=AGENT_ID
            )
            
            # 解析结果
            memories = []
            if hasattr(result, 'items'):
                items = result.items
            elif hasattr(result, 'memories'):
                items = result.memories
            else:
                items = []
            
            for item in items[:limit]:
                if hasattr(item, 'content'):
                    memories.append({
                        'content': item.content,
                        'type': getattr(item, 'memory_type', 'unknown')
                    })
            
            return memories
            
        except Exception as e:
            print(f"❌ 检索失败: {e}")
            return []
    
    async def store_important_fact(self, fact: str, fact_type: str = 'profile') -> bool:
        """
        存储重要事实
        
        Args:
            fact: 事实内容
            fact_type: 类型 (profile/event/preference)
        
        Returns:
            bool: 是否成功
        """
        conversation = [
            {"role": "assistant", "content": f"重要信息: {fact}"}
        ]
        
        try:
            result = await self.client.memorize(
                conversation=conversation,
                user_id=USER_ID,
                agent_id=AGENT_ID
            )
            print(f"✅ 事实已存储: {fact[:40]}...")
            return True
        except Exception as e:
            print(f"❌ 存储失败: {e}")
            return False


# 便捷函数
async def store_memory(user_msg: str, assistant_msg: str) -> bool:
    """快捷存储记忆"""
    async with MemoryManager() as mm:
        return await mm.store_conversation(user_msg, assistant_msg)

async def get_relevant_memories(query: str, limit: int = 5) -> List[Dict]:
    """快捷检索记忆"""
    async with MemoryManager() as mm:
        return await mm.retrieve_relevant_memories(query, limit)


if __name__ == '__main__':
    import asyncio
    
    # 测试
    async def test():
        print("🧠 测试记忆管理器...")
        
        async with MemoryManager() as mm:
            # 测试存储
            print("\n📤 测试存储...")
            result = await mm.store_conversation(
                "我喜欢用 VS Code 写代码",
                "好的，我记住了你喜欢用 VS Code！"
            )
            print(f"存储结果: {result}")
            
            # 测试检索
            print("\n🔍 测试检索...")
            memories = await mm.retrieve_relevant_memories("编辑器偏好")
            print(f"检索到 {len(memories)} 条记忆")
            for m in memories[:3]:
                print(f"  - {m.get('content', '无内容')[:50]}...")
    
    asyncio.run(test())
