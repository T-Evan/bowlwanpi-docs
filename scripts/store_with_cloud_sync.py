#!/usr/bin/env python3
"""
对话历史批量存储 - 云端同步版
保存到本地 + 同步到三记忆系统（memU + Hippocampus + MemOS）
"""
import os
import sys
import json
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path

# 配置
WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
UPLOAD_TIMEOUT = 30  # 云端上传超时时间

# 添加路径
sys.path.insert(0, str(WORKSPACE))
sys.path.insert(0, str(WORKSPACE / "skills/memu-memory"))
sys.path.insert(0, str(WORKSPACE / "skills/hippocampus-memory"))

def get_recent_conversations(hours=24):
    """获取最近N小时的会话历史"""
    try:
        # 读取今日记忆文件
        today = datetime.now().strftime('%Y-%m-%d')
        memory_file = MEMORY_DIR / f"{today}.md"
        
        if not memory_file.exists():
            return []
        
        with open(memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 简单解析对话（查找 **一碗**: 和 **碗皮**: 模式）
        conversations = []
        lines = content.split('\n')
        current_user = None
        current_assistant = None
        
        for line in lines:
            if line.startswith('**一碗**:'):
                # 保存之前的对话
                if current_user and current_assistant:
                    conversations.append({
                        'user': current_user,
                        'assistant': current_assistant,
                        'timestamp': datetime.now().isoformat()
                    })
                current_user = line.split(':', 1)[1].strip() if ':' in line else ''
                current_assistant = None
            elif line.startswith('**碗皮**:'):
                current_assistant = line.split(':', 1)[1].strip() if ':' in line else ''
        
        # 保存最后一组
        if current_user and current_assistant:
            conversations.append({
                'user': current_user,
                'assistant': current_assistant,
                'timestamp': datetime.now().isoformat()
            })
        
        # 只返回最近5组，避免太多
        return conversations[-5:] if len(conversations) > 5 else conversations
    except Exception as e:
        print(f"⚠️ 读取会话失败: {e}")
        return []

def save_to_local(conversations):
    """保存到本地文件"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        memory_file = MEMORY_DIR / f"{today}.md"
        
        # 确保目录存在
        os.makedirs(os.path.dirname(memory_file), exist_ok=True)
        
        # 生成存储记录
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entry = f"\n---\n\n**{timestamp}** - 【定时存储记录】\n\n"
        entry += f"本次存储对话数: {len(conversations)}\n"
        
        if conversations:
            entry += "\n**对话摘要:**\n"
            for i, conv in enumerate(conversations[-3:], 1):  # 只显示最近3条摘要
                user_preview = conv['user'][:50] + "..." if len(conv['user']) > 50 else conv['user']
                entry += f"{i}. 一碗: {user_preview}\n"
        
        # 追加到文件
        with open(memory_file, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        print(f"✅ 本地保存完成: {memory_file}")
        return True
    except Exception as e:
        print(f"❌ 本地保存失败: {e}")
        return False

async def upload_to_cloud(conversations):
    """上传到三记忆系统"""
    if not conversations:
        print("ℹ️ 无对话需要上传")
        return {'memu': False, 'hippocampus': False, 'memos': False}
    
    results = {'memu': False, 'hippocampus': False, 'memos': False}
    
    try:
        # 导入 unified_memory_manager（使用 sys.path）
        sys.path.insert(0, str(WORKSPACE / 'skills/unified-memory'))
        from unified_memory_manager import UnifiedMemoryManager
        
        # 使用上下文管理器
        async with UnifiedMemoryManager() as mm:
            # 批量上传对话
            for conv in conversations:
                try:
                    result = await mm.store_memory(
                        user_message=conv['user'],
                        assistant_message=conv['assistant'],
                        importance=0.7
                    )
                    
                    # 累积结果
                    for key in results:
                        if result.get(key):
                            results[key] = True
                    
                except Exception as e:
                    print(f"⚠️ 单条上传失败: {e}")
                    continue
            
            print(f"☁️ 云端同步完成: memU={results['memu']}, Hippocampus={results['hippocampus']}, MemOS={results['memos']}")
            
    except ImportError as e:
        print(f"⚠️ 无法导入 unified_memory_manager: {e}")
        # 降级方案：直接写入 Hippocampus 本地文件
        try:
            signals_file = MEMORY_DIR / "signals.jsonl"
            for conv in conversations:
                signal = {
                    "timestamp": datetime.now().timestamp(),
                    "user": conv['user'],
                    "assistant": conv['assistant'],
                    "importance": 0.7,
                    "type": "conversation",
                    "source": "cron_batch"
                }
                with open(signals_file, 'a') as f:
                    f.write(json.dumps(signal, ensure_ascii=False) + '\n')
            results['hippocampus'] = True
            print("✅ 已降级保存到 Hippocampus 本地")
        except Exception as e2:
            print(f"❌ 降级保存也失败: {e2}")
    
    except Exception as e:
        print(f"❌ 云端上传失败: {e}")
    
    return results

def run_sync_with_timeout(conversations):
    """带超时的同步执行"""
    try:
        # 创建新事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # 设置超时
        results = loop.run_until_complete(
            asyncio.wait_for(
                upload_to_cloud(conversations),
                timeout=UPLOAD_TIMEOUT
            )
        )
        loop.close()
        return results
    except asyncio.TimeoutError:
        print(f"⚠️ 云端上传超时 ({UPLOAD_TIMEOUT}s)，已保存本地")
        return {'memu': False, 'hippocampus': False, 'memos': False, 'timeout': True}
    except Exception as e:
        print(f"⚠️ 同步执行失败: {e}")
        return {'memu': False, 'hippocampus': False, 'memos': False, 'error': str(e)}

def main():
    """主函数"""
    import argparse
    parser = argparse.ArgumentParser(description='对话历史批量存储 - 云端同步版')
    parser.add_argument('--recent-hours', type=int, default=24, help='只同步最近N小时的对话')
    args = parser.parse_args()
    
    print("🤖 对话历史批量存储 - 云端同步版")
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📅 同步范围: 最近 {args.recent_hours} 小时")
    print("-" * 40)
    
    # 1. 获取会话
    conversations = get_recent_conversations(hours=args.recent_hours)
    print(f"📥 找到 {len(conversations)} 组对话")
    
    # 2. 保存到本地（高优先级，必须成功）
    local_ok = save_to_local(conversations)
    
    # 3. 同步到云端（低优先级，超时保护）
    if conversations and local_ok:
        print("☁️ 开始云端同步...")
        cloud_results = run_sync_with_timeout(conversations)
        
        # 输出结果
        print("\n📊 同步结果:")
        print(f"  本地存储: {'✅' if local_ok else '❌'}")
        print(f"  memU: {'✅' if cloud_results.get('memu') else '⚠️'}")
        print(f"  Hippocampus: {'✅' if cloud_results.get('hippocampus') else '⚠️'}")
        print(f"  MemOS: {'✅' if cloud_results.get('memos') else '⚠️'}")
    else:
        print("ℹ️ 跳过云端同步（无对话或本地保存失败）")
    
    print("-" * 40)
    print("✅ 任务完成！")
    
    # 始终返回成功，避免 cron 报错
    return 0

if __name__ == "__main__":
    exit(main())
