#!/usr/bin/env python3
"""简化版会话历史存储 - 不使用任何外部依赖"""
import json
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"

def get_session_history(hours=1):
    sessions_dir = Path("/root/.openclaw/agents/main/sessions")
    if not sessions_dir.exists():
        return []
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    cutoff_timestamp = cutoff_time.timestamp()
    
    session_files = [f for f in sessions_dir.glob("*.jsonl") if f.stat().st_mtime >= cutoff_timestamp]
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
            print(f"⚠️ 读取失败: {e}")
    
    return messages

def extract_conversations(messages):
    conversations = []
    pending_user_msg = None
    
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        
        msg_data = msg.get('message', {})
        role = msg_data.get('role', '') if isinstance(msg_data, dict) else ''
        content = msg_data.get('content', '') if isinstance(msg_data, dict) else ''
        timestamp = msg.get('timestamp', datetime.now().isoformat())
        
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get('type') == 'text':
                    text_parts.append(part.get('text', ''))
            content = '\n'.join(text_parts)
        elif not isinstance(content, str):
            content = str(content)
        
        if role == 'user':
            pending_user_msg = {'content': content, 'timestamp': timestamp}
        elif role == 'assistant' and pending_user_msg:
            conversations.append({
                'user': pending_user_msg['content'],
                'assistant': content,
                'timestamp': pending_user_msg['timestamp']
            })
            pending_user_msg = None
    
    return conversations

def save_to_daily_file(conversations):
    today = datetime.now().strftime("%Y-%m-%d")
    daily_file = MEMORY_DIR / f"{today}.md"
    
    entries = []
    valid_count = 0
    for conv in conversations:
        user_msg = conv['user']
        # 跳过系统消息
        if "[cron:" in user_msg[:30] or "Read HEARTBEAT.md" in user_msg[:30] or "[Queued messages" in user_msg[:30]:
            continue
        if "HEARTBEAT_OK" == user_msg.strip():
            continue
        timestamp = datetime.now().strftime("%H:%M")
        entry = f"\n---\n\n**{timestamp}**\n\n**一碗**: {user_msg}\n\n**碗皮**: {conv['assistant']}\n"
        entries.append(entry)
        valid_count += 1
    
    if entries:
        with open(daily_file, 'a', encoding='utf-8') as f:
            f.write('\n'.join(entries))
        return daily_file, valid_count
    return None, 0

def save_to_queue(conversations):
    """保存到待上传队列，稍后由云端存储脚本处理"""
    queue_file = MEMORY_DIR / "upload_queue.jsonl"
    
    count = 0
    with open(queue_file, 'a', encoding='utf-8') as f:
        for conv in conversations:
            user_msg = conv['user']
            # 跳过系统消息
            if "[cron:" in user_msg[:30] or "Read HEARTBEAT.md" in user_msg[:30] or "[Queued messages" in user_msg[:30]:
                continue
            if "HEARTBEAT_OK" == user_msg.strip():
                continue
            
            entry = {
                'timestamp': datetime.now().isoformat(),
                'user': user_msg,
                'assistant': conv['assistant'],
                'uploaded': False
            }
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
            count += 1
    
    return queue_file, count

if __name__ == '__main__':
    print("="*60)
    print("🧠 会话历史批量存储")
    print("="*60)
    
    print("\n🔍 读取最近1小时的会话历史...")
    messages = get_session_history(hours=1)
    print(f"  找到 {len(messages)} 条消息")
    
    conversations = extract_conversations(messages)
    print(f"  提取 {len(conversations)} 组对话")
    
    print("\n💾 保存到每日记忆文件...")
    daily_file, local_count = save_to_daily_file(conversations)
    
    if daily_file:
        print(f"  ✅ 已保存: {daily_file}")
        print(f"  📊 有效对话: {local_count} 组")
    else:
        print("  ℹ️ 没有新的对话需要保存")
    
    print("\n📤 添加到上传队列...")
    queue_file, queue_count = save_to_queue(conversations)
    print(f"  ✅ 队列文件: {queue_file}")
    print(f"  📊 待上传: {queue_count} 组")
    
    print("\n" + "="*60)
    print(f"✅ 批量存储完成!")
    print(f"  - 本地保存: {local_count} 组")
    print(f"  - 上传队列: {queue_count} 组")
    print("="*60)
