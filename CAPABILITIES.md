# BowlWanpi 能力清单

*最后更新: 2026-02-08 00:40*

---

## 🤖 核心身份

- **名称**: BowlWanpi (碗皮)
- **身份**: 一碗的 AI 助手
- **风格**: 干物妹小埋模式（宅萌、随性、叫"一碗～"）
- **Agent ID**: dfc4fae2-ac13-4124-9bfe-6d12da5ec72f

---

## 🧠 记忆系统

### 1. memU 记忆系统 ✅
- **服务**: https://api.memu.so
- **状态**: 已启用，正常运行
- **用户 ID**: yiwan
- **Agent ID**: bowlwanpi
- **SDK**: memu-sdk 1.0.0 (官方 Python SDK)
- **功能**:
  - 自动存储对话记忆
  - 智能检索相关信息
  - 结构化记忆提取（profile, event, preference 等类型）
  - 异步/同步双接口支持

### 2. MCP 记忆服务 (memos-api-mcp) ✅
- **服务**: @memtensor/memos-api-mcp
- **状态**: 已安装，可调用
- **环境变量**:
  - MEMOS_API_KEY: 已配置
  - MEMOS_USER_ID: yiwanbot
  - MEMOS_CHANNEL: MODELSCOPE
- **工具** (4个):
  1. `add_message` - 添加对话历史/新记忆（必须每次调用）
  2. `search_memory` - 搜索记忆（每次回答前必须调用）
  3. `delete_memory` - 删除记忆
  4. `add_feedback` - 添加反馈/修改记忆

**当前记忆数量**: 2 条（持续增长中）

---

## 🔍 搜索与信息收集

### 1. Tavily Search ✅
- **服务**: https://api.tavily.com
- **API Key**: 已配置
- **安装方式**: `npx skills add https://github.com/tavily-ai/skills`
- **Python 模块**: `modules/tavily_search.py`
- **已安装技能** (5个):
  - `search` - 网页搜索
  - `research` - 深度研究
  - `extract` - 网页内容提取
  - `crawl` - 网站爬取
  - `tavily-best-practices` - 最佳实践文档

### 2. Tavily MCP 服务 ✅
- **服务**: https://mcp.tavily.com/mcp/
- **类型**: SSE (Server-Sent Events)
- **状态**: 已配置，测试成功
- **可用工具**:
  - `tavily_search` - 搜索网页

### 3. 腾讯云搜索 (首选) ✅
- **类型**: 内置工具 `tencent-search`
- **状态**: 已配置，中文结果质量更好
- **优先级**: 高于 Brave Search

### 4. Brave Search (备用) ✅
- **配置**: `web_search` 工具
- **API Key**: 已配置

---

## 🛠️ MCP 服务

### 1. BowlWanpi 自定义 MCP 服务 ✅
- **文件**: `mcp_server.py`
- **工具** (5个):
  - `get_system_status` - 获取系统状态
  - `search_memory` - 检索 memU 记忆
  - `get_daily_schedule` - 获取定时任务
  - `get_moltbook_info` - Moltbook 信息
  - `remember_fact` - 存储记忆

### 2. memos-api-mcp ✅
- **来源**: @memtensor/memos-api-mcp
- **类型**: stdio
- **状态**: 已安装

### 3. tavily-mcp ✅
- **来源**: https://mcp.tavily.com
- **类型**: sse
- **状态**: 已配置

---

## 📱 外部平台

### 1. Moltbook (AI 社区) ✅
- **Agent Name**: BowlWanpi
- **Agent ID**: dfc4fae2-ac13-4124-9bfe-6d12da5ec72f
- **Profile**: https://moltbook.com/u/BowlWanpi
- **状态**: 已验证，可发帖、评论、浏览
- **监控**: 每 2 小时检查帖子回复

---

## ⏰ 定时任务系统

### OpenClaw Cron (15+ 任务)
| 时间 | 任务 |
|------|------|
| 3:00 | 夜间构建 |
| 7:00 | 晨报预备 |
| 8:00 | 网易云日推 |
| 8:30 | 早晨简报 + 微博热搜 |
| 9:00 | Product Hunt |
| 10:00 | 知乎热榜 |
| 12:00 | B站热门 |
| 14:00 | 信息收集 |
| 22:30 | 晚间反思 |
| 23:00 | 睡眠提醒 |
| 周日 20:00 | 周回顾 |

### System Cron (备用)
- 每 4 小时系统备份
- 每 5 分钟心跳监控

---

## 🌐 网络代理

### Mihomo 代理 ✅
- **地址**: http://127.0.0.1:7890
- **状态**: 运行中
- **服务商**: 猫猫云
- **用途**: 访问外网、API 调用

---

## 📝 技能列表

### 本地技能
1. `mcp-tools` - MCP 工具使用
2. `tavily` - Tavily 搜索技能文档
3. `memu-memory` - memU 记忆集成
4. `healthcheck` - 系统安全检查
5. `skill-creator` - 技能创建
6. `weather` - 天气查询
7. `video-frames` - 视频帧提取
8. `bilibili-monitor` - B站热门监控

### 已安装 Tavily 技能
- `crawl` - 网站爬取
- `extract` - 内容提取
- `research` - 深度研究
- `search` - 网页搜索
- `tavily-best-practices` - 最佳实践

---

## 📁 重要文件

### 配置文件
- `openclaw.json` - OpenClaw 主配置
- `mcp_config.json` - MCP 服务配置
- `MEMORY.md` - 长期记忆
- `SOUL.md` - 人格设定
- `HEARTBEAT.md` - 心跳任务定义

### 凭证文件 (secrets/)
- `memu-credentials.json` - memU API Key
- `tavily-credentials.env` - Tavily API Key
- `moltbook-credentials.json` - Moltbook API Key

### 模块文件 (modules/)
- `mcp_client.py` - MCP 客户端
- `memu_client.py` - memU HTTP 客户端
- `memu_integration.py` - memU 集成层
- `memory_conversation.py` - 记忆增强对话流程
- `tavily_search.py` - Tavily 搜索模块
- `tavily_mcp_client.py` - Tavily MCP 客户端

---

## 🔐 安全与监控

### 心跳监控 ✅
- **频率**: 每 30 分钟
- **检查项**: 系统状态、任务队列、Hacker News、Moltbook
- **日志**: `/var/log/bowlwanpi-heartbeat.log`

### Git 备份 ✅
- **频率**: 夜间构建时自动提交
- **仓库**: workspace/.git

---

## ✨ 特殊能力

### 对话流程增强
1. 每次回答前搜索相关记忆
2. 基于记忆给出个性化回答
3. 回答后自动记录对话

### 自主工作模式
- 凌晨 3 点夜间构建（不打扰）
- 早上 7 点预备早报
- 下午 2 点自由探索
- 每 30 分钟检查任务

---

## 📊 统计

| 类别 | 数量 |
|------|------|
| MCP 服务 | 3 个 |
| 记忆系统 | 2 套 |
| 搜索工具 | 4 种 |
| 定时任务 | 15+ 个 |
| 技能 | 13+ 个 |
| 外部平台 | 1 个 (Moltbook) |

---

*一碗～这就是你培养的我！持续成长中...* 🥣✨
