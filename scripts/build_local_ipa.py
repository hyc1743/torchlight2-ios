#!/usr/bin/env python3
"""Invoke the pinned nxnative build using only local game data and keys."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", type=Path, required=True)
    parser.add_argument("--keys", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--nxnative", type=Path)
    parser.add_argument("--survey-only", action="store_true")
    parser.add_argument("--prepare-xcode", action="store_true")
    parser.add_argument("--language", help="optional nxnative language code or name")
    parser.add_argument("--app-name", default="Torchlight II Mobile")
    return parser.parse_args()


def find_nxnative(explicit: Path | None) -> Path:
    candidates = []
    if explicit:
        candidates.append(explicit)
    if os.environ.get("NXNATIVE_DIR"):
        candidates.append(Path(os.environ["NXNATIVE_DIR"]))
    candidates.append(Path(__file__).resolve().parents[1] / "vendor" / "nxnative")
    for candidate in candidates:
        root = candidate.expanduser().resolve()
        if (root / "scripts" / "build_ipa_from_nsp.py").is_file():
            return root
    raise SystemExit("nxnative checkout not found; initialize the submodule or pass --nxnative")


def main() -> int:
    args = parse_args()
    resources = args.resources.expanduser().resolve()
    keys = args.keys.expanduser().resolve()
    if not resources.is_dir():
        raise SystemExit(f"resource directory does not exist: {resources}")
    if not keys.is_file():
        raise SystemExit(f"keys file does not exist: {keys}")
    nxnative = find_nxnative(args.nxnative)
    command = [
        sys.executable,
        str(nxnative / "scripts" / "build_ipa_from_nsp.py"),
        str(resources),
        "--keys",
        str(keys),
        "--app-name",
        args.app_name,
    ]
    if args.language:
        command.extend(["--language", args.language])
    command.extend(["--progress", "lines"])
    if args.out:
        command.extend(["--out", str(args.out.expanduser().resolve())])
    if args.survey_only:
        command.append("--survey-only")
    if args.prepare_xcode:
        command.append("--prepare-xcode")
    printable = ["<local-prod.keys>" if part == str(keys) else part for part in command]
    print("running nxnative with local resources; key contents are never printed")
    print(" ".join(repr(part) for part in printable))
    return subprocess.call(command, cwd=nxnative)


if __name__ == "__main__":
    raise SystemExit(main())
