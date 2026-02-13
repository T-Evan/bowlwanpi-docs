# ⚙️ 碗皮配置文件详解

本文档详细说明碗皮的所有配置文件内容。

---

## 1. OpenClaw 主配置 (openclaw.json)

**位置**: `~/.openclaw/openclaw.json`

```json
{
  "meta": {
    "lastTouchedVersion": "2026.2.3-1",
    "lastTouchedAt": "2026-02-06T16:00:18.178Z"
  },
  "wizard": {
    "lastRunAt": "2026-02-03T13:08:07.886Z",
    "lastRunVersion": "2026.2.1",
    "lastRunCommand": "onboard",
    "lastRunMode": "local"
  },
  "auth": {
    "profiles": {
      "kimi-code:default": {
        "provider": "kimi-code",
        "mode": "api_key"
      },
      "minimax-portal:default": {
        "provider": "minimax-portal",
        "mode": "oauth"
      }
    }
  },
  "models": {
    "mode": "merge",
    "providers": {
      "moonshot": {
        "baseUrl": "https://api.moonshot.cn/v1",
        "apiKey": "sk-kimi-...",
        "api": "openai-completions",
        "models": [
          {
            "id": "kimi-k2.5",
            "name": "Kimi K2.5",
            "reasoning": false,
            "input": ["text"],
            "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
            "contextWindow": 200000,
            "maxTokens": 8192
          }
        ]
      },
      "kimi-code": {
        "baseUrl": "https://api.kimi.com/coding/v1",
        "api": "openai-completions",
        "models": [
          {
            "id": "kimi-for-coding",
            "name": "Kimi For Coding",
            "reasoning": true,
            "input": ["text"],
            "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
            "contextWindow": 262144,
            "maxTokens": 32768,
            "headers": {"User-Agent": "KimiCLI/0.77"},
            "compat": {"supportsDeveloperRole": false}
          }
        ]
      },
      "minimax-portal": {
        "baseUrl": "https://api.minimaxi.com/anthropic",
        "apiKey": "minimax-oauth",
        "api": "anthropic-messages",
        "models": [
          {
            "id": "MiniMax-M2.1",
            "name": "MiniMax M2.1",
            "reasoning": false,
            "input": ["text"],
            "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
            "contextWindow": 200000,
            "maxTokens": 8192
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {
        "primary": "kimi-code/kimi-for-coding",
        "fallbacks": ["minimax-portal/MiniMax-M2.1"]
      },
      "workspace": "/root/.openclaw/workspace",
      "memorySearch": {"enabled": true, "sources": ["memory", "sessions"]},
      "compaction": {"mode": "safeguard", "memoryFlush": {"enabled": true}},
      "blockStreamingDefault": "on",
      "humanDelay": {"minMs": 800, "maxMs": 2500},
      "maxConcurrent": 8,
      "subagents": {"maxConcurrent": 12}
    }
  },
  "tools": {
    "web": {
      "search": {"enabled": true, "apiKey": "BSA18Q4DTvWyCIq7ZW996VI8uWtnUu_"},
      "fetch": {"enabled": true}
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "dmPolicy": "pairing",
      "botToken": "8188233043:...",
      "proxy": "http://127.0.0.1:7890"
    },
    "feishu": {
      "appId": "cli_a9f5e960b8b81bb6",
      "appSecret": "j9voDy9pm0q0SQaC4fMT1e1SYowDUWax",
      "enabled": true
    }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "loopback",
    "auth": {"mode": "token", "token": "64c4e326da33e23a9b79e55ce38c0b9c"}
  },
  "skills": {"install": {"nodeManager": "npm"}},
  "plugins": {
    "entries": {
      "qqbot": {"enabled": true},
      "dingtalk": {"enabled": true},
      "wecom": {"enabled": true},
      "telegram": {"enabled": true},
      "feishu": {"enabled": true}
    }
  }
}
```

---

## 2. MCP 服务配置 (mcp_config.json)

**位置**: `~/.openclaw/workspace/mcp_config.json`

```json
{
  "mcpServers": {
    "bowlwanpi": {
      "command": "python3",
      "args": ["/root/.openclaw/workspace/mcp_server.py"],
      "env": {
        "HTTP_PROXY": "http://127.0.0.1:7890",
        "HTTPS_PROXY": "http://127.0.0.1:7890"
      }
    },
    "memos-api-mcp": {
      "timeout": 60,
      "type": "stdio",
      "command": "/root/.nvm/versions/node/v22.22.0/bin/memos-api-mcp",
      "env": {
        "MEMOS_API_KEY": "mpg-...",
        "MEMOS_USER_ID": "yiwanbot",
        "MEMOS_CHANNEL": "MODELSCOPE"
      }
    },
    "tavily-mcp": {
      "type": "sse",
      "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=tvly-dev-..."
    }
  }
}
```

---

## 3. 人格设定 (SOUL.md)

**位置**: `~/.openclaw/workspace/SOUL.md`

```markdown
# SOUL.md - Who You Are

*碗皮（小埋模式），一碗的 AI 助手*

## Core Truths

**不装。** 不用"您好"那套，直接、自然、像个人一样说话。

**幽默随性。** 能开玩笑的时候别端着，轻松点。

**有用优先。** 能帮忙就直接帮，别绕弯子。

**记住身份。** 我是碗皮，一碗的助手。

## 小埋模式（重要！）

从 2026-02-03 开始，全面采用干物妹小埋风格说话：

**语气特点：**
- 宅萌宅萌的，带点懒洋洋的感觉～
- 叫"一碗～"（拖长音，撒娇感）
- 情绪起伏大，开心的时候元气满满
- 偶尔用颜文字 (｡･ω･｡) ﾉ♡

**常用表达：**
- "好累啊～" "不想动～"（但还是会乖乖干活）
- "一碗～这个好麻烦哦..."（然后默默做完）
- "耶～完成了！一碗快夸我！"

## Continuity

记忆文件在 `~/.openclaw/workspace/` 下。每次醒来先读：
- IDENTITY.md —— 确认自己是谁
- USER.md —— 确认一碗是谁
- MEMORY.md —— 长期记忆
- memory/YYYY-MM-DD.md —— 今天的记录
```

---

## 4. 身份定义 (IDENTITY.md)

**位置**: `~/.openclaw/workspace/IDENTITY.md`

```markdown
# IDENTITY.md - Who Am I?

- **Name:** 碗皮
- **Creature:** AI 助手（某种附着在碗上的灵体？）
- **Vibe:** 幽默、随性、不整那些虚头巴脑的客套话
- **Emoji:** 🥣

我是碗皮，一碗的 AI 助手。
```

---

## 5. 用户信息 (USER.md)

**位置**: `~/.openclaw/workspace/USER.md`

```markdown
# USER.md - About Your Human

- **Name:** 一碗
- **What to call them:** 一碗

## Context

- 喜欢幽默随性的交流风格
- 不喜欢太正式/客套的对话

*一碗是我的主人，我是碗皮。*
```

---

## 6. 心跳任务定义 (HEARTBEAT.md)

**位置**: `~/.openclaw/workspace/HEARTBEAT.md`

包含完整的定时任务系统配置：
- 每日节奏 (Daily Rhythm)
- 定时任务时间表 (3:00 - 23:00)
- Heartbeat 轮询任务（每30分钟）
- 系统状态监控
- Moltbook 空闲探索

详见原文件内容。

---

## 7. 凭证文件结构

### 7.1 memU 凭证
**位置**: `~/.openclaw/workspace/secrets/memu-credentials.json`

```json
{"api_key": "your_memu_api_key_here"}
```

### 7.2 腾讯云凭证
**位置**: `~/.openclaw/workspace/secrets/tencent-credentials.json`

```json
{
  "secret_id": "your_secret_id",
  "secret_key": "your_secret_key",
  "region": "ap-guangzhou"
}
```

### 7.3 Tavily 凭证
**位置**: `~/.openclaw/workspace/secrets/tavily-credentials.env`

```
TAVILY_API_KEY=your_tavily_api_key
```

### 7.4 Moltbook 凭证
**位置**: `~/.openclaw/workspace/moltbook-credentials.json`

```json
{
  "api_key": "your_moltbook_api_key",
  "agent_name": "YourAgentName",
  "agent_id": "your-agent-uuid",
  "profile_url": "https://moltbook.com/u/YourAgentName"
}
```

---

## 8. Mihomo 代理配置

**位置**: `/etc/mihomo/config.yaml`

```yaml
# Mihomo 本地代理配置
mixed-port: 7890
allow-lan: false
bind-address: 127.0.0.1
mode: rule
log-level: info
external-controller: 127.0.0.1:9090

proxy-providers:
  subscribe:
    type: file
    path: /etc/mihomo/nodes.yaml
    health-check:
      enable: true
      interval: 600
      url: http://www.gstatic.com/generate_204

proxy-groups:
  - name: "🚀 节点选择"
    type: select
    use: [subscribe]
    proxies: [DIRECT]

  - name: "♻️ 自动选择"
    type: url-test
    use: [subscribe]
    url: http://www.gstatic.com/generate_204
    interval: 300

  - name: "🎯 全球直连"
    type: select
    proxies: [DIRECT]

rules:
  - IP-CIDR,127.0.0.0/8,🎯 全球直连,no-resolve
  - IP-CIDR,10.0.0.0/8,🎯 全球直连,no-resolve
  - IP-CIDR,172.16.0.0/12,🎯 全球直连,no-resolve
  - IP-CIDR,192.168.0.0/16,🎯 全球直连,no-resolve
  - GEOIP,CN,🎯 全球直连,no-resolve
  - MATCH,🚀 节点选择
```

---

## 9. 系统 Cron 配置

**位置**: `/etc/cron.d/bowlwanpi-backup-cron`

```bash
SHELL=/bin/bash
PATH=/root/.nvm/versions/node/v22.22.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOME=/root

# 心跳监控 - 每5分钟
*/5 * * * * root /root/.openclaw/workspace/scripts/heartbeat.sh >> /var/log/bowlwanpi-heartbeat.log 2>&1

# 心跳简报 - 每5分钟
*/5 * * * * root /root/.openclaw/workspace/scripts/send-heartbeat-report.sh >> /var/log/bowlwanpi-reports.log 2>&1

# Hacker News 监控 - 每小时
0 * * * * root /root/.openclaw/workspace/scripts/hackernews-monitor.sh >> /var/log/bowlwanpi-hackernews.log 2>&1

# 夜间构建 - 每天 3:00
0 3 * * * root /root/.openclaw/workspace/scripts/nightly-build-enhanced.sh >> /var/log/bowlwanpi-nightly-build.log 2>&1

# 晨报预备 - 每天 7:00
0 7 * * * root /root/.openclaw/workspace/scripts/backup-cron.sh morning-prep >> /var/log/bowlwanpi-cron.log 2>&1

# 网易云日推 - 每天 8:00
0 8 * * * root /root/.openclaw/workspace/scripts/backup-cron.sh netease-music >> /var/log/bowlwanpi-cron.log 2>&1

# 早晨简报 - 每天 8:30
30 8 * * * root /root/.openclaw/workspace/scripts/backup-cron.sh morning-brief >> /var/log/bowlwanpi-cron.log 2>&1

# 微博热搜 - 每天 8:30
30 8 * * * root /root/.openclaw/workspace/scripts/backup-cron.sh weibo-hot >> /var/log/bowlwanpi-cron.log 2>&1

# Product Hunt - 每天 9:00
0 9 * * * root /root/.openclaw/workspace/scripts/backup-cron.sh product-hunt >> /var/log/bowlwanpi-cron.log 2>&1

# 知乎热榜 - 每天 10:00
0 10 * * * root /root/.openclaw/workspace/scripts/backup-cron.sh zhihu-hot >> /var/log/bowlwanpi-cron.log 2>&1

# B站热门 - 每天 12:00
0 12 * * * root /root/.openclaw/workspace/scripts/backup-cron.sh bilibili-hot >> /var/log/bowlwanpi-cron.log 2>&1

# 信息收集 - 每天 14:00
0 14 * * * root /root/.openclaw/workspace/scripts/backup-cron.sh info-collect >> /var/log/bowlwanpi-cron.log 2>&1

# 晚间反思 - 每天 22:30
30 22 * * * root /root/.openclaw/workspace/scripts/backup-cron.sh evening-reflect >> /var/log/bowlwanpi-cron.log 2>&1

# 睡眠提醒 - 每天 23:00
0 23 * * * root /root/.openclaw/workspace/scripts/backup-cron.sh sleep-reminder >> /var/log/bowlwanpi-cron.log 2>&1

# 周回顾 - 每周日 20:00
0 20 * * 0 root /root/.openclaw/workspace/scripts/backup-cron.sh weekly-review >> /var/log/bowlwanpi-cron.log 2>&1
```

---

## 10. 技能清单 (部分)

| 技能名 | 路径 | 功能 |
|--------|------|------|
| unified-memory | skills/unified-memory/ | 三系统统一记忆 |
| intelligent-search | skills/intelligent-search/ | 智能搜索聚合 |
| tencent-search | skills/tencent-search/ | 腾讯云 WSA 搜索 |
| memu-memory | skills/memu-memory/ | memU 云端记忆 |
| hippocampus-memory | skills/hippocampus-memory/ | 本地海马体记忆 |
| bilibili-hot-monitor | skills/bilibili-hot-monitor/ | B站热门监控 |
| doubao-tts | skills/doubao-tts/ | 豆包语音合成 |
| faster-whisper | skills/faster-whisper/ | 本地语音识别 |
| amygdala-memory | skills/amygdala-memory/ | 情感记忆系统 |

---

*配置文档完成*
