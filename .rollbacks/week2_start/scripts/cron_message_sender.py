#!/usr/bin/env python3
"""
定时任务消息发送器
用于 cron 定时推送消息到飞书
"""

import sys
import json
import os
from datetime import datetime

# 飞书配置
FEISHU_USER_ID = "ou_a22ce6536f26dee3fec9397a9a1b87b5"

def send_to_feishu(message):
    """发送消息到飞书"""
    try:
        # 写入待发送消息文件
        pending_file = "/tmp/bowlwanpi-cron-messages"
        with open(pending_file, 'a') as f:
            f.write(f"{json.dumps({'time': datetime.now().isoformat(), 'content': message})}\n")
        return True
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 2:
        # 从标准输入读取
        message = sys.stdin.read()
    else:
        message = sys.argv[1]
    
    if not message.strip():
        print("No message provided")
        sys.exit(1)
    
    # 添加时间戳
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    full_message = f"[{timestamp}]\n\n{message}"
    
    if send_to_feishu(full_message):
        print("Message queued successfully")
        sys.exit(0)
    else:
        print("Failed to queue message")
        sys.exit(1)

if __name__ == "__main__":
    main()
