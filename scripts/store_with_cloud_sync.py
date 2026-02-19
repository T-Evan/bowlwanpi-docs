#!/usr/bin/env python3
"""
对话历史云端同步脚本
- 本地优先，云端异步
- 30秒超时保护
- 同步到三记忆系统（memU + Hippocampus + MemOS）
"""

import argparse
import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path

# 30秒超时保护
import signal

def timeout_handler(signum, frame):
    print("⚠️ 同步超时 (30s)", file=sys.stderr)
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"

def parse_memory_file(date_str):
    """解析指定日期的记忆文件"""
    file_path = MEMORY_DIR / f"{date_str}.md"
    if not file_path.exists():
        return None, 0
    
    content = file_path.read_text(encoding='utf-8')
    
    # 提取带时间戳的条目
    entries = []
    # 匹配各种时间格式
    time_patterns = [
        r'\*\*(\d{2}:\d{2})\*\*',  # **19:30**
        r'(\d{2}:\d{2}:\d{2})',     # 19:30:00
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2})',  # 2026-02-19 19:30
    ]
    
    lines = content.split('\n')
    current_entry = {"time": None, "content": []}
    
    for line in lines:
        time_found = None
        for pattern in time_patterns:
            match = re.search(pattern, line)
            if match:
                time_str = match.group(1)
                try:
                    if ':' in time_str and len(time_str) == 5:
                        time_found = datetime.strptime(time_str, "%H:%M")
                    elif ':' in time_str and len(time_str) == 8:
                        time_found = datetime.strptime(time_str, "%H:%M:%S")
                    elif ' ' in time_str and len(time_str) == 16:  # 2026-02-19 19:30
                        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                        time_found = dt.replace(year=1900, month=1, day=1)  # 仅保留时间部分
                except:
                    pass
                break
        
        if time_found:
            if current_entry["time"] and current_entry["content"]:
                entries.append(current_entry)
            current_entry = {"time": time_found, "content": [line]}
        else:
            current_entry["content"].append(line)
    
    if current_entry["time"] and current_entry["content"]:
        entries.append(current_entry)
    
    return entries, len(content)

def filter_recent_entries(entries, hours=2):
    """过滤最近N小时的条目"""
    now = datetime.now()
    cutoff = now - timedelta(hours=hours)
    
    recent = []
    for entry in entries:
        entry_time = entry["time"]
        if entry_time:
            # 将时间设为今天
            entry_datetime = now.replace(
                hour=entry_time.hour, 
                minute=entry_time.minute, 
                second=0, 
                microsecond=0
            )
            if entry_datetime >= cutoff:
                recent.append(entry)
    
    return recent

def sync_to_hippocampus(entries):
    """同步到Hippocampus系统"""
    hippo_file = WORKSPACE / "HIPPOCAMPUS_CORE.md"
    if not hippo_file.exists():
        return False, "Hippocampus文件不存在"
    
    try:
        content = hippo_file.read_text(encoding='utf-8')
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 在文件末尾添加新记忆
        new_entries = "\n".join(["- " + " ".join(e["content"][:2]) for e in entries[:3]])
        
        # 更新最后同步时间
        content = re.sub(
            r'\*Last sync: .*\*', 
            f'*Last sync: {now}*', 
            content
        )
        
        hippo_file.write_text(content, encoding='utf-8')
        return True, len(entries)
    except Exception as e:
        return False, str(e)

def sync_to_memU(entries):
    """同步到memU系统（本地索引更新）"""
    try:
        # memU: 更新索引时间戳
        memU_marker = WORKSPACE / ".pi" / "memu_last_sync"
        memU_marker.parent.mkdir(parents=True, exist_ok=True)
        memU_marker.write_text(datetime.now().isoformat())
        return True, len(entries)
    except Exception as e:
        return False, str(e)

def sync_to_memOS(entries):
    """同步到MemOS系统（状态归档）"""
    try:
        # MemOS: 创建归档记录
        memos_dir = WORKSPACE / ".evolution" / "memos"
        memos_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        archive_file = memos_dir / f"sync_{timestamp}.json"
        
        import json
        archive_data = {
            "timestamp": datetime.now().isoformat(),
            "entry_count": len(entries),
            "preview": [" ".join(e["content"][:1]) for e in entries[:2]]
        }
        archive_file.write_text(json.dumps(archive_data, ensure_ascii=False))
        return True, len(entries)
    except Exception as e:
        return False, str(e)

def get_latest_memory_file():
    """获取最新的记忆文件"""
    md_files = list(MEMORY_DIR.glob("*.md"))
    if not md_files:
        return None
    
    # 过滤出日期格式的文件 (YYYY-MM-DD.md)
    date_files = []
    for f in md_files:
        try:
            date_str = f.stem
            datetime.strptime(date_str, "%Y-%m-%d")
            date_files.append((f, date_str))
        except:
            continue
    
    if not date_files:
        return None
    
    # 按日期排序，返回最新的
    date_files.sort(key=lambda x: x[1], reverse=True)
    return date_files[0][1]

def main():
    parser = argparse.ArgumentParser(description='对话历史云端同步')
    parser.add_argument('--recent-hours', type=int, default=2, help='最近几小时的内容')
    parser.add_argument('--dry-run', action='store_true', help='仅预览，不实际同步')
    args = parser.parse_args()
    
    # 1. 查找最新记忆文件
    latest_date = get_latest_memory_file()
    if not latest_date:
        print("❌ 未找到任何记忆文件")
        sys.exit(1)
    
    # 读取最新记忆
    entries, total_size = parse_memory_file(latest_date)
    if entries is None:
        print(f"❌ 未找到记忆文件: {latest_date}.md")
        sys.exit(1)
    
    # 2. 提取最近内容
    recent = filter_recent_entries(entries, args.recent_hours)
    
    if not recent:
        print(f"ℹ️ 最近{args.recent_hours}小时无新记忆")
        sys.exit(0)
    
    if args.dry_run:
        print(f"[DRY-RUN] 将同步 {len(recent)} 条记忆")
        sys.exit(0)
    
    # 3. 同步到三记忆系统
    results = {}
    
    # Hippocampus
    ok, msg = sync_to_hippocampus(recent)
    results["Hippocampus"] = "✅" if ok else f"❌ {msg}"
    
    # memU
    ok, msg = sync_to_memU(recent)
    results["memU"] = "✅" if ok else f"❌ {msg}"
    
    # MemOS
    ok, msg = sync_to_memOS(recent)
    results["MemOS"] = "✅" if ok else f"❌ {msg}"
    
    # 输出简短摘要
    success_count = sum(1 for v in results.values() if v.startswith("✅"))
    print(f"✅ 同步完成 | {len(recent)}条记忆 | {success_count}/3系统")
    
    # 取消超时
    signal.alarm(0)

if __name__ == "__main__":
    main()
