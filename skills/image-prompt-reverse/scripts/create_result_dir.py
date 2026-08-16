#!/usr/bin/env python3
"""Create a unique Image Prompt Reverse result directory in Downloads."""

from __future__ import annotations

import argparse
import re
import unicodedata
from datetime import datetime
from pathlib import Path

DEFAULT_FOLDER_NAME = "image-prompt-reverse"
MAX_SLUG_LENGTH = 48


def source_slug(source: Path) -> str:
    """Return a short filesystem-safe slug derived from the source filename."""
    normalized = unicodedata.normalize("NFKD", source.stem).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug[:MAX_SLUG_LENGTH].rstrip("-") or "image"


def default_output_root() -> Path:
    """Return the Skill's default root inside the current user's Downloads folder."""
    return Path.home() / "Downloads" / DEFAULT_FOLDER_NAME


def create_result_dir(source: Path, output_root: Path, timestamp: str | None = None) -> Path:
    """Create and return a unique timestamped result directory."""
    stamp = timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
    basename = f"{stamp}-{source_slug(source)}"
    output_root = output_root.expanduser()

    counter = 1
    while True:
        suffix = "" if counter == 1 else f"-{counter}"
        candidate = output_root / f"{basename}{suffix}"
        try:
            candidate.mkdir(parents=True, exist_ok=False)
            return candidate.resolve()
        except FileExistsError:
            counter += 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Reference image path, used to derive the result slug")
    parser.add_argument(
        "--output-root",
        type=Path,
        default=default_output_root(),
        help="Explicit result root; defaults to the user's Downloads/image-prompt-reverse folder",
    )
    args = parser.parse_args()

    if not args.source.is_file():
        parser.error(f"reference image not found: {args.source}")

    try:
        result_dir = create_result_dir(args.source, args.output_root)
    except OSError as error:
        parser.exit(
            1,
            f"ERROR: could not create a result directory under {args.output_root.expanduser()}: {error}. "
            "Request filesystem permission for this destination; do not fall back to the conversation project.\n",
        )

    print(result_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
