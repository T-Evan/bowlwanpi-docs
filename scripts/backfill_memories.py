#!/usr/bin/env python3
"""
记忆补传脚本 - 将近期本地记忆批量上传到三记忆系统
"""
import asyncio
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')

from memu_sdk import MemUClient

# 配置
CREDENTIALS_PATH = '/root/.openclaw/workspace/secrets/memu-credentials.json'
MEMORY_DIR = '/root/.openclaw/workspace/memory'
HIPPOCAMPUS_DIR = '/root/.openclaw/workspace/skills/hippocampus-memory'
USER_ID = 'yiwan'
AGENT_ID = 'bowlwanpi'


def load_memu_credentials():
    """加载 memU 凭证"""
    try:
        with open(CREDENTIALS_PATH, 'r') as f:
            creds = json.load(f)
            return creds.get('api_key', '')
    except Exception as e:
        print(f"⚠️ 加载 memU 凭证失败: {e}")
        return ''


def parse_memory_file(filepath):
    """解析记忆文件，提取对话对"""
    conversations = []
    
    if not os.path.exists(filepath):
        return conversations
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # 提取用户-助手对话模式
    # 模式: **一碗**: 消息内容
    #       **碗皮**: 回复内容
    
    # 按时间块分割
    time_blocks = re.split(r'\n---\n', content)
    
    for block in time_blocks:
        lines = block.strip().split('\n')
        i = 0
        while i < len(lines):
            # 查找用户消息
            user_match = re.search(r'\*\*一碗\*\*[:：]\s*(.+)', lines[i])
            if user_match:
                user_msg = user_match.group(1).strip()
                
                # 查找接下来的助手回复
                j = i + 1
                assistant_msgs = []
                while j < len(lines):
                    if re.search(r'\*\*碗皮\*\*[:：]\s*(.+)', lines[j]):
                        assistant_msg = re.search(r'\*\*碗皮\*\*[:：]\s*(.+)', lines[j]).group(1).strip()
                        assistant_msgs.append(assistant_msg)
                        j += 1
                    elif lines[j].strip().startswith('-') or lines[j].strip().startswith('*'):
                        # 列表项可能是回复的一部分
                        assistant_msgs.append(lines[j].strip())
                        j += 1
                    elif lines[j].strip() == '' or '**' in lines[j]:
                        break
                    else:
                        assistant_msgs.append(lines[j].strip())
                        j += 1
                
                if assistant_msgs:
                    conversations.append({
                        'user': user_msg,
                        'assistant': '\n'.join(assistant_msgs),
                        'timestamp': datetime.now().isoformat()
                    })
                    i = j
                else:
                    i += 1
            else:
                i += 1
    
    return conversations


async def upload_to_memu(client, conversations):
    """上传到 memU"""
    success = 0
    for conv in conversations:
        try:
            conversation = [
                {"role": "user", "content": conv['user']},
                {"role": "assistant", "content": conv['assistant'][:1000]}  # 限制长度
            ]
            result = await client.memorize(
                conversation=conversation,
                user_id=USER_ID,
                agent_id=AGENT_ID
            )
            if result and result.task_id:
                success += 1
        except Exception as e:
            print(f"  ❌ memU 上传失败: {e}")
    return success


def upload_to_hippocampus(conversations):
    """上传到 Hippocampus"""
    signals_file = f"{MEMORY_DIR}/signals.jsonl"
    success = 0
    
    try:
        with open(signals_file, 'a') as f:
            for conv in conversations:
                signal = {
                    "timestamp": datetime.now().timestamp(),
                    "user": conv['user'],
                    "assistant": conv['assistant'],
                    "importance": 0.7,
                    "type": "conversation",
                    "source": "backfill"
                }
                f.write(json.dumps(signal, ensure_ascii=False) + '\n')
                success += 1
    except Exception as e:
        print(f"  ❌ Hippocampus 上传失败: {e}")
    
    return success


async def upload_to_memos(conversations):
    """上传到 MemOS"""
    try:
        # 使用 curl 调用 MemOS API
        import subprocess
        import hashlib
        
        api_base = "https://memos.memtensor.cn/api/openmem/v1"
        api_key = "mpg-vCI2aAscjA0ckABPMVa6BhQARfckS+bm9YINlcnG"
        user_id = "yiwanbot"
        
        success = 0
        for conv in conversations:
            try:
                conversation_first = conv['user'][:50]
                conversation_id = hashlib.md5(f"{user_id}\n{conversation_first}".encode()).hexdigest()
                
                chat_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                messages = [
                    {"role": "user", "content": conv['user'], "chat_time": chat_time},
                    {"role": "assistant", "content": conv['assistant'][:1000], "chat_time": chat_time}
                ]
                
                data = {
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "messages": messages
                }
                
                cmd = [
                    "curl", "-s", "-X", "POST",
                    f"{api_base}/add/message",
                    "-H", f"Authorization: Token {api_key}",
                    "-H", "Content-Type: application/json",
                    "-d", json.dumps(data, ensure_ascii=False),
                    "--max-time", "10"
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    success += 1
            except:
                pass
        
        return success
    except Exception as e:
        print(f"  ❌ MemOS 上传失败: {e}")
        return 0


async def main():
    print("=" * 60)
    print("🧠 记忆补传任务")
    print("=" * 60)
    
    # 处理最近3天的记忆文件
    dates = ['2026-02-10', '2026-02-11', '2026-02-12']
    all_conversations = []
    
    for date in dates:
        filepath = f"{MEMORY_DIR}/{date}.md"
        print(f"\n📁 读取 {date}.md...")
        conversations = parse_memory_file(filepath)
        print(f"  找到 {len(conversations)} 组对话")
        all_conversations.extend(conversations)
    
    if not all_conversations:
        print("\n⚠️ 没有找到可上传的对话")
        return
    
    print(f"\n📊 总计: {len(all_conversations)} 组对话待上传")
    
    # 限制上传数量，避免超时
    if len(all_conversations) > 50:
        print(f"  限制上传最近 50 组（避免超时）")
        all_conversations = all_conversations[-50:]
    
    # 上传到三系统
    results = {'memu': 0, 'hippo': 0, 'memos': 0}
    
    # 1. memU
    print("\n☁️  上传到 memU...")
    api_key = load_memu_credentials()
    if api_key:
        async with MemUClient(api_key=api_key) as client:
            results['memu'] = await upload_to_memu(client, all_conversations)
            print(f"  ✅ {results['memu']}/{len(all_conversations)} 成功")
    else:
        print("  ❌ 无 API Key")
    
    # 2. Hippocampus
    print("\n🧠 上传到 Hippocampus...")
    results['hippo'] = upload_to_hippocampus(all_conversations)
    print(f"  ✅ {results['hippo']}/{len(all_conversations)} 成功")
    
    # 3. MemOS
    print("\n🗄️  上传到 MemOS...")
    results['memos'] = await upload_to_memos(all_conversations)
    print(f"  ✅ {results['memos']}/{len(all_conversations)} 成功")
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 补传完成")
    print("=" * 60)
    print(f"memU:       {results['memu']:3d}/{len(all_conversations)}")
    print(f"Hippocampus: {results['hippo']:3d}/{len(all_conversations)}")
    print(f"MemOS:      {results['memos']:3d}/{len(all_conversations)}")
    
    # 记录到日志
    log_entry = f"""
【记忆补传】{datetime.now().isoformat()}
- memU: {results['memu']}/{len(all_conversations)}
- Hippocampus: {results['hippo']}/{len(all_conversations)}
- MemOS: {results['memos']}/{len(all_conversations)}
"""
    with open(f"{MEMORY_DIR}/nightly-build.log", 'a') as f:
        f.write(log_entry)
    
    print(f"\n📝 已记录到 nightly-build.log")


if __name__ == '__main__':
    asyncio.run(main())
