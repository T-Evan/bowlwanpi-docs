#!/usr/bin/env python3
"""
NOW.md 自动更新脚本
- 读取当前系统状态
- 更新 NOW.md 关键字段
- 用于快速恢复上下文
"""

import json
import os
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
NOW_FILE = MEMORY_DIR / "NOW.md"

def get_system_status():
    """获取系统状态"""
    status = {
        "gateway": "❓",
        "proxy": "❓",
        "cron": "❓",
        "memory": "❓"
    }
    
    # Check Gateway
    try:
        import subprocess
        result = subprocess.run(
            ["curl", "-sf", "--max-time", "2", "http://127.0.0.1:18789/health"],
            capture_output=True
        )
        status["gateway"] = "✅" if result.returncode == 0 else "❌"
    except:
        pass
    
    # Check Proxy
    try:
        result = subprocess.run(
            ["pgrep", "-f", "mihomo"],
            capture_output=True
        )
        status["proxy"] = "✅" if result.returncode == 0 else "❌"
    except:
        pass
    
    # Check last memory sync
    try:
        log_file = MEMORY_DIR / f"storage-v3-{datetime.now().strftime('%Y%m%d')}.log"
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1]
                    if '成功' in last_line or 'stored' in last_line:
                        status["memory"] = "✅"
                    else:
                        status["memory"] = "⚠️"
        else:
            status["memory"] = "⬜"
    except:
        pass
    
    return status

def get_pending_tasks():
    """获取待处理任务"""
    try:
        task_file = MEMORY_DIR / "task-queue.json"
        with open(task_file, 'r') as f:
            data = json.load(f)
            pending = [t for t in data.get('tasks', []) if t.get('status') == 'pending']
            return pending[:3]  # Top 3
    except:
        return []

def update_now_md():
    """更新 NOW.md"""
    if not NOW_FILE.exists():
        print("❌ NOW.md 不存在")
        return False
    
    try:
        with open(NOW_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Update timestamp
        now = datetime.now().strftime('%Y-%m-%d %H:%M')
        content = content.replace(
            '*最后更新: 2026-02-17 --:--*',
            f'*最后更新: {now}*'
        )
        
        # Update system status
        status = get_system_status()
        
        # Simple string replacement for status table
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if '| Gateway |' in line and '|' in line:
                parts = line.split('|')
                if len(parts) >= 4:
                    line = f"| Gateway | {status['gateway']} | 运行中 |"
            elif '| 代理 |' in line or '| Proxy |' in line:
                parts = line.split('|')
                if len(parts) >= 4:
                    line = f"| 代理 | {status['proxy']} | Mihomo |"
            elif '| 记忆同步 |' in line:
                parts = line.split('|')
                if len(parts) >= 4:
                    line = f"| 记忆同步 | {status['memory']} | 上次: {now} |"
            new_lines.append(line)
        
        content = '\n'.join(new_lines)
        
        # Update pending tasks
        tasks = get_pending_tasks()
        if tasks:
            task_section = "### 待处理任务（按优先级）\n"
            for i, task in enumerate(tasks, 1):
                task_desc = task.get('content', 'Unknown')[:50]
                task_section += f"{i}. {task_desc}\n"
            
            # Replace task section
            if "### 待处理任务" in content:
                # Find and replace
                import re
                pattern = r'(### 待处理任务（按优先级）\n)(.*?)(\n###|$)'
                replacement = r'\1' + ''.join([f"{i+1}. {t.get('content', 'Unknown')[:50]}\n" for i, t in enumerate(tasks)]) + r'\3'
                content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        with open(NOW_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ NOW.md 已更新 ({now})")
        return True
        
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        return False

def main():
    print("📝 更新 NOW.md...")
    update_now_md()
    print("\n📋 当前状态:")
    status = get_system_status()
    for k, v in status.items():
        print(f"  {k}: {v}")

if __name__ == '__main__':
    main()
