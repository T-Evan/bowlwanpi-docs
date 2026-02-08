---
name: unified-memory
description: 三记忆系统整合 - 同时使用 memU (云端)、Hippocampus (本地)、MemOS (MCP)，实现记忆的云端+本地+MCP三重备份和互补优势。
---

# 🧠 统一记忆系统 (Unified Memory)

## 概述

同时使用三套记忆系统：

- ✅ **memU** - 云端 AI 记忆（语义理解）
- ✅ **Hippocampus** - 本地文件记忆（重要度评分/衰减）
- ✅ **MemOS** - MCP 服务记忆（快速访问）

实现 **三重备份 + 互补优势**！

## 三套系统的分工

| 特性 | **memU** | **Hippocampus** | **MemOS** |
|------|----------|-----------------|-----------|
| **存储位置** | 云端 API | 本地 JSON | MCP 服务 |
| **优势** | 语义检索、跨设备 | 重要度评分、记忆衰减 | 快速访问、简单接口 |
| **检索方式** | AI 语义匹配 | 重要度加权 + 关键词 | 关键词搜索 |
| **数据安全** | 加密云端存储 | 完全本地可控 | MCP 服务管理 |
| **适用场景** | 跨会话记忆、复杂查询 | 本地优先、隐私敏感 | 快速存取、简单需求 |

## 文件结构

```
skills/unified-memory/
├── SKILL.md                      # 本文档
├── unified_memory_manager.py     # 核心管理类
│   ├── MemOSClient              # MemOS MCP 客户端
│   ├── UnifiedMemoryManager     # 三系统管理器
│   └── 便捷函数 (store_to_all_systems, retrieve_merged 等)
└── hooks/
    ├── after_response.py         # 回复后存储三系统
    └── before_response.py        # 回复前检索三系统
```

## 使用方法

### 自动模式（推荐）

系统自动将重要对话同时存储到三个系统：
1. 收到消息 → 从三系统检索相关记忆
2. 生成回复 → 存储到 memU + Hippocampus + MemOS

### 手动使用

```python
from skills.unified-memory.unified_memory_manager import (
    store_to_all_systems,
    retrieve_from_all_systems,
    retrieve_merged
)
import asyncio

# 存储到三系统
result = asyncio.run(store_to_all_systems(
    user_msg="我喜欢喝绿茶",
    assistant_msg="记住了！",
    importance=0.8,
    enable_memu=True,      # 启用 memU
    enable_hippo=True,     # 启用 Hippocampus
    enable_memos=True      # 启用 MemOS
))
# 返回: {'memu': True, 'hippocampus': True, 'memos': True}

# 从三系统检索
memories = asyncio.run(retrieve_from_all_systems("茶"))
# 返回: {'memu': [...], 'hippocampus': [...], 'memos': [...]}

# 合并检索（去重后）
merged = asyncio.run(retrieve_merged("茶", limit=10))
# 返回: [{'content': '...', 'source': 'memu', 'type': '...'}, ...]
```

### 高级用法

```python
from skills.unified-memory.unified_memory_manager import UnifiedMemoryManager
import asyncio

async def advanced():
    # 自定义启用哪些系统
    async with UnifiedMemoryManager(
        enable_memu=True,
        enable_hippo=True,
        enable_memos=False  # 禁用 MemOS
    ) as mm:
        # 存储
        result = await mm.store_memory("用户消息", "助手回复")
        
        # 检索
        memories = await mm.retrieve_memories("查询")
        
        # 合并检索（自动去重）
        all_memories = await mm.retrieve_all("查询", limit=10)
        
        # 查看统计
        stats = mm.get_memory_stats()
        print(stats)

asyncio.run(advanced())
```

## 配置

### memU 配置
文件：`/root/.openclaw/workspace/secrets/memu-credentials.json`
```json
{
  "api_key": "your-memu-api-key"
}
```

### Hippocampus 配置
已在 `skills/hippocampus-memory/` 中配置完成，自动运行编码流水线。

### MemOS 配置
已在 `mcp_config.json` 中配置：
```json
{
  "memos-api-mcp": {
    "type": "stdio",
    "command": "/root/.nvm/versions/node/v22.22.0/bin/memos-api-mcp",
    "env": {
      "MEMOS_API_KEY": "...",
      "MEMOS_USER_ID": "yiwanbot",
      "MEMOS_CHANNEL": "MODELSCOPE"
    }
  }
}
```

## 定期维护

### Hippocampus 编码流水线（自动）
通过 cron 每天自动运行：
```bash
# 编码新信号
./skills/hippocampus-memory/scripts/encode-pipeline.sh

# 应用记忆衰减
./skills/hippocampus-memory/scripts/decay.sh
```

### 手动触发
```bash
# 立即编码
./skills/hippocampus-memory/scripts/encode-pipeline.sh

# 生成脑图仪表盘
./skills/hippocampus-memory/scripts/generate-dashboard.sh
open ~/.openclaw/workspace/brain-dashboard.html
```

## 状态

| 系统 | 状态 |
|------|------|
| memU 集成 | ✅ 已完成 |
| Hippocampus 集成 | ✅ 已完成 |
| MemOS 集成 | ✅ 已完成 |
| 三系统存储 | ✅ 已完成 |
| 三系统检索 | ✅ 已完成 |
| 合并检索 | ✅ 已完成 |
| 自动 hooks | ✅ 已完成 |

---

*集成时间: 2026-02-08*
*版本: 2.0.0 (三系统整合)*
