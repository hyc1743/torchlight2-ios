#!/usr/bin/env python3
"""Stage verified local resource parts and prod.keys for the macOS runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from pathlib import Path


MAX_PART_BYTES = 512_000_000
CHUNK_BYTES = 4 * 1024 * 1024


def digest(path: Path) -> tuple[int, str]:
    h = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for block in iter(lambda: source.read(CHUNK_BYTES), b""):
            h.update(block)
            size += len(block)
    return size, h.hexdigest()


def safe_part(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"manifest path escapes parts directory: {relative}") from exc
    return path


def verify_manifest(parts: Path) -> dict:
    manifest_path = parts / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != 1:
        raise ValueError("unsupported resource manifest schema")
    maximum = int(manifest.get("max_part_bytes", 0))
    if maximum <= 0 or maximum > MAX_PART_BYTES:
        raise ValueError(f"manifest max_part_bytes exceeds 512 MB: {maximum}")
    checked = 0
    for source in manifest.get("sources", []):
        for item in source.get("parts", []):
            size, sha = digest(safe_part(parts, item["path"]))
            if size != int(item["bytes"]) or sha.lower() != item["sha256"].lower():
                raise ValueError(f"part hash or size mismatch: {item['path']}")
            if size > MAX_PART_BYTES:
                raise ValueError(f"part exceeds 512 MB: {item['path']}")
            checked += 1
    return {"sources": len(manifest.get("sources", [])), "parts": checked, "max_part_bytes": maximum}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts", type=Path, required=True)
    parser.add_argument("--keys", type=Path, required=True)
    parser.add_argument("--runner-temp", type=Path, required=True)
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    parts = args.parts.expanduser().resolve()
    keys = args.keys.expanduser().resolve()
    runner_temp = args.runner_temp.expanduser().resolve()
    if not parts.is_dir():
        raise SystemExit(f"parts directory does not exist: {parts}")
    if not keys.is_file():
        raise SystemExit(f"keys file does not exist: {keys}")
    summary = verify_manifest(parts)
    target_parts = runner_temp / "torchlight2-resource-parts"
    target_keys = runner_temp / "torchlight2-prod.keys"
    if not args.replace and (target_parts.exists() or target_keys.exists()):
        raise SystemExit("runner staging targets already exist; use --replace to overwrite them")
    target_parts.mkdir(parents=True, exist_ok=True)
    for source in parts.rglob("*"):
        relative = source.relative_to(parts)
        destination = target_parts / relative
        if source.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
        elif source.is_file():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    target_keys.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(keys, target_keys)
    try:
        os.chmod(target_keys, 0o600)
    except OSError:
        pass
    print(json.dumps({"staged_parts": str(target_parts), "staged_keys": str(target_keys), **summary}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
