#!/usr/bin/env python3
"""
Post-response hook - 对话后自动存储记忆
由 OpenClaw 在每次回复后调用
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
    """主函数 - 从环境变量或标准输入读取对话内容"""
    
    # 尝试从环境变量读取
    user_msg = os.environ.get('USER_MESSAGE', '')
    assistant_msg = os.environ.get('ASSISTANT_MESSAGE', '')
    
    # 或者从命令行参数
    if len(sys.argv) >= 3:
        user_msg = sys.argv[1]
        assistant_msg = sys.argv[2]
    
    if not user_msg or not assistant_msg:
        print("⚠️ 没有对话内容，跳过存储")
        return
    
    # 存储记忆
    async def store():
        try:
            async with MemoryManager() as mm:
                result = await mm.store_conversation(user_msg, assistant_msg)
                if result:
                    print("✅ 记忆已自动存储")
                else:
                    print("ℹ️ 对话不需要存储")
        except Exception as e:
            print(f"❌ 存储出错: {e}")
    
    asyncio.run(store())

if __name__ == '__main__':
    main()
