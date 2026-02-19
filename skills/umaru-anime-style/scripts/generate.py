#!/usr/bin/env python3
"""Generate fixed 'anime texture' style images via beauty-generation-api wrapper."""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
from datetime import datetime
from pathlib import Path

BASE = (
    "Premium anime-style girl portrait, anime texture, clean lineart, rich cel-shading, "
    "long flowing golden-orange hair, large amber eyes, oversized orange hoodie, "
    "warm cinematic lighting"
)


def build_prompt(scene: str, mood: str, action: str, mode: str, expression: str, persona: str) -> str:
    parts = [BASE]

    if persona:
        parts.append(persona)
    if mood:
        parts.append(f"{mood} expression")
    if expression:
        parts.append(expression)

    # Mirror mode is better for full-body / outfit storytelling; direct mode for close-up emotions.
    if mode == "mirror":
        parts.append("mirror selfie composition, full-body anime shot, clear outfit details")
    else:
        parts.append("close-up direct selfie, eye contact, warm smile, not a mirror selfie")

    if action:
        parts.append(action)
    if scene:
        parts.append(f"in {scene}")

    parts.append("high quality illustration")
    return ", ".join(parts)


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
    return cleaned[:28] if cleaned else "na"


def _extract_generated_file(stdout: str, output_dir: str) -> Path | None:
    # Prefer explicit file line from the upstream script output.
    match = re.search(r"File:\s*(/\S+)", stdout)
    if match:
        p = Path(match.group(1))
        if p.exists():
            return p

    # Fallback: newest generated file in output dir.
    files = sorted(Path(output_dir).glob("beauty_generated_*.*"), key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0] if files else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default="a cozy gamer bedroom")
    parser.add_argument("--mood", default="playful")
    parser.add_argument("--action", default="holding a game controller")
    parser.add_argument("--mode", choices=["mirror", "direct"], default="direct")
    parser.add_argument("--expression", default="gentle caring expression")
    parser.add_argument(
        "--persona",
        default="anime virtual girlfriend vibe, gentle, caring, cute, emotionally present",
    )
    parser.add_argument("--output-dir", default="/root/.openclaw/workspace/tmp")
    args = parser.parse_args()

    prompt = build_prompt(args.scene, args.mood, args.action, args.mode, args.expression, args.persona)
    cmd = (
        "python3 /root/.openclaw/workspace/skills/beauty-generation-api/scripts/generate.py "
        f"--prompt {shlex.quote(prompt)} --output-dir {shlex.quote(args.output_dir)}"
    )
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="")

    if proc.returncode != 0:
        return proc.returncode

    generated = _extract_generated_file(proc.stdout or "", args.output_dir)
    if not generated:
        return 0

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"umaru_{ts}_m-{_slug(args.mood)}_s-{_slug(args.scene)}_a-{_slug(args.action)}{generated.suffix}"
    target = generated.with_name(filename)
    generated.rename(target)
    print(f"Renamed: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
