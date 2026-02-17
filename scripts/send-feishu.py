#!/usr/bin/env python3
"""
直接发送飞书消息 - 绕过 OpenClaw CLI
用于系统 cron 定时任务
"""

import sys
import json
import urllib.request
import urllib.error
import os

# 从 credentials 文件读取配置
CREDENTIALS_FILE = "/clawd-data/moltbook-credentials.json"

# 飞书默认配置
FEISHU_APP_ID = "cli_a22ce6536f26d00b"
FEISHU_USER_ID = "user:ou_a22ce6536f26dee3fec9397a9a1b87b5"

def get_feishu_token():
    """获取飞书 tenant_access_token"""
    try:
        # 尝试从环境变量获取
        token = os.environ.get("FEISHU_TOKEN")
        if token:
            return token
        
        # 尝试从 credentials 文件读取
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'r') as f:
                creds = json.load(f)
                # 这里应该调用飞书 API 获取 token
                # 简化处理，返回 None 让调用者处理
                return None
    except Exception as e:
        print(f"Error getting token: {e}", file=sys.stderr)
    return None

def send_feishu_message(content, user_id=None):
    """发送飞书消息"""
    if user_id is None:
        user_id = FEISHU_USER_ID
    
    # 这里需要实现实际的飞书 API 调用
    # 暂时使用 echo 输出到日志
    print(f"[FEISHU MESSAGE TO {user_id}]")
    print(content)
    return True

def send_via_openclaw_api(content):
    """尝试通过 OpenClaw Gateway API 发送"""
    try:
        import subprocess
        import tempfile
        
        # 创建临时消息文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            msg_file = f.name
        
        # 使用环境变量方式传递消息
        env = os.environ.copy()
        env['BOWLWANPI_MESSAGE'] = content
        
        result = subprocess.run(
            ['openclaw', 'message', 'send', '--channel', 'feishu', '--target', FEISHU_USER_ID],
            input=content,
            capture_output=True,
            text=True,
            env=env
        )
        
        os.unlink(msg_file)
        
        if result.returncode == 0:
            return True
        else:
            print(f"Error: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error sending via openclaw: {e}", file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: send-feishu.py '<message>'", file=sys.stderr)
        sys.exit(1)
    
    message = sys.argv[1]
    
    # 尝试多种发送方式
    if send_via_openclaw_api(message):
        print("Message sent successfully via OpenClaw API")
        sys.exit(0)
    
    # 如果都失败，记录到文件等待主会话处理
    pending_file = "/tmp/bowlwanpi-pending-messages"
    with open(pending_file, 'a') as f:
        f.write(f"{json.dumps({'time': str(os.times()), 'content': message})}\n")
    
    print(f"Message queued to {pending_file}")

if __name__ == "__main__":
    main()
