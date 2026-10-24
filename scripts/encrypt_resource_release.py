#!/usr/bin/env python3
"""Encrypt/decrypt split game-resource parts for a GitHub Release build."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

CHUNK = 4 * 1024 * 1024
MAGIC = b"TL2RESENC\x01"


def key_from(value: str) -> bytes:
    try:
        key = bytes.fromhex(value.strip())
    except ValueError:
        raise SystemExit("resource key must be 64 hexadecimal characters") from None
    if len(key) != 32:
        raise SystemExit("resource key must be 64 hexadecimal characters")
    return key


def digest(path: Path) -> tuple[int, str]:
    h = hashlib.sha256(); size = 0
    with path.open("rb") as f:
        for block in iter(lambda: f.read(CHUNK), b""):
            h.update(block); size += len(block)
    return size, h.hexdigest()


def aesgcm():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as exc:
        raise SystemExit("install cryptography first: python -m pip install cryptography") from exc
    return AESGCM


def seal_file(source: Path, target: Path, key: bytes) -> dict:
    AESGCM = aesgcm(); nonce = os.urandom(12)
    raw = source.read_bytes()
    plain_sha = hashlib.sha256(raw).hexdigest()
    aad = MAGIC + len(raw).to_bytes(8, "little") + bytes.fromhex(plain_sha)
    encrypted = AESGCM(key).encrypt(nonce, raw, aad)
    target.write_bytes(aad + nonce + encrypted)
    size, sha = digest(target)
    return {"name": source.name, "encrypted": target.name, "bytes": len(raw),
            "sha256": plain_sha, "encrypted_bytes": size, "encrypted_sha256": sha}


def open_file(source: Path, target: Path, key: bytes, expected: dict) -> None:
    AESGCM = aesgcm(); data = source.read_bytes()
    header = len(MAGIC) + 8 + 32
    if len(data) < header + 12 + 16 or data[:len(MAGIC)] != MAGIC:
        raise SystemExit(f"invalid encrypted resource: {source.name}")
    aad = data[:header]; nonce = data[header:header + 12]
    plain = AESGCM(key).decrypt(nonce, data[header + 12:], aad)
    if len(plain) != int(expected["bytes"]) or hashlib.sha256(plain).hexdigest() != expected["sha256"]:
        raise SystemExit(f"resource digest mismatch: {expected['name']}")
    target.write_bytes(plain)


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("seal"); s.add_argument("parts", type=Path); s.add_argument("output", type=Path)
    s.add_argument("--key-file", type=Path, default=Path(".local/torchlight2-resource.key"))
    o = sub.add_parser("open"); o.add_argument("release", type=Path); o.add_argument("output", type=Path)
    o.add_argument("--key", default=os.environ.get("TORCHLIGHT2_RESOURCE_KEY", ""))
    args = p.parse_args()
    if args.command == "seal":
        key_path = args.key_file
        if key_path.exists(): key = key_from(key_path.read_text())
        else:
            key = os.urandom(32); key_path.parent.mkdir(parents=True, exist_ok=True)
            key_path.write_text(key.hex() + "\n");
            try: key_path.chmod(0o600)
            except OSError: pass
        manifest = json.loads((args.parts / "manifest.json").read_text(encoding="utf-8"))
        args.output.mkdir(parents=True, exist_ok=True)
        files = []
        for source in manifest.get("sources", []):
            for part in source.get("parts", []):
                input_path = args.parts / part["path"]
                # Release assets must use a portable name: GitHub normalizes
                # brackets and other punctuation in uploaded asset names.
                asset_name = f"part-{len(files):04d}.enc"
                item = seal_file(input_path, args.output / asset_name, key)
                item.update({"name": part["path"], "source": source["name"]})
                files.append(item)
        (args.output / "cloud-manifest.json").write_text(json.dumps({"schema": 1, "source_manifest": manifest, "parts": files}, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"parts": len(files), "key_file": str(key_path), "output": str(args.output)}))
    else:
        key = key_from(args.key)
        manifest = json.loads((args.release / "cloud-manifest.json").read_text(encoding="utf-8"))
        args.output.mkdir(parents=True, exist_ok=True)
        for item in manifest["parts"]:
            target = args.output / item["name"]
            target.parent.mkdir(parents=True, exist_ok=True)
            open_file(args.release / item["encrypted"], target, key, item)
        (args.output / "manifest.json").write_text(json.dumps(manifest["source_manifest"], indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"parts": len(manifest["parts"]), "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
