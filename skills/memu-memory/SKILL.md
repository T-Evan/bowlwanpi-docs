---
name: memu-memory
description: 连接 memU 记忆系统，为 BowlWanpi 提供持久记忆能力。自动存储重要对话，检索相关历史，让碗皮更懂一碗。
---

# 🧠 memU 记忆系统

## 功能概述

这个 skill 让 BowlWanpi 拥有了**持久记忆能力**：

- 💾 **自动存储**：重要对话自动保存到 memU
- 🔍 **智能检索**：回答前检索相关历史记忆
- 📊 **用户画像**：维护一碗的偏好和习惯
- 🎯 **意图预测**：基于记忆预测下一步需求

## 实现文件

```
memu-memory/
├── SKILL.md                 # 本文档
├── config.json              # 配置文件
├── memory_manager.py        # 核心管理类
└── hooks/
    ├── before_response.py   # 回复前检索记忆
    └── after_response.py    # 回复后存储记忆
```

## 工作原理

### 1. 记忆存储 (after_response.py)

每次对话后，系统自动判断：
- 是否包含重要信息？
- 是否是用户的偏好/习惯？
- 是否需要长期记住？

**重要标准**（config.json 中配置）：
- 用户明确说"记住"、"提醒"、"约定"
- 包含个人偏好（"我喜欢"、"我习惯"）
- 包含重要决策或信息
- 技术选型、工具配置
- 长对话（>500字）且包含技术内容

如果是，自动存储到 memU 云端记忆库。

### 2. 记忆检索 (before_response.py)

每次收到消息时，系统会：
- 检索与当前话题相关的历史记忆
- 将相关记忆注入系统提示
- 让回复更有上下文感

### 3. 记忆增强回复

示例：
```
一碗：我想喝茶

[系统检索到记忆]
💭 相关记忆：
1. 一碗喜欢喝绿茶（2026-02-07）

[碗皮回复]
🥣 好呀～我记得你喜欢绿茶，要我帮你查查现在的茶叶推荐吗？
```

## 使用方法

### 自动模式（默认）
无需手动操作，系统全自动运行：
1. 收到消息 → 自动检索相关记忆
2. 生成回复 → 自动判断并存储重要对话

### 手动模式

```python
from skills.memu-memory.memory_manager import MemoryManager
import asyncio

async def example():
    async with MemoryManager() as mm:
        # 存储对话
        await mm.store_conversation(
            user_message="我喜欢用 VS Code",
            assistant_message="好的，记住了！"
        )
        
        # 检索记忆
        memories = await mm.retrieve_relevant_memories("编辑器")
```

### 命令行工具

```bash
# 存储记忆
python skills/memu-memory/hooks/after_response.py "用户消息" "助手回复"

# 检索记忆
python skills/memu-memory/hooks/before_response.py "查询内容"
```

## 配置

编辑 `config.json`：

```json
{
  "auto_store": true,           // 是否自动存储
  "store_threshold": {
    "min_length": 10,           // 最小长度
    "important_keywords": [     // 重要关键词
      "记住", "提醒", "约定",
      "我喜欢", "配置", "方案"
    ]
  },
  "retrieve": {
    "enabled": true,            // 是否启用检索
    "before_response": true,    // 回复前检索
    "max_memories": 5          // 最大检索条数
  }
}
```

## 技术细节

**后端服务**：memU (https://memu.pro/)
**存储方式**：云端加密存储
**检索算法**：语义相似度匹配
**隐私保护**：敏感信息自动过滤

## 状态

- ✅ 基础存储/检索 - 已完成
- ✅ 智能判断 - 已完成（基于关键词和规则）
- ✅ 自动 hooks - 已完成
- 🔄 意图预测 - 开发中
- ⏳ 记忆可视化 - 待开发

---

*集成时间: 2026-02-07*
*版本: 0.2.0*
*更新: 2026-02-08 - 实现完整自动存储/检索功能*
