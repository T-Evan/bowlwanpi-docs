# Multi-Agent DAG v0.1（最小试点）

## 目标（只做最小闭环）
- 让现有主代理 + 子代理 + cron 从“串行口头编排”变成“可追踪 DAG 编排”。
- 覆盖两条高频链路：
  1) 网站发布链路（内容生成 -> 校验 -> 发布 -> 通知）
  2) 资讯链路（抓取 -> 去重 -> 摘要 -> 分发）
- 结果要求：可重试、可恢复、可观察（状态/日志/失败原因）。

## DAG 节点状态机
最小状态集合：
- `PENDING`：等待依赖完成
- `READY`：依赖已满足，可被调度
- `RUNNING`：执行中
- `SUCCESS`：执行成功
- `FAILED_RETRYABLE`：失败，可重试
- `FAILED_FINAL`：重试耗尽/不可重试
- `SKIPPED`：被上游策略跳过（如校验失败后不发布）

状态流转：
- `PENDING -> READY -> RUNNING -> SUCCESS`
- `RUNNING -> FAILED_RETRYABLE -> READY`（按退避重试）
- `RUNNING -> FAILED_FINAL`
- `READY/PENDING -> SKIPPED`（由策略判定）

## 失败与重试策略（务实版）
- 节点级字段：`retry.maxAttempts`、`retry.backoffSec`、`retry.backoffFactor`。
- 默认建议：`maxAttempts=3`，`backoffSec=30`，`backoffFactor=2`。
- 不同错误类型：
  - 网络/超时：可重试
  - 参数错误/数据校验失败：不可重试（直接 `FAILED_FINAL`）
- 幂等要求：每个节点以 `runId + nodeId` 写入结果，重复执行不重复副作用（尤其发布和通知）。

## 与现有体系集成
- 主代理（qmd）：
  - 负责创建 DAG run（写入 run 元数据、初始节点状态）。
  - 负责收尾汇总和异常升级（人工介入提示）。
- 子代理（sessions_spawn）：
  - 每个 `RUNNING` 节点映射为一个子代理任务（或脚本任务）。
  - 子代理完成后回写节点结果（`SUCCESS/FAILED_*` + 输出）。
- cron：
  - 每 1-5 分钟触发“调度心跳”：扫描 `READY` 节点并派发。
  - 可保留现有业务 cron，不冲突；DAG 只接管多步骤链路。
- 通知（message）：
  - 仅在 run 完成或失败终止时发通知，避免噪音。

---

## 可执行 JSON 示例 1：网站发布链路

```json
{
  "dagId": "site-publish-v01",
  "runId": "run-20260221-website-001",
  "context": {
    "workspace": "/root/.openclaw/workspace",
    "channel": "whatsapp"
  },
  "nodes": [
    {
      "id": "generate",
      "kind": "agent",
      "task": "生成网站数据文件并更新 docs/data",
      "deps": [],
      "retry": { "maxAttempts": 2, "backoffSec": 20, "backoffFactor": 2 }
    },
    {
      "id": "validate",
      "kind": "shell",
      "command": "python3 skills/website-publisher/scripts/update.py --dry-run",
      "deps": ["generate"],
      "retry": { "maxAttempts": 2, "backoffSec": 30, "backoffFactor": 2 }
    },
    {
      "id": "publish",
      "kind": "shell",
      "command": "python3 skills/website-publisher/scripts/publish.py",
      "deps": ["validate"],
      "retry": { "maxAttempts": 3, "backoffSec": 30, "backoffFactor": 2 }
    },
    {
      "id": "notify",
      "kind": "message",
      "template": "网站发布完成：{{runId}}",
      "deps": ["publish"],
      "retry": { "maxAttempts": 1, "backoffSec": 5, "backoffFactor": 1 }
    }
  ],
  "policy": {
    "onFailure": "stop",
    "skipDownstreamOnFailed": true
  }
}
```

执行说明（最小实现）：
- 调度器每轮挑选 `READY` 节点；
- `kind=agent` 用 `sessions_spawn`；`kind=shell` 用 `exec`；`kind=message` 用 `message.send`；
- 每个节点落盘 `runs/<runId>.json` 记录状态和输出。

## 可执行 JSON 示例 2：资讯链路

```json
{
  "dagId": "news-brief-v01",
  "runId": "run-20260221-news-001",
  "context": {
    "topic": "AI 热点",
    "target": "daily-brief"
  },
  "nodes": [
    {
      "id": "collect",
      "kind": "shell",
      "command": "python3 scripts/push_cn_hot_topics.py --collect-only",
      "deps": [],
      "retry": { "maxAttempts": 3, "backoffSec": 20, "backoffFactor": 2 }
    },
    {
      "id": "dedup",
      "kind": "shell",
      "command": "python3 scripts/push_cn_hot_topics.py --dedup",
      "deps": ["collect"],
      "retry": { "maxAttempts": 2, "backoffSec": 15, "backoffFactor": 2 }
    },
    {
      "id": "summarize",
      "kind": "agent",
      "task": "将今日热点整理成 5 条摘要，含来源与一句点评",
      "deps": ["dedup"],
      "retry": { "maxAttempts": 2, "backoffSec": 30, "backoffFactor": 2 }
    },
    {
      "id": "distribute",
      "kind": "message",
      "template": "今日资讯简报已生成并推送",
      "deps": ["summarize"],
      "retry": { "maxAttempts": 1, "backoffSec": 5, "backoffFactor": 1 }
    }
  ],
  "policy": {
    "onFailure": "continue-noncritical",
    "criticalNodes": ["collect", "dedup", "summarize"]
  }
}
```

---

## 落地步骤

### 今天可做（v0.1）
1. 建立 `runs/` 目录与最小 run schema（run 状态 + 节点状态 + 输出）。
2. 写一个 200-300 行调度脚本（Python/Node 均可）：
   - 读取 DAG JSON
   - 计算 `READY`
   - 调用 `sessions_spawn` / `exec` / `message`
   - 回写状态
3. 用网站发布链路跑通一次，确保失败可重试，成功能通知。

### 本周可做（v0.2）
1. 补可视化：`docs/data/dag-runs.json` + 简单页面展示节点状态。
2. 支持并发上限（如同时最多 2 个 `RUNNING` 节点）。
3. 增加人工闸门节点（例如发布前人工确认）。
4. 增加失败分类与告警模板（网络失败/数据错误/权限错误）。

## 边界（本版不做）
- 不引入复杂分布式队列。
- 不做跨机器一致性锁。
- 不做多租户隔离（先单 workspace 可用）。
