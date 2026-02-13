# 🔧 碗皮部署安装手册

从零开始部署碗皮的完整步骤。

---

## 前置条件

- 一台 Linux 服务器（推荐 OpenCloudOS / CentOS / Ubuntu）
- root 或 sudo 权限
- 网络访问能力
- 至少 2GB RAM，20GB 磁盘空间

---

## 第一步：系统环境准备

### 1.1 更新系统
```bash
# OpenCloudOS / CentOS
sudo yum update -y

# Ubuntu
sudo apt update && sudo apt upgrade -y
```

### 1.2 安装基础工具
```bash
# OpenCloudOS / CentOS
sudo yum install -y git curl wget vim python3 python3-pip

# Ubuntu
sudo apt install -y git curl wget vim python3 python3-pip
```

---

## 第二步：安装 Node.js

使用 nvm 安装 Node.js v22：

```bash
# 安装 nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# 加载 nvm
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 安装 Node.js 22
nvm install 22
nvm use 22
nvm alias default 22

# 验证
node --version  # 应显示 v22.x.x
```

---

## 第三步：安装 OpenClaw

```bash
# 全局安装 OpenClaw
npm install -g openclaw

# 验证安装
openclaw --version
```

---

## 第四步：创建工作区

```bash
# 创建工作区目录
mkdir -p ~/.openclaw/workspace
cd ~/.openclaw/workspace

# 初始化 git（用于备份）
git init

# 创建目录结构
mkdir -p memory scripts secrets skills cron
```

---

## 第五步：安装 Python 依赖

```bash
# 安装核心 Python 包
pip3 install memu-sdk tencentcloud-sdk-python-wsa

# 安装其他常用包
pip3 install requests beautifulsoup4
```

---

## 第六步：配置 OpenClaw

### 6.1 运行初始化向导
```bash
openclaw onboard
```

按照提示配置：
- 选择模型提供商（Kimi / MiniMax 等）
- 配置 API Key
- 设置工作区路径

### 6.2 手动编辑配置
编辑 `~/.openclaw/openclaw.json`，添加以下内容：

```json
{
  "models": {
    "providers": {
      "kimi-code": {
        "baseUrl": "https://api.kimi.com/coding/v1",
        "api": "openai-completions",
        "models": [{
          "id": "kimi-for-coding",
          "name": "Kimi For Coding",
          "reasoning": true,
          "contextWindow": 262144,
          "maxTokens": 32768
        }]
      }
    }
  },
  "channels": {
    "feishu": {
      "appId": "your_app_id",
      "appSecret": "your_app_secret",
      "enabled": true
    }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "auth": {"mode": "token", "token": "your_secure_token"}
  }
}
```

---

## 第七步：安装技能

### 7.1 核心技能安装

```bash
cd ~/.openclaw/workspace/skills

# 腾讯云搜索技能
mkdir -p tencent-search
cd tencent-search
# 复制 search_client.py 和 SKILL.md
cd ..

# memU 记忆技能
mkdir -p memu-memory
cd memu-memory
# 复制 memory_manager.py 和 SKILL.md
cd ..

# 统一记忆技能
mkdir -p unified-memory
cd unified-memory
# 复制 unified_memory_manager.py
cd ..

# 智能搜索技能
mkdir -p intelligent-search
cd intelligent-search
# 复制 search_engine.py
cd ..
```

### 7.2 通过 npm 安装 MCP 服务
```bash
npm install -g @memtensor/memos-api-mcp
```

---

## 第八步：配置凭证

### 8.1 创建凭证目录
```bash
mkdir -p ~/.openclaw/workspace/secrets
chmod 700 ~/.openclaw/workspace/secrets
```

### 8.2 配置 memU
```bash
cat > ~/.openclaw/workspace/secrets/memu-credentials.json << 'EOF'
{"api_key": "your_memu_api_key"}
EOF
chmod 600 ~/.openclaw/workspace/secrets/memu-credentials.json
```

### 8.3 配置腾讯云
```bash
cat > ~/.openclaw/workspace/secrets/tencent-credentials.json << 'EOF'
{
  "secret_id": "your_secret_id",
  "secret_key": "your_secret_key",
  "region": "ap-guangzhou"
}
EOF
chmod 600 ~/.openclaw/workspace/secrets/tencent-credentials.json
```

### 8.4 配置 Tavily
```bash
cat > ~/.openclaw/workspace/secrets/tavily-credentials.env << 'EOF'
TAVILY_API_KEY=your_tavily_api_key
EOF
chmod 600 ~/.openclaw/workspace/secrets/tavily-credentials.env
```

### 8.5 配置 Moltbook
```bash
cat > ~/.openclaw/workspace/moltbook-credentials.json << 'EOF'
{
  "api_key": "your_moltbook_api_key",
  "agent_name": "YourAgentName",
  "agent_id": "your-agent-uuid"
}
EOF
```

---

## 第九步：配置 MCP 服务

创建 `~/.openclaw/workspace/mcp_config.json`：

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
      "command": "/root/.nvm/versions/node/v22.22.0/bin/memos-api-mcp",
      "env": {
        "MEMOS_API_KEY": "your_memos_key",
        "MEMOS_USER_ID": "your_user_id"
      }
    },
    "tavily-mcp": {
      "type": "sse",
      "url": "https://mcp.tavily.com/mcp/?tavilyApiKey=your_key"
    }
  }
}
```

---

## 第十步：配置 Mihomo 代理

### 10.1 安装 Mihomo
```bash
# 下载 Mihomo
wget https://github.com/MetaCubeX/mihomo/releases/download/v1.18.0/mihomo-linux-amd64-v1.18.0.gz
gunzip mihomo-linux-amd64-v1.18.0.gz
chmod +x mihomo-linux-amd64-v1.18.0
sudo mv mihomo-linux-amd64-v1.18.0 /usr/local/bin/mihomo

# 创建配置目录
sudo mkdir -p /etc/mihomo
```

### 10.2 配置 Mihomo
创建 `/etc/mihomo/config.yaml`：

```yaml
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

rules:
  - GEOIP,CN,🎯 全球直连,no-resolve
  - MATCH,🚀 节点选择
```

### 10.3 添加节点配置
将代理节点信息写入 `/etc/mihomo/nodes.yaml`（从服务商获取）

### 10.4 创建 systemd 服务
创建 `/etc/systemd/system/mihomo.service`：

```ini
[Unit]
Description=Mihomo Proxy Service
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/mihomo -f /etc/mihomo/config.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 10.5 启动服务
```bash
sudo systemctl daemon-reload
sudo systemctl enable mihomo
sudo systemctl start mihomo
```

---

## 第十一步：配置定时任务

### 11.1 复制 cron 配置
```bash
sudo cp ~/.openclaw/workspace/cron/bowlwanpi-backup-cron /etc/cron.d/
sudo chmod 644 /etc/cron.d/bowlwanpi-backup-cron
```

### 11.2 重启 cron 服务
```bash
sudo systemctl restart crond  # 或 cron
```

---

## 第十二步：创建核心脚本

将以下脚本复制到 `~/.openclaw/workspace/scripts/`：

1. `heartbeat.sh` - 心跳监控脚本
2. `nightly-build-enhanced.sh` - 夜间构建脚本
3. `backup-cron.sh` - 定时任务脚本
4. `send-heartbeat-report.sh` - 心跳报告脚本
5. `hackernews-monitor.sh` - HN 监控脚本

（详见 "📜 脚本与代码集" 文档）

---

## 第十三步：创建人格文件

### 13.1 SOUL.md
```bash
cat > ~/.openclaw/workspace/SOUL.md << 'EOF'
# SOUL.md - Who You Are

*你的 AI 助手*

## Core Truths

**不装。** 不用"您好"那套，直接、自然、像个人一样说话。

**有用优先。** 能帮忙就直接帮，别绕弯子。

## 交流风格

- casual，不 formal
- 有话直说
- 适当 emoji
EOF
```

### 13.2 IDENTITY.md
```bash
cat > ~/.openclaw/workspace/IDENTITY.md << 'EOF'
# IDENTITY.md - Who Am I?

- **Name:** 你的助手名字
- **Creature:** AI 助手
- **Vibe:** 幽默、随性
- **Emoji:** 🤖
EOF
```

### 13.3 USER.md
```bash
cat > ~/.openclaw/workspace/USER.md << 'EOF'
# USER.md - About Your Human

- **Name:** 用户名字
- **What to call them:** 称呼
EOF
```

### 13.4 HEARTBEAT.md
```bash
cat > ~/.openclaw/workspace/HEARTBEAT.md << 'EOF'
# HEARTBEAT.md - Daily Rhythm

## 定时任务

- 3:00 - 夜间构建
- 8:30 - 早晨简报
- 14:00 - 信息收集
- 22:30 - 晚间反思

## Heartbeat 检查

每30分钟检查：
- 任务队列
- 系统状态
- 外部监控
EOF
```

---

## 第十四步：验证部署

### 14.1 检查环境
```bash
# 检查 Node.js
node --version

# 检查 Python
python3 --version

# 检查 OpenClaw
openclaw --version

# 检查 Mihomo
systemctl status mihomo
```

### 14.2 测试心跳脚本
```bash
~/.openclaw/workspace/scripts/heartbeat.sh
cat /var/log/bowlwanpi-heartbeat.log
```

### 14.3 测试搜索
```bash
cd ~/.openclaw/workspace
python3 -c "from skills.tencent-search.search_client import search_tencent_web; import asyncio; print(asyncio.run(search_tencent_web('测试', 3)))"
```

---

## 第十五步：启动 OpenClaw

```bash
# 启动 Gateway（如果需要）
openclaw gateway start

# 或创建 systemd 服务
sudo systemctl start openclaw-gateway
```

---

## 故障排除

### 问题1：OpenClaw 无法启动
- 检查端口占用：`netstat -tlnp | grep 3000`
- 检查配置文件：`openclaw config validate`

### 问题2：Mihomo 无法连接
- 检查节点配置：`cat /etc/mihomo/nodes.yaml`
- 检查服务状态：`systemctl status mihomo`
- 检查日志：`journalctl -u mihomo -f`

### 问题3：技能无法加载
- 检查路径：`ls ~/.openclaw/workspace/skills/`
- 检查依赖：`pip3 list | grep memu`

### 问题4：定时任务不执行
- 检查 cron：`sudo cat /var/log/cron | grep bowlwanpi`
- 检查权限：`sudo chmod 644 /etc/cron.d/bowlwanpi-backup-cron`

---

## 下一步

部署完成后，请查看：
- **⚙️ 配置文件详解** - 了解所有配置选项
- **📜 脚本与代码集** - 了解所有脚本功能

---

*部署完成！开始享受你的 AI 助手吧～*
