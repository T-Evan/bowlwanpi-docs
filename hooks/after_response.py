#!/usr/bin/env python3
"""
OpenClaw Hook - 回复后实时存储到三记忆系统
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

from unified_memory_manager import UnifiedMemoryManager, store_to_all_systems

# 配置
MEMORY_DIR = '/root/.openclaw/workspace/memory'
SESSION_FILE = f"{MEMORY_DIR}/realtime-storage.jsonl"

def save_to_daily_log(user_message: str, assistant_message: str):
    """保存到每日记忆文件"""
    today = datetime.now().strftime("%Y-%m-%d")
    daily_file = f"{MEMORY_DIR}/{today}.md"
    
    # 追加到每日文件
    timestamp = datetime.now().strftime("%H:%M")
    entry = f"\n---\n\n**{timestamp}**\n\n**一碗**: {user_message}\n\n**碗皮**: {assistant_message}\n"
    
    try:
        with open(daily_file, 'a', encoding='utf-8') as f:
            f.write(entry)
        return True
    except Exception as e:
        print(f"⚠️ 每日日志写入失败: {e}")
        return False

def save_to_realtime_log(user_message: str, assistant_message: str):
    """保存到实时存储日志"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user": user_message,
        "assistant": assistant_message,
        "stored_to": ["daily_log"]
    }
    
    try:
        with open(SESSION_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        return True
    except Exception as e:
        print(f"⚠️ 实时日志写入失败: {e}")
        return False

async def store_to_memory_systems(user_message: str, assistant_message: str):
    """存储到三记忆系统"""
    try:
        result = await store_to_all_systems(
            user_msg=user_message,
            assistant_msg=assistant_message,
            importance=0.7,
            enable_memu=True,
            enable_hippo=True,
            enable_memos=True
        )
        return result
    except Exception as e:
        print(f"⚠️ 记忆系统存储失败: {e}")
        return {'memu': False, 'hippocampus': False, 'memos': False}

def after_response_hook(user_message: str, assistant_message: str):
    """
    回复后执行的 hook
    自动存储对话到三记忆系统
    """
    print("🧠 实时存储对话到记忆系统...")
    
    # 1. 保存到每日日志
    log_result = save_to_daily_log(user_message, assistant_message)
    
    # 2. 保存到实时日志
    realtime_result = save_to_realtime_log(user_message, assistant_message)
    
    # 3. 异步存储到三记忆系统
    try:
        result = asyncio.run(store_to_memory_systems(user_message, assistant_message))
        print(f"  ✅ memU: {'成功' if result['memu'] else '失败'}")
        print(f"  ✅ Hippocampus: {'成功' if result['hippocampus'] else '失败'}")
        print(f"  ✅ MemOS: {'成功' if result['memos'] else '失败'}")
    except Exception as e:
        print(f"  ❌ 记忆系统存储异常: {e}")
    
    print("✅ 实时存储完成")

# Hook 入口
if __name__ == '__main__':
    # 测试
    after_response_hook(
        "测试实时存储",
        "实时存储功能已启用！"
    )
