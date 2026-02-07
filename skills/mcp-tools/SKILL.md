# MCP Tools Skill for BowlWanpi

让 BowlWanpi 能够调用 MCP 服务。

## ✅ 已完成配置

### memos-api-mcp 服务
**路径**: `/root/.nvm/versions/node/v22.22.0/bin/memos-api-mcp`

**状态**: ✅ 已连接，4 个工具可用

**可用工具**:
1. **add_message** - 添加对话历史/新记忆
2. **search_memory** - 搜索记忆
3. **delete_memory** - 删除记忆
4. **add_feedback** - 添加反馈/修改记忆

---

## 🚀 使用方法

### 方法 1: 直接导入调用

```python
from modules.mcp_client import call_mcp_tool_sync

# 搜索记忆
result = call_mcp_tool_sync(
    "memos-api-mcp",
    "search_memory",
    query="用户偏好",
    conversation_first_message="首次对话",
    memory_limit_number=5
)

# 添加记忆
result = call_mcp_tool_sync(
    "memos-api-mcp",
    "add_message",
    conversation_first_message="首次对话",
    messages=[
        {"role": "user", "content": "用户说的话"},
        {"role": "assistant", "content": "AI的回复"}
    ]
)
```

### 方法 2: 在技能中使用

创建技能脚本，导入 mcp_client 模块调用工具。

### 方法 3: 测试示例

```bash
cd /root/.openclaw/workspace
python3 examples/mcp_usage_example.py
```

---

## 📁 相关文件

- `modules/mcp_client.py` - MCP 客户端实现
- `examples/mcp_usage_example.py` - 使用示例
- `mcp_config.json` - MCP 服务配置（用于其他客户端）

---

## ➕ 添加新的 MCP 服务

编辑 `modules/mcp_client.py` 中的 `MCP_SERVERS`:

```python
MCP_SERVERS = {
    "your-server": {
        "command": "/path/to/server",
        "args": ["--option"],
        "env": {"KEY": "value"}
    }
}
```

---

## ⚠️ 限制说明

1. OpenClaw 原生不支持 MCP，需要通过 Python 脚本调用
2. 每次调用需要建立新连接（有一定开销）
3. 异步 API 需要使用 asyncio

---

## 🔧 技术细节

- **传输方式**: stdio
- **SDK**: mcp (Model Context Protocol Python SDK)
- **连接管理**: 每次调用独立连接
