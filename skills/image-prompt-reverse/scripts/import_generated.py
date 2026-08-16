#!/usr/bin/env python3
"""Copy a built-in image-generation result into an Image Prompt Reverse result directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": ".png",
    b"\xff\xd8\xff": ".jpg",
    b"GIF87a": ".gif",
    b"GIF89a": ".gif",
}


def infer_suffix(path: Path) -> str:
    head = path.read_bytes()[:16]
    if head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return ".webp"
    for signature, suffix in SIGNATURES.items():
        if head.startswith(signature):
            return suffix
    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif"}:
        return ".jpg" if path.suffix.lower() == ".jpeg" else path.suffix.lower()
    raise ValueError("generated file is not a recognized raster image")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("result_dir", type=Path)
    args = parser.parse_args()

    if not args.source.is_file() or args.source.stat().st_size == 0:
        raise FileNotFoundError(f"generated image not found or empty: {args.source}")
    args.result_dir.mkdir(parents=True, exist_ok=True)
    suffix = infer_suffix(args.source)
    target = args.result_dir / f"generated-image{suffix}"
    version = 2
    while target.exists():
        target = args.result_dir / f"generated-image-v{version}{suffix}"
        version += 1
    shutil.copy2(args.source, target)
    print(target.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
