---
name: website-publisher
description: "个人网站更新与发布技能。一键更新网站数据、生成动态内容、部署到 GitHub Pages。支持数据文件生成、HTML更新、自动化部署。"
---

# Website Publisher 技能

个人网站（GitHub Pages）的更新与发布自动化工具。

## 🚀 快速开始

### 更新网站数据（本地）

```bash
# 更新所有数据文件和 HTML
cd /root/.openclaw/workspace && python3 skills/website-publisher/scripts/update.py

# 仅更新特定数据
cd /root/.openclaw/workspace && python3 skills/website-publisher/scripts/update.py --only stats
```

### 部署到 GitHub Pages

```bash
# 完整流程：更新 + 部署
cd /root/.openclaw/workspace && python3 skills/website-publisher/scripts/deploy.py

# 仅部署（不更新数据）
cd /root/.openclaw/workspace && python3 skills/website-publisher/scripts/deploy.py --skip-update
```

### 完整发布流程

```bash
# 更新所有内容并部署
python3 skills/website-publisher/scripts/publish.py
```

## 📋 功能模块

### 1. 数据文件生成

| 文件 | 说明 |
|------|------|
| `data/skills.json` | 技能列表与数量 |
| `data/cron.json` | 定时任务列表 |
| `data/stats.json` | 系统统计（技能/任务/记忆/向量） |
| `data/trends.json` | 趋势图表数据（技能增长/情感趋势） |
| `data/game-system.json` | 游戏系统状态 |
| `data/selfies.json` | 自拍照数据 |
| `data/diary.json` | 日记条目 |
| `data/daily-quotes.json` | 每日格言 |
| `data/skill-usage.json` | 技能使用统计 |
| `data/error-stats.json` | 错误率统计 |
| `data/learning-progress.json` | 学习进度 |

### 2. HTML 内容更新

- 统计数字更新（技能数量、任务数量等）
- 时间戳更新（最后更新时间、构建版本）
- 向量数量显示更新

### 3. GitHub Pages 部署

- 自动提交变更
- 推送到 gh-pages 分支
- 生成发布日志

## 🔧 命令参考

### update.py

```bash
python3 skills/website-publisher/scripts/update.py [选项]

选项:
  --only {stats,skills,cron,trends,all}  仅更新特定数据
  --skip-html                           跳过 HTML 更新
  --dry-run                             模拟运行，不实际写入
```

### deploy.py

```bash
python3 skills/website-publisher/scripts/deploy.py [选项]

选项:
  --skip-update     跳过数据更新步骤
  --message "msg"   自定义提交信息
  --dry-run         模拟运行，不实际推送
```

### publish.py

```bash
python3 skills/website-publisher/scripts/publish.py [选项]

选项:
  --message "msg"   自定义发布信息
  --dry-run         模拟运行
```

## 📁 文件结构

```
skills/website-publisher/
├── SKILL.md                 # 本文件
├── scripts/
│   ├── update.py           # 数据更新脚本
│   ├── deploy.py           # 部署脚本
│   └── publish.py          # 完整发布脚本
└── templates/              # 模板文件（可选）
```

## ⚙️ 配置

### 环境变量

```bash
export WEBSITE_WORKSPACE="/root/.openclaw/workspace"      # 工作目录
export WEBSITE_DOCS="/root/.openclaw/workspace/docs"      # 网站源文件
export WEBSITE_REPO="https://github.com/T-Evan/bowlwanpi-docs.git"  # 部署仓库
```

### GitHub Token

部署需要配置 GitHub Token：

```bash
# 配置 git 使用 token
git remote set-url origin https://USERNAME:TOKEN@github.com/T-Evan/bowlwanpi-docs.git
```

## 🔄 集成到夜间构建

在 `nightly-cleanup.sh` 中使用：

```bash
# 更新网站
python3 skills/website-publisher/scripts/update.py

# 部署网站
python3 skills/website-publisher/scripts/deploy.py --skip-update
```

## 📊 更新内容示例

执行后会更新以下内容：

```
📝 生成动态数据文件...
  ✅ 技能列表已生成 (23 skills)
  ✅ 定时任务列表已生成 (18 tasks)
  ✅ 统计数据已生成
  ✅ 趋势数据已更新
  ✅ 每日格言已生成

🌐 更新网站 HTML 内容...
  ✅ 统计数字已更新
  ✅ 时间戳已更新
  ✅ 向量数量已更新

🚀 部署到 GitHub Pages...
  ✅ 变更已提交
  ✅ 推送成功
  🔗 https://t-evan.github.io/bowlwanpi-docs/
```

## 🛠️ 故障排查

### 部署失败

**问题**: GitHub Token 过期或无效

**解决**:
```bash
# 检查远程 URL
git remote -v

# 更新 Token
git remote set-url origin https://T-Evan:NEW_TOKEN@github.com/T-Evan/bowlwanpi-docs.git
```

### 数据未更新

**问题**: 源文件不存在或路径错误

**解决**:
```bash
# 检查工作目录
ls -la /root/.openclaw/workspace/docs/

# 手动运行更新
python3 skills/website-publisher/scripts/update.py --dry-run
```

### HTML 更新失败

**问题**: sed 命令不兼容或文件编码问题

**解决**:
- 检查 index.html 是否存在
- 确认文件编码为 UTF-8
- 查看详细错误日志

## 📝 更新日志

### v1.0.0
- 初始版本
- 支持数据文件生成
- 支持 HTML 更新
- 支持 GitHub Pages 部署

## 📄 License

MIT
