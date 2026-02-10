#!/usr/bin/env python3
"""
实时存储备用方案 - 会话历史批量存储 v3.0
修复：跳过有问题的 memU 初始化，使用可靠的本地存储 + 简单 HTTP API
"""

import json
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
CREDENTIALS_PATH = '/root/.openclaw/workspace/secrets/memu-credentials.json'

def check_proxy():
    """检查代理是否正常工作"""
    try:
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 
             '--max-time', '3', '--proxy', 'http://127.0.0.1:7890', 'https://www.google.com'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() == '200'
    except:
        return False

def get_session_history(hours=1):
    """获取最近 N 小时的会话历史"""
    from datetime import datetime, timedelta
    
    sessions_dir = Path("/root/.openclaw/agents/main/sessions")
    if not sessions_dir.exists():
        return []
    
    cutoff_time = datetime.now() - timedelta(hours=hours)
    cutoff_timestamp = cutoff_time.timestamp()
    
    session_files = [f for f in sessions_dir.glob("*.jsonl") if f.stat().st_mtime >= cutoff_timestamp]
    
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
            pending_user_msg = {'content': content[:500], 'timestamp': timestamp}
        elif role == 'assistant' and pending_user_msg:
            conversations.append({
                'user': pending_user_msg['content'],
                'assistant': content[:1000],
                'timestamp': pending_user_msg['timestamp']
            })
            pending_user_msg = None
    
    return conversations

def save_to_hippocampus(conversations):
    """保存到 Hippocampus (本地文件，最可靠)"""
    try:
        signals_file = f"{MEMORY_DIR}/signals.jsonl"
        count = 0
        for conv in conversations:
            signal = {
                "timestamp": datetime.now().timestamp(),
                "user": conv['user'],
                "assistant": conv['assistant'],
                "importance": 0.7,
                "type": "conversation"
            }
            with open(signals_file, 'a') as f:
                f.write(json.dumps(signal, ensure_ascii=False) + '\n')
            count += 1
        return count
    except Exception as e:
        print(f"⚠️ Hippocampus 保存失败: {e}")
        return 0

def upload_to_memu_single(conv, api_key):
    """使用 curl 直接上传单个对话到 memU (绕过 SDK)"""
    try:
        import hashlib
        user_id = 'yiwan'
        agent_id = 'bowlwanpi'
        conversation_id = hashlib.md5(f"{user_id}\n{conv['user'][:50]}".encode()).hexdigest()
        
        data = {
            "conversation": [
                {"role": "user", "content": conv['user']},
                {"role": "assistant", "content": conv['assistant']}
            ],
            "user_id": user_id,
            "agent_id": agent_id
        }
        
        cmd = [
            'curl', '-s', '-X', 'POST',
            'https://api.memu.so/memorize',
            '-H', f'Authorization: Bearer {api_key}',
            '-H', 'Content-Type: application/json',
            '--proxy', 'http://127.0.0.1:7890',
            '--max-time', '5',
            '-d', json.dumps(data, ensure_ascii=False)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
        return result.returncode == 0
    except:
        return False

def upload_to_memos_single(conv):
    """使用 curl 直接上传单个对话到 MemOS"""
    try:
        import hashlib
        from datetime import datetime
        
        user_id = 'yiwanbot'
        api_key = "mpg-vCI2aAscjA0ckABPMVa6BhQARfckS+bm9YINlcnG"
        conversation_id = hashlib.md5(f"{user_id}\n{conv['user'][:50]}".encode()).hexdigest()
        
        chat_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        data = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "messages": [
                {"role": "user", "content": conv['user'], "chat_time": chat_time},
                {"role": "assistant", "content": conv['assistant'], "chat_time": chat_time}
            ]
        }
        
        cmd = [
            'curl', '-s', '-X', 'POST',
            'https://memos.memtensor.cn/api/openmem/v1/add_message',
            '-H', f'Authorization: Token {api_key}',
            '-H', 'Content-Type: application/json',
            '--proxy', 'http://127.0.0.1:7890',
            '--max-time', '5',
            '-d', json.dumps(data, ensure_ascii=False)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
        return result.returncode == 0
    except:
        return False

def store_to_all_systems_simple(conversations):
    """简化的双系统存储（memU 已禁用，使用 Hipppcampus + MemOS）"""
    # memU 已禁用（API 长期不可用）
    MEMU_ENABLED = False
    api_key = None  # 不再加载 memU credentials
    
    memu_count = 0  # 保持为 0（已禁用）
    hippo_count = 0
    memos_count = 0
    
    print(f"☁️ 上传到双记忆系统（Hippo + MemOS，memU 已禁用）...")
    print(f"   注: memU API 长期不可用，已自动跳过以节省资源")
    print()
    
    for i, conv in enumerate(conversations):
        print(f"  [{i+1}/{len(conversations)}] {conv['user'][:30]}...")
        
        # 1. Hippocampus (本地，最可靠)
        hippo_ok = save_to_hippocampus([conv]) > 0
        if hippo_ok:
            hippo_count += 1
        
        # 2. memU (已禁用，跳过)
        # memu_ok = False
        # if MEMU_ENABLED and api_key:
        #     memu_ok = upload_to_memu_single(conv, api_key)
        #     if memu_ok:
        #         memu_count += 1
        
        # 3. MemOS (云端)
        memos_ok = upload_to_memos_single(conv)
        if memos_ok:
            memos_count += 1
        
        status = []
        if hippo_ok:
            status.append("H✅")
        # memU 已禁用，不再显示
        # if memu_ok:
        #     status.append("M✅")
        if memos_ok:
            status.append("O✅")
        print(f"      {' | '.join(status) if status else '⚠️ 失败'}")
    
    print()
    print(f"📊 上传统计: Hippo={hippo_count}/{len(conversations)} | MemOS={memos_count}/{len(conversations)} | memU=已禁用")
    
    # 如果有失败，检查代理
    if hippo_count < len(conversations) or memos_count < len(conversations):
        print()
        print("🔍 检查网络代理...")
        if check_proxy():
            print("  ✅ 代理正常")
        else:
            print("  ⚠️ 代理异常，请检查 Mihomo")
    
    # 返回统计（memu_count 固定为 0，因为已禁用）
    return 0, hippo_count, memos_count

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

def main():
    """主函数（同步版本，避免异步卡住）"""
    print("="*60)
    print("🧠 会话历史批量存储 v3.0")
    print("   同步执行 | curl 上传 | 5秒超时")
    print("="*60)
    print()
    
    # 1. 获取会话历史
    print("🔍 读取最近1小时的会话历史...")
    messages = get_session_history(hours=1)
    print(f"  找到 {len(messages)} 条消息")
    
    # 2. 提取对话
    conversations = extract_conversations(messages)
    print(f"  提取 {len(conversations)} 组对话")
    print()
    
    if not conversations:
        print("ℹ️ 没有新的对话需要存储")
        return 0
    
    # 3. 保存到本地（高优先级）
    print("💾 保存到每日记忆文件...")
    local_ok = save_to_daily_file(conversations)
    print(f"  {'✅' if local_ok else '❌'} 本地保存")
    print()
    
    # 4. 上传到云端
    memu, hippo, memos = store_to_all_systems_simple(conversations)
    
    # 5. 记录日志
    print()
    print("📝 记录执行日志...")
    log_file = MEMORY_DIR / "nightly-build.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')} UTC] 对话历史批量存储\n")
        f.write(f"{'='*60}\n")
        f.write(f"📨 {len(messages)} 条消息 → {len(conversations)} 组对话\n")
        f.write(f"💾 本地: {'✅' if local_ok else '❌'}\n")
        f.write(f"☁️ 云端: Hippo={hippo} | memU={memu} | MemOS={memos}\n")
        f.write(f"{'='*60}\n")
    
    print()
    print("="*60)
    # memU 已禁用，只检查 Hippo 和 MemOS
    success = (hippo == len(conversations) and memos == len(conversations))
    if success:
        print("✅ 全部完成！Hippo + MemOS 双系统成功")
    else:
        print(f"⚠️ 完成！Hippo={hippo} | MemOS={memos} | memU=已禁用")
    print("="*60)
    
    return 0

if __name__ == '__main__':
    exit(main())
