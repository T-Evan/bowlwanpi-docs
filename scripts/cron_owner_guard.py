#!/usr/bin/env python3
"""Cron owner guard.

Checks Linux cron and OpenClaw cron against owner rules so each business task has
one scheduler owner.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_LINUX_CRON = Path("/etc/cron.d/bowlwanpi-backup-cron")
DEFAULT_WORKSPACE_CRON = Path("/root/.openclaw/workspace/cron/bowlwanpi-backup-cron")
DEFAULT_OPENCLAW_JOBS = Path("/root/.openclaw/cron/jobs.json")
DEFAULT_RULES = Path("/root/.openclaw/workspace/cron/owner-rules.json")
DEFAULT_REPORT_DIR = Path("/root/.openclaw/workspace/health-checks")


@dataclass
class RuleResult:
    task: str
    owner: str
    required: bool
    linux_active: bool
    openclaw_active: bool
    status: str
    detail: str


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_linux_cron(path: Path) -> list[str]:
    if not path.exists():
        return []

    active_lines: list[str] = []
    env_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if env_re.match(line):
            continue
        active_lines.append(line)

    return active_lines


def load_openclaw_enabled_jobs(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = load_json(path)
    jobs = data.get("jobs", [])
    return [j for j in jobs if j.get("enabled", True)]


def rule_match_linux(rule: dict[str, Any], lines: list[str]) -> bool:
    patterns = rule.get("linux_patterns", [])
    if not patterns:
        return False
    return any(any(p in line for p in patterns) for line in lines)


def rule_match_openclaw(rule: dict[str, Any], jobs: list[dict[str, Any]]) -> bool:
    names = set(rule.get("openclaw_names", []))
    ids = set(rule.get("openclaw_ids", []))
    if not names and not ids:
        return False

    for job in jobs:
        if job.get("id") in ids:
            return True
        if job.get("name") in names:
            return True
    return False


def evaluate_rule(rule: dict[str, Any], linux_lines: list[str], jobs: list[dict[str, Any]]) -> RuleResult:
    task = rule["task"]
    owner = rule.get("owner", "openclaw")
    required = bool(rule.get("required", True))

    linux_active = rule_match_linux(rule, linux_lines)
    openclaw_active = rule_match_openclaw(rule, jobs)

    if owner == "linux":
        if linux_active and not openclaw_active:
            return RuleResult(task, owner, required, linux_active, openclaw_active, "ok", "owner respected")
        if linux_active and openclaw_active:
            return RuleResult(task, owner, required, linux_active, openclaw_active, "conflict", "duplicate on both schedulers")
        if (not linux_active) and openclaw_active:
            return RuleResult(task, owner, required, linux_active, openclaw_active, "conflict", "running on wrong owner (openclaw)")
        status = "missing" if required else "optional-missing"
        return RuleResult(task, owner, required, linux_active, openclaw_active, status, "not active")

    if owner == "openclaw":
        if openclaw_active and not linux_active:
            return RuleResult(task, owner, required, linux_active, openclaw_active, "ok", "owner respected")
        if openclaw_active and linux_active:
            return RuleResult(task, owner, required, linux_active, openclaw_active, "conflict", "duplicate on both schedulers")
        if (not openclaw_active) and linux_active:
            return RuleResult(task, owner, required, linux_active, openclaw_active, "conflict", "running on wrong owner (linux)")
        status = "missing" if required else "optional-missing"
        return RuleResult(task, owner, required, linux_active, openclaw_active, status, "not active")

    # owner == either
    if linux_active and openclaw_active:
        return RuleResult(task, owner, required, linux_active, openclaw_active, "conflict", "duplicate on both schedulers")
    if linux_active or openclaw_active:
        return RuleResult(task, owner, required, linux_active, openclaw_active, "ok", "active on one scheduler")
    status = "missing" if required else "optional-missing"
    return RuleResult(task, owner, required, linux_active, openclaw_active, status, "not active")


def write_report(payload: dict[str, Any], report_dir: Path) -> tuple[Path, Path]:
    report_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = report_dir / f"cron_owner_guard_{ts}.json"
    md_path = report_dir / f"cron_owner_guard_{ts}.md"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Cron Owner Guard Report",
        "",
        f"- Generated: {payload['generatedAtUtc']}",
        f"- Linux cron file: `{payload['linuxCronFile']}`",
        f"- OpenClaw jobs file: `{payload['openclawJobsFile']}`",
        f"- Rules file: `{payload['rulesFile']}`",
        "",
        "| Task | Owner | Linux | OpenClaw | Status | Detail |",
        "|---|---|---|---|---|---|",
    ]

    for r in payload["results"]:
        lines.append(
            f"| {r['task']} | {r['owner']} | {'Y' if r['linuxActive'] else 'N'} | "
            f"{'Y' if r['openclawActive'] else 'N'} | {r['status']} | {r['detail']} |"
        )

    lines.extend(
        [
            "",
            f"- OK: {payload['summary']['ok']}",
            f"- Conflicts: {payload['summary']['conflicts']}",
            f"- Missing required: {payload['summary']['missingRequired']}",
            f"- Optional missing: {payload['summary']['optionalMissing']}",
            "",
        ]
    )

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Cron owner guard")
    parser.add_argument("--rules", default=str(DEFAULT_RULES))
    parser.add_argument("--linux-cron", default=str(DEFAULT_LINUX_CRON))
    parser.add_argument("--openclaw-jobs", default=str(DEFAULT_OPENCLAW_JOBS))
    parser.add_argument("--report", action="store_true", help="write JSON/MD report files")
    parser.add_argument("--report-dir", default=str(DEFAULT_REPORT_DIR))
    parser.add_argument("--check", action="store_true", help="return non-zero when conflicts exist")
    parser.add_argument("--quiet", action="store_true", help="print summary only")
    args = parser.parse_args()

    rules_path = Path(args.rules)
    linux_path = Path(args.linux_cron)
    openclaw_path = Path(args.openclaw_jobs)

    if not linux_path.exists() and DEFAULT_WORKSPACE_CRON.exists():
        linux_path = DEFAULT_WORKSPACE_CRON

    if not rules_path.exists():
        print(f"rules file not found: {rules_path}", file=sys.stderr)
        return 2

    rules_data = load_json(rules_path)
    rules = rules_data.get("rules", [])

    linux_lines = parse_linux_cron(linux_path)
    openclaw_jobs = load_openclaw_enabled_jobs(openclaw_path)

    results = [evaluate_rule(rule, linux_lines, openclaw_jobs) for rule in rules]

    summary = {
        "ok": sum(1 for r in results if r.status == "ok"),
        "conflicts": sum(1 for r in results if r.status == "conflict"),
        "missingRequired": sum(1 for r in results if r.status == "missing"),
        "optionalMissing": sum(1 for r in results if r.status == "optional-missing"),
    }

    payload = {
        "generatedAtUtc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "linuxCronFile": str(linux_path),
        "openclawJobsFile": str(openclaw_path),
        "rulesFile": str(rules_path),
        "summary": summary,
        "results": [
            {
                "task": r.task,
                "owner": r.owner,
                "required": r.required,
                "linuxActive": r.linux_active,
                "openclawActive": r.openclaw_active,
                "status": r.status,
                "detail": r.detail,
            }
            for r in results
        ],
    }

    if args.report:
        json_path, md_path = write_report(payload, Path(args.report_dir))
        if not args.quiet:
            print(f"report_json={json_path}")
            print(f"report_md={md_path}")

    if not args.quiet:
        for r in results:
            print(
                f"[{r.status}] {r.task}: owner={r.owner} "
                f"linux={'Y' if r.linux_active else 'N'} openclaw={'Y' if r.openclaw_active else 'N'} ({r.detail})"
            )

    print(
        "summary "
        f"ok={summary['ok']} conflicts={summary['conflicts']} "
        f"missing_required={summary['missingRequired']} optional_missing={summary['optionalMissing']}"
    )

    if args.check and (summary["conflicts"] > 0 or summary["missingRequired"] > 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
