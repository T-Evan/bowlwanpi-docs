---
name: daily-creative-brief
description: Daily creative inspiration generator for AI agents. Combines memory analysis, trend insights, creative challenges, and micro-content creation to boost agent creativity.
triggers:
  - pattern: "(?i)(creative brief|daily inspiration|creativity boost|灵感|创造挑战|今日挑战)"
  - pattern: "(?i)(generate idea|creative mode|brainstorm|创造力)"
  - pattern: "(?i)(创造面板|dashboard|追踪|进度|成就)"
  - pattern: "(?i)(快速记录|灵感记录|quick create|quick idea)"
---

# Daily Creative Brief 🎨

每日创意简报生成器 - 让 AI 助手保持创造力满格！

## Features

- 🧠 **记忆关联**: 从历史对话中提取灵感线索
- 🔥 **趋势洞察**: 分析 AI 圈最新动态
- 🎯 **创造挑战**: 生成今日实践任务
- ✍️ **微内容**: 生成可分享的创意内容
- 📊 **追踪面板**: 可视化展示创造进度
- ⚡ **快速工具**: 快速记录灵感、代码、笔记

## Usage

### 生成简报
```bash
python3 scripts/generate_brief.py
```

### 查看面板
```bash
python3 scripts/dashboard.py
```

### 快速创造
```bash
# 灵感、代码、笔记、社交媒体内容、链接收藏
python3 scripts/quick_create.py [type] [args]
```

### 记录完成
```bash
python3 scripts/log_creation.py "完成了XX"
```

## Components

1. **Memory Miner** - 挖掘记忆找灵感
2. **Trend Analyzer** - 分析趋势找方向  
3. **Challenge Generator** - 生成创造任务
4. **Content Crafter** - 创作微内容
5. **Progress Dashboard** - 追踪创造进度
6. **Quick Tools** - 快速记录各种创意
