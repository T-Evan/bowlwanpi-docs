#!/usr/bin/env python3
"""
实时存储备用方案 - 会话历史批量存储 v2.0
新增：超时控制、重试机制、代理检查
"""

import json
import os
import sys
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')
sys.path.insert(0, '/root/.openclaw/workspace/skills/unified-memory')

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
UPLOAD_TIMEOUT = 5  # 秒 - 上传超时时间
MAX_RETRIES = 3     # 最大重试次数
PROXY_URL = "http://127.0.0.1:7890"  # Mihomo 代理

# 导入状态跟踪
try:
    from unified_memory_manager import store_to_all_systems
    IMPORT_SUCCESS = True
except ImportError as e:
    store_to_all_systems = None
    IMPORT_SUCCESS = False
    print(f"⚠️ 无法导入 unified_memory_manager: {e}")

def check_proxy():
    """检查代理是否正常工作"""
    try:
        result = subprocess.run(
            ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 
             '--max-time', '3', '--proxy', PROXY_URL, 'https://www.google.com'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.stdout.strip() == '200':
            return True
        return False
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
    
    session_files = [
        f for f in sessions_dir.glob("*.jsonl")
        if f.stat().st_mtime >= cutoff_timestamp
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
            pending_user_msg = {
                'content': content[:500],  # 限制长度
                'timestamp': timestamp
            }
        elif role == 'assistant' and pending_user_msg:
            conversations.append({
                'user': pending_user_msg['content'],
                'assistant': content[:1000],  # 限制长度
                'timestamp': pending_user_msg['timestamp']
            })
            pending_user_msg = None
    
    return conversations

async def store_with_timeout(conv, timeout=UPLOAD_TIMEOUT):
    """带超时的存储，支持重试"""
    if not store_to_all_systems:
        return {'memu': False, 'hippocampus': False, 'memos': False, 'timeout': True}
    
    for attempt in range(MAX_RETRIES):
        try:
            result = await asyncio.wait_for(
                store_to_all_systems(
                    user_msg=conv['user'],
                    assistant_msg=conv['assistant'],
                    importance=0.7
                ),
                timeout=timeout
            )
            return {**result, 'timeout': False, 'attempts': attempt + 1}
        except asyncio.TimeoutError:
            print(f"  ⏱️ 超时 (尝试 {attempt + 1}/{MAX_RETRIES})")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(1)  # 等待1秒再重试
        except Exception as e:
            print(f"  ❌ 错误: {e}")
            break
    
    return {'memu': False, 'hippocampus': False, 'memos': False, 'timeout': True, 'attempts': MAX_RETRIES}

async def store_conversations_batch(conversations):
    """批量存储对话，带超时和重试"""
    if not IMPORT_SUCCESS:
        print("❌ 无法导入存储函数，跳过云端上传")
        return 0, 0, 0, 0
    
    success_count = 0
    memu_count = 0
    hippo_count = 0
    memos_count = 0
    timeout_count = 0
    
    print(f"☁️ 上传到三记忆系统（超时: {UPLOAD_TIMEOUT}秒，重试: {MAX_RETRIES}次）...")
    print()
    
    for i, conv in enumerate(conversations):
        print(f"  [{i+1}/{len(conversations)}] {conv['user'][:30]}...")
        
        result = await store_with_timeout(conv)
        
        if result.get('memu'):
            memu_count += 1
        if result.get('hippocampus'):
            hippo_count += 1
        if result.get('memos'):
            memos_count += 1
        if result.get('timeout'):
            timeout_count += 1
        
        if all([result.get('memu'), result.get('hippocampus'), result.get('memos')]):
            success_count += 1
            print(f"      ✅ 全部成功")
        elif result.get('timeout'):
            print(f"      ⚠️ 超时（{result.get('attempts', MAX_RETRIES)}次尝试）")
        else:
            print(f"      ⚠️ 部分失败")
    
    print()
    print(f"📊 三系统上传统计:")
    print(f"  memU: {memu_count}/{len(conversations)} {'⚠️ 需检查' if memu_count < len(conversations) else '✅'}")
    print(f"  Hippocampus: {hippo_count}/{len(conversations)} {'⚠️ 需检查' if hippo_count < len(conversations) else '✅'}")
    print(f"  MemOS: {memos_count}/{len(conversations)} {'⚠️ 需检查' if memos_count < len(conversations) else '✅'}")
    
    if timeout_count > 0:
        print(f"  ⏱️ 超时次数: {timeout_count}")
        
        # 检查代理
        print()
        print("🔍 检查网络代理状态...")
        if check_proxy():
            print("  ✅ 代理正常 (Mihomo port 7890)")
        else:
            print("  ⚠️ 代理可能异常，请检查 Mihomo 是否运行")
    
    return success_count, memu_count, hippo_count, memos_count

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
    print("🧠 会话历史批量存储 v2.0")
    print(f"   超时: {UPLOAD_TIMEOUT}s | 重试: {MAX_RETRIES}次 | 代理检查: 开启")
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
    
    # 3. 保存到本地（优先保证）
    print("💾 保存到每日记忆文件（高优先级）...")
    if save_to_daily_file(conversations):
        print("  ✅ 本地保存成功")
    else:
        print("  ❌ 本地保存失败")
    print()
    
    # 4. 上传到云端（非阻塞，超时保护）
    success, memu, hippo, memos = await store_conversations_batch(conversations)
    
    # 5. 记录日志
    print()
    print("📝 记录执行日志...")
    log_file = MEMORY_DIR / "nightly-build.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')} UTC] 对话历史批量存储\n")
        f.write(f"{'='*60}\n")
        f.write(f"📨 找到 {len(messages)} 条消息（最近1小时）\n")
        f.write(f"💬 提取 {len(conversations)} 组对话\n")
        f.write(f"💾 已保存到: memory/{datetime.now().strftime('%Y-%m-%d')}.md\n")
        f.write(f"☁️ 三记忆系统上传:\n")
        f.write(f"   - memU: {memu}/{len(conversations)}\n")
        f.write(f"   - Hippocampus: {hippo}/{len(conversations)}\n")
        f.write(f"   - MemOS: {memos}/{len(conversations)}\n")
        f.write(f"状态: {'✅ 全部成功' if success == len(conversations) else '⚠️ 部分成功'}\n")
        f.write(f"{'='*60}\n")
    
    print()
    print("="*60)
    if success == len(conversations):
        print("✅ 批量存储完成! 本地+云端全部成功")
    elif success > 0:
        print("⚠️ 批量存储完成! 本地成功，云端部分成功")
    else:
        print("⚠️ 批量存储完成! 本地成功，云端失败（已记录）")
    print("="*60)
    
    return 0

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
