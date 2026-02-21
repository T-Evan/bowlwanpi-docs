# 回执保障机制 v1（非口头规矩）

## 目标
把“调度了但没回执”从人治变成机制约束：每个任务有票据、有超时催报、有结构化回执校验、有审计闭环。

## 四条硬约束

### 1) 任务票据（Task Ledger）
- 每次子代理调度前，必须在 `memory/task-ledger.json` 新增一条任务票据。
- 必填字段：`task_id`、`owner`、`status`、`created_at`、`updated_at`、`summary`。
- `status` 最小集合：`pending` / `running` / `closed` / `failed`。

### 2) 2/5 分钟超时催报
- 任务处于 `pending` 且超过 2 分钟：触发一级提醒（轻催报）。
- 任务处于 `pending` 且超过 5 分钟：触发二级提醒（升级提醒）。
- 催报只针对未关闭票据，避免噪音。

### 3) RESULT/RISKS/NEXT 字段校验
- 子代理回传必须包含结构化字段：
  - `RESULT`
  - `RISKS`
  - `NEXT`
- 若缺字段，任务不得标记 `closed`，应回到 `running` 并补齐回执。

### 4) 医生审计（Doctor Audit）
- `doctor_worker` 负责周期审计：
  - 扫描长期 `pending/running` 票据
  - 识别缺回执字段的异常关闭
  - 输出审计摘要并给修复建议

## 数据与脚本
- 账本：`memory/task-ledger.json`
- 催报脚本：`scripts/receipt_guard.py`
- 脚本职责：读取账本并输出超时告警摘要（2 分钟与 5 分钟分级）

## 最小落地规则
- 调度时：先写票据，再 spawn。
- 完成时：先做字段校验，再 `closed`。
- 日常：按 cron/心跳调用催报脚本，保持账本清洁。
