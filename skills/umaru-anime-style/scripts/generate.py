#!/usr/bin/env python3
"""Generate fixed 'anime texture' style images via beauty-generation-api wrapper."""

from __future__ import annotations

import argparse
import shlex
import subprocess

BASE = (
    "Premium anime-style girl portrait, anime texture, clean lineart, rich cel-shading, "
    "long flowing golden-orange hair, large amber eyes, oversized orange hoodie, "
    "warm cinematic lighting"
)


def build_prompt(scene: str, mood: str, action: str) -> str:
    parts = [BASE]
    if mood:
        parts.append(f"{mood} expression")
    if action:
        parts.append(action)
    if scene:
        parts.append(f"in {scene}")
    parts.append("high quality illustration")
    return ", ".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene", default="a cozy gamer bedroom")
    parser.add_argument("--mood", default="playful")
    parser.add_argument("--action", default="holding a game controller")
    parser.add_argument("--output-dir", default="/root/.openclaw/workspace/tmp")
    args = parser.parse_args()

    prompt = build_prompt(args.scene, args.mood, args.action)
    cmd = (
        "python3 /root/.openclaw/workspace/skills/beauty-generation-api/scripts/generate.py "
        f"--prompt {shlex.quote(prompt)} --output-dir {shlex.quote(args.output_dir)}"
    )
    proc = subprocess.run(cmd, shell=True)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
