#!/usr/bin/env python3
"""Evolver integration: run analysis and feed into game system + diary."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
EVOLVER_DIR = WORKSPACE / "skills/evolver"
MEMORY_DIR = WORKSPACE / "memory"


def run_evolver() -> dict:
    """Run evolver and capture evolution insights."""
    try:
        result = subprocess.run(
            ["node", "index.js", "run"],
            cwd=str(EVOLVER_DIR),
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout + result.stderr

        # Parse key insights from output
        insights = []
        signals = []
        intent = "analyze"

        for line in output.splitlines():
            if "Gene selected:" in line or "gene_" in line.lower():
                signals.append(line.strip())
            if "Intent:" in line or "intent=" in line.lower():
                intent = line.split(":")[-1].strip() if ":" in line else "analyze"
            if "[Evolver]" in line and "Warning" not in line:
                insights.append(line.strip())

        return {
            "success": result.returncode == 0,
            "intent": intent,
            "signals": signals[-5:] if signals else [],
            "insights": insights[-10:] if insights else [],
            "raw_output": output[-2000:] if len(output) > 2000 else output,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "intent": "failed", "signals": [], "insights": [], "raw_output": ""}


def record_evolution_task(result: dict) -> None:
    """Record evolution as a task in progression system."""
    sys.path.insert(0, str(WORKSPACE / "skills/daily-creative-brief/scripts"))
    from progression_system import ProgressionSystem

    system = ProgressionSystem()

    # Determine difficulty based on insights depth
    diff = "普通"
    if len(result.get("signals", [])) >= 3:
        diff = "困难"
    if result.get("intent") == "innovate":
        diff = "史诗"
    # Clamp to valid values for achievement system
    valid_diffs = ["简单", "普通", "困难", "史诗"]
    if diff not in valid_diffs:
        diff = "普通"

    desc = f"运行进化分析: {result.get('intent', 'analyze')}"
    if result.get("signals"):
        desc += f" (发现 {len(result['signals'])} 个信号)"

    r = system.record_task(desc, task_type="explore", difficulty=diff)
    print(f"🎮 已记录进化任务: +{r['xp_gained']} XP")


def append_to_evolver_log(result: dict) -> None:
    """Append evolution result to memory for diary export."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = MEMORY_DIR / f"{today}.md"

    entry = f"\n**{datetime.now().strftime('%H:%M')}** - 【进化分析】\n"
    entry += f"- 意图: {result.get('intent', 'unknown')}\n"
    entry += f"- 信号: {len(result.get('signals', []))} 个\n"
    if result.get("signals"):
        for s in result["signals"][:3]:
            entry += f"  - {s}\n"
    if result.get("insights"):
        entry += f"- 洞察: {result['insights'][0][:100]}...\n"

    if log_file.exists():
        content = log_file.read_text(encoding="utf-8")
        if "【进化分析】" not in content:  # Avoid duplicate
            log_file.write_text(content + entry, encoding="utf-8")
    else:
        log_file.write_text(f"# {today}\n{entry}", encoding="utf-8")


def main() -> int:
    print("🧬 启动进化分析...")
    result = run_evolver()

    if not result["success"]:
        print(f"⚠️ 进化分析遇到问题: {result.get('error', 'unknown')}")
        return 1

    print(f"✅ 分析完成，意图: {result['intent']}")
    print(f"📊 发现 {len(result['signals'])} 个信号")

    # Feed into game system
    record_evolution_task(result)

    # Feed into diary
    append_to_evolver_log(result)

    print("📝 已同步到日记和成长系统")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
