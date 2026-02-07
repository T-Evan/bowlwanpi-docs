#!/usr/bin/env python3
"""
MCP 客户端封装
让 BowlWanpi 能够调用其他 MCP 服务
"""
import json
import os
import asyncio
from typing import Any
from contextlib import AsyncExitStack

# MCP 服务配置
MCP_SERVERS = {
    "memos-api-mcp": {
        "command": "/root/.nvm/versions/node/v22.22.0/bin/memos-api-mcp",
        "env": {
            "MEMOS_API_KEY": "mpg-vCI2aAscjA0ckABPMVa6BhQARfckS+bm9YINlcnG",
            "MEMOS_USER_ID": "yiwanbot",
            "MEMOS_CHANNEL": "MODELSCOPE"
        }
    }
}


async def list_mcp_tools(server_name: str = "memos-api-mcp"):
    """列出 MCP 服务器的可用工具"""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    
    config = MCP_SERVERS.get(server_name)
    if not config:
        raise ValueError(f"未知 MCP 服务器: {server_name}")
    
    # 设置环境变量
    env = os.environ.copy()
    env.update(config.get("env", {}))
    
    # 创建服务器参数
    server_params = StdioServerParameters(
        command=config["command"],
        args=config.get("args", []),
        env=env
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            return tools_result.tools


async def call_mcp_tool(server_name: str, tool_name: str, **kwargs) -> Any:
    """
    调用 MCP 工具
    
    示例:
        result = await call_mcp_tool("memos-api-mcp", "create_memo", content="今天天气不错")
    """
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    
    config = MCP_SERVERS.get(server_name)
    if not config:
        raise ValueError(f"未知 MCP 服务器: {server_name}")
    
    # 设置环境变量
    env = os.environ.copy()
    env.update(config.get("env", {}))
    
    # 创建服务器参数
    server_params = StdioServerParameters(
        command=config["command"],
        args=config.get("args", []),
        env=env
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, kwargs)
            return result


def call_mcp_tool_sync(server_name: str, tool_name: str, **kwargs) -> Any:
    """同步调用 MCP 工具"""
    return asyncio.run(call_mcp_tool(server_name, tool_name, **kwargs))


def list_mcp_tools_sync(server_name: str = "memos-api-mcp"):
    """同步列出 MCP 工具"""
    return asyncio.run(list_mcp_tools(server_name))


if __name__ == "__main__":
    # 测试连接
    async def test():
        print("🔌 连接到 memos-api-mcp...")
        tools = await list_mcp_tools("memos-api-mcp")
        
        print(f"✅ 已连接！发现 {len(tools)} 个工具:\n")
        for tool in tools:
            print(f"📌 {tool.name}")
            print(f"   描述: {tool.description}")
            if tool.inputSchema:
                print(f"   参数: {json.dumps(tool.inputSchema, indent=2, ensure_ascii=False)}")
            print()
    
    asyncio.run(test())
