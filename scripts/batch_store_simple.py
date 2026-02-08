#!/usr/bin/env python3
"""
简化版 - 对话历史批量存储
由于原脚本的异步问题，使用简化同步版本
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"

# 确保目录存在
MEMORY_DIR.mkdir(exist_ok=True)

def get_session_history(hours=1):
    """获取最近 N 小时的会话历史"""
    sessions_dir = Path("/root/.openclaw/agents/main/sessions")
    if not sessions_dir.exists():
        return []
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    cutoff_timestamp = cutoff_time.timestamp()
    
    session_files = [
        f for f in sessions_dir.glob("*.jsonl")
        if f.stat().st_mtime >= cutoff_timestamp
    ]
    
    if not session_files:
        print(f"ℹ️ 最近 {hours} 小时内没有新的会话文件")
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
        
        msg_data = msg.get('message', {})
        role = msg_data.get('role', '') if isinstance(msg_data, dict) else ''
        content = msg_data.get('content', '') if isinstance(msg_data, dict) else ''
        
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
    
    # 读取已有内容避免重复
    existing_content = ""
    if daily_file.exists():
        existing_content = daily_file.read_text(encoding='utf-8')
    
    new_entries = []
    for conv in conversations:
        # 检查是否已存在
        if conv['user'] in existing_content and conv['assistant'][:50] in existing_content:
            continue
        
        timestamp = datetime.now().strftime("%H:%M")
        entry = f"\n---\n\n**{timestamp}**\n\n**一碗**: {conv['user']}\n\n**碗皮**: {conv['assistant'][:500]}...\n"
        new_entries.append(entry)
    
    if new_entries:
        with open(daily_file, 'a', encoding='utf-8') as f:
            f.write('\n'.join(new_entries))
        print(f"💾 已保存 {len(new_entries)} 条对话到: {daily_file}")
        return True
    else:
        print("ℹ️ 没有新的对话需要保存（都已存在）")
        return False

def main():
    """主函数"""
    print("="*60)
    print("🧠 简化版 - 对话历史批量存储")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    print()
    
    # 1. 获取会话历史
    print("🔍 读取会话历史...")
    messages = get_session_history(hours=2)  # 读取最近2小时
    print(f"  找到 {len(messages)} 条消息")
    
    # 2. 提取对话对
    conversations = extract_conversations(messages)
    print(f"  提取 {len(conversations)} 组对话")
    print()
    
    if not conversations:
        print("ℹ️ 没有新的对话需要存储")
        result = "无新对话"
    else:
        # 3. 保存到每日文件
        print("💾 保存到每日记忆文件...")
        saved = save_to_daily_file(conversations)
        result = f"保存 {len([c for c in conversations if c])} 条对话" if saved else "无新内容"
    
    print()
    print("="*60)
    print("✅ 批量存储完成!")
    print("="*60)
    
    # 记录到 nightly-build.log
    log_file = MEMORY_DIR / "nightly-build.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 对话历史批量存储: {result}\n")
    
    return 0

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
