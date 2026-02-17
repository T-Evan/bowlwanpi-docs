# OpenClaw Cron Archive

This folder stores snapshots of OpenClaw cron jobs that were archived (removed from active scheduler).

- `disabled-jobs-20260217_132236Z.json`: snapshot of 17 disabled/legacy jobs archived on 2026-02-17.

Restore approach:
1. Open the snapshot JSON and copy needed job objects.
2. Recreate with `cron add` (or `cron update` on existing IDs if re-import tooling is available).
3. Keep `delivery.channel` and `delivery.to` aligned with current Feishu target format (`user:<open_id>`).
