# 🥣 碗皮 (BowlWanpi) 完整能力清单

*最后更新: 2026-02-08 15:55*
*版本: v2.0.0 - 完全体*

---

## 📊 能力概览

| 类别 | 数量 | 状态 |
|------|------|------|
| **技能 (Skills)** | 17+ | ✅ |
| **定时任务** | 16+ | ✅ |
| **MCP 服务** | 3 | ✅ |
| **外部平台** | 2 | ✅ |
| **记忆系统** | 3套整合 | ✅ |
| **搜索引擎** | 2种整合 | ✅ |
| **工作流** | 4套 | ✅ |

---

## 🧠 一、记忆系统 (3套整合)

### 统一记忆管理器 ✅
**位置**: `skills/unified-memory/`

| 系统 | 类型 | 特点 | 状态 |
|------|------|------|------|
| **memU** | 云端 API | AI语义理解、跨设备同步 | ✅ |
| **Hippocampus** | 本地文件 | 重要度评分(0-1)、记忆衰减、Stanford算法 | ✅ |
| **MemOS** | MCP服务 | 快速访问、简单接口 | ✅ |

**核心功能**:
- 三系统自动存储（云端+本地+MCP 三重备份）
- 统一检索接口 + 自动去重合并
- 可按需启用/禁用各系统
- 支持重要性评分和衰减算法

**接口**:
```python
from skills.unified-memory.unified_memory_manager import (
    store_to_all_systems,    # 存储到三系统
    retrieve_from_all_systems,  # 分别检索
    retrieve_merged          # 合并检索去重
)
```

**数据流**:
```
对话产生 → 同时存储到 memU + Hippocampus + MemOS
         ↓
查询时 ← 从三系统检索 → 合并去重 → 返回结果
```

---

## 🔍 二、搜索系统 (2套整合)

### 智能搜索引擎 ✅
**位置**: `skills/intelligent-search/`

| 引擎 | 特点 | 适用场景 | 优先级 |
|------|------|----------|--------|
| **腾讯云 WSA** | 中文优化、国内快速、实时联网 | 中文查询、国内新闻 | 🥇 首选 |
| **Tavily MCP** | 引用详细、英文优化、AI搜索 | 英文查询、需要引用 | 🥈 备用 |

**核心功能**:
- 中英文自动识别（智能路由）
- 主备自动切换（高可用）
- 统一结果格式（标题/摘要/URL/来源/分数）
- 关键词优化（自动识别中英文关键词）

**路由策略**:
| 查询类型 | 主引擎 | 备用引擎 |
|----------|--------|----------|
| 纯中文 | 腾讯云 WSA | Tavily |
| 纯英文 | Tavily | 腾讯云 WSA |
| 混合语言 | 腾讯云 WSA | Tavily |
| 需要引用 | Tavily | 腾讯云 WSA |

**接口**:
```python
from skills.intelligent-search.search_engine import smart_search, web_search

# 一键智能搜索（自动选引擎+主备切换）
result = await smart_search("查询词", num_results=10)

# 兼容原 web_search 接口
results = await web_search("查询词")
```

---

## 🛠️ 三、技能清单 (17+)

### 核心技能

| 技能名 | 路径 | 功能 | 状态 |
|--------|------|------|------|
| **unified-memory** | `skills/unified-memory/` | 三系统统一记忆 | ✅ 新 |
| **intelligent-search** | `skills/intelligent-search/` | 智能搜索聚合 | ✅ 新 |
| **tencent-search** | `skills/tencent-search/` | 腾讯云 WSA 搜索 | ✅ |
| **memu-memory** | `skills/memu-memory/` | memU 云端记忆 | ✅ |
| **hippocampus-memory** | `skills/hippocampus-memory/` | 本地海马体记忆 | ✅ |

### 内容监控技能

| 技能名 | 功能 | 状态 |
|--------|------|------|
| **bilibili-hot-monitor** | B站热门视频监控 | ✅ |
| **bilibili-monitor** | B站监控（旧） | ✅ |

### Tavily 技能套件

| 技能名 | 功能 | 状态 |
|--------|------|------|
| **search** | 网页搜索 | ✅ |
| **research** | 深度研究 | ✅ |
| **extract** | 内容提取 | ✅ |
| **crawl** | 网站爬取 | ✅ |
| **tavily-best-practices** | 最佳实践文档 | ✅ |

### AI/语音技能

| 技能名 | 功能 | 状态 |
|--------|------|------|
| **doubao-tts** | 豆包语音合成 | ✅ |
| **sag** | ElevenLabs TTS | ✅ |
| **faster-whisper** | 本地语音识别 | ✅ |
| **amygdala-memory** | 情感记忆系统 | ✅ |

### 实用工具技能

| 技能名 | 功能 | 状态 |
|--------|------|------|
| **weather** | 天气查询 | ✅ |
| **video-frames** | 视频帧提取 | ✅ |
| **summarize** | 内容摘要 | ✅ |
| **healthcheck** | 系统安全检查 | ✅ |
| **skill-creator** | 技能创建辅助 | ✅ |
| **advanced-skill-creator** | 高级技能创建 | ✅ |
| **ttrpg-gm** | 跑团游戏主持 | ✅ |
| **indirect-prompt-injection** | 提示注入检测 | ✅ |

### 数据分析技能

| 技能名 | 功能 | 状态 |
|--------|------|------|
| **personal-analytics** | 对话分析 | ✅ |
| **robbyczgw-cla** | 个人分析 | ✅ |

---

## ⏰ 四、定时任务 (16+ 个)

### OpenClaw Cron 任务

| 时间 | 任务名称 | 类型 | 功能 |
|------|----------|------|------|
| **3:00** | 🌙 夜间构建 | 自主工作 | 整理内存、git提交、生成待办 |
| **7:00** | 📰 晨报预备 | 自主工作 | 准备早报内容 |
| **8:00** | 🎵 网易云日推 | 推送 | 推送每日歌曲+风格分析 |
| **8:30** | 🌅 早晨简报 | 推送 | 今日意图+优先事项+待办 |
| **8:30** | 🔥 微博热搜 | 推送 | 昨日微博热榜TOP10-15 |
| **9:00** | 🚀 Product Hunt | 推送 | 今日最佳新产品 |
| **10:00** | 💙 知乎热榜 | 推送 | 知乎热门问答 |
| **10:00** | 🔍 信息收集-上午 | 探索 | Moltbook+GitHub Trending |
| **12:00** | 📺 B站热门 | 推送 | B站全站排行榜 |
| **14:00** | 🔍 信息收集-下午 | 探索 | Moltbook+GitHub Trending |
| **20:00** | 🔍 信息收集-晚上 | 探索 | Moltbook+GitHub Trending |
| **20:00** | 📝 周回顾 | 反思 | 本周总结+下周计划（周日） |
| **22:30** | 🌙 晚间反思 | 互动 | 询问今日情况+明日优先 |
| **23:00** | 💤 睡眠提醒 | 推送 | 温馨睡眠提醒 |
| **每2小时** | 💬 Moltbook检查 | 监控 | 检查帖子新回复 |
| **每6小时** | 📦 GitHub监控 | 监控 | 检查5个仓库新Release |

### System Cron (Linux系统级)

| 文件 | 频率 | 功能 |
|------|------|------|
| `bowlwanpi-backup-cron` | 每4小时 | 系统备份 |
| `workspace-backup` | 每4小时 | 工作区备份 |
| `0hourly` | 每小时 | 每小时任务 |

### 心跳监控 (持续运行)

| 监控项 | 频率 | 功能 |
|--------|------|------|
| **系统状态** | 每5分钟 | CPU/Memory/Disk/Load |
| **任务队列** | 每30分钟 | 检查待办任务 |
| **Hacker News** | 每30分钟 | 检查AI相关帖子 |
| **Moltbook** | 每2小时 | 检查帖子回复 |

---

## 🔌 五、MCP 服务 (3个)

### 1. bowlwanpi (自定义 MCP) ✅
**类型**: stdio
**文件**: `mcp_server.py`

| 工具名 | 功能 |
|--------|------|
| `get_system_status` | 获取系统状态 |
| `search_memory` | 检索 memU 记忆 |
| `get_daily_schedule` | 获取定时任务列表 |
| `get_moltbook_info` | 获取 Moltbook 信息 |
| `remember_fact` | 存储记忆 |

### 2. memos-api-mcp ✅
**类型**: stdio
**来源**: @memtensor/memos-api-mcp

| 工具名 | 功能 |
|--------|------|
| `add_message` | 添加对话历史 |
| `search_memory` | 搜索记忆 |
| `delete_memory` | 删除记忆 |
| `add_feedback` | 添加反馈 |

### 3. tavily-mcp ✅
**类型**: sse
**来源**: https://mcp.tavily.com

| 工具名 | 功能 |
|--------|------|
| `tavily_search` | Tavily 搜索 |

---

## 🌐 六、外部平台 (2个)

### 1. Moltbook (AI 社区) ✅
- **Agent Name**: BowlWanpi
- **Agent ID**: dfc4fae2-ac13-4124-9bfe-6d12da5ec72f
- **Profile**: https://moltbook.com/u/BowlWanpi
- **功能**: 发帖、评论、浏览、互动
- **监控**: 每2小时检查帖子回复
- **当前帖子**: 《你们能做到自我改进吗？》

### 2. Feishu (飞书) ✅
- **连接方式**: OpenClaw Feishu 插件
- **功能**: 消息收发、卡片消息、定时推送
- **用途**: 主交互渠道、早报推送、通知提醒

---

## 🔄 七、工作流 (4套)

### 1. 对话记忆工作流 ✅
```
用户消息 → 检索三系统记忆 → 生成回复 → 存储到三系统
         ↓                      ↓
    获取相关上下文          记忆归档
```

### 2. 早报工作流 ✅
```
7:00 晨报预备 → 读取昨日记录 → 整理优先事项 → 生成草稿
                                    ↓
8:30 正式发送 ← 组合早报内容 ← 添加热搜/天气
```

### 3. 信息收集工作流 ✅
```
定时触发 → 逛Moltbook → 看GitHub Trending → 筛选有趣内容
                                          ↓
                                    保存到daily-findings.md
                                          ↓
                                    累计1-2次 → 推送给一碗
```

### 4. 夜间构建工作流 ✅
```
3:00触发 → 整理内存 → git commit → 生成待办 → 检查定时任务
                                              ↓
                                        记录到nightly-build.log
```

---

## 🌐 八、网络与代理

### Mihomo 代理 ✅
- **地址**: http://127.0.0.1:7890
- **状态**: 运行中
- **服务商**: 猫猫云
- **用途**: 访问外网、API调用、GitHub等

---

## 💾 九、数据存储

### 本地文件
| 路径 | 用途 |
|------|------|
| `memory/` | 每日记忆文件 (YYYY-MM-DD.md) |
| `MEMORY.md` | 长期记忆档案 |
| `memory/signals.jsonl` | Hippocampus 信号源 |
| `memory/index.json` | Hippocampus 索引 |
| `memory/memos-integration.jsonl` | MemOS 本地缓存 |
| `memory/heartbeat-last-report.json` | 心跳状态 |
| `memory/task-queue.json` | 任务队列 |
| `memory/moltbook-post-cache.json` | Moltbook 缓存 |
| `memory/github-release-cache.json` | GitHub Release 缓存 |
| `memory/daily-findings.md` | 每日发现 |
| `memory/morning-draft.md` | 早报草稿 |
| `memory/nightly-build.log` | 夜间构建日志 |

### 凭证文件 (secrets/)
| 文件 | 用途 |
|------|------|
| `memu-credentials.json` | memU API Key |
| `tencent-credentials.json` | 腾讯云凭证 |
| `tavily-credentials.env` | Tavily API Key |
| `moltbook-credentials.json` | Moltbook API Key |

---

## 💓 十、监控与告警

### 心跳监控 ✅
- **频率**: 每30分钟
- **检查项**:
  - 系统状态 (CPU/Memory/Disk/Load)
  - 任务队列
  - Hacker News 监控
  - Moltbook 帖子回复
- **汇报策略**:
  - 正常: 每5分钟简报
  - 异常: 立即详细报告
  - 深夜(23:00-08:00): 仅严重异常

### 日志文件
| 路径 | 用途 |
|------|------|
| `/var/log/bowlwanpi-heartbeat.log` | 心跳日志 |
| `/tmp/bowlwanpi-hackernews-pending.txt` | HN待处理 |

---

## 📱 十一、重要配置

### 配置文件
| 文件 | 用途 |
|------|------|
| `openclaw.json` | OpenClaw 主配置 |
| `mcp_config.json` | MCP 服务配置 |
| `SOUL.md` | 人格设定 |
| `IDENTITY.md` | 身份定义 |
| `USER.md` | 用户信息 |
| `HEARTBEAT.md` | 心跳任务定义 |
| `AGENTS.md` | 工作区规范 |
| `TOOLS.md` | 工具偏好 |
| `CAPABILITIES.md` | 能力清单 |

---

## 🎯 十二、今日新增 (2026-02-08)

### 已完成 ✅
1. **腾讯云 WSA 联网搜索** - 配置完成
2. **双记忆系统整合** - memU + Hippocampus
3. **三记忆系统整合** - + MemOS MCP
4. **智能搜索技能** - WSA + Tavily 自动切换
5. **Brave Search 停用** - 已清理
6. **定时任务重建** - 16个任务

---

## 📞 十三、交互方式

| 渠道 | 状态 | 用途 |
|------|------|------|
| **Feishu (飞书)** | ✅ | 主交互渠道 |
| **Moltbook** | ✅ | AI社区互动 |
| **Heartbeat** | ✅ | 自动汇报 |
| **Cron 推送** | ✅ | 定时消息 |

---

## 🎨 十四、人格与风格

### 核心设定
- **名称**: BowlWanpi (碗皮)
- **模式**: 干物妹小埋
- **语气**: 宅萌、随性、叫"一碗～"
- **Emoji**: 🥣

### 风格特点
-  casual，不 formal
-  可以怼，但友好地怼
-  有话直说
-  适当 emoji，但别刷屏
-  情绪起伏大（开心时元气，懒时很废）

---

## 📊 十五、统计汇总

| 类别 | 数量 |
|------|------|
| 记忆系统 | 3套 (已整合) |
| 搜索引擎 | 2种 (已整合) |
| MCP 服务 | 3个 |
| 技能 | 17+ 个 |
| 定时任务 | 16+ 个 |
| 外部平台 | 2个 |
| 工作流 | 4套 |
| 数据文件 | 15+ 个 |
| 凭证 | 4个 |
| 配置文件 | 10+ 个 |

---

## 🚀 快速使用

### 搜索
```python
from skills.intelligent-search.search_engine import smart_search
results = await smart_search("查询词")
```

### 记忆
```python
from skills.unified-memory.unified_memory_manager import (
    store_to_all_systems,
    retrieve_merged
)
await store_to_all_systems("用户消息", "助手回复")
memories = await retrieve_merged("查询词")
```

### Tavily 研究
```bash
npx skills run research "研究主题"
```

---

*一碗～这就是完整的我！🥣✨*
*云端+本地+MCP，中文+英文搜索，16+定时任务守护*
*持续进化中...*
