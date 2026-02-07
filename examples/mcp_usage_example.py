#!/usr/bin/env python3
"""
MCP 工具使用示例
展示如何在 BowlWanpi 中调用 MCP 工具
"""
import sys
sys.path.insert(0, '/root/.openclaw/workspace')

from modules.mcp_client import call_mcp_tool_sync, list_mcp_tools_sync

def main():
    print("🧠 MCP 工具使用示例\n")
    
    # 示例 1: 列出可用工具
    print("1️⃣ 列出可用工具:")
    tools = list_mcp_tools_sync("memos-api-mcp")
    for tool in tools:
        print(f"   - {tool.name}")
    print()
    
    # 示例 2: 搜索记忆
    print("2️⃣ 搜索记忆:")
    try:
        result = call_mcp_tool_sync(
            "memos-api-mcp",
            "search_memory",
            query="用户偏好",
            conversation_first_message="测试查询",
            memory_limit_number=5
        )
        print(f"   结果: {result}")
    except Exception as e:
        print(f"   错误: {e}")
    print()
    
    # 示例 3: 添加消息
    print("3️⃣ 添加消息到记忆:")
    try:
        result = call_mcp_tool_sync(
            "memos-api-mcp",
            "add_message",
            conversation_first_message="首次对话",
            messages=[
                {"role": "user", "content": "你好，我是测试用户"},
                {"role": "assistant", "content": "你好！很高兴认识你～"}
            ]
        )
        print(f"   结果: {result}")
    except Exception as e:
        print(f"   错误: {e}")
    
    print("\n✅ 示例完成！")

if __name__ == "__main__":
    main()
