#!/usr/bin/env python3
"""Reassemble and verify resource parts created by split_resources.py."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


CHUNK_BYTES = 4 * 1024 * 1024


def hash_and_copy(part: Path, output, expected_bytes: int) -> str:
    digest = hashlib.sha256()
    copied = 0
    with part.open("rb") as source:
        while True:
            block = source.read(CHUNK_BYTES)
            if not block:
                break
            copied += len(block)
            if copied > expected_bytes:
                raise ValueError(f"part is larger than manifest: {part}")
            digest.update(block)
            output.write(block)
    if copied != expected_bytes:
        raise ValueError(f"part size mismatch for {part}: {copied} != {expected_bytes}")
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(CHUNK_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_part_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"manifest path escapes its directory: {relative}") from exc
    return candidate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path(".local/Gamedata"))
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != 1:
        raise SystemExit(f"unsupported manifest schema: {manifest.get('schema')}")
    root = manifest_path.parent
    output_dir = args.output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    for source in manifest.get("sources", []):
        destination = output_dir / source["name"]
        if args.dry_run:
            print(f"would assemble {destination}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            mode="wb", dir=destination.parent, prefix=f".{destination.name}.", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            try:
                for part in source["parts"]:
                    part_path = safe_part_path(root, part["path"])
                    actual = hash_and_copy(part_path, temporary, int(part["bytes"]))
                    if actual.lower() != part["sha256"].lower():
                        raise ValueError(f"part hash mismatch: {part_path}")
                temporary.flush()
                os.fsync(temporary.fileno())
            except Exception:
                temporary_path.unlink(missing_ok=True)
                raise
        os.replace(temporary_path, destination)
        if destination.stat().st_size != int(source["bytes"]):
            raise ValueError(f"assembled size mismatch: {destination}")
        if sha256_file(destination).lower() != source["sha256"].lower():
            raise ValueError(f"assembled hash mismatch: {destination}")
        print(f"assembled {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
