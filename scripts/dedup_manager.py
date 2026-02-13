#!/usr/bin/env python3
"""
去重管理器 - 防止重复推送相同内容
"""
import json
import os
import sys
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

HISTORY_FILE = Path("/root/.openclaw/workspace/memory/dedup-history.json")
MAX_PUSHES = 3
CLEANUP_DAYS = 7

def load_history():
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    return {"records": []}

def save_history(history):
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def get_content_hash(content):
    return hashlib.md5(content.encode()).hexdigest()[:16]

def cleanup_old(history):
    cutoff = datetime.now() - timedelta(days=CLEANUP_DAYS)
    history["records"] = [
        r for r in history["records"]
        if datetime.fromisoformat(r["first_seen"]) > cutoff
    ]
    return history

def check_and_record(content, source):
    history = cleanup_old(load_history())
    content_hash = get_content_hash(content)
    
    # 查找现有记录
    for record in history["records"]:
        if record["hash"] == content_hash:
            record["push_count"] += 1
            record["last_pushed"] = datetime.now().isoformat()
            record["sources"].append({
                "source": source,
                "time": datetime.now().isoformat()
            })
            save_history(history)
            
            if record["push_count"] <= MAX_PUSHES:
                return {
                    "should_push": True,
                    "push_count": record["push_count"],
                    "reason": f"第 {record['push_count']} 次推送（最多{MAX_PUSHES}次）"
                }
            else:
                return {
                    "should_push": False,
                    "push_count": record["push_count"],
                    "reason": f"已达到最大推送次数 ({MAX_PUSHES}次)，不再推送"
                }
    
    # 新内容，创建记录
    new_record = {
        "hash": content_hash,
        "content_preview": content[:100] + "..." if len(content) > 100 else content,
        "first_seen": datetime.now().isoformat(),
        "last_pushed": datetime.now().isoformat(),
        "push_count": 1,
        "sources": [{"source": source, "time": datetime.now().isoformat()}]
    }
    history["records"].append(new_record)
    save_history(history)
    
    return {
        "should_push": True,
        "push_count": 1,
        "reason": "新内容，首次推送"
    }

if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[1] != "check":
        print("Usage: dedup_manager.py check <content> <source>")
        sys.exit(1)
    
    content = sys.argv[2]
    source = sys.argv[3]
    result = check_and_record(content, source)
    
    print(json.dumps(result, ensure_ascii=False))
    print(f"是否推送: {result['should_push']}")
