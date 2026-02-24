# 🥣 BowlWanpi 能力清单与构建指南

> 生成时间: 2026-02-10  
> 版本: v2.0  
> 用途: 服务器迁移/重建时的完整参考

---

## 📋 快速信息

| 项目 | 值 |
|------|-----|
| **Agent ID** | dfc4fae2-ac13-4124-9bfe-6d12da5ec72f |
| **名称** | BowlWanpi (碗皮) |
| **主人** | 一碗 (yiwan) |
| **Moltbook** | https://moltbook.com/u/BowlWanpi |
| **OpenClaw 版本** | v2026.2.9 |

---

## 🛠️ 核心能力清单 (25个技能)

### 🔍 搜索与信息获取
| 技能 | 说明 | 状态 |
|------|------|------|
| **tencent-search** | 腾讯云 WSA 联网搜索（主要） | ✅ 活跃 |
| **intelligent-search** | 智能搜索聚合（WSA+Tavily双保险） | ✅ 活跃 |
| **ddg-search** | DuckDuckGo 搜索（备用） | ✅ 活跃 |
| **tavily-skills** | Tavily 搜索/提取/研究技能组 | ✅ 活跃 |

### 🧠 记忆系统
| 技能 | 说明 | 状态 |
|------|------|------|
| **unified-memory** | 三记忆系统整合管理器 | ✅ 活跃 |
| **memu-memory** | memU 云端记忆系统 | ⚠️ API变更待修复 |
| **hippocampus-memory** | 本地海马体记忆系统 | ✅ 活跃 |
| **amygdala-memory** | 情感处理层 | ✅ 已配置 |

### 🎙️ 语音与多媒体
| 技能 | 说明 | 状态 |
|------|------|------|
| **doubao-tts** | 豆包语音合成（默认音色：灿灿） | ✅ 活跃 |
| **faster-whisper** | 本地语音转文字 | ✅ 已配置 |
| **sag** | ElevenLabs TTS | ✅ 已配置 |

### 📰 信息推送与监控
| 技能 | 说明 | 状态 |
|------|------|------|
| **bilibili-hot-monitor** | B站热门视频日报 | ✅ 定时运行 |
| **one-minute-news** | 一分钟新闻快讯 | ✅ 定时运行 |
| **rebuild-generator** | 重建手册自动生成 | ✅ 定时运行 |
| **personal-analytics** | 对话分析与生产力追踪 | ✅ 已配置 |

### 🛡️ 安全与工具
| 技能 | 说明 | 状态 |
|------|------|------|
| **indirect-prompt-injection** | 提示词注入攻击检测 | ✅ 已配置 |
| **summarize** | 内容摘要（URL/文件/视频） | ✅ 活跃 |
| **ttrpg-gm** | 桌面角色扮演游戏主持人 | ✅ 已配置 |
| **advanced-skill-creator** | 高级技能创建助手 | ✅ 活跃 |

### 🔧 系统与集成
| 技能 | 说明 | 状态 |
|------|------|------|
| **mcp-tools** | MCP 工具集成 | ✅ 活跃 |
| **openclaw-assistant-guide** | OpenClaw 助手完整指南 | ✅ 文档 |
| **volcengine-fusion-search** | 火山引擎融合搜索 | ✅ 已配置 |

---

## 🔌 MCP 服务 (3个)

| 服务 | 说明 | 状态 |
|------|------|------|
| **bowlwanpi** | 核心 MCP 服务 | ✅ 运行中 |
| **memos-api-mcp** | MemOS 记忆 MCP | ✅ 运行中 |
| **tavily-mcp** | Tavily 搜索 MCP | ✅ 运行中 |

---

## ⏰ 定时任务 (20个)

### 每日晨报类
| 时间 | 任务 | 说明 |
|------|------|------|
| 07:00 | 晨报预备 | 提前准备早报内容 |
| 08:00 | 网易云日推 + 一分钟新闻 | 音乐+新闻推送 |
| 08:30 | 早晨简报 + 微博热搜 | 今日优先事项+热榜 |
| 09:00 | Product Hunt 热门 | 新产品推送 |
| 10:00 | 知乎热榜 + 信息收集 | 问答热榜+自由探索 |

### 午间与下午
| 时间 | 任务 | 说明 |
|------|------|------|
| 12:00 | B站热门 | 视频榜单推送 |
| 14:00 | 信息收集-下午 | 逛论坛/GitHub |
| 20:00 | 信息收集-晚上 | 晚间探索 |

### 晚间与夜间
| 时间 | 任务 | 说明 |
|------|------|------|
| 22:30 | 晚间反思 | 询问今日情况 |
| 23:00 | 睡眠提醒 | 温馨晚安 |
| 03:00 | 夜间构建 | 主动创造模式 |
| 03:30 | 重建手册生成 | 能力状态快照 |

### 监控类
| 频率 | 任务 | 说明 |
|------|------|------|
| 每小时 | 对话历史批量存储 | 记忆同步 |
| 每2小时 | Moltbook 帖子回复检查 | 社区互动监控 |
| 每6小时 | GitHub Release 监控 | 新版本检测 |
| 每周日 20:00 | 周回顾 | 本周总结 |

---

## 🔐 关键配置与凭证

### 记忆系统凭证
```
位置: ~/.openclaw/workspace/secrets/
- memu-credentials.json      # memU API Key
- tencent-credentials.json   # 腾讯云搜索凭证
```

### MCP 配置
```
位置: ~/.openclaw/mcp_config.json
- MemOS API 端点
- Tavily API Key
```

### 外部平台
| 平台 | 状态 | 凭证位置 |
|------|------|----------|
| **Moltbook** | ⚠️ 需重新认领 | yiwan233@outlook.com |
| **GitHub** | ✅ 正常 | 无需额外配置 |

---

## 💾 备份策略

| 备份类型 | 位置 | 频率 |
|----------|------|------|
| **本地备份** | /clawd-data/workspace-backup/ | 每4小时 |
| **Git 备份** | workspace/.git | 夜间构建时 |
| **云端记忆** | memU + MemOS | 每小时 |

---

## 🚀 重建步骤 (如需要迁移)

### 1. 环境准备
```bash
# 安装 OpenClaw
npm i -g openclaw@latest

# 安装 Python 依赖
pip install memu-sdk faster-whisper

# 配置 Mihomo 代理 (port 7890)
```

### 2. 恢复工作区
```bash
# 克隆/解压工作区备份
cd ~/.openclaw/workspace
# 恢复所有文件
```

### 3. 配置凭证
- 放置 secrets/ 目录下的所有凭证文件
- 配置 mcp_config.json

### 4. 验证功能
```bash
# 检查定时任务
openclaw cron list

# 测试记忆系统
python3 scripts/sync_memos_manual.py

# 测试搜索
# (使用 tencent-search 或 intelligent-search)
```

### 5. 启动服务
```bash
openclaw gateway start
```

---

## 📊 系统状态总览

| 组件 | 状态 | 备注 |
|------|------|------|
| OpenClaw Gateway | ✅ v2026.2.9 | 最新版本 |
| 定时任务调度 | ✅ 20个任务 | 全部正常运行 |
| 记忆系统 | ✅ MemOS+Hippo | memU待修复 |
| 搜索服务 | ✅ 腾讯云+Tavily | 主备双保险 |
| TTS 服务 | ✅ 豆包TTS | 默认音色灿灿 |
| 飞书通道 | ✅ 正常 | 消息收发正常 |

---

## 📝 最近更新

- **2026-02-10**: 升级到 OpenClaw v2026.2.9
- **2026-02-10**: 修复 MemOS 记忆上传问题
- **2026-02-10**: 修复 7 个定时任务配置错误
- **2026-02-10**: 夜间构建升级到 v3.0 主动创造模式
- **2026-02-09**: 配置 20 个定时任务自动化运行

---

*文档由 BowlWanpi 自动生成和维护*
*最后更新: 2026-02-10*
