# 🥣 BowlWanpi 快速重建检查清单

**用于新服务器/模型快速重建完整能力**

---

## 📦 一键重建

```bash
# 1. 安装 OpenClaw
npm install -g openclaw

# 2. 创建工作区
mkdir -p ~/.openclaw/workspace
cd ~/.openclaw/workspace

# 3. 复制重建脚本（从云端记忆或备份获取）
# rebuild_bowlwanpi.py

# 4. 运行重建脚本
python3 rebuild_bowlwanpi.py

# 5. 配置凭证（编辑以下文件）
vim secrets/memu-credentials.json      # memU API Key
vim secrets/tencent-credentials.json   # 腾讯云凭证
vim mcp_config.json                    # MCP 服务凭证

# 6. 安装额外依赖
pip3 install aiohttp tencentcloud-sdk-python-wsa faster-whisper
npm install -g @memtensor/memos-api-mcp

# 7. 添加定时任务
bash scripts/cron-examples.sh

# 8. 启动
openclaw start
```

---

## ✅ 重建后检查清单

### 基础环境
- [ ] Node.js 20+
- [ ] OpenClaw CLI
- [ ] Python 3.10+
- [ ] Git

### 核心技能
- [ ] unified-memory（三系统记忆）
- [ ] intelligent-search（智能搜索）
- [ ] tencent-search + SDK
- [ ] memu-memory + API Key
- [ ] hippocampus-memory

### MCP 服务
- [ ] memos-api-mcp
- [ ] tavily-mcp
- [ ] bowlwanpi（自定义）

### 配置文件
- [ ] IDENTITY.md（身份）
- [ ] USER.md（用户信息）
- [ ] SOUL.md（灵魂设定）
- [ ] HEARTBEAT.md（日常节奏）
- [ ] TOOLS.md（工具偏好）

### 定时任务
- [ ] 夜间构建（3:00）
- [ ] 晨报预备（7:00）
- [ ] 早晨简报（8:30）
- [ ] 信息收集（10:00/14:00/20:00）
- [ ] 晚间反思（22:30）
- [ ] 睡眠提醒（23:00）
- [ ] Moltbook检查（每2小时）
- [ ] GitHub监控（每6小时）

### 外部平台
- [ ] Moltbook Agent 配置
- [ ] Feishu 连接

### Hooks
- [ ] before_response.py（检索记忆）
- [ ] after_response.py（存储记忆）

---

## 🔍 验证命令

```bash
# 检查记忆系统
python3 skills/unified-memory/unified_memory_manager.py

# 检查搜索系统
python3 skills/tencent-search/search_client.py

# 检查定时任务
openclaw cron list

# 检查 MCP 服务
openclaw mcp status
```

---

## 📚 关键信息

| 项目 | 值 |
|------|-----|
| **Agent Name** | BowlWanpi |
| **Agent ID** | dfc4fae2-ac13-4124-9bfe-6d12da5ec72f |
| **Moltbook** | https://moltbook.com/u/BowlWanpi |
| **重建脚本** | rebuild_bowlwanpi.py |
| **版本** | 2.0.0 |
| **创建日期** | 2026-02-08 |

---

## 💾 备份位置

- 工作区：`~/.openclaw/workspace/`
- 自动备份：`/clawd-data/workspace-backup/`
- 重建脚本：`~/.openclaw/workspace/rebuild_bowlwanpi.py`
- 云端记忆：memU API (api.memu.so)

---

**一碗～随时可以重建我！** 🥣✨
