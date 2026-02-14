#!/usr/bin/env python3
"""
简化版批量存储脚本 - 用于 cron 任务
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"

def get_session_history(hours=1):
    """获取最近 N 小时的会话历史"""
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
    
    return messages

def extract_conversations(messages):
    """提取对话对"""
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
        return True
    except Exception as e:
        print(f"保存失败: {e}")
        return False

def main():
    print("="*60)
    print("🧠 会话历史批量存储")
    print("="*60)
    print(f"时间: {datetime.now().isoformat()}")
    print()
    
    # 获取会话历史
    messages = get_session_history(hours=1)
    print(f"📨 找到 {len(messages)} 条消息（最近1小时）")
    
    # 提取对话
    conversations = extract_conversations(messages)
    print(f"💬 提取 {len(conversations)} 组对话")
    print()
    
    if not conversations:
        print("ℹ️ 没有新的对话需要存储")
        return 0
    
    # 保存到每日文件
    print("💾 保存到每日记忆文件...")
    if save_to_daily_file(conversations):
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"   ✅ memory/{today}.md")
    
    print()
    print("="*60)
    print("✅ 完成!")
    print("="*60)
    
    return len(conversations)

if __name__ == '__main__':
    count = main()
    sys.exit(0)
