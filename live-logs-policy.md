# 实时日志展示策略（verifiable-only）

- 实时日志只展示可验证执行摘要。
- 允许来源仅限：`cron-runs`、`website-publisher`、`subagent-receipt`。
- 日志必须包含字段：`timestamp`、`source`、`status`（可附 `message`）。
- 不展示内部思维、推理过程或不可验证内容。
