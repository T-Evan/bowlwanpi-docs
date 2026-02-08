#!/usr/bin/env python3
"""
实时存储备用方案 - 会话历史批量存储
由于 OpenClaw hooks 未配置，使用此脚本手动存储对话历史
"""

import json
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')
sys.path.insert(0, '/root/.openclaw/workspace/skills/unified-memory')

try:
    from unified_memory_manager import store_to_all_systems
except ImportError:
    store_to_all_systems = None
    print("⚠️ 无法导入 unified_memory_manager")

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"

def get_session_history(hours=1):
    """获取最近 N 小时的会话历史"""
    from datetime import datetime, timedelta
    
    # 尝试从 OpenClaw 会话文件读取
    sessions_dir = Path("/root/.openclaw/agents/main/sessions")
    if not sessions_dir.exists():
        return []
    
    # 获取最近 N 小时内修改过的会话文件
    cutoff_time = datetime.now() - timedelta(hours=hours)
    cutoff_timestamp = cutoff_time.timestamp()
    
    session_files = [
        f for f in sessions_dir.glob("*.jsonl")
        if f.stat().st_mtime >= cutoff_timestamp
    ]
    
    if not session_files:
        print(f"ℹ️ 最近 {hours} 小时内没有新的会话文件")
        return []
    
    # 按修改时间排序
    session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    messages = []
    for session_file in session_files[:3]:  # 最多检查3个文件
        try:
            with open(session_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            msg = json.loads(line)
                            # 检查消息时间戳是否在范围内
                            msg_time = msg.get('timestamp', 0)
                            if isinstance(msg_time, (int, float)):
                                msg_time = msg_time / 1000  # 转换为秒
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
            print(f"⚠️ 读取会话文件失败: {e}")
    
    return messages

def extract_conversations(messages):
    """提取对话对"""
    conversations = []
    pending_user_msg = None
    
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        
        # OpenClaw 格式: role 在 message 对象内
        msg_data = msg.get('message', {})
        role = msg_data.get('role', '') if isinstance(msg_data, dict) else ''
        content = msg_data.get('content', '') if isinstance(msg_data, dict) else ''
        timestamp = msg.get('timestamp', datetime.now().isoformat())
        
        # 提取纯文本内容
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get('type') == 'text':
                    text_parts.append(part.get('text', ''))
            content = '\n'.join(text_parts)
        elif not isinstance(content, str):
            content = str(content)
        
        if role == 'user':
            pending_user_msg = {
                'content': content,
                'timestamp': timestamp
            }
        elif role == 'assistant' and pending_user_msg:
            conversations.append({
                'user': pending_user_msg['content'],
                'assistant': content,
                'timestamp': pending_user_msg['timestamp']
            })
            pending_user_msg = None
    
    return conversations

async def store_conversations_batch(conversations):
    """批量存储对话"""
    if store_to_all_systems is None:
        print("❌ 无法导入存储函数")
        return False
    
    success_count = 0
    memu_count = 0
    hippo_count = 0
    memos_count = 0
    
    for conv in conversations:
        try:
            result = await store_to_all_systems(
                user_msg=conv['user'],
                assistant_msg=conv['assistant'],
                importance=0.7
            )
            
            if result['memu']:
                memu_count += 1
            if result['hippocampus']:
                hippo_count += 1
            if result['memos']:
                memos_count += 1
            
            if all(result.values()):
                success_count += 1
                print(f"  ✅ 存储: {conv['user'][:30]}...")
            else:
                print(f"  ⚠️ 部分失败: {conv['user'][:30]}...")
                
        except Exception as e:
            print(f"  ❌ 存储失败: {e}")
    
    print(f"\n📊 三系统上传统计:")
    print(f"  memU: {memu_count}/{len(conversations)}")
    print(f"  Hippocampus: {hippo_count}/{len(conversations)}")
    print(f"  MemOS: {memos_count}/{len(conversations)}")
    
    return success_count

def save_to_daily_file(conversations):
    """保存到每日记忆文件"""
    today = datetime.now().strftime("%Y-%m-%d")
    daily_file = MEMORY_DIR / f"{today}.md"
    
    entries = []
    for conv in conversations:
        timestamp = datetime.now().strftime("%H:%M")
        entry = f"\n---\n\n**{timestamp}**\n\n**一碗**: {conv['user']}\n\n**碗皮**: {conv['assistant']}\n"
        entries.append(entry)
    
    try:
        with open(daily_file, 'a', encoding='utf-8') as f:
            f.write('\n'.join(entries))
        print(f"💾 已保存到每日文件: {daily_file}")
        return True
    except Exception as e:
        print(f"⚠️ 保存失败: {e}")
        return False

async def main():
    """主函数"""
    print("="*60)
    print("🧠 会话历史批量存储")
    print("="*60)
    print()
    
    # 1. 获取最近1小时的会话历史
    print("🔍 读取最近1小时的会话历史...")
    messages = get_session_history(hours=1)
    print(f"  找到 {len(messages)} 条消息（最近1小时）")
    
    # 2. 提取对话对
    conversations = extract_conversations(messages)
    print(f"  提取 {len(conversations)} 组对话")
    print()
    
    if not conversations:
        print("ℹ️ 没有新的对话需要存储")
        return 0
    
    # 3. 保存到每日文件
    print("💾 保存到每日记忆文件...")
    save_to_daily_file(conversations)
    print()
    
    # 4. 上传到云端记忆
    if store_to_all_systems:
        print("☁️ 上传到三记忆系统...")
        success = await store_conversations_batch(conversations)
        print(f"  成功存储: {success}/{len(conversations)}")
    else:
        print("⚠️ 跳过云端存储（无法导入存储模块）")
    
    print()
    print("="*60)
    print("✅ 批量存储完成!")
    print("="*60)
    
    return 0

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
