# DAG Runner Quickstart (v0.1)

## 1) 运行方式
在工作区执行：

```bash
cd /root/.openclaw/workspace
python3 scripts/dag_runner.py \
  --dag docs/dag-examples/site-publish.v0.1.json \
  --dry-run
```

- `--dry-run`：只做拓扑调度与状态流转，不执行 shell 命令。
- 不带 `--dry-run`：按 DAG 节点实际执行 `command`。

## 2) 输出位置
- 运行历史写入：`docs/data/dag-runs.json`
- 每次 run 会追加一条记录（保留最近 100 条），包含：
  - run 状态
  - 节点状态（pending/in_progress/done/failed/skipped）
  - attempts/maxRetries
  - depOutputs（依赖输出透传）

## 3) DAG JSON 最小字段
每个节点最少需要：

```json
{
  "id": "node-id",
  "command": "echo hello",
  "deps": [],
  "maxRetries": 0
}
```

说明：
- `deps`：依赖节点 id 列表。
- `maxRetries`：失败后最多重试次数（不含首轮）。
- `mockFailures`（可选）：用于演示重试，表示前 N 次尝试强制失败（dry-run 也生效）。
- 依赖输出会在节点结果中写入 `depOutputs`，并注入环境变量 `DEP_OUTPUTS_JSON`。

## 4) 失败与跳过规则
- 节点失败且仍可重试：回到 `pending`。
- 重试耗尽：`failed`。
- 任一依赖 `failed`/`skipped`：下游节点 `skipped`。

## 5) 示例运行命令与预期结果

### 5.1 网站发布链路（site-publish）
```bash
cd /root/.openclaw/workspace
python3 scripts/dag_runner.py --dag docs/dag-examples/site-publish.v0.1.json --dry-run
```
预期：
- run `state=done`
- `generate -> validate -> publish -> notify` 全部 `done`

### 5.2 资讯链路（news-push）
```bash
cd /root/.openclaw/workspace
python3 scripts/dag_runner.py --dag docs/dag-examples/news-push.v0.1.json --dry-run
```
预期：
- run `state=done`
- `collect -> dedup -> summarize -> push` 全部 `done`

### 5.3 失败重试演示（retry-demo）
```bash
cd /root/.openclaw/workspace
python3 scripts/dag_runner.py --dag docs/dag-examples/retry-demo.v0.1.json --dry-run
```
预期：
- `flaky` 节点第 1 次失败，第 2 次成功（`attempts=2`）
- 下游 `after_retry` 正常执行，最终 run `state=done`
- 运行记录追加到 `docs/data/dag-runs.json`

## 6) 与现有流程的关系
- v0.1 是独立脚本，不会替换或破坏现有 cron/发布流程。
- 建议先在 dry-run 验证 DAG 设计，再切换到实跑。
