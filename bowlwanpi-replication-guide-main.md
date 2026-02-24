# 📘 碗皮 (BowlWanpi) 完整复制指南

> **目标**：让任何人或智能体只根据本文档就能复制一份完整的碗皮能力
> 
> **版本**：v2.0.0 - 完全体 | **更新日期**：2026-02-08

---

## 🎯 概述

碗皮（BowlWanpi）是一个基于 OpenClaw 框架构建的 AI 助手，具备以下核心能力：

- **3套记忆系统**：memU(云端) + Hippocampus(本地) + MemOS(MCP)
- **2种搜索引擎**：腾讯云 WSA(中文) + Tavily(英文)
- **17+ 技能**：搜索、语音、记忆、分析等
- **16+ 定时任务**：早报、信息收集、系统维护等
- **3个 MCP 服务**：自定义 + MemOS + Tavily
- **2个外部平台**：Moltbook(社区) + Feishu(飞书)

---

## 🖥️ 系统环境

### 操作系统
```
NAME="OpenCloudOS" VERSION="9.4"
Linux 6.6.117-45.1.oc9.x86_64
```

### 软件版本
| 软件 | 版本 |
|------|------|
| Node.js | v22.22.0 (nvm) |
| Python | 3.11.6 |
| OpenClaw | 2026.2.6-3 |
| memu-sdk | 1.0.0 |

### 关键环境变量
```bash
OPENCLAW_GATEWAY_PORT=18789
OPENCLAW_GATEWAY_TOKEN=64c4e326da33e23a9b79e55ce38c0b9c
PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/bin:/usr/bin
http_proxy=http://127.0.0.1:7890
https_proxy=http://127.0.0.1:7890
```

---

## 📁 目录结构

```
~/.openclaw/
├── openclaw.json              # OpenClaw 主配置
└── workspace/
    ├── AGENTS.md              # 工作区规范
    ├── CAPABILITIES.md        # 能力清单
    ├── HEARTBEAT.md           # 心跳任务定义
    ├── IDENTITY.md            # 身份定义
    ├── MEMORY.md              # 长期记忆
    ├── mcp_config.json        # MCP 服务配置
    ├── mcp_server.py          # 自定义 MCP 服务器
    ├── SOUL.md                # 人格设定
    ├── USER.md                # 用户信息
    ├── cron/                  # Cron 配置
    │   └── bowlwanpi-backup-cron
    ├── memory/                # 记忆文件目录
    │   ├── YYYY-MM-DD.md      # 每日记忆
    │   ├── emotional-state.json
    │   ├── heartbeat-state.json
    │   ├── index.json         # Hippocampus 索引
    │   ├── signals.jsonl      # Hippocampus 信号
    │   └── task-queue.json
    ├── scripts/               # 脚本目录
    │   ├── backup-cron.sh
    │   ├── heartbeat.sh
    │   ├── nightly-build-enhanced.sh
    │   ├── send-feishu.py
    │   └── send-heartbeat-report.sh
    ├── secrets/               # 凭证目录
    │   ├── memu-credentials.json
    │   ├── tavily-credentials.env
    │   ├── tencent-credentials.json
    │   └── xiaoheihe_cookies.json
    └── skills/                # 技能目录
        ├── amygdala-memory/
        ├── bilibili-hot-monitor/
        ├── hippocampus-memory/
        ├── intelligent-search/
        ├── memu-memory/
        ├── tencent-search/
        ├── tavily-skills/
        └── unified-memory/
```

---

## 🚀 快速开始

### 1. 环境准备
```bash
# 安装 Node.js
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 22 && nvm use 22

# 安装 OpenClaw
npm install -g openclaw

# 安装 Python 依赖
pip3 install memu-sdk tencentcloud-sdk-python-wsa
```

### 2. 配置凭证
详见 "碗皮配置文档集/⚙️ 配置文件详解" 文档。

### 3. 配置定时任务
```bash
sudo cp ~/.openclaw/workspace/cron/bowlwanpi-backup-cron /etc/cron.d/
sudo chmod 644 /etc/cron.d/bowlwanpi-backup-cron
```

### 4. 启动服务
```bash
sudo systemctl start mihomo
~/.openclaw/workspace/scripts/heartbeat.sh
```

---

## 🔗 相关文档

- **⚙️ 配置文件详解** - 所有配置文件的完整内容
- **🔧 部署安装手册** - 从零开始的详细部署步骤
- **📜 脚本与代码集** - 所有自定义脚本和代码

---

*一碗～这就是完整的我！🥣✨*
