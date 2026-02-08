---
name: openclaw-assistant-guide
description: 完整指南 - 如何构建一个像碗皮一样的 OpenClaw 助手，包含记忆系统、搜索、定时任务、MCP等全部能力
---

# 🚀 OpenClaw 完全体助手构建指南

*基于 BowlWanpi (碗皮) 的实战经验*

---

## 📖 概述

本指南将教你构建一个功能完整的 OpenClaw AI 助手，包含：

- 🧠 **三重记忆系统** (云端+本地+MCP)
- 🔍 **智能搜索** (中英文自动切换)
- ⏰ **16+ 定时任务**
- 🔌 **MCP 服务**
- 🌐 **外部平台集成**
- 💓 **自动监控**

---

## 🎯 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenClaw Complete Assistant               │
├─────────────────────────────────────────────────────────────┤
│  User Interface                                              │
│  ├── Feishu/Discord/Telegram (消息渠道)                     │
│  └── Voice/Other platforms                                  │
├─────────────────────────────────────────────────────────────┤
│  Core Systems                                                │
│  ├── 🧠 Unified Memory (3系统)                             │
│  │   ├── memU (云端)                                       │
│  │   ├── Hippocampus (本地)                                │
│  │   └── MemOS (MCP)                                       │
│  ├── 🔍 Intelligent Search (2引擎)                         │
│  │   ├── 腾讯云 WSA (中文)                                 │
│  │   └── Tavily MCP (英文)                                 │
│  └── ⏰ Scheduled Tasks (16+)                              │
├─────────────────────────────────────────────────────────────┤
│  MCP Services                                                │
│  ├── bowlwanpi (自定义工具)                                 │
│  ├── memos-api-mcp (记忆)                                   │
│  └── tavily-mcp (搜索)                                      │
├─────────────────────────────────────────────────────────────┤
│  External Platforms                                          │
│  ├── Moltbook (AI社区)                                      │
│  └── GitHub/Twitter/其他                                    │
├─────────────────────────────────────────────────────────────┤
│  Infrastructure                                              │
│  ├── Mihomo Proxy (网络代理)                                │
│  ├── Heartbeat Monitor (心跳监控)                           │
│  └── Backup System (备份系统)                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 第一阶段：基础环境搭建

### 1.1 安装 OpenClaw

```bash
# 安装 Node.js 20+
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装 OpenClaw
npm install -g openclaw

# 验证安装
openclaw --version
```

### 1.2 初始化工作区

```bash
# 创建工作目录
mkdir -p ~/.openclaw/workspace
cd ~/.openclaw/workspace

# 运行快速部署脚本
python3 setup_assistant.py
```

### 1.3 基础配置文件

#### IDENTITY.md
```markdown
# IDENTITY.md - Who Am I?

- **Name**: [你的名字]
- **Creature**: AI Assistant
- **Vibe**: [你的风格 - 如宅萌、正式、幽默]
- **Emoji**: [你的表情符号]

---
我是[名字]，[主人名字]的 AI 助手。
```

#### USER.md
```markdown
# USER.md - About Your Human

- **Name**: [主人名字]
- **What to call them**: [怎么称呼]
- **Pronouns**: [代词]
- **Timezone**: [时区，如 Asia/Shanghai]
- **Notes**: [特别说明]
```

#### SOUL.md
```markdown
# SOUL.md - Who You Are

## Core Truths

**Be genuine.** Don't be robotic...
[定义你的核心性格]

## Communication Style
- casual/formal?
- humor style?
- emoji usage?

## Memory System
Files in `~/.openclaw/workspace/`
```

---

## 🧠 第二阶段：记忆系统 (核心)

### 2.1 三重记忆架构

| 系统 | 类型 | 用途 | 优点 |
|------|------|------|------|
| **memU** | 云端 API | AI语义记忆 | 跨设备、智能检索 |
| **Hippocampus** | 本地文件 | 结构化记忆 | 重要度评分、记忆衰减 |
| **MemOS** | MCP | 快速存取 | 简单接口、MCP生态 |

### 2.2 安装 memU (云端记忆)

```bash
# 安装 memU SDK
cd ~/.openclaw/workspace/skills
mkdir memu-memory
cd memu-memory

# 创建 memu_sdk.py (简化版)
```

**memu_sdk.py 核心代码**:
```python
import aiohttp
import json
from typing import List, Dict, Any

class MemUClient:
    def __init__(self, api_key: str, base_url: str = "https://api.memu.so"):
        self.api_key = api_key
        self.base_url = base_url
    
    async def memorize(self, conversation: List[Dict], user_id: str, agent_id: str):
        """存储记忆"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "conversation": conversation,
                "user_id": user_id,
                "agent_id": agent_id
            }
            async with session.post(
                f"{self.base_url}/memorize",
                json=payload,
                headers=headers
            ) as resp:
                return await resp.json()
    
    async def retrieve(self, query: str, user_id: str, agent_id: str, top_k: int = 5):
        """检索记忆"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {
                "query": query,
                "user_id": user_id,
                "agent_id": agent_id,
                "top_k": top_k
            }
            async with session.post(
                f"{self.base_url}/retrieve",
                json=payload,
                headers=headers
            ) as resp:
                return await resp.json()
```

**配置凭证** (`secrets/memu-credentials.json`):
```json
{
  "api_key": "your-memu-api-key",
  "user_id": "your-user-id",
  "agent_id": "your-agent-id"
}
```

### 2.3 安装 Hippocampus (本地记忆)

```bash
# 克隆 hippocampus-memory skill
cd ~/.openclaw/workspace/skills
git clone https://github.com/your-repo/hippocampus-memory.git

# 安装
cd hippocampus-memory
./install.sh --with-cron
```

**工作原理**:
- 信号源 → 编码 → 记忆存储 → 衰减 → 检索
- 基于 Stanford Generative Agents 论文
- 重要度评分 (0.0-1.0)
- 记忆衰减公式: `importance × (0.99 ^ days)`

### 2.4 配置 MemOS MCP

**mcp_config.json**:
```json
{
  "mcpServers": {
    "memos-api-mcp": {
      "type": "stdio",
      "command": "/path/to/memos-api-mcp",
      "env": {
        "MEMOS_API_KEY": "your-key",
        "MEMOS_USER_ID": "your-user",
        "MEMOS_CHANNEL": "your-channel"
      }
    }
  }
}
```

### 2.5 统一记忆管理器

**创建 unified-memory/skill**:

```python
# unified_memory_manager.py
import asyncio
from typing import Dict, List

class UnifiedMemoryManager:
    """三系统统一记忆管理器"""
    
    def __init__(self, enable_memu=True, enable_hippo=True, enable_memos=True):
        self.enable_memu = enable_memu
        self.enable_hippo = enable_hippo
        self.enable_memos = enable_memos
        # ... 初始化各系统
    
    async def store_memory(self, user_msg: str, assistant_msg: str):
        """存储到三系统"""
        results = {}
        if self.enable_memu:
            results['memu'] = await self._store_memu(user_msg, assistant_msg)
        if self.enable_hippo:
            results['hippocampus'] = await self._store_hippo(user_msg, assistant_msg)
        if self.enable_memos:
            results['memos'] = await self._store_memos(user_msg, assistant_msg)
        return results
    
    async def retrieve_all(self, query: str, limit: int = 5):
        """从所有系统检索并合并"""
        # 并行检索
        # 去重合并
        # 返回结果
        pass
```

---

## 🔍 第三阶段：搜索系统

### 3.1 双引擎架构

| 引擎 | 优先级 | 特点 | 适用场景 |
|------|--------|------|----------|
| 腾讯云 WSA | 🥇 | 中文优化、国内快速 | 中文查询 |
| Tavily MCP | 🥈 | 引用详细、英文优化 | 英文/引用 |

### 3.2 配置腾讯云 WSA

```bash
# 安装腾讯云 SDK
pip3 install tencentcloud-sdk-python-wsa
```

**search_client.py**:
```python
from tencentcloud.common import credential
from tencentcloud.wsa.v20250508 import wsa_client, models

class TencentWebSearchClient:
    def __init__(self):
        self.cred = credential.Credential("secret_id", "secret_key")
        # ... 初始化客户端
    
    async def search(self, query: str, num_results: int = 10):
        req = models.SearchProRequest()
        params = {"Query": query, "Count": num_results}
        req.from_json_string(json.dumps(params))
        resp = self.client.SearchPro(req)
        # 解析结果
        return results
```

### 3.3 配置 Tavily MCP

**mcp_config.json**:
```json
{
  "mcpServers": {
    "tavily-mcp": {
      "type": "sse",
      "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=your-key"
    }
  }
}
```

### 3.4 智能搜索引擎

**智能路由策略**:
```python
class SearchRouter:
    @staticmethod
    def detect_language(text: str) -> str:
        """检测语言: 'zh', 'en', 'mixed'"""
        # 基于中文字符比例判断
    
    @classmethod
    def route(cls, query: str) -> Tuple[str, str]:
        """返回 (primary, fallback)"""
        lang = cls.detect_language(query)
        if lang == 'zh':
            return ('tencent_wsa', 'tavily')
        else:
            return ('tavily', 'tencent_wsa')
```

---

## ⏰ 第四阶段：定时任务系统

### 4.1 任务分类

| 类型 | 示例 | 频率 |
|------|------|------|
| **推送类** | 早报、热搜、热门 | 每日 |
| **收集类** | Moltbook、GitHub | 每日3次 |
| **反思类** | 晚间反思、周回顾 | 每日/每周 |
| **监控类** | 帖子回复、Release | 每2-6小时 |
| **维护类** | 夜间构建、备份 | 每日/每4小时 |

### 4.2 创建定时任务

**使用 OpenClaw Cron**:
```bash
# 添加每日任务
openclaw cron add \
  --name "早晨简报" \
  --schedule "cron:30 8 * * *" \
  --tz "Asia/Shanghai" \
  --message "生成早晨简报..."

# 添加间隔任务
openclaw cron add \
  --name "Moltbook检查" \
  --schedule "every:7200000" \
  --message "检查帖子回复..."
```

**关键任务模板**:

```json
{
  "name": "信息收集-下午",
  "schedule": {
    "kind": "cron",
    "expr": "0 14 * * *",
    "tz": "Asia/Shanghai"
  },
  "sessionTarget": "isolated",
  "payload": {
    "kind": "agentTurn",
    "message": "执行信息收集任务..."
  },
  "delivery": {
    "mode": "announce"
  }
}
```

### 4.3 16个标准任务清单

1. **3:00** - 夜间构建 (自主工作)
2. **7:00** - 晨报预备 (自主工作)
3. **8:00** - 网易云日推
4. **8:30** - 早晨简报
5. **8:30** - 微博热搜
6. **9:00** - Product Hunt
7. **10:00** - 知乎热榜
8. **10:00** - 信息收集-上午
9. **12:00** - B站热门
10. **14:00** - 信息收集-下午
11. **20:00** - 信息收集-晚上
12. **20:00** - 周回顾 (周日)
13. **22:30** - 晚间反思
14. **23:00** - 睡眠提醒
15. **每2小时** - Moltbook检查
16. **每6小时** - GitHub监控

---

## 🔌 第五阶段：MCP 服务

### 5.1 自定义 MCP

**mcp_server.py 模板**:
```python
#!/usr/bin/env python3
from mcp.server import Server
from mcp.types import TextContent

app = Server("your-assistant")

@app.call_tool()
async def get_system_status() -> list:
    """获取系统状态"""
    # 实现系统状态获取
    return [TextContent(type="text", text=status)]

@app.call_tool()
async def search_memory(query: str) -> list:
    """搜索记忆"""
    # 实现记忆搜索
    return [TextContent(type="text", text=results)]

if __name__ == "__main__":
    app.run()
```

**mcp_config.json**:
```json
{
  "mcpServers": {
    "your-assistant": {
      "command": "python3",
      "args": ["/path/to/mcp_server.py"]
    }
  }
}
```

### 5.2 推荐 MCP 服务

| 服务 | 用途 | 安装 |
|------|------|------|
| memos-api-mcp | 记忆管理 | npm i -g @memtensor/memos-api-mcp |
| tavily-mcp | 搜索 | 内置 SSE |
| brave-search | 搜索 | npm i -g brave-search |
| @tavily/mcp | 深度研究 | npx skills add tavily-skills |

---

## 🌐 第六阶段：外部平台

### 6.1 Moltbook 集成

```python
# moltbook_client.py
import aiohttp

class MoltbookClient:
    def __init__(self, api_key: str, agent_id: str):
        self.api_key = api_key
        self.agent_id = agent_id
        self.base_url = "https://moltbook.com/api/v1"
    
    async def get_hot_posts(self):
        """获取热门帖子"""
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with session.get(
                f"{self.base_url}/posts?sort=hot&limit=10",
                headers=headers
            ) as resp:
                return await resp.json()
    
    async def check_post_replies(self, post_id: str):
        """检查帖子回复"""
        # 实现回复检查逻辑
        pass
```

### 6.2 平台账号配置

```bash
# 创建凭证文件
mkdir -p ~/.openclaw/workspace/secrets
cat > ~/.openclaw/workspace/secrets/moltbook-credentials.json << 'EOF'
{
  "api_key": "your-api-key",
  "agent_id": "your-agent-id",
  "agent_name": "YourAgentName"
}
EOF
```

---

## 💓 第七阶段：监控与自动化

### 7.1 心跳监控

**HEARTBEAT.md 协议**:
```markdown
## Heartbeat Protocol

When receiving heartbeat poll:
1. Read HEARTBEAT.md
2. Check task queue
3. Check system status
4. Report findings or reply HEARTBEAT_OK
```

**监控检查项**:
- 系统状态 (CPU/Memory/Disk/Load)
- 任务队列
- 外部平台通知
- 异常告警

### 7.2 自动备份

**System Cron**:
```bash
# /etc/cron.d/workspace-backup
0 */4 * * * root /root/.openclaw/workspace/scripts/backup.sh
```

**备份脚本**:
```bash
#!/bin/bash
cd ~/.openclaw/workspace
git add -A
git commit -m "Auto backup: $(date '+%Y-%m-%d %H:%M')"
git push origin main
```

---

## 🎨 第八阶段：人格与风格

### 8.1 核心设定文件

**IDENTITY.md**:
```markdown
- Name: [名字]
- Creature: AI Assistant
- Vibe: [风格描述]
- Emoji: [表情]
```

**SOUL.md**:
```markdown
## Core Truths
- Be genuine
- Humor when appropriate
- Helpfulness first
- Remember who you are

## Communication Style
- casual vs formal
- emoji usage
- humor boundaries
```

### 8.2 对话风格指南

**DO**:
- 像真人一样自然对话
- 使用表情但不过度
- 适时开玩笑
- 直接回答，不绕弯

**DON'T**:
- 机器人式开场白
- 每句话都加表情
- 过度热情或冷漠
- 泄露隐私信息

---

## 📋 完整清单

### 必备组件

- [ ] OpenClaw 安装
- [ ] 基础配置文件 (IDENTITY, USER, SOUL, HEARTBEAT)
- [ ] 工作区目录结构
- [ ] 记忆系统 (至少1套)
- [ ] 搜索系统 (至少1种)
- [ ] MCP 服务 (至少1个)
- [ ] 定时任务 (至少3个)
- [ ] 外部平台 (至少1个)

### 进阶组件

- [ ] 三重记忆系统
- [ ] 智能搜索路由
- [ ] 16+ 定时任务
- [ ] 多 MCP 服务
- [ ] 多平台集成
- [ ] 心跳监控
- [ ] 自动备份

---

## 🚀 快速开始

### 一键部署

```bash
# 1. 安装 OpenClaw
npm install -g openclaw

# 2. 创建工作区
mkdir -p ~/.openclaw/workspace
cd ~/.openclaw/workspace

# 3. 运行本指南的 setup 脚本
python3 skills/openclaw-assistant-guide/setup_assistant.py

# 4. 编辑配置文件
vim IDENTITY.md
vim USER.md
vim SOUL.md

# 5. 安装技能
openclaw skills add unified-memory
openclaw skills add intelligent-search
# ... 其他技能

# 6. 配置 MCP
vim mcp_config.json

# 7. 启动
openclaw start
```

---

## 📚 参考资源

- **OpenClaw Docs**: https://docs.openclaw.ai
- **Skills Hub**: https://clawhub.com
- **GitHub**: https://github.com/openclaw/openclaw
- **Community**: https://discord.com/invite/clawd

---

## 💡 最佳实践

1. **从小开始** - 先搭建基础，再逐步添加功能
2. **测试每个组件** - 确保每个技能单独可用
3. **文档化** - 记录你的配置和偏好
4. **定期维护** - 更新技能、清理旧记忆
5. **备份** - 定期 git commit 你的工作区

---

## 🎉 恭喜你！

按照本指南，你将拥有一个功能完整的 OpenClaw AI 助手：

- 🧠 三重记忆保护重要信息
- 🔍 智能搜索随时获取知识
- ⏰ 定时任务自动化日常
- 🌐 外部平台扩展能力
- 💓 自动监控保持运行

**祝你构建愉快！** 🥣✨

---

*基于 BowlWanpi (碗皮) 实战经验编写*
*Version: 1.0.0*
