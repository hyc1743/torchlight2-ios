#!/usr/bin/env python3
"""Invoke the pinned NX2Apple/nxnative build using local game data and keys."""

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
    parser.add_argument("--backend", choices=("nx2apple", "nxnative"), default="nx2apple")
    parser.add_argument("--backend-dir", "--nxnative", dest="backend_dir", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--survey-only", action="store_true")
    parser.add_argument("--prepare-xcode", action="store_true")
    parser.add_argument("--full-romfs", action="store_true", help="embed RomFS in the IPA; default is NX2Apple's slim IPA")
    parser.add_argument("--language", help="optional backend language code or name")
    parser.add_argument("--app-name", default="Torchlight II Mobile")
    return parser.parse_args()


def find_backend(explicit: Path | None, backend: str) -> Path:
    candidates = []
    if explicit:
        candidates.append(explicit)
    env_name = "NX2APPLE_DIR" if backend == "nx2apple" else "NXNATIVE_DIR"
    if os.environ.get(env_name):
        candidates.append(Path(os.environ[env_name]))
    candidates.append(Path(__file__).resolve().parents[1] / "vendor" / backend)
    for candidate in candidates:
        root = candidate.expanduser().resolve()
        if (root / "scripts" / "build_ipa_from_nsp.py").is_file():
            return root
    raise SystemExit(f"{backend} checkout not found; initialize submodules or pass --backend-dir")


def main() -> int:
    args = parse_args()
    resources = args.resources.expanduser().resolve()
    keys = args.keys.expanduser().resolve()
    if not resources.is_dir():
        raise SystemExit(f"resource directory does not exist: {resources}")
    if not keys.is_file():
        raise SystemExit(f"keys file does not exist: {keys}")
    backend = find_backend(args.backend_dir, args.backend)
    command = [
        sys.executable,
        str(backend / "scripts" / "build_ipa_from_nsp.py"),
        str(resources),
        "--keys",
        str(keys),
        "--app-name",
        args.app_name,
    ]
    if args.language:
        command.extend(["--language", args.language])
    if args.work_dir:
        if args.backend != "nx2apple":
            raise SystemExit("--work-dir is supported by the NX2Apple backend only")
        command.extend(["--work-dir", str(args.work_dir.expanduser().resolve())])
    command.extend(["--progress", "lines"])
    if args.out:
        command.extend(["--out", str(args.out.expanduser().resolve())])
    if args.survey_only:
        command.append("--survey-only")
    if args.prepare_xcode:
        command.append("--prepare-xcode")
    env = os.environ.copy()
    if args.full_romfs:
        env["DM_FULL_ROMFS"] = "1"
    printable = ["<local-prod.keys>" if part == str(keys) else part for part in command]
    print(f"running {args.backend} with local resources; key contents are never printed")
    print(" ".join(repr(part) for part in printable))
    return subprocess.call(command, cwd=backend, env=env)


if __name__ == "__main__":
    raise SystemExit(main())
