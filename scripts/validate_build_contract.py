#!/usr/bin/env python3
"""Run the pre-Mac validation contract for the public Torchlight II wrapper."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_PUBLIC_PART_BYTES = 512_000_000


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def check_contract_files() -> dict:
    required = [
        ".gitignore",
        ".github/workflows/build-ipa.yml",
        "scripts/split_resources.py",
        "scripts/assemble_resources.py",
        "scripts/inspect_nsp_set.py",
        "scripts/build_local_ipa.py",
        "scripts/validate_public_tree.py",
        "scripts/validate_ipa.py",
        "scripts/stage_runner_inputs.py",
        "scripts/pack_romfs_for_iphone.py",
    ]
    missing = [item for item in required if not (ROOT / item).is_file()]
    if missing:
        raise ValueError(f"missing contract files: {missing}")
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for entry in ("Gamedata/", "*.nsp", "*.nsz", "prod.keys", "title.keys"):
        if entry not in ignore:
            raise ValueError(f".gitignore misses {entry}")
    workflow = (ROOT / ".github/workflows/build-ipa.yml").read_text(encoding="utf-8")
    for required_text in (
        "validate_public_tree.py",
        "assemble_resources.py",
        "build_local_ipa.py",
        "self-hosted",
        "publish_ipa:",
        "default: false",
        "backend nx2apple",
    ):
        if required_text not in workflow:
            raise ValueError(f"workflow misses {required_text}")
    if not (ROOT / "vendor" / "nx2apple" / "dm" / "tools" / "romfs_arc.py").is_file():
        raise ValueError("NX2Apple ROMFSARC tool is missing")
    return {"required_files": len(required), "workflow_contract": True}


def check_public_tree() -> None:
    run(sys.executable, "scripts/validate_public_tree.py")


def check_split_round_trip() -> dict:
    with tempfile.TemporaryDirectory(prefix="torchlight2-contract-") as raw:
        work = Path(raw)
        source = work / "source"
        parts = work / "parts"
        restored = work / "restored"
        source.mkdir()
        # The fixture crosses a part boundary without creating a large test file.
        first = bytes((i * 17) % 251 for i in range(1_300_123))
        second = b"torchlight2-contract\0" * 137
        (source / "base.nsp").write_bytes(first)
        (source / "dlc.nsp").write_bytes(second)
        run(
            sys.executable,
            "scripts/split_resources.py",
            str(source),
            "--output",
            str(parts),
            "--max-bytes",
            "500000",
        )
        manifest = json.loads((parts / "manifest.json").read_text(encoding="utf-8"))
        sizes = [item["bytes"] for source_item in manifest["sources"] for item in source_item["parts"]]
        if max(sizes) > MAX_PUBLIC_PART_BYTES:
            raise ValueError(f"part exceeds public limit: {max(sizes)}")
        run(
            sys.executable,
            "scripts/assemble_resources.py",
            str(parts / "manifest.json"),
            "--output-dir",
            str(restored),
        )
        for name in ("base.nsp", "dlc.nsp"):
            original = source / name
            rebuilt = restored / name
            if original.stat().st_size != rebuilt.stat().st_size:
                raise ValueError(f"size mismatch after round trip: {name}")
            if hashlib.sha256(original.read_bytes()).hexdigest() != hashlib.sha256(rebuilt.read_bytes()).hexdigest():
                raise ValueError(f"hash mismatch after round trip: {name}")
        return {"fixture_sources": 2, "fixture_parts": len(sizes), "fixture_max_bytes": max(sizes)}


def check_romfs_arc() -> dict:
    tool = ROOT / "vendor" / "nx2apple" / "dm" / "tools" / "romfs_arc.py"
    if not tool.is_file():
        raise ValueError("NX2Apple ROMFSARC tool is missing")
    with tempfile.TemporaryDirectory(prefix="torchlight2-romfs-contract-") as raw:
        work = Path(raw)
        romfs = work / "romfs"
        output = work / "archive"
        (romfs / "Pack").mkdir(parents=True)
        (romfs / "Sound").mkdir(parents=True)
        (romfs / "Pack" / "main.bin").write_bytes(bytes(range(256)) * 5)
        (romfs / "Sound" / "voice.dat").write_bytes(b"voice" * 701)
        run(
            sys.executable,
            "scripts/pack_romfs_for_iphone.py",
            "--romfs",
            str(romfs),
            "--output",
            str(output),
            "--shard-mib",
            "1",
        )
        manifest = json.loads((output / "romfs-manifest.json").read_text(encoding="utf-8"))
        sizes = [int(item["bytes"]) for item in manifest["parts"]]
        if not sizes or max(sizes) > MAX_PUBLIC_PART_BYTES:
            raise ValueError("ROMFSARC fixture exceeded the public part limit")
        return {"romfsarc_parts": len(sizes), "romfsarc_max_bytes": max(sizes)}


def main() -> int:
    result = {"contract": check_contract_files()}
    check_public_tree()
    result["public_tree"] = "passed"
    result["round_trip"] = check_split_round_trip()
    result["romfs_arc"] = check_romfs_arc()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
