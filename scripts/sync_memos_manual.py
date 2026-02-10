#!/usr/bin/env python3
"""
手动同步待上传的记忆到 MemOS
修复云端记忆上传问题
"""

import json
import os
import subprocess
from datetime import datetime

# 配置
MEMOS_API_KEY = "mpg-vCI2aAscjA0ckABPMVa6BhQARfckS+bm9YINlcnG"
MEMOS_API_BASE = "https://memos.memtensor.cn/api/openmem/v1"
USER_ID = "yiwanbot"
MEMORY_DIR = "/root/.openclaw/workspace/memory"

def upload_to_memos(user_msg, assistant_msg, timestamp=None):
    """上传单条记忆到 MemOS"""
    if timestamp is None:
        timestamp = datetime.now()
    
    chat_time = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    # 生成 conversation_id
    import hashlib
    conv_id = hashlib.md5(f"{USER_ID}\n{user_msg[:50]}".encode()).hexdigest()
    
    data = {
        "user_id": USER_ID,
        "conversation_id": conv_id,
        "messages": [
            {"role": "user", "content": user_msg, "chat_time": chat_time},
            {"role": "assistant", "content": assistant_msg, "chat_time": chat_time}
        ]
    }
    
    cmd = [
        "curl", "-s", "-X", "POST",
        f"{MEMOS_API_BASE}/add/message",
        "-H", f"Authorization: Token {MEMOS_API_KEY}",
        "-H", "Content-Type: application/json",
        "--max-time", "10",
        "-d", json.dumps(data, ensure_ascii=False)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0 and result.stdout:
        try:
            response = json.loads(result.stdout)
            return response.get("code") == 0
        except:
            pass
    return False

def sync_today_memories():
    """同步今天的记忆"""
    today_file = os.path.join(MEMORY_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.md")
    
    if not os.path.exists(today_file):
        print(f"❌ 今日记忆文件不存在: {today_file}")
        return 0
    
    # 读取记忆文件
    with open(today_file, 'r') as f:
        content = f.read()
    
    # 解析对话对
    conversations = []
    lines = content.split('\n')
    current_user = None
    current_assistant = None
    
    for line in lines:
        line = line.strip()
        if line.startswith('**一碗**: '):
            if current_user and current_assistant:
                conversations.append((current_user, current_assistant))
            current_user = line.replace('**一碗**: ', '').strip()
            current_assistant = None
        elif line.startswith('**碗皮**: '):
            current_assistant = line.replace('**碗皮**: ', '').strip()
    
    # 添加最后一组
    if current_user and current_assistant:
        conversations.append((current_user, current_assistant))
    
    print(f"📊 找到 {len(conversations)} 组对话待同步")
    
    # 上传
    success_count = 0
    for i, (user_msg, assistant_msg) in enumerate(conversations, 1):
        if upload_to_memos(user_msg, assistant_msg):
            success_count += 1
            print(f"✅ [{i}/{len(conversations)}] 上传成功")
        else:
            print(f"❌ [{i}/{len(conversations)}] 上传失败")
    
    return success_count

if __name__ == "__main__":
    print("🚀 开始同步今日记忆到 MemOS...")
    print("=" * 50)
    
    count = sync_today_memories()
    
    print("=" * 50)
    print(f"✅ 同步完成！成功上传 {count} 条记忆到 MemOS")
    print(f"📁 本地备份: {MEMORY_DIR}/memos-integration.jsonl")
