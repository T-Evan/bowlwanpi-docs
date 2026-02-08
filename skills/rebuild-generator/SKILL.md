---
name: rebuild-generator
description: 重建手册生成器 - 自动扫描当前能力状态，生成重建摘要并上传到记忆系统
---

# 🥣 重建手册生成器 (rebuild-generator)

## 功能

自动完成以下任务：
1. 🔍 扫描当前技能、MCP服务、记忆系统等能力状态
2. 📝 生成重建摘要文档
3. 💾 保存本地副本到 memory/rebuild-summary-YYYY-MM-DD.md
4. ☁️ 上传重建信息到三记忆系统（memU + Hippocampus + MemOS）

## 使用方法

### 手动运行

```bash
cd /root/.openclaw/workspace
python3 skills/rebuild-generator/rebuild_generator.py
```

### 定时任务配置

建议在以下时机自动运行：
- 夜间构建（3:00）- 每日更新能力快照
- 技能变更后 - 手动触发

## 输出

### 本地文件
- 位置: `memory/rebuild-summary-YYYY-MM-DD.md`
- 包含: 当前所有能力清单、重建关键信息

### 云端记忆
- 存储到三记忆系统
- 重要度: 0.9 (高)
- 用途: 新服务器重建时可检索

## 依赖

- unified-memory
- memu-memory
- hippocampus-memory

## 创建时间

2026-02-08
