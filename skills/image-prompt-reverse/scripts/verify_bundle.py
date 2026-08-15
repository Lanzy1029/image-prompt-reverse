#!/usr/bin/env python3
"""Verify a completed reverse-engineering bundle and write its manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from extract_prompt import extract_prompt


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def one_match(folder: Path, pattern: str, label: str) -> Path:
    matches = sorted(folder.glob(pattern))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {label}; found {len(matches)} matching {pattern}")
    return matches[0]


def check_image(path: Path) -> None:
    head = path.read_bytes()[:16]
    valid = (
        head.startswith(b"\x89PNG\r\n\x1a\n")
        or head.startswith(b"\xff\xd8\xff")
        or head.startswith(b"GIF87a")
        or head.startswith(b"GIF89a")
        or (head.startswith(b"RIFF") and head[8:12] == b"WEBP")
        or head.startswith(b"BM")
        or head.startswith((b"II*\x00", b"MM\x00*"))
        or (len(head) >= 12 and head[4:8] == b"ftyp")
    )
    if not valid:
        raise ValueError(f"unrecognized image signature: {path.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir", type=Path)
    args = parser.parse_args()
    folder = args.result_dir.resolve()

    original = one_match(folder, "original-image.*", "original image")
    generated = one_match(folder, "generated-image.*", "generated image")
    palette = folder / "color-palette.png"
    analysis = folder / "image-analysis.json"
    report = folder / "reverse-engineering.md"
    prompt_file = folder / "gpt-image-prompt.txt"
    for path in (palette, analysis, report, prompt_file):
        if not path.is_file() or path.stat().st_size == 0:
            raise FileNotFoundError(f"required artifact missing or empty: {path.name}")
    for path in (original, generated, palette):
        check_image(path)

    report_text = report.read_text(encoding="utf-8")
    marked_prompt = extract_prompt(report_text)
    saved_prompt = prompt_file.read_text(encoding="utf-8").strip()
    if marked_prompt != saved_prompt:
        raise ValueError("gpt-image-prompt.txt does not exactly match the marked report prompt")
    for name in (original.name, palette.name, generated.name):
        if f"./{name}" not in report_text:
            raise ValueError(f"report does not link to {name}")

    files = [original, palette, analysis, report, prompt_file, generated]
    manifest = {
        "status": "pass",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "prompt_matches_report": True,
        "files": {
            path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in files
        },
    }
    manifest_path = folder / "bundle-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(files) + 1} artifacts verified in {folder}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
