# HEARTBEAT.md - 简化版

> 精简执行清单，30秒内决策，不废话。

## ⚡ 心跳检查流程（每30分钟）

### Step 1: 读任务队列
- `memory/task-queue.json` 有待办？→ **执行** → 汇报
- 没有 → 继续

### Step 2: 读心跳日志
- `/var/log/bowlwanpi-heartbeat.log` 有异常？→ **报告**
- 正常 → 继续

### Step 3: 5分钟简报检查
- 距离上次汇报 ≥5分钟？→ **发送简报** → 更新时间戳
- 不足 → 回 `HEARTBEAT_OK`

---

## 📋 快捷命令

| 场景 | 行动 |
|-----|------|
| 有待办任务 | 执行 → "完成 xxx" |
| 系统异常 | 报告 → "⚠️ 发现 xxx 异常" |
| 正常状态 | `HEARTBEAT_OK` |
| 深夜(23-8点) | 仅报告严重异常 |

---

## 📁 关键文件位置

```
memory/
  ├── task-queue.json          # 待办任务
  ├── heartbeat-last-report.json  # 上次汇报时间
  ├── daily-findings.md        # 今日发现
  └── YYYY-MM-DD.md           # 每日记忆

/var/log/bowlwanpi-heartbeat.log  # 系统心跳
/tmp/bowlwanpi-hackernews-pending.txt  # HN 待推送
```

---

## 🎯 执行原则

1. **不等待** - 有活就干，不请示
2. **不啰嗦** - 结果导向，一句话汇报
3. **不打扰** - 深夜只报严重问题

---

## 🌙 夜间构建（03:00）

自动运行，无需干预：
- `scripts/nightly-cleanup.sh`
- 清理 health-checks
- 提交 git
- 创建今日记忆文件

---

*我是 BowlWanpi，一碗的小埋～*
