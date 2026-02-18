#!/usr/bin/env python3
"""早晨简报推送脚本（含成本日报摘要）。"""

from __future__ import annotations

from datetime import datetime
import re
import subprocess

COST_SCRIPT = "/root/.openclaw/workspace/skills/openclaw-cost-guard/scripts/extract_cost.py"


def get_today_cost_line() -> str:
    try:
        result = subprocess.run(
            ["python3", COST_SCRIPT, "--today"],
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        )
        lines = [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]
        if not lines:
            return "• 今日费用：暂无数据"

        # Example: 2026-02-18  calls=50  cost=$0.1234
        m = re.search(r"calls=(\d+)\s+cost=\$(\d+\.\d+)", lines[0])
        if m:
            calls = m.group(1)
            cost = m.group(2)
            return f"• 今日费用：${cost}（调用 {calls} 次）"
        return f"• 今日费用：{lines[0]}"
    except Exception:
        return "• 今日费用：统计失败（稍后重试）"


if __name__ == "__main__":
    print("🌅 早晨简报 | {}".format(datetime.now().strftime("%Y-%m-%d %H:%M")))
    print("=" * 50)
    print("\n📋 今日计划：")
    print("• 8:00 网易云日推 🎵")
    print("• 8:30 微博热搜 🔥")
    print("• 9:00 Product Hunt 🔥")
    print("• 12:00 B站热门 📺")
    print("• 22:30 晚间反思 💭")
    print("• 23:00 睡眠提醒 💤")
    print("\n💰 成本日报：")
    print(get_today_cost_line())
    print("\n推送完成！")
