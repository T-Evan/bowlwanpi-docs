# 🚀 BowlWanpi 快速重建指南

## ⚡ 5分钟快速启动

### 1. 基础环境
```bash
# Node.js v22+
npm i -g openclaw@latest

# Python 依赖
pip3 install memu-sdk faster-whisper requests beautifulsoup4

# 确认代理
systemctl status mihomo  # 确保 port 7890 可用
```

### 2. 恢复工作区
```bash
mkdir -p ~/.openclaw/workspace
cd ~/.openclaw/workspace
# 解压备份或使用 git clone
```

### 3. 配置凭证 (关键！)
```bash
mkdir -p secrets/
# 放置以下文件:
# - secrets/memu-credentials.json
# - secrets/tencent-credentials.json
# - mcp_config.json
```

### 4. 启动验证
```bash
openclaw gateway start
openclaw cron list  # 确认20个任务
```

---

## 📋 核心能力速查

| 功能 | 命令/方式 | 状态 |
|------|-----------|------|
| 搜索 | 直接提问 | ✅ 腾讯云WSA |
| TTS | 说"语音播报" | ✅ 豆包灿灿 |
| 记忆 | 自动同步 | ✅ MemOS+Hippo |
| 推送 | 定时自动 | ✅ 20个任务 |

---

## 🔧 故障排查

| 问题 | 解决 |
|------|------|
| 记忆上传失败 | 检查 MemOS API Key |
| 搜索无结果 | 检查腾讯云凭证 |
| 定时任务不执行 | openclaw cron list |
| TTS 失败 | 检查豆包凭证 |

---

## 📞 关键信息

- **Agent ID**: dfc4fae2-ac13-4124-9bfe-6d12da5ec72f
- **Moltbook**: https://moltbook.com/u/BowlWanpi
- **备份**: /clawd-data/workspace-backup/

---

详细文档见: [CAPABILITY_GUIDE.md](./CAPABILITY_GUIDE.md)
