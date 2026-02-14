#!/usr/bin/env python3
"""
上传到三记忆系统的脚本
"""

import json
import os
import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')
sys.path.insert(0, '/root/.openclaw/workspace/skills/hippocampus-memory')
sys.path.insert(0, '/root/.openclaw/workspace/skills/unified-memory')

from unified_memory_manager import store_to_all_systems

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"

def get_recent_conversations(hours=1):
    """获取最近 N 小时的会话历史并提取对话对"""
    sessions_dir = Path("/root/.openclaw/agents/main/sessions")
    if not sessions_dir.exists():
        return []
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    cutoff_timestamp = cutoff_time.timestamp()
    
    session_files = [
        f for f in sessions_dir.glob("*.jsonl")
        if f.stat().st_mtime >= cutoff_timestamp and not f.name.endswith('.lock')
    ]
    
    if not session_files:
        return []
    
    session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    messages = []
    for session_file in session_files[:3]:
        try:
            with open(session_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            msg = json.loads(line)
                            msg_time = msg.get('timestamp', 0)
                            if isinstance(msg_time, (int, float)):
                                msg_time = msg_time / 1000
                            elif isinstance(msg_time, str):
                                try:
                                    msg_time = datetime.fromisoformat(msg_time.replace('Z', '+00:00')).timestamp()
                                except:
                                    msg_time = 0
                            
                            if msg_time >= cutoff_timestamp:
                                messages.append(msg)
                        except:
                            continue
        except Exception as e:
            print(f"读取失败: {e}")
    
    # 提取对话对
    conversations = []
    pending_user_msg = None
    
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        
        msg_data = msg.get('message', {})
        role = msg_data.get('role', '') if isinstance(msg_data, dict) else ''
        content = msg_data.get('content', '') if isinstance(msg_data, dict) else ''
        
        # 提取纯文本
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get('type') == 'text':
                    text_parts.append(part.get('text', ''))
            content = '\n'.join(text_parts)
        elif not isinstance(content, str):
            content = str(content)
        
        if role == 'user':
            pending_user_msg = content
        elif role == 'assistant' and pending_user_msg:
            conversations.append({
                'user': pending_user_msg,
                'assistant': content
            })
            pending_user_msg = None
    
    return conversations

async def upload_to_memory_systems(conversations):
    """批量上传到三记忆系统"""
    if not conversations:
        print("ℹ️ 没有对话需要上传")
        return {'memu': 0, 'hippocampus': 0, 'memos': 0}
    
    print(f"☁️ 开始上传 {len(conversations)} 组对话到三记忆系统...")
    print()
    
    stats = {'memu': 0, 'hippocampus': 0, 'memos': 0}
    
    for i, conv in enumerate(conversations, 1):
        try:
            result = await store_to_all_systems(
                user_msg=conv['user'],
                assistant_msg=conv['assistant'],
                importance=0.7
            )
            
            if result.get('memu'):
                stats['memu'] += 1
            if result.get('hippocampus'):
                stats['hippocampus'] += 1
            if result.get('memos'):
                stats['memos'] += 1
            
            status = "✅" if all(result.values()) else "⚠️"
            print(f"  {status} [{i}/{len(conversations)}] {conv['user'][:40]}...")
            
        except Exception as e:
            print(f"  ❌ [{i}/{len(conversations)}] 上传失败: {e}")
    
    return stats

async def main():
    print("="*60)
    print("🧠 三记忆系统批量上传")
    print("="*60)
    print(f"时间: {datetime.now().isoformat()}")
    print()
    
    # 获取最近1小时的对话
    print("🔍 获取最近1小时的对话...")
    conversations = get_recent_conversations(hours=1)
    print(f"  找到 {len(conversations)} 组对话")
    print()
    
    if not conversations:
        print("ℹ️ 没有新对话需要上传")
        return 0
    
    # 上传到三记忆系统
    stats = await upload_to_memory_systems(conversations)
    
    print()
    print("="*60)
    print("📊 上传统计:")
    print(f"  memU:        {stats['memu']}/{len(conversations)}")
    print(f"  Hippocampus: {stats['hippocampus']}/{len(conversations)}")
    print(f"  MemOS:       {stats['memos']}/{len(conversations)}")
    print("="*60)
    
    return len(conversations)

if __name__ == '__main__':
    count = asyncio.run(main())
    sys.exit(0)
