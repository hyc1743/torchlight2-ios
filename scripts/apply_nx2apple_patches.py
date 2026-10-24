#!/usr/bin/env python3
"""Apply the repository's NX2Apple ROMFSARC segment patch idempotently."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-dir", type=Path, default=Path("vendor/nx2apple"))
    parser.add_argument(
        "--patch",
        type=Path,
        default=Path("patches/nx2apple-romfsarc-segments.patch"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    backend = args.backend_dir.expanduser().resolve()
    patch = args.patch.expanduser().resolve()
    if not (backend / ".git").exists():
        raise SystemExit(f"NX2Apple checkout is missing: {backend}")
    if not patch.is_file():
        raise SystemExit(f"NX2Apple patch is missing: {patch}")
    check = subprocess.run(
        ["git", "-C", str(backend), "apply", "--check", str(patch)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check.returncode == 0:
        subprocess.run(["git", "-C", str(backend), "apply", str(patch)], check=True)
        print(f"applied {patch.name}")
        return 0
    reverse = subprocess.run(
        ["git", "-C", str(backend), "apply", "--reverse", "--check", str(patch)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if reverse.returncode == 0:
        print(f"already applied {patch.name}")
        return 0
    sys.stderr.write(check.stderr or reverse.stderr)
    raise SystemExit("NX2Apple patch does not apply cleanly to the pinned checkout")


if __name__ == "__main__":
    raise SystemExit(main())
