#!/usr/bin/env python3
"""
会话历史捕获与存储系统 v4.0
- 从 OpenClaw 会话 JSONL 读取对话
- 写入本地记忆文件（人类可读格式）
- 同步到云端记忆系统
"""

import os
import sys
import json
import asyncio
import glob
from datetime import datetime, timedelta
from pathlib import Path

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
SESSIONS_DIR = Path("/root/.openclaw/agents/main/sessions")
UPLOAD_TIMEOUT = 30

# 添加路径
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(WORKSPACE / "skills/unified-memory"))
sys.path.insert(0, str(WORKSPACE / "skills/memu-memory"))
sys.path.insert(0, str(WORKSPACE / "skills/hippocampus-memory"))

def get_today_sessions():
    """获取今天的会话文件"""
    today = datetime.now().strftime('%Y-%m-%d')
    session_files = []
    
    if not SESSIONS_DIR.exists():
        return []
    
    for jsonl_file in SESSIONS_DIR.glob("*.jsonl"):
        try:
            # 检查文件修改时间
            mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
            if mtime.strftime('%Y-%m-%d') == today:
                session_files.append(jsonl_file)
        except:
            continue
    
    # 按修改时间排序，最新的在前
    session_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return session_files

def extract_text_from_content(content):
    """从 content 字段提取文本"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                texts.append(item.get('text', ''))
            elif isinstance(item, str):
                texts.append(item)
        return '\n'.join(texts)
    return ''

def extract_conversations_from_session(jsonl_file, max_age_hours=24):
    """从会话文件中提取对话"""
    conversations = []
    current_user = None
    current_assistant = None
    
    try:
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    msg = json.loads(line)
                except:
                    continue
                
                # 只处理 message 类型
                if msg.get('type') != 'message':
                    continue
                
                message_data = msg.get('message', {})
                
                # 检查消息时间 (UTC 时间)
                msg_time_str = msg.get('timestamp') or msg.get('time')
                skip_msg = False
                if msg_time_str:
                    try:
                        # 处理 UTC 时间 (带 Z 后缀)
                        msg_time_str_clean = msg_time_str.replace('Z', '+00:00')
                        msg_time = datetime.fromisoformat(msg_time_str_clean)
                        # 转换为本地时间进行比较
                        msg_time_local = msg_time.replace(tzinfo=None)
                        if msg_time_local < cutoff_time:
                            skip_msg = True
                    except Exception as e:
                        pass
                
                if skip_msg:
                    continue
                
                role = message_data.get('role', '')
                content = extract_text_from_content(message_data.get('content', ''))
                
                if not content or len(content) < 5:  # 跳过太短的消息
                    continue
                
                # 识别用户消息
                if role == 'user':
                    # 跳过 cron/system 消息
                    if '[cron:' in content or content.startswith('[System'):
                        continue
                    
                    # 保存之前的对话
                    if current_user and current_assistant:
                        conversations.append({
                            'user': current_user,
                            'assistant': current_assistant,
                            'timestamp': datetime.now().isoformat()
                        })
                    current_user = content
                    current_assistant = None
                
                # 识别助手消息
                elif role == 'assistant':
                    # 跳过工具调用和系统消息
                    if content.startswith('🔧') or content.startswith('⚠️'):
                        continue
                    current_assistant = content
        
        # 保存最后一组
        if current_user and current_assistant:
            conversations.append({
                'user': current_user,
                'assistant': current_assistant,
                'timestamp': datetime.now().isoformat()
            })
    
    except Exception as e:
        print(f"⚠️ 解析会话文件失败 {jsonl_file}: {e}")
    
    return conversations

def write_to_memory_file(conversations):
    """写入记忆文件（人类可读格式）"""
    if not conversations:
        return False
    
    today = datetime.now().strftime('%Y-%m-%d')
    memory_file = MEMORY_DIR / f"{today}.md"
    
    try:
        os.makedirs(MEMORY_DIR, exist_ok=True)
        
        # 读取现有内容
        existing_content = ""
        if memory_file.exists():
            with open(memory_file, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        
        # 生成新内容
        new_content = f"# {today} - 今日对话记录\n\n"
        new_content += f"*自动生成于 {datetime.now().strftime('%H:%M')}*\n\n"
        
        for i, conv in enumerate(conversations, 1):
            new_content += f"---\n\n"
            new_content += f"**一碗**: {conv['user']}\n\n"
            new_content += f"**碗皮**: {conv['assistant']}\n\n"
        
        # 追加而非覆盖（保留已有内容）
        with open(memory_file, 'a', encoding='utf-8') as f:
            if existing_content and not existing_content.endswith('\n'):
                f.write('\n')
            f.write(new_content)
        
        print(f"✅ 记忆文件更新: {memory_file} (+{len(conversations)} 段对话)")
        return True
    
    except Exception as e:
        print(f"❌ 写入记忆文件失败: {e}")
        return False

async def sync_to_cloud_systems(conversations):
    """同步到云端记忆系统"""
    if not conversations:
        return
    
    try:
        from unified_memory_manager_v3 import store_to_all_systems
        
        print(f"\n☁️ 同步到云端记忆系统...")
        
        synced = 0
        for i, conv in enumerate(conversations[-3:], 1):  # 只同步最近3条
            try:
                result = await asyncio.wait_for(
                    store_to_all_systems(
                        user_msg=conv['user'][:500],
                        assistant_msg=conv['assistant'][:1000],
                        importance=0.6,
                        enable_memu=True,
                        enable_hippo=True,
                        enable_memos=True,
                        enable_qmdr=True
                    ),
                    timeout=UPLOAD_TIMEOUT
                )
                
                if any(result.values()):
                    synced += 1
                    print(f"  ✅ 对话 {i}: 同步成功")
                else:
                    print(f"  ⚠️ 对话 {i}: 部分失败")
                
                await asyncio.sleep(0.3)
            
            except asyncio.TimeoutError:
                print(f"  ⏱️ 对话 {i}: 超时")
            except Exception as e:
                print(f"  ❌ 对话 {i}: {e}")
        
        print(f"\n📊 云端同步: {synced}/{min(len(conversations), 3)} 成功")
    
    except Exception as e:
        print(f"❌ 云端同步失败: {e}")

def main():
    """主函数"""
    print(f"🧠 会话历史捕获系统 v4.0 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 1. 获取今天的会话文件
    session_files = get_today_sessions()
    if not session_files:
        print("⚠️ 未找到今天的会话文件")
        return 0
    
    print(f"📁 找到 {len(session_files)} 个今日会话文件")
    
    # 2. 提取对话
    all_conversations = []
    for session_file in session_files[:3]:  # 最多处理3个文件
        conversations = extract_conversations_from_session(session_file)
        if conversations:
            all_conversations.extend(conversations)
            print(f"  📄 {session_file.name}: {len(conversations)} 段对话")
    
    if not all_conversations:
        print("⚠️ 未提取到对话内容")
        return 0
    
    print(f"\n📊 总计: {len(all_conversations)} 段对话")
    
    # 3. 写入本地记忆文件
    write_to_memory_file(all_conversations)
    
    # 4. 同步到云端
    try:
        asyncio.run(sync_to_cloud_systems(all_conversations))
    except Exception as e:
        print(f"⚠️ 云端同步异常: {e}")
    
    print("\n✅ 会话捕获完成")
    return 0

if __name__ == '__main__':
    exit(main())
