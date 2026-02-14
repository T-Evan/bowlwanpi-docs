---
name: unified-memory
description: 三记忆系统整合 - 同时使用 memU (云端)、Hippocampus (本地)、MemOS (MCP)，实现记忆的云端+本地+MCP三重备份和互补优势。
---

# 🧠 统一记忆系统 (Unified Memory) v3.0

## 概述

同时使用**四套**记忆系统：

- ✅ **memU** - 云端 AI 记忆（语义理解）
- ✅ **Hippocampus** - 本地文件记忆（重要度评分/衰减）
- ✅ **MemOS** - MCP 服务记忆（快速访问）
- ✅ **QMDR** - 本地向量搜索（快速语义检索）

实现 **四重备份 + 互补优势**！

## 四套系统的分工

| 特性 | **memU** | **Hippocampus** | **MemOS** | **QMDR** |
|------|----------|-----------------|-----------|----------|
| **存储位置** | 云端 API | 本地 JSON | MCP 服务 | 本地向量索引 |
| **优势** | 语义检索、跨设备 | 重要度评分、记忆衰减 | 快速访问、简单接口 | 本地快速搜索、隐私保护 |
| **检索方式** | AI 语义匹配 | 重要度加权 + 关键词 | 关键词搜索 | 向量语义搜索 |
| **数据安全** | 加密云端存储 | 完全本地可控 | MCP 服务管理 | 完全本地、不上云 |
| **适用场景** | 跨会话记忆、复杂查询 | 本地优先、隐私敏感 | 快速存取、简单需求 | 本地快速语义搜索 |

## 文件结构

```
skills/unified-memory/
├── SKILL.md                      # 本文档
├── unified_memory_manager.py     # v2.0 核心管理类（三系统）
├── unified_memory_manager_v3.py  # v3.0 核心管理类（四系统，含 QMDR）
│   ├── QMDRClient               # QMDR 本地向量搜索客户端
│   ├── MemOSClient              # MemOS MCP 客户端
│   ├── UnifiedMemoryManagerV3   # 四系统管理器
│   └── 便捷函数 (store_to_all_systems, retrieve_merged 等)
└── hooks/
    ├── after_response.py         # 回复后存储四系统
    └── before_response.py        # 回复前检索四系统
```

## 使用方法

### V3.0 推荐用法（四系统）

```python
from skills.unified-memory.unified_memory_manager_v3 import (
    store_to_all_systems,
    retrieve_from_all_systems,
    retrieve_merged,
    UnifiedMemoryManagerV3
)
import asyncio

# 存储到四系统
result = asyncio.run(store_to_all_systems(
    user_msg="我喜欢喝绿茶",
    assistant_msg="记住了！",
    importance=0.8,
    enable_memu=True,      # 启用 memU
    enable_hippo=True,     # 启用 Hippocampus
    enable_memos=True,     # 启用 MemOS
    enable_qmdr=True       # 启用 QMDR (新增)
))
# 返回: {'memu': True, 'hippocampus': True, 'memos': True, 'qmdr': True}

# 从四系统检索
memories = asyncio.run(retrieve_from_all_systems("茶"))
# 返回: {'memu': [...], 'hippocampus': [...], 'memos': [...], 'qmdr': [...]}

# 合并检索（去重后）- 优先使用 QMDR 本地搜索
merged = asyncio.run(retrieve_merged("茶", limit=10))
# 返回: [{'content': '...', 'source': 'qmdr/memU/hippo/memos', 'type': '...'}, ...]
```

### 高级用法

```python
from skills.unified-memory.unified_memory_manager_v3 import UnifiedMemoryManagerV3
import asyncio

async def advanced():
    # 自定义启用哪些系统
    async with UnifiedMemoryManagerV3(
        enable_memu=True,
        enable_hippo=True,
        enable_memos=True,
        enable_qmdr=True    # 启用 QMDR 本地向量搜索
    ) as mm:
        # 存储
        result = await mm.store_memory("用户消息", "助手回复")
        
        # 检索
        memories = await mm.retrieve_memories("查询")
        
        # 合并检索（自动去重，优先 QMDR）
        all_memories = await mm.retrieve_merged("查询", limit=10)
        
        # QMDR 特有的：重新索引所有文档
        reindex_result = await mm.reindex_qmdr()
        print(f"索引了 {reindex_result.get('indexed', 0)} 个文档")
        
        # 查看统计
        stats = mm.get_memory_stats()
        print(stats)

asyncio.run(advanced())
```

### QMDR 特有功能

```python
from skills.unified-memory.unified_memory_manager_v3 import QMDRClient

# 直接使用 QMDR 客户端
qmdr = QMDRClient(collection='memory')

# 搜索本地记忆
results = qmdr.search("定时任务", limit=5)
for r in results:
    print(f"{r['file']}: 相关度 {r['score']}%")

# 重新索引所有文档
result = qmdr.reindex_all()
print(f"索引完成: {result['indexed']} 成功, {result['failed']} 失败")
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
| **QMDR 集成 (v3.0 新增)** | ✅ **已完成** |
| 四系统存储 | ✅ 已完成 |
| 四系统检索 | ✅ 已完成 |
| 合并检索 | ✅ 已完成 (优先 QMDR) |
| 自动 hooks | ✅ 已完成 |

---

*集成时间: 2026-02-08*  
*QMDR 集成: 2026-02-14*  
*版本: 3.0.0 (四系统整合)*
