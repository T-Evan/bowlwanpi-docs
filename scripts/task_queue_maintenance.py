#!/usr/bin/env python3
"""Task queue lifecycle maintenance.

- Archives pending_confirmation tasks that are overdue by deadline.
- Archives stale pending_confirmation tasks by age (default 3 days).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


QUEUE_FILE = Path("/root/.openclaw/workspace/memory/task-queue.json")
REPORT_FILE = Path("/tmp/bowlwanpi-task-queue-maintenance.txt")


@dataclass
class ArchiveResult:
    task_id: str
    reason: str


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        if "T" in value:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        # Treat date-only as end of day UTC
        return datetime.fromisoformat(value + "T23:59:59+00:00")
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Maintain task queue lifecycle")
    parser.add_argument("--queue", default=str(QUEUE_FILE))
    parser.add_argument("--stale-days", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    queue_path = Path(args.queue)
    if not queue_path.exists():
        REPORT_FILE.write_text("ℹ️ task queue not found, skipped\n", encoding="utf-8")
        return 0

    data: dict[str, Any] = json.loads(queue_path.read_text(encoding="utf-8"))
    tasks = data.get("tasks", [])
    completed = data.get("completed", [])

    now = datetime.now(timezone.utc)
    stale_seconds = args.stale_days * 86400
    remain: list[dict[str, Any]] = []
    archived: list[ArchiveResult] = []

    for task in tasks:
        status = str(task.get("status", "")).lower()
        if status != "pending_confirmation":
            remain.append(task)
            continue

        created = parse_date(str(task.get("created", "")))
        deadline = parse_date(str(task.get("deadline", "")))

        reason = ""
        if deadline and deadline < now:
            reason = "overdue_deadline"
        elif created and (now - created).total_seconds() > stale_seconds:
            reason = f"stale_pending_confirmation_{args.stale_days}d"

        if not reason:
            remain.append(task)
            continue

        archived_task = dict(task)
        archived_task["status"] = "archived_auto"
        archived_task["archived_at"] = now.isoformat().replace("+00:00", "Z")
        archived_task["archive_reason"] = reason
        completed.append(archived_task)
        archived.append(ArchiveResult(task_id=str(task.get("id", "unknown")), reason=reason))

    if archived and not args.dry_run:
        data["tasks"] = remain
        data["completed"] = completed
        data["lastUpdated"] = now.strftime("%Y-%m-%d")
        queue_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if archived:
        lines = ["🧹 task queue lifecycle:"]
        for item in archived:
            lines.append(f"- archived {item.task_id}: {item.reason}")
        REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        REPORT_FILE.write_text("✅ task queue lifecycle: no stale pending_confirmation tasks\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
