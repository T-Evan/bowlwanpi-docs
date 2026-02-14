#!/usr/bin/env python3
"""处理上传队列 - 同步上传到三记忆系统"""
import json
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
QUEUE_FILE = MEMORY_DIR / "upload_queue.jsonl"

def load_queue():
    """加载待上传队列"""
    if not QUEUE_FILE.exists():
        return []
    
    items = []
    with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    item = json.loads(line.strip())
                    if not item.get('uploaded', False):
                        items.append(item)
                except:
                    continue
    return items

def save_to_memos(user_msg, assistant_msg):
    """使用 curl 保存到 MemOS"""
    try:
        import hashlib
        
        user_id = "yiwanbot"
        conversation_first = user_msg[:50]
        conversation_id = hashlib.md5(f"{user_id}\n{conversation_first}".encode()).hexdigest()
        
        chat_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        data = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "messages": [
                {"role": "user", "content": user_msg, "chat_time": chat_time},
                {"role": "assistant", "content": assistant_msg, "chat_time": chat_time}
            ]
        }
        
        cmd = [
            "curl", "-s", "-X", "POST",
            "https://memos.memtensor.cn/api/openmem/v1/add/message",
            "-H", "Authorization: Token mpg-vCI2aAscjA0ckABPMVa6BhQARfckS+bm9YINlcnG",
            "-H", "Content-Type: application/json",
            "--proxy", "http://127.0.0.1:7890",
            "-d", json.dumps(data, ensure_ascii=False),
            "--max-time", "15"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        
        if result.returncode == 0 and result.stdout:
            try:
                resp = json.loads(result.stdout)
                return resp.get("code") == 0 or "task_id" in str(resp)
            except:
                return bool(result.stdout.strip())
        return False
    except Exception as e:
        print(f"    ⚠️ MemOS: {e}")
        return False

def save_to_hippocampus(user_msg, assistant_msg):
    """保存到 Hippocampus (本地 signals.jsonl)"""
    try:
        import time
        signals_file = MEMORY_DIR / "signals.jsonl"
        
        signal = {
            "timestamp": time.time(),
            "user": user_msg,
            "assistant": assistant_msg,
            "importance": 0.6,
            "type": "conversation"
        }
        
        with open(signals_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(signal, ensure_ascii=False) + '\n')
        
        return True
    except Exception as e:
        print(f"    ⚠️ Hippocampus: {e}")
        return False

def save_to_memu(user_msg, assistant_msg):
    """使用 HTTP API 保存到 memU"""
    try:
        # 尝试使用 curl 调用 memU API
        api_key = "memu-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoib3J0b2RhIiwiYXBpX2tleV9pZCI6ImFwbl9VNzVmQXZ3eXl2ZWR2QjVYdmdoZzRlIn0.sYky_BoEA_0Mlr-O9X02-zFrOMUO06I4sK_8yhE3HLk"
        
        data = {
            "conversation": [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg}
            ],
            "user_id": "yiwan",
            "agent_id": "bowlwanpi"
        }
        
        cmd = [
            "curl", "-s", "-X", "POST",
            "https://api.memu.so/v1/memorize",
            "-H", f"Authorization: Bearer {api_key}",
            "-H", "Content-Type: application/json",
            "--proxy", "http://127.0.0.1:7890",
            "-d", json.dumps(data, ensure_ascii=False),
            "--max-time", "15"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        
        if result.returncode == 0 and result.stdout:
            try:
                resp = json.loads(result.stdout)
                # memU 返回成功通常有 success=True 或包含 memory_id
                return resp.get("success") == True or "memory_id" in str(resp) or "extracts" in str(resp)
            except:
                return bool(result.stdout.strip())
        return False
    except Exception as e:
        print(f"    ⚠️ memU: {e}")
        return False

def process_queue():
    """处理上传队列"""
    items = load_queue()
    
    if not items:
        print("ℹ️ 上传队列为空")
        return 0, 0, 0, 0
    
    print(f"\n📤 处理 {len(items)} 条待上传记录...\n")
    
    memu_count = 0
    hippo_count = 0
    memos_count = 0
    
    for i, item in enumerate(items, 1):
        user_msg = item.get('user', '')
        assistant_msg = item.get('assistant', '')
        
        if not user_msg or not assistant_msg:
            continue
        
        print(f"  [{i}/{len(items)}] 正在上传...")
        
        # 上传到三个系统
        memu_ok = save_to_memu(user_msg, assistant_msg)
        hippo_ok = save_to_hippocampus(user_msg, assistant_msg)
        memos_ok = save_to_memos(user_msg, assistant_msg)
        
        if memu_ok: memu_count += 1
        if hippo_ok: hippo_count += 1
        if memos_ok: memos_count += 1
        
        status = []
        if memu_ok: status.append("memU✅")
        if hippo_ok: status.append("Hippo✅")
        if memos_ok: status.append("MemOS✅")
        
        if status:
            print(f"      {' | '.join(status)}")
        else:
            print(f"      ⚠️ 全部失败")
    
    return memu_count, hippo_count, memos_count, len(items)

def clear_queue():
    """清空上传队列"""
    try:
        # 备份后清空
        if QUEUE_FILE.exists():
            backup = MEMORY_DIR / f"upload_queue_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl.bak"
            QUEUE_FILE.rename(backup)
            print(f"\n💾 队列已备份: {backup}")
        return True
    except Exception as e:
        print(f"\n⚠️ 备份失败: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("☁️ 三记忆系统批量上传")
    print("="*60)
    
    memu_c, hippo_c, memos_c, total = process_queue()
    
    print(f"\n📊 上传统计:")
    print(f"  memU: {memu_c}/{total}")
    print(f"  Hippocampus: {hippo_c}/{total}")
    print(f"  MemOS: {memos_c}/{total}")
    
    # 清空队列
    clear_queue()
    
    print("\n" + "="*60)
    print("✅ 云端上传完成!")
    print("="*60)
