#!/usr/bin/env python3
"""Build and verify an NX2Apple ROMFSARC archive for local iPhone transfer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


MAX_PART_BYTES = 512_000_000
CHUNK_BYTES = 4 * 1024 * 1024


def sha256_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for block in iter(lambda: source.read(CHUNK_BYTES), b""):
            digest.update(block)
            size += len(block)
    return size, digest.hexdigest()


def find_tool(explicit: Path | None) -> Path:
    candidates = []
    if explicit:
        candidates.append(explicit)
    if os.environ.get("NX2APPLE_DIR"):
        candidates.append(Path(os.environ["NX2APPLE_DIR"]))
    candidates.append(Path(__file__).resolve().parents[1] / "vendor" / "nx2apple")
    for candidate in candidates:
        tool = candidate.expanduser().resolve() / "dm" / "tools" / "romfs_arc.py"
        if tool.is_file():
            return tool
    raise SystemExit("NX2Apple romfs_arc.py not found; initialize vendor/nx2apple")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--romfs", type=Path, required=True, help="extracted RomFS directory")
    parser.add_argument("--output", type=Path, required=True, help="local output directory for romfs.idx and shards")
    parser.add_argument("--backend-dir", type=Path)
    parser.add_argument("--shard-mib", type=int, default=200)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    romfs = args.romfs.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not romfs.is_dir():
        raise SystemExit(f"RomFS directory does not exist: {romfs}")
    if output == romfs or romfs in output.parents:
        raise SystemExit("output directory must not be inside RomFS")
    if not (1 <= args.shard_mib <= 488):
        raise SystemExit("--shard-mib must be between 1 and 488 so every shard stays below 512 MB")
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"output directory is not empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    tool = find_tool(args.backend_dir)
    subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("apply_nx2apple_patches.py")),
            "--backend-dir",
            str(tool.parents[2]),
            "--patch",
            "patches/nx2apple-romfsarc-global-shards.patch",
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[1],
    )
    base = output / "romfs"
    command = [
        sys.executable,
        str(tool),
        "pack",
        str(romfs),
        str(base),
        "--shard-mib",
        str(args.shard_mib),
    ]
    subprocess.run(command, check=True, cwd=tool.parents[2])
    subprocess.run(
        [sys.executable, str(tool), "verify", str(base), str(romfs)],
        check=True,
        cwd=tool.parents[2],
    )
    artifacts = [
        path
        for path in sorted(output.iterdir())
        if path.name == "romfs.idx" or (path.name.startswith("romfs.") and path.name[6:].isdigit())
    ]
    if not artifacts:
        raise SystemExit("romfs_arc.py produced no archive files")
    records = []
    for path in artifacts:
        size, sha = sha256_file(path)
        if size > MAX_PART_BYTES:
            raise SystemExit(f"ROMFSARC part exceeds 512 MB: {path} ({size})")
        records.append({"name": path.name, "bytes": size, "sha256": sha})
    manifest = {
        "schema": 1,
        "format": "nx2apple-romfsarc-v2",
        "shard_mib": args.shard_mib,
        "max_part_bytes": MAX_PART_BYTES,
        "parts": records,
    }
    (output / "romfs-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(output), "parts": len(records), "max_bytes": max(x["bytes"] for x in records)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
