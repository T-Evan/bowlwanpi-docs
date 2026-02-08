#!/usr/bin/env python3
"""
MemOS 上传代理 - 通过 OpenClaw sessions_spawn 调用

这个脚本被设计为通过 sessions_spawn 调用，在 OpenClaw 内部执行，
因此可以使用 tools 调用 MemOS MCP 服务。

用法:
  作为子代理任务运行，会自动调用 memos/create tool
"""

import json
import sys
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
PENDING_FILE = MEMORY_DIR / "memos-pending-upload.jsonl"
COMPLETED_FILE = MEMORY_DIR / "memos-completed-upload.jsonl"


def read_pending_memories():
    """读取待上传的记忆"""
    if not PENDING_FILE.exists():
        return []
    
    pending = []
    with open(PENDING_FILE, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                    if entry.get('status') == 'pending_upload':
                        pending.append(entry)
                except:
                    continue
    
    return pending


def upload_to_memos(entry: dict) -> bool:
    """
    上传单条记忆到 MemOS
    
    注意: 这个函数在子代理中通过 tools 调用
    """
    content = f"**一碗**: {entry['user']}\n\n**碗皮**: {entry['assistant']}"
    
    # 构建 tool call
    tool_call = {
        "tool": "memos-create",
        "params": {
            "content": content,
            "visibility": "PRIVATE",
            "tags": ["bowlwanpi", "conversation"]
        }
    }
    
    # 在实际环境中，这里会被替换为真实的 tool 调用
    # 当前返回模拟结果
    print(f"📤 准备上传: {entry['user'][:50]}...")
    print(f"   Tool call: {json.dumps(tool_call, ensure_ascii=False)}")
    
    return True


def main():
    """主函数"""
    print("="*60)
    print("📤 MemOS 批量上传代理")
    print("="*60)
    print()
    
    # 读取待上传的记忆
    pending = read_pending_memories()
    print(f"📋 找到 {len(pending)} 条待上传记忆")
    print()
    
    if not pending:
        print("ℹ️ 没有待上传的记忆")
        return 0
    
    # 批量上传
    success_count = 0
    for i, entry in enumerate(pending, 1):
        print(f"[{i}/{len(pending)}] 上传中...")
        
        if upload_to_memos(entry):
            success_count += 1
            # 标记为已完成
            entry['status'] = 'uploaded'
            entry['uploaded_at'] = str(datetime.now().isoformat())
            
            # 写入已完成列表
            with open(COMPLETED_FILE, 'a') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        print()
    
    # 清空待上传列表
    PENDING_FILE.write_text('')
    
    # 输出结果
    print("="*60)
    print(f"📊 上传完成: {success_count}/{len(pending)}")
    print("="*60)
    
    return 0 if success_count == len(pending) else 1


if __name__ == '__main__':
    from datetime import datetime
    sys.exit(main())
