# 🥣 BowlWanpi 重建摘要（UTC）

- 任务: cron:63fbb8ef-726f-4918-9fd8-f4ee796e1a93（重建手册生成）
- 生成时间: 2026-02-16 18:24 UTC
- 执行环境: /root/.openclaw/workspace

## 1) 任务执行结果

- 重建手册生成器已执行: `python3 skills/rebuild-generator/rebuild_generator.py`
- 为匹配 UTC 日期再次执行: `TZ=UTC python3 skills/rebuild-generator/rebuild_generator.py`
- 本地摘要文件: `memory/rebuild-summary-2026-02-16.md` ✅
- 三记忆系统上传状态（生成器回执）:
  - memU: ✅
  - Hippocampus: ✅
  - MemOS: ✅

## 2) 当前能力扫描快照

### 技能系统

- 技能目录总数: 34
- 含 `SKILL.md` 的标准技能数: 30
- 技能列表:
  - .clawhub
  - advanced-skill-creator
  - ai-brain-builder
  - amygdala-memory
  - batch-processor
  - bilibili-hot-monitor
  - daily-creative-brief
  - ddg-search
  - doubao-tts
  - faster-whisper
  - friction-detector
  - hippocampus-memory
  - indirect-prompt-injection
  - intelligent-search
  - mcp-tools
  - memu-memory
  - one-minute-news
  - openclaw-assistant-guide
  - openclaw-cost-guard
  - personal-analytics
  - rebuild-generator
  - robbyczgw-cla
  - sag
  - security-check
  - self-improving-agent
  - session-cost
  - skills
  - summarize
  - tavily
  - tavily-skills
  - tencent-search
  - ttrpg-gm
  - unified-memory
  - volcengine-fusion-search

### MCP 服务

- MCP 配置源: `config/mcp_config.json`
- MCP 服务总数: 3
- 服务列表:
  - bowlwanpi
  - memos-api-mcp
  - tavily-mcp

### 记忆系统

- unified-memory 模块: ✅ (`skills/unified-memory/unified_memory_manager.py`)
- memU 凭证文件: ✅ (`secrets/memu-credentials.json`)
- Hippocampus 本地存储: ✅ (`memory/hippocampus.jsonl`)
- MemOS 待上传队列文件: ✅ (`memory/memos-pending-upload.jsonl`)
- 本次上传回执: memU ✅ / Hippocampus ✅ / MemOS ✅

### 网关与通道

- Gateway 状态: running（openclaw gateway status）
- 启用通道: telegram, feishu
- 启用插件: qqbot, dingtalk, wecom, telegram, feishu, minimax-portal-auth
- 配置告警: 检测到 `feishu` duplicate plugin id（建议后续清理重复来源）

## 3) 重建关键路径

- 主配置: `/root/.openclaw/openclaw.json`
- 重建脚本: `scripts/rebuild_bowlwanpi.py`
- 重建检查清单: `REBUILD_CHECKLIST.md`
- 备份目录: `/clawd-data/workspace-backup/`
- Git 仓库: `/root/.openclaw/workspace/.git`

## 4) 备注

- 生成器原始逻辑默认按本地时区命名文件，会生成 `2026-02-17` 版本；本次已额外生成 UTC 日期版本 `2026-02-16`，便于 cron（UTC）对齐。
- `openclaw cron list` 当前出现 gateway timeout，建议在低负载时复查 cron 作业可见性。

---
自动维护任务完成。
