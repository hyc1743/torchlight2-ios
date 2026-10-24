#!/usr/bin/env python3
"""Validate the structural contract of an unsigned iOS IPA."""

from __future__ import annotations

import argparse
import json
import plistlib
import zipfile
from pathlib import Path


FORBIDDEN_SUFFIXES = (".nsp", ".nsz", ".ncz", ".xci", ".nca", ".tik", ".cert", ".keys")
MACHO_MAGICS = {
    b"\xfe\xed\xfa\xcf",  # 64-bit big endian
    b"\xcf\xfa\xed\xfe",  # 64-bit little endian
    b"\xca\xfe\xba\xbe",  # fat big endian
    b"\xbe\xba\xfe\xca",  # fat little endian
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = args.ipa.expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"IPA does not exist: {path}")
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if any(name.startswith("/") or ".." in Path(name).parts for name in names):
            raise SystemExit("IPA contains an unsafe archive path")
        forbidden = [name for name in names if name.lower().endswith(FORBIDDEN_SUFFIXES)]
        if forbidden:
            raise SystemExit(f"IPA contains forbidden game archive/key files: {forbidden[:5]}")
        apps = sorted({name.split("/", 2)[1] for name in names if name.startswith("Payload/") and name.count("/") >= 2})
        if len(apps) != 1 or not apps[0].endswith(".app"):
            raise SystemExit(f"expected one Payload/*.app, found {apps}")
        app = f"Payload/{apps[0]}"
        plist_name = app + "/Info.plist"
        if plist_name not in names:
            raise SystemExit("IPA app is missing Info.plist")
        info = plistlib.loads(archive.read(plist_name))
        executable = info.get("CFBundleExecutable")
        identifier = info.get("CFBundleIdentifier")
        if not isinstance(executable, str) or not executable:
            raise SystemExit("Info.plist has no CFBundleExecutable")
        if not isinstance(identifier, str) or not identifier:
            raise SystemExit("Info.plist has no CFBundleIdentifier")
        executable_name = app + "/" + executable
        if executable_name not in names:
            raise SystemExit(f"app executable is missing: {executable}")
        executable_bytes = archive.read(executable_name)
        if executable_bytes[:4] not in MACHO_MAGICS:
            raise SystemExit(f"app executable is not a Mach-O image: {executable}")
        resource_roots = sorted(
            name.split("/", 2)[1]
            for name in names
            if name.startswith(app + "/") and name.count("/") >= 2
        )
        result = {
            "ipa": str(path),
            "bytes": path.stat().st_size,
            "entries": len(names),
            "app": apps[0],
            "bundle_id": identifier,
            "executable": executable,
            "has_romfs": any(name.startswith(app + "/romfs/") for name in names),
            "has_msl": any(name.startswith(app + "/msl/") for name in names),
            "resource_roots": sorted(set(resource_roots)),
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
