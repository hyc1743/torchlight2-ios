#!/usr/bin/env python3
"""Split local Switch resource archives into verified, size-bounded parts.

Only the resulting manifest and parts are intended to be moved between local
machines. The script never reads or prints key values and never adds game data
to the Git repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile


DEFAULT_MAX_BYTES = 500_000_000
RESOURCE_SUFFIXES = {".nsp", ".nsz", ".xci"}
CHUNK_BYTES = 4 * 1024 * 1024


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(CHUNK_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(path: Path, root: Path) -> str:
    relative = path.resolve().relative_to(root.resolve())
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"path escapes output directory: {path}")
    return relative.as_posix()


def atomic_write_part(destination: Path, source, length: int) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    written = 0
    with NamedTemporaryFile(
        mode="wb", dir=destination.parent, prefix=f".{destination.name}.", delete=False
    ) as temporary:
        temporary_name = Path(temporary.name)
        try:
            while written < length:
                block = source.read(min(CHUNK_BYTES, length - written))
                if not block:
                    raise IOError(f"unexpected end of source while writing {destination}")
                temporary.write(block)
                digest.update(block)
                written += len(block)
            temporary.flush()
            os.fsync(temporary.fileno())
        except Exception:
            temporary_name.unlink(missing_ok=True)
            raise
    os.replace(temporary_name, destination)
    return digest.hexdigest()


def split_file(source: Path, output_root: Path, max_bytes: int) -> dict:
    source_size = source.stat().st_size
    source_hash = sha256_file(source)
    safe_name = source.name.replace("/", "_").replace("\\", "_")
    part_count = (source_size + max_bytes - 1) // max_bytes or 1
    parts = []
    with source.open("rb") as handle:
        for index in range(part_count):
            length = min(max_bytes, source_size - index * max_bytes)
            relative = Path(safe_name) / f"part-{index + 1:04d}"
            destination = output_root / relative
            part_hash = atomic_write_part(destination, handle, length)
            parts.append(
                {
                    "path": safe_relative(destination, output_root),
                    "bytes": length,
                    "sha256": part_hash,
                }
            )
    return {
        "name": source.name,
        "bytes": source_size,
        "sha256": source_hash,
        "parts": parts,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resources", type=Path, help="local directory containing NSP/NSZ/XCI files")
    parser.add_argument("--output", type=Path, default=Path("resource-parts"))
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_BYTES,
        help=f"maximum bytes per part (default: {DEFAULT_MAX_BYTES})",
    )
    parser.add_argument("--manifest-name", default="manifest.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    resources = args.resources.expanduser().resolve()
    output = args.output.expanduser().resolve()
    if not resources.is_dir():
        raise SystemExit(f"resource directory does not exist: {resources}")
    if args.max_bytes <= 0:
        raise SystemExit("--max-bytes must be positive")
    if output == resources or resources in output.parents:
        raise SystemExit("output directory must not be inside the source resource directory")

    sources = sorted(
        path for path in resources.iterdir() if path.is_file() and path.suffix.lower() in RESOURCE_SUFFIXES
    )
    if not sources:
        raise SystemExit(f"no NSP/NSZ/XCI files found in {resources}")

    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": 1,
        "max_part_bytes": args.max_bytes,
        "sources": [split_file(path, output, args.max_bytes) for path in sources],
    }
    manifest_path = output / args.manifest_name
    temporary = manifest_path.with_name(f".{manifest_path.name}.tmp")
    temporary.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, manifest_path)
    print(f"wrote {manifest_path}")
    for source in manifest["sources"]:
        print(f"{source['name']}: {source['bytes']} bytes -> {len(source['parts'])} parts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
