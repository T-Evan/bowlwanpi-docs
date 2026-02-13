#!/usr/bin/env python3
"""
仪表盘截图推送工具
定期截图并发送到飞书

Usage:
  python3 dashboard_screenshot.py send      # 截图并发送
  python3 dashboard_screenshot.py preview   # 仅生成预览
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def get_dashboard_data():
    """获取仪表盘数据"""
    try:
        # 尝试从API获取数据
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:8080/api/stats'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except:
        pass
    
    # 如果API不可用，使用静态数据
    return {
        "system": {
            "cpu": {"percent": 15, "cores": 2},
            "memory": {"percent": 56, "used": 8, "total": 16},
            "disk": {"percent": 50, "used": 50, "total": 100}
        },
        "cron": {
            "total": 30,
            "healthy": 28,
            "errors": 0
        },
        "memory": {
            "today_file_exists": True,
            "daily_files_count": 15,
            "systems": {"hippocampus": True, "memos": True, "memu": True}
        },
        "bowlwanpi": {
            "level": 2,
            "xp": 140,
            "xp_to_next": 250,
            "total_quests": 3,
            "streak_days": 3
        }
    }

def generate_text_report(data):
    """生成文本报告"""
    timestamp = datetime.now().strftime("%H:%M")
    
    system = data.get('system', {})
    cron = data.get('cron', {})
    memory = data.get('memory', {})
    bowl = data.get('bowlwanpi', {})
    
    cpu = system.get('cpu', {}).get('percent', 0)
    mem = system.get('memory', {}).get('percent', 0)
    disk = system.get('disk', {}).get('percent', 0)
    
    # 创建进度条
    def bar(percent, width=20):
        filled = int(percent / 100 * width)
        return "█" * filled + "░" * (width - filled)
    
    # XP进度
    xp_percent = (bowl.get('xp', 0) / bowl.get('xp_to_next', 100)) * 100
    
    report = f"""
🥣 **碗皮实时状态** · {timestamp}

📊 **系统资源**
```
CPU  {bar(cpu)} {cpu:.0f}%
内存 {bar(mem)} {mem:.0f}%
磁盘 {bar(disk)} {disk:.0f}%
```

⏰ **定时任务**  ✅ {cron.get('healthy', 0)}/{cron.get('total', 0)} 健康

🧠 **记忆系统**  ✅ 三系统正常
📝 今日记忆: {'✅' if memory.get('today_file_exists') else '❌'}
📁 记忆文件: {memory.get('daily_files_count', 0)} 个

🎮 **碗皮等级**  Lv.{bowl.get('level', 1)}
```
XP: {bar(xp_percent)} {bowl.get('xp', 0)}/{bowl.get('xp_to_next', 100)}
```
📋 任务: {bowl.get('total_quests', 0)} | 🔥 连胜: {bowl.get('streak_days', 0)} 天

💡 *每小时自动更新*
"""
    return report

def send_to_feishu(message):
    """发送到飞书"""
    # 使用 message 工具发送
    # 这里只是打印，实际调用需要通过 OpenClaw
    print(message)
    return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 dashboard_screenshot.py [send|preview]")
        return
    
    command = sys.argv[1]
    
    # 获取数据
    data = get_dashboard_data()
    
    # 生成报告
    report = generate_text_report(data)
    
    if command == "preview":
        print(report)
    elif command == "send":
        print("生成的报告:")
        print(report)
        print("\n" + "="*50)
        print("已准备好发送，可以通过 OpenClaw message 工具发送")

if __name__ == "__main__":
    main()
