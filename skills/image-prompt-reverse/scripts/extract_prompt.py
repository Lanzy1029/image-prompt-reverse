#!/usr/bin/env python3
"""Extract the canonical GPT Image prompt block from a reverse-engineering report."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

START = "<!-- GPT_IMAGE_PROMPT_START -->"
END = "<!-- GPT_IMAGE_PROMPT_END -->"


def extract_prompt(markdown: str) -> str:
    if markdown.count(START) != 1 or markdown.count(END) != 1:
        raise ValueError("report must contain exactly one prompt start marker and one end marker")
    start = markdown.index(START) + len(START)
    end = markdown.index(END, start)
    block = markdown[start:end].strip()
    fenced = re.fullmatch(r"```(?:text)?\s*\n([\s\S]*?)\n```", block)
    if not fenced:
        raise ValueError("prompt markers must contain exactly one ```text fenced block")
    prompt = fenced.group(1).strip()
    if len(prompt) < 80:
        raise ValueError("extracted prompt is too short to be executable")
    if len(prompt) > 6000:
        raise ValueError("extracted prompt exceeds the 6000-character safety limit")
    if "<prompt>" in prompt or "TODO" in prompt:
        raise ValueError("extracted prompt still contains a placeholder")
    return prompt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    prompt = extract_prompt(args.report.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(prompt + "\n", encoding="utf-8")
    print(f"Extracted {len(prompt)} characters to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
