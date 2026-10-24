#!/usr/bin/env python3
"""Inspect an NSP/NSZ set without decrypting content or reading key files."""

from __future__ import annotations

import argparse
import json
import re
import struct
import xml.etree.ElementTree as ET
from pathlib import Path


TITLE_ID = re.compile(r"^(?P<id>[0-9a-fA-F]{16})[0-9a-fA-F]{16}\.(?:tik|cert)$")
EXPECTED_BASE = "010090400d366000"
EXPECTED_UPDATE = "010090400d366800"
EXPECTED_DLC = "010090400d367001"


def pfs0_entries(path: Path) -> list[tuple[str, int, int]]:
    with path.open("rb") as handle:
        if handle.read(4) != b"PFS0":
            raise ValueError(f"{path.name}: not a PFS0 container")
        count, string_bytes, _ = struct.unpack("<III", handle.read(12))
        entries = [struct.unpack("<QQII", handle.read(24)) for _ in range(count)]
        strings = handle.read(string_bytes)
        data_base = handle.tell()
        result = []
        for offset, size, name_offset, _ in entries:
            end = strings.find(b"\0", name_offset)
            if end < 0:
                raise ValueError(f"{path.name}: unterminated PFS0 name")
            name = strings[name_offset:end].decode("utf-8", "replace")
            result.append((name, data_base + offset, size))
        return result


def cnmt_summary(path: Path, entry: tuple[str, int, int]) -> dict | None:
    name, offset, size = entry
    if not name.endswith(".cnmt.xml"):
        return None
    with path.open("rb") as handle:
        handle.seek(offset)
        root = ET.fromstring(handle.read(size))
    return {
        "type": root.findtext("Type"),
        "id": root.findtext("Id"),
        "version": root.findtext("Version"),
        "patch_id": root.findtext("PatchId"),
    }


def title_id_from_entries(entries: list[tuple[str, int, int]]) -> str | None:
    for name, _, _ in entries:
        match = TITLE_ID.match(name)
        if match:
            return match.group("id").lower()
    return None


def inspect(path: Path) -> dict:
    entries = pfs0_entries(path)
    summaries = [summary for entry in entries if (summary := cnmt_summary(path, entry))]
    return {
        "name": path.name,
        "bytes": path.stat().st_size,
        "container": "PFS0",
        "title_id_from_ticket": title_id_from_entries(entries),
        "cnmt": summaries,
        "members": [{"name": name, "bytes": size} for name, _, size in entries],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resources", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.resources.expanduser().resolve()
    paths = sorted(path for path in root.iterdir() if path.suffix.lower() in {".nsp", ".nsz"})
    if not paths:
        raise SystemExit(f"no NSP/NSZ files found in {root}")
    records = [inspect(path) for path in paths]
    if args.as_json:
        print(json.dumps(records, indent=2, sort_keys=True))
    else:
        for record in records:
            print(f"{record['name']}: {record['bytes']} bytes, title_id={record['title_id_from_ticket']}")
            for cnmt in record["cnmt"]:
                print(
                    f"  {cnmt['type']} {cnmt['id']} version={cnmt['version']} patch_id={cnmt['patch_id']}"
                )
    ids = {record["title_id_from_ticket"] for record in records}
    unexpected = ids - {EXPECTED_BASE, EXPECTED_UPDATE, EXPECTED_DLC}
    if unexpected:
        raise SystemExit(f"unexpected Torchlight II title IDs: {sorted(unexpected)}")
    if EXPECTED_BASE not in ids or EXPECTED_UPDATE not in ids:
        raise SystemExit("the local set must contain both the base title and update title")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
