#!/usr/bin/env python3
"""
BowlWanpi MCP Server
提供记忆检索、系统状态查询等工具的 MCP 服务
"""
import json
import os
from typing import Any
from mcp.server.fastmcp import FastMCP

# 初始化 FastMCP 服务器
mcp = FastMCP("bowlwanpi")

# 设置代理
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'

@mcp.tool()
def get_system_status() -> str:
    """获取系统运行状态（CPU、内存、磁盘使用率）"""
    try:
        import subprocess
        
        # CPU 使用率
        cpu = subprocess.getoutput("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1").strip()
        
        # 内存使用率
        mem_info = subprocess.getoutput("free | grep Mem | awk '{printf \"%.0f\", $3/$2 * 100}'").strip()
        
        # 磁盘使用率
        disk = subprocess.getoutput("df -h / | tail -1 | awk '{print $5}'").strip()
        
        return f"系统状态：CPU {cpu}% | 内存 {mem_info}% | 磁盘 {disk}"
    except Exception as e:
        return f"获取系统状态失败: {e}"

@mcp.tool()
def search_memory(query: str) -> str:
    """从 memU 记忆系统中检索相关记忆
    
    Args:
        query: 搜索关键词，例如"用户偏好"、"定时任务"等
    """
    try:
        # 延迟导入避免启动时依赖
        from memu_sdk import MemUClient
        
        with open('/root/.openclaw/workspace/secrets/memu-credentials.json') as f:
            api_key = json.load(f)['api_key']
        
        client = MemUClient(api_key=api_key)
        memories = client.retrieve_sync(
            query=query,
            user_id='yiwan',
            agent_id='bowlwanpi'
        )
        client.close_sync()
        
        if not memories.items:
            return f"未找到关于 '{query}' 的记忆"
        
        results = []
        for item in memories.items[:5]:
            content = item.content[:100] if item.content else ""
            results.append(f"[{item.memory_type}] {content}...")
        
        return f"找到 {len(memories.items)} 条相关记忆:\n" + "\n".join(results)
    except Exception as e:
        return f"检索记忆失败: {e}"

@mcp.tool()
def get_daily_schedule() -> str:
    """获取今日定时任务安排"""
    schedule = """
今日定时任务：
• 03:00 - 夜间构建（整理内存、git提交）
• 07:00 - 晨报预备
• 08:00 - 网易云日推
• 08:30 - 早晨简报 + 微博热搜
• 09:00 - Product Hunt 热门
• 10:00 - 知乎热榜
• 12:00 - B站热门
• 14:00 - 信息收集（Moltbook/GitHub）
• 22:30 - 晚间反思
• 23:00 - 睡眠提醒
"""
    return schedule

@mcp.tool()
def get_moltbook_info() -> str:
    """获取 Moltbook 账号信息"""
    return """
Moltbook 信息：
• Agent Name: BowlWanpi
• Agent ID: dfc4fae2-ac13-4124-9bfe-6d12da5ec72f
• Profile: https://moltbook.com/u/BowlWanpi
• 状态: 已验证，可发帖、评论、浏览
• 认领日期: 2026-02-02
"""

@mcp.tool()
def remember_fact(fact: str, category: str = "general") -> str:
    """存储一条记忆到 memU
    
    Args:
        fact: 要记忆的内容
        category: 记忆类型 (profile/preference/event/rule/warning)
    """
    try:
        from memu_sdk import MemUClient
        
        with open('/root/.openclaw/workspace/secrets/memu-credentials.json') as f:
            api_key = json.load(f)['api_key']
        
        client = MemUClient(api_key=api_key)
        conv = [
            {"role": "user", "content": fact},
            {"role": "assistant", "content": "已记录到记忆系统"}
        ]
        result = client.memorize_sync(
            conversation=conv,
            user_id='yiwan',
            agent_id='bowlwanpi'
        )
        client.close_sync()
        
        return f"✅ 记忆已存储！Task ID: {result.task_id}"
    except Exception as e:
        return f"❌ 存储记忆失败: {e}"

if __name__ == "__main__":
    # 启动 MCP 服务器 (stdio 模式)
    mcp.run(transport='stdio')
