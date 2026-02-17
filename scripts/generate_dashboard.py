#!/usr/bin/env python3
"""
系统仪表盘生成器
- 整合所有系统状态
- 生成可视化报告
- 支持定时推送
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
MEMORY_DIR = WORKSPACE / "memory"
STATS_DIR = WORKSPACE / "stats"
HEALTH_DIR = WORKSPACE / "health-checks"

class SystemDashboard:
    """系统仪表盘"""
    
    def __init__(self):
        self.data = {}
    
    def collect_system_status(self):
        """收集系统状态"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "gateway": "unknown",
            "proxy": "unknown",
            "disk_usage": 0,
            "memory_usage": 0,
            "cpu_usage": 0
        }
        
        # Check Gateway
        try:
            result = subprocess.run(
                ["curl", "-sf", "--max-time", "2", "http://127.0.0.1:18789/health"],
                capture_output=True
            )
            status["gateway"] = "running" if result.returncode == 0 else "down"
        except:
            pass
        
        # Check Proxy
        try:
            result = subprocess.run(
                ["pgrep", "-f", "mihomo"],
                capture_output=True
            )
            status["proxy"] = "running" if result.returncode == 0 else "down"
        except:
            pass
        
        # Disk usage
        try:
            result = subprocess.run(
                ["df", "/"],
                capture_output=True,
                text=True
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 5:
                    status["disk_usage"] = int(parts[4].replace('%', ''))
        except:
            pass
        
        # Memory usage
        try:
            result = subprocess.run(
                ["free"],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if 'Mem:' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        total = int(parts[1])
                        used = int(parts[2])
                        status["memory_usage"] = int(used / total * 100)
                    break
        except:
            pass
        
        return status
    
    def collect_memory_stats(self):
        """收集记忆统计"""
        today = datetime.now().strftime('%Y-%m-%d')
        memory_file = MEMORY_DIR / f"{today}.md"
        
        stats = {
            "today_file_exists": memory_file.exists(),
            "today_file_size": 0,
            "today_conversations": 0
        }
        
        if memory_file.exists():
            stats["today_file_size"] = memory_file.stat().st_size
            
            # 简单统计对话数
            try:
                content = memory_file.read_text()
                stats["today_conversations"] = content.count("**一碗**:")
            except:
                pass
        
        # 统计历史文件
        stats["total_memory_files"] = len(list(MEMORY_DIR.glob("*.md")))
        
        return stats
    
    def collect_task_stats(self):
        """收集任务统计"""
        try:
            with open(MEMORY_DIR / "task-queue.json", 'r') as f:
                data = json.load(f)
            
            pending = len([t for t in data.get("tasks", []) if t.get("status") == "pending"])
            completed = len(data.get("completed", []))
            
            return {
                "pending": pending,
                "completed": completed,
                "total": pending + completed
            }
        except:
            return {"pending": 0, "completed": 0, "total": 0}
    
    def collect_cron_stats(self):
        """收集定时任务统计"""
        try:
            log_file = Path("/var/log/bowlwanpi-cron.log")
            if log_file.exists():
                # 统计今日执行的任务
                today = datetime.now().strftime('%Y-%m-%d')
                result = subprocess.run(
                    ["grep", today, str(log_file)],
                    capture_output=True,
                    text=True
                )
                lines = result.stdout.strip().split('\n')
                return {
                    "today_executions": len([l for l in lines if l.strip()]),
                    "log_size_kb": log_file.stat().st_size // 1024
                }
        except:
            pass
        
        return {"today_executions": 0, "log_size_kb": 0}
    
    def generate_dashboard(self) -> str:
        """生成仪表盘报告"""
        system = self.collect_system_status()
        memory = self.collect_memory_stats()
        tasks = self.collect_task_stats()
        cron = self.collect_cron_stats()
        
        # Status emojis
        gateway_emoji = "🟢" if system["gateway"] == "running" else "🔴"
        proxy_emoji = "🟢" if system["proxy"] == "running" else "🔴"
        disk_emoji = "🟢" if system["disk_usage"] < 80 else "🟡" if system["disk_usage"] < 90 else "🔴"
        
        dashboard = f"""# 🎮 碗皮系统仪表盘

*更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

---

## 📊 系统状态

| 组件 | 状态 | 详情 |
|------|------|------|
| {gateway_emoji} Gateway | {system['gateway']} | OpenClaw 网关 |
| {proxy_emoji} Proxy | {system['proxy']} | Mihomo 代理 |
| {disk_emoji} Disk | {system['disk_usage']}% | 磁盘使用 |
| 💾 Memory | {system['memory_usage']}% | 内存使用 |

---

## 🧠 记忆系统

- 📄 今日记忆: {'✅' if memory['today_file_exists'] else '❌'} ({memory['today_file_size']:,} bytes)
- 💬 今日对话: {memory['today_conversations']} 段
- 📁 历史文件: {memory['total_memory_files']} 个

---

## 📋 任务队列

- ⏳ 待处理: {tasks['pending']}
- ✅ 已完成: {tasks['completed']}
- 📊 总计: {tasks['total']}

---

## ⏰ 定时任务

- 🔄 今日执行: {cron['today_executions']} 次
- 📄 日志大小: {cron['log_size_kb']} KB

---

## 📈 快速链接

- [MEMORY.md](memory/MEMORY.md) - 长期记忆
- [NOW.md](memory/NOW.md) - 当前状态
- [stats/](stats/) - 性能统计

---

*碗皮实时状态 • 自动生成*
"""
        
        return dashboard
    
    def save_and_display(self):
        """保存并显示仪表盘"""
        dashboard = self.generate_dashboard()
        
        # 保存到文件
        dashboard_file = WORKSPACE / "DASHBOARD.md"
        with open(dashboard_file, 'w') as f:
            f.write(dashboard)
        
        print(dashboard)
        print(f"\n📄 仪表盘已保存: {dashboard_file}")

def main():
    dashboard = SystemDashboard()
    dashboard.save_and_display()

if __name__ == "__main__":
    main()
