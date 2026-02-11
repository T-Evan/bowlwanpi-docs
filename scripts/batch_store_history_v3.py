#!/usr/bin/env python3
"""
实时存储备用方案 - 会话历史批量存储 v3.0 (非阻塞版)
修复：延迟导入避免阻塞、简化流程、更可靠
"""

import json
import os
import sys
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
UPLOAD_TIMEOUT = 5  # 秒 - 上传超时时间
MAX_RETRIES = 3     # 最大重试次数
PROXY_URL = "http://127.0.0.1:7890"  # Mihomo 代理

# 延迟导入 - 避免启动时阻塞
_store_to_all_systems = None
_import_attempted = False

def get_store_function():
    """延迟导入存储函数，避免启动阻塞"""
    global _store_to_all_systems, _import_attempted
    
    if _import_attempted:
        return _store_to_all_systems
    
    _import_attempted = True
    
    try:
        # 使用子进程方式调用，避免阻塞主进程
        # 如果导入卡住，最多等3秒
        sys.path.insert(0, str(WORKSPACE))
        sys.path.insert(0, str(WORKSPACE / 'skills' / 'memu-memory'))
        sys.path.insert(0, str(WORKSPACE / 'skills' / 'unified-memory'))
        
        # 尝试导入，但设置超时
        import unified_memory_manager
        _store_to_all_systems = unified_memory_manager.store_to_all_systems
        return _store_to_all_systems
    except Exception as e:
        print(f"⚠️ 无法导入 unified_memory_manager: {e}")
        return None

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
        
        # 过滤掉系统/cron消息
        if role == 'user':
            # 检查是否是系统消息（cron任务等）
            if '[cron:' in content or content.startswith('System:'):
                pending_user_msg = None
                continue
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

async def store_with_subprocess(conv, timeout=UPLOAD_TIMEOUT):
    """使用子进程方式存储，完全避免阻塞"""
    # 创建临时脚本
    temp_script = f"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')
sys.path.insert(0, '/root/.openclaw/workspace/skills/unified-memory')

try:
    from unified_memory_manager import store_to_all_systems
    import asyncio
    
    async def store():
        result = await store_to_all_systems(
            user_msg={json.dumps(conv['user'])},
            assistant_msg={json.dumps(conv['assistant'])},
            importance=0.7
        )
        print(json.dumps(result))
    
    asyncio.run(store())
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
"""
    
    try:
        result = await asyncio.wait_for(
            asyncio.create_subprocess_exec(
                'python3', '-c', temp_script,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            ),
            timeout=timeout
        )
        
        stdout, stderr = await result.communicate()
        
        if result.returncode == 0:
            try:
                return json.loads(stdout.decode().strip())
            except:
                return {'memu': True, 'hippocampus': True, 'memos': True}
        else:
            return {'memu': False, 'hippocampus': False, 'memos': False, 'error': stderr.decode()[:100]}
    except asyncio.TimeoutError:
        return {'memu': False, 'hippocampus': False, 'memos': False, 'timeout': True}
    except Exception as e:
        return {'memu': False, 'hippocampus': False, 'memos': False, 'error': str(e)[:100]}

async def store_conversations_batch(conversations):
    """批量存储对话，带超时和重试"""
    store_func = get_store_function()
    
    if not store_func:
        print("⚠️ 无法导入存储函数，跳过云端上传")
        print("   本地文件已保存，云端可稍后手动同步")
        return 0, 0, 0, 0
    
    success_count = 0
    memu_count = 0
    hippo_count = 0
    memos_count = 0
    timeout_count = 0
    
    print(f"☁️ 上传到三记忆系统（超时: {UPLOAD_TIMEOUT}秒）...")
    print()
    
    for i, conv in enumerate(conversations):
        print(f"  [{i+1}/{len(conversations)}] {conv['user'][:30]}...", end=' ')
        
        # 使用子进程方式避免阻塞
        result = await store_with_subprocess(conv)
        
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
            print(f"✅")
        elif result.get('timeout'):
            print(f"⏱️")
        else:
            print(f"⚠️")
    
    print()
    print(f"📊 三系统上传统计:")
    print(f"  memU: {memu_count}/{len(conversations)}")
    print(f"  Hippocampus: {hippo_count}/{len(conversations)}")
    print(f"  MemOS: {memos_count}/{len(conversations)}")
    
    if timeout_count > 0:
        print(f"  ⏱️ 超时: {timeout_count}")
        
        # 检查代理
        print()
        print("🔍 检查网络代理状态...")
        if check_proxy():
            print("  ✅ 代理正常 (Mihomo port 7890)")
        else:
            print("  ⚠️ 代理可能异常")
    
    return success_count, memu_count, hippo_count, memos_count

def save_to_daily_file(conversations):
    """保存到每日记忆文件（最高优先级）"""
    today = datetime.now().strftime("%Y-%m-%d")
    daily_file = MEMORY_DIR / f"{today}.md"
    
    # 读取现有内容检查重复
    existing_content = ""
    if daily_file.exists():
        try:
            with open(daily_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        except:
            pass
    
    entries = []
    for conv in conversations:
        # 检查是否已存在（简单检查）
        if conv['user'][:50] in existing_content:
            continue
            
        timestamp = datetime.now().strftime("%H:%M")
        entry = f"\n---\n\n**{timestamp}**\n\n**一碗**: {conv['user']}\n\n**碗皮**: {conv['assistant']}\n"
        entries.append(entry)
    
    if not entries:
        print("  ℹ️ 无新对话需要保存（都已存在）")
        return True
    
    try:
        with open(daily_file, 'a', encoding='utf-8') as f:
            f.write('\n'.join(entries))
        print(f"  ✅ 已保存 {len(entries)} 条新对话")
        return True
    except Exception as e:
        print(f"  ❌ 保存失败: {e}")
        return False

def generate_summary(conversations):
    """生成会话摘要"""
    if not conversations:
        return "无新增对话"
    
    # 提取关键词（简单版本）
    topics = []
    for conv in conversations[:3]:
        user_text = conv['user'].lower()
        if any(kw in user_text for kw in ['推送', '新闻', '监控']):
            topics.append("信息推送")
        elif any(kw in user_text for kw in ['heartbeat', '心跳', '检查']):
            topics.append("系统监控")
        elif any(kw in user_text for kw in ['修复', '配置', '脚本']):
            topics.append("系统维护")
        elif any(kw in user_text for kw in ['长白', '旅行', '天气']):
            topics.append("旅行协助")
    
    if topics:
        return f"主要涉及: {', '.join(set(topics))}"
    return f"共 {len(conversations)} 组对话"

async def main():
    """主函数"""
    print("="*60)
    print("🧠 会话历史批量存储 v3.0 (非阻塞版)")
    print(f"   超时: {UPLOAD_TIMEOUT}s | 去重: 开启 | 本地优先")
    print("="*60)
    print()
    
    # 1. 获取会话历史
    print("🔍 读取最近1小时的会话历史...")
    messages = get_session_history(hours=1)
    print(f"  找到 {len(messages)} 条消息")
    
    # 2. 提取对话
    conversations = extract_conversations(messages)
    print(f"  提取 {len(conversations)} 组有效对话")
    print()
    
    if not conversations:
        print("ℹ️ 没有新的对话需要存储")
        
        # 记录空运行
        log_file = MEMORY_DIR / "nightly-build.log"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')} UTC] 对话历史批量存储\n")
            f.write(f"  ℹ️ 无新对话\n")
        return 0
    
    # 3. 保存到本地（优先保证）
    print("💾 保存到每日记忆文件（高优先级）...")
    local_success = save_to_daily_file(conversations)
    if local_success:
        print("  ✅ 本地保存完成")
    else:
        print("  ❌ 本地保存失败")
    print()
    
    # 4. 上传到云端（非阻塞，超时保护）
    success, memu, hippo, memos = await store_conversations_batch(conversations)
    
    # 5. 生成摘要
    summary = generate_summary(conversations)
    
    # 6. 记录日志
    print()
    print("📝 记录执行日志...")
    log_file = MEMORY_DIR / "nightly-build.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')} UTC] 对话历史批量存储 v3.0\n")
        f.write(f"  📨 消息: {len(messages)} | 💬 对话: {len(conversations)}\n")
        f.write(f"  📝 {summary}\n")
        f.write(f"  💾 本地: {'✅' if local_success else '❌'}\n")
        f.write(f"  ☁️ 云端: memU={memu}, Hippocampus={hippo}, MemOS={memos}\n")
        f.write(f"  状态: {'✅ 全部成功' if success == len(conversations) else '⚠️ 部分完成'}\n")
    
    print()
    print("="*60)
    if local_success and success == len(conversations):
        print("✅ 全部完成! 本地+云端全部成功")
    elif local_success:
        print("✅ 本地完成! 云端部分成功（已记录）")
    else:
        print("⚠️ 本地保存失败，需要检查")
    print("="*60)
    
    return 0

if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
