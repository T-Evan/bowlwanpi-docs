#!/usr/bin/env python3
"""
手动上传今日对话到记忆系统
"""

import json
import sys
import asyncio
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')
sys.path.insert(0, '/root/.openclaw/workspace/skills/unified-memory')

from unified_memory_manager import store_to_all_systems

def extract_conversations():
    """提取今日对话"""
    sessions_dir = Path('/root/.openclaw/agents/main/sessions')
    session_files = sorted(sessions_dir.glob('*.jsonl'), key=lambda x: x.stat().st_mtime, reverse=True)
    
    all_conversations = []
    
    for session_file in session_files[:5]:  # 检查最近5个会话
        messages = []
        with open(session_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        msg = json.loads(line)
                        if msg.get('type') == 'message' and 'message' in msg:
                            messages.append(msg['message'])
                    except:
                        continue
        
        # 提取对话对
        for i in range(len(messages) - 1):
            curr = messages[i]
            next_msg = messages[i + 1]
            
            if curr.get('role') == 'user' and next_msg.get('role') == 'assistant':
                user_content = curr.get('content', [])
                assistant_content = next_msg.get('content', [])
                
                # 提取文本
                if user_content and len(user_content) > 0:
                    user_text = user_content[0].get('text', '') if isinstance(user_content, list) else str(user_content)
                else:
                    continue
                
                if assistant_content and len(assistant_content) > 0:
                    if isinstance(assistant_content, list):
                        texts = [c.get('text', '') for c in assistant_content if c.get('type') == 'text']
                        assistant_text = '\n'.join(texts) if texts else str(assistant_content)
                    else:
                        assistant_text = str(assistant_content)
                else:
                    continue
                
                # 过滤系统消息
                if user_text.startswith('System:') or user_text.startswith('[cron:'):
                    continue
                if len(user_text) < 5:
                    continue
                    
                all_conversations.append({
                    'user': user_text[:800],
                    'assistant': assistant_text[:3000]
                })
    
    return all_conversations

async def upload_conversations(conversations):
    """批量上传对话"""
    print(f"📤 开始上传 {len(conversations)} 组对话...\n")
    
    success_count = 0
    memu_count = 0
    hippo_count = 0
    memos_count = 0
    
    for i, conv in enumerate(conversations):
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
                print(f"  ✅ [{i+1}/{len(conversations)}] 上传成功")
            else:
                print(f"  ⚠️  [{i+1}/{len(conversations)}] 部分失败")
                
        except Exception as e:
            print(f"  ❌ [{i+1}/{len(conversations)}] 上传失败: {e}")
    
    return success_count, memu_count, hippo_count, memos_count

def save_to_daily_file(conversations):
    """保存到每日文件"""
    today = datetime.now().strftime("%Y-%m-%d")
    memory_dir = Path("/root/.openclaw/workspace/memory")
    memory_dir.mkdir(exist_ok=True)
    
    daily_file = memory_dir / f"{today}.md"
    
    # 追加模式
    with open(daily_file, 'a', encoding='utf-8') as f:
        for conv in conversations:
            timestamp = datetime.now().strftime("%H:%M")
            f.write(f"\n---\n\n**{timestamp}**\n\n**一碗**: {conv['user'][:200]}\n\n**碗皮**: {conv['assistant'][:500]}\n")
    
    print(f"\n💾 已保存到: {daily_file}")

async def main():
    print("="*60)
    print("🧠 手动上传今日对话")
    print("="*60)
    print()
    
    # 提取对话
    print("🔍 提取今日对话...")
    conversations = extract_conversations()
    print(f"  找到 {len(conversations)} 组有效对话\n")
    
    if not conversations:
        print("ℹ️ 没有对话需要上传")
        return 0
    
    # 上传到记忆系统
    success, memu, hippo, memos = await upload_conversations(conversations)
    
    # 保存到每日文件
    save_to_daily_file(conversations)
    
    # 汇总
    print()
    print("="*60)
    print("📊 上传汇总")
    print("="*60)
    print(f"  总对话数: {len(conversations)}")
    print(f"  全部成功: {success}")
    print(f"  memU: {memu}/{len(conversations)}")
    print(f"  Hippocampus: {hippo}/{len(conversations)}")
    print(f"  MemOS: {memos}/{len(conversations)}")
    print("="*60)
    
    return 0

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
