#!/usr/bin/env python3
"""
Pre-response hook - 回复前检索相关记忆
由 OpenClaw 在每次回复前调用
"""

import json
import sys
import os

# 添加路径
sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')

from memory_manager import MemoryManager
import asyncio

def main():
    """主函数 - 检索与当前话题相关的记忆"""
    
    # 从环境变量或命令行获取用户消息
    user_msg = os.environ.get('USER_MESSAGE', '')
    
    if len(sys.argv) >= 2:
        user_msg = sys.argv[1]
    
    if not user_msg:
        print("⚠️ 没有用户消息，跳过检索")
        return json.dumps({"memories": []})
    
    # 检索记忆
    async def retrieve():
        try:
            async with MemoryManager() as mm:
                memories = await mm.retrieve_relevant_memories(user_msg, limit=5)
                
                if memories:
                    print(f"💭 检索到 {len(memories)} 条相关记忆")
                    for m in memories[:3]:
                        content = m.get('content', '')[:60]
                        print(f"   • {content}...")
                
                # 输出 JSON 格式供主程序使用
                result = {
                    "memories": memories,
                    "count": len(memories)
                }
                print(json.dumps(result))
                
        except Exception as e:
            print(f"❌ 检索出错: {e}", file=sys.stderr)
            print(json.dumps({"memories": [], "count": 0}))
    
    asyncio.run(retrieve())

if __name__ == '__main__':
    main()
