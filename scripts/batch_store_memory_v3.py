#!/usr/bin/env python3
"""
四记忆系统自动存储脚本 v3.1
每小时自动存储对话历史到 memU + Hippocampus + MemOS + QMDR
简化版：从 daily memory 文件读取并同步到四系统
"""

import sys
import os
import json
import asyncio
import glob
from datetime import datetime, timedelta

# 添加路径
sys.path.insert(0, '/root/.openclaw/workspace')
sys.path.insert(0, '/root/.openclaw/workspace/skills/unified-memory')
sys.path.insert(0, '/root/.openclaw/workspace/skills/memu-memory')
sys.path.insert(0, '/root/.openclaw/workspace/skills/hippocampus-memory')

from unified_memory_manager_v3 import store_to_all_systems

# 记忆目录
MEMORY_DIR = '/root/.openclaw/workspace/memory'

def load_today_memory():
    """加载今天的记忆文件"""
    today_file = os.path.join(MEMORY_DIR, f"{datetime.now().strftime('%Y-%m-%d')}.md")
    
    if not os.path.exists(today_file):
        return None
    
    try:
        with open(today_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        print(f"读取记忆文件失败: {e}")
        return None

def parse_conversations(content):
    """解析记忆文件中的对话"""
    if not content:
        return []
    
    conversations = []
    sections = content.split('---')
    
    for section in sections:
        lines = section.strip().split('\n')
        user_msg = []
        assistant_msg = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('**一碗**:') or line.startswith('**User**:'):
                msg = line.split(':', 1)[1].strip() if ':' in line else ''
                if msg:
                    user_msg.append(msg)
            elif line.startswith('**碗皮**:') or line.startswith('**Assistant**:'):
                msg = line.split(':', 1)[1].strip() if ':' in line else ''
                if msg:
                    assistant_msg.append(msg)
        
        if user_msg and assistant_msg:
            conversations.append({
                'user': '\n'.join(user_msg[-2:]),  # 最近2条
                'assistant': '\n'.join(assistant_msg[-2:]),
                'importance': 0.6 if len(user_msg) > 1 else 0.5
            })
    
    return conversations

async def store_to_four_systems():
    """存储到四记忆系统"""
    print(f"🧠 四记忆系统自动存储 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 加载今天的记忆
    content = load_today_memory()
    if not content:
        print("❌ 今天的记忆文件为空或不存在")
        return
    
    # 解析对话
    conversations = parse_conversations(content)
    if not conversations:
        print("⚠️ 未找到可存储的对话")
        return
    
    print(f"📄 找到 {len(conversations)} 段对话")
    
    # 只存储最近的几段（避免太多）
    recent_conv = conversations[-3:]  # 最近3段
    
    stored = 0
    for i, conv in enumerate(recent_conv, 1):
        print(f"\n📝 处理第 {i}/{len(recent_conv)} 段对话...")
        print(f"   用户: {conv['user'][:50]}...")
        
        try:
            result = await store_to_all_systems(
                user_msg=conv['user'][:500],
                assistant_msg=conv['assistant'][:1000],
                importance=conv['importance'],
                enable_memu=True,
                enable_hippo=True,
                enable_memos=True,
                enable_qmdr=True
            )
            
            status = ' | '.join([f"{k}:{'✅' if v else '❌'}" for k, v in result.items()])
            print(f"   结果: {status}")
            
            if any(result.values()):
                stored += 1
            
            # 小延迟避免 API 限流
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ 存储失败: {e}")
    
    print("\n" + "=" * 60)
    print(f"✅ 完成: 成功存储 {stored}/{len(recent_conv)} 段对话")
    
    # 记录日志
    log_file = os.path.join(MEMORY_DIR, f"storage-v3-{datetime.now().strftime('%Y%m%d')}.log")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().isoformat()}] 存储了 {stored}/{len(recent_conv)} 段对话\n")

def main():
    """主函数"""
    try:
        asyncio.run(store_to_four_systems())
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0

if __name__ == '__main__':
    exit(main())
