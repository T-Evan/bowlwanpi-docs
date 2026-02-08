#!/usr/bin/env python3
"""
OpenClaw Hook - 回复前从三记忆系统检索相关记忆
"""

import json
import os
import sys
import asyncio
from datetime import datetime

# 添加路径
sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')
sys.path.insert(0, '/root/.openclaw/workspace/skills/unified-memory')

try:
    from unified_memory_manager import UnifiedMemoryManager, retrieve_merged
except ImportError:
    print("⚠️ unified_memory_manager 导入失败")
    retrieve_merged = None

async def retrieve_relevant_memories(query: str, limit: int = 3):
    """从三记忆系统检索相关记忆"""
    if retrieve_merged is None:
        return []
    
    try:
        memories = await retrieve_merged(query, limit=limit)
        return memories
    except Exception as e:
        print(f"⚠️ 记忆检索失败: {e}")
        return []

def before_response_hook(user_message: str):
    """
    回复前执行的 hook
    检索相关记忆提供上下文
    """
    print("🔍 检索相关记忆...")
    
    try:
        # 异步检索记忆
        memories = asyncio.run(retrieve_relevant_memories(user_message, limit=3))
        
        if memories:
            print(f"  ✅ 找到 {len(memories)} 条相关记忆")
            for i, mem in enumerate(memories, 1):
                source = mem.get('source', 'unknown')
                content = mem.get('content', '')[:50]
                print(f"    {i}. [{source}] {content}...")
        else:
            print("  ℹ️ 未找到相关记忆")
        
        return memories
    except Exception as e:
        print(f"  ❌ 记忆检索异常: {e}")
        return []

# Hook 入口
if __name__ == '__main__':
    # 测试
    memories = before_response_hook("测试检索记忆")
    print(f"\n检索结果: {len(memories)} 条")
