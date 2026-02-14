#!/usr/bin/env python3
"""
测试修复后的 memU 连接
"""
import asyncio
import sys
sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')

from memu_sdk import MemUClient

with open('/root/.openclaw/workspace/secrets/memu-credentials.json', 'r') as f:
    import json
    creds = json.load(f)
    API_KEY = creds.get('api_key', '')

print("🧠 测试 memU v3 API...")
print(f"API Key: {API_KEY[:20]}...")
print("-" * 50)

async def test():
    async with MemUClient(api_key=API_KEY) as client:
        print("✅ 客户端初始化成功")
        
        # 测试存储
        print("\n📤 测试存储记忆...")
        try:
            result = await client.memorize(
                conversation=[
                    {"role": "user", "content": "一碗喜欢喝咖啡"},
                    {"role": "assistant", "content": "记住了，一碗喜欢喝咖啡！"}
                ],
                user_id='yiwan',
                agent_id='bowlwanpi'
            )
            print(f"✅ 存储成功!")
            print(f"   Task ID: {result.task_id}")
            print(f"   Items: {len(result.items)} 条")
            for item in result.items[:3]:
                print(f"   - [{item.memory_type}] {item.summary[:50]}...")
        except Exception as e:
            print(f"❌ 存储失败: {e}")
            return False
        
        # 测试检索
        print("\n🔍 测试检索记忆...")
        try:
            result = await client.retrieve(
                query="一碗喜欢什么饮料",
                user_id='yiwan',
                agent_id='bowlwanpi'
            )
            print(f"✅ 检索成功!")
            print(f"   Items: {len(result.items)} 条")
            print(f"   Categories: {len(result.categories)} 个")
            for item in result.items[:3]:
                print(f"   - [{item.memory_type}] {item.summary[:50]}...")
        except Exception as e:
            print(f"❌ 检索失败: {e}")
            return False
        
        print("\n🎉 memU 连接正常！")
        return True

success = asyncio.run(test())
sys.exit(0 if success else 1)
