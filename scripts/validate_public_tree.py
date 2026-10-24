#!/usr/bin/env python3
"""Fail if tracked files contain game archives, keys, or extracted content."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


FORBIDDEN_NAMES = {
    "prod.keys",
    "title.keys",
}
FORBIDDEN_SUFFIXES = {
    ".nsp",
    ".nsz",
    ".ncz",
    ".xci",
    ".nca",
    ".tik",
    ".cert",
}


def tracked_files(root: Path) -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return [p.relative_to(root) for p in root.rglob("*") if p.is_file() and ".git" not in p.parts]
    return [Path(item) for item in result.stdout.decode().split("\0") if item]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    violations = []
    for relative in tracked_files(root):
        name = relative.name.lower()
        if name in FORBIDDEN_NAMES or any(name.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
            violations.append(relative.as_posix())
    if violations:
        print("forbidden game data or key files are tracked:", file=sys.stderr)
        print("\n".join(f"- {item}" for item in violations), file=sys.stderr)
        return 1
    print("public tree validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
