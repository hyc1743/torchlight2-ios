#!/usr/bin/env python3
"""Convert local NSZ inputs to temporary NSP files for nx_extract."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def find_nsz(explicit: Path | None) -> Path:
    candidates = []
    if explicit:
        candidates.append(explicit)
    if os.environ.get("NSZ_DIR"):
        candidates.append(Path(os.environ["NSZ_DIR"]))
    candidates.append(Path(__file__).resolve().parents[1] / "vendor" / "nsz")
    for candidate in candidates:
        root = candidate.expanduser().resolve()
        script = root / "nsz.py" if root.is_dir() else root
        if script.is_file():
            return script
    raise SystemExit("NSZ tool not found; initialize vendor/nsz or pass --nsz-dir")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--keys", type=Path, required=True)
    parser.add_argument("--nsz-dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    resources = args.resources.expanduser().resolve()
    output = args.output.expanduser().resolve()
    keys = args.keys.expanduser().resolve()
    if not resources.is_dir():
        raise SystemExit(f"resource directory does not exist: {resources}")
    if not keys.is_file():
        raise SystemExit(f"keys file does not exist: {keys}")
    if output == resources or resources in output.parents:
        raise SystemExit("normalized output must not be inside the input directory")
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"normalized output is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    nsz = find_nsz(args.nsz_dir)
    for source in sorted(resources.iterdir()):
        suffix = source.suffix.lower()
        if suffix in {".nsp", ".xci"}:
            shutil.copy2(source, output / source.name)
        elif suffix == ".nsz":
            command = [
                sys.executable,
                str(nsz),
                "-D",
                "-o",
                str(output),
                "--keys",
                str(keys),
                "--machine-readable",
                str(source),
            ]
            subprocess.run(command, check=True, cwd=nsz.parent)
    normalized = sorted(output.glob("*.nsp")) + sorted(output.glob("*.xci"))
    if not normalized:
        raise SystemExit("normalization produced no NSP/XCI inputs")
    print(f"normalized {len(normalized)} inputs into {output}")
    for path in normalized:
        print(f"  {path.name} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
