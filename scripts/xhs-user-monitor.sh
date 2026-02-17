#!/bin/bash
# 小红书用户笔记监控 - 改进版
# 通过获取推荐feed并筛选目标用户的内容

USER_ID="60707e5100000000010078b3"
USER_NAME="目标用户"
MONITOR_DIR="/root/.openclaw/workspace/memory/xiaohongshu-users"
LOG_FILE="/var/log/bowlwanpi-xhs-user-monitor.log"
NOTES_HISTORY="$MONITOR_DIR/${USER_ID}_notes.json"

mkdir -p "$MONITOR_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔍 开始监控用户: $USER_ID" >> "$LOG_FILE"

# 检查MCP服务器
if ! curl -s http://localhost:18060/api/v1/login/status > /dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ MCP服务器未运行" >> "$LOG_FILE"
    exit 1
fi

# 获取推荐feed并筛选用户笔记
cd /root/.openclaw/workspace/skills/xiaohongshu-mcp/scripts

python3 << 'EOF'
import json
import requests
import os
import sys
from datetime import datetime

USER_ID = "60707e5100000000010078b3"
MONITOR_DIR = "/root/.openclaw/workspace/memory/xiaohongshu-users"
LOG_FILE = "/var/log/bowlwanpi-xhs-user-monitor.log"
NOTES_HISTORY = f"{MONITOR_DIR}/{USER_ID}_notes.json"

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {msg}\n")

def load_history():
    if os.path.exists(NOTES_HISTORY):
        try:
            with open(NOTES_HISTORY, 'r') as f:
                return json.load(f)
        except:
            return {"notes": [], "last_check": ""}
    return {"notes": [], "last_check": ""}

def save_history(history):
    with open(NOTES_HISTORY, 'w') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_feeds():
    try:
        resp = requests.get("http://localhost:18060/api/v1/feeds/list", timeout=30)
        data = resp.json()
        if data.get("success"):
            return data.get("data", {}).get("feeds", [])
    except Exception as e:
        log(f"❌ 获取feed失败: {e}")
    return []

def send_notification(title, author, link):
    message = f"""🍠 小红书用户更新提醒

👤 用户ID: {USER_ID}
📝 标题: {title}
✍️ 作者: {author}

🔗 链接: {link}

⏰ 检测时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    # 发送到飞书
    try:
        import subprocess
        result = subprocess.run(
            ["openclaw", "message", "send", "--channel", "feishu", 
             "--target", "user:ou_a22ce6536f26dee3fec9397a9a1b87b5", "--message", "-"],
            input=message,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            log(f"✅ 通知已发送: {title}")
        else:
            log(f"⚠️ 发送通知失败: {result.stderr}")
    except Exception as e:
        log(f"❌ 发送通知出错: {e}")

def main():
    log("🔍 开始检查...")
    
    # 加载历史记录
    history = load_history()
    known_ids = {n["id"] for n in history.get("notes", [])}
    
    # 获取当前feed
    feeds = get_feeds()
    if not feeds:
        log("⚠️ 未获取到feed数据")
        return
    
    # 筛选目标用户的笔记
    user_notes = []
    new_notes = []
    
    for feed in feeds:
        note_card = feed.get("noteCard", {})
        user = note_card.get("user", {})
        
        if user.get("userId") == USER_ID:
            note_info = {
                "id": feed.get("id"),
                "title": note_card.get("displayTitle", "无标题"),
                "author": user.get("nickname", "未知"),
                "xsec_token": feed.get("xsecToken"),
                "time": note_card.get("time", ""),
                "liked_count": note_card.get("interactInfo", {}).get("likedCount", 0),
                "found_at": datetime.now().isoformat()
            }
            user_notes.append(note_info)
            
            # 检查是否为新笔记
            if feed.get("id") not in known_ids:
                new_notes.append(note_info)
                link = f"https://www.xiaohongshu.com/explore/{note_info['id']}?xsec_token={note_info['xsec_token']}"
                send_notification(note_info['title'], note_info['author'], link)
    
    # 更新历史记录
    if user_notes:
        # 合并历史记录，保留最近的50条
        all_notes = new_notes + history.get("notes", [])
        all_notes = all_notes[:50]  # 只保留50条
        history["notes"] = all_notes
        history["last_check"] = datetime.now().isoformat()
        save_history(history)
        
        log(f"✅ 找到 {len(user_notes)} 条用户笔记，其中 {len(new_notes)} 条是新笔记")
    else:
        log("ℹ️ 本次检查未在feed中发现该用户的笔记")

if __name__ == "__main__":
    main()
EOF

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ 监控完成" >> "$LOG_FILE"
