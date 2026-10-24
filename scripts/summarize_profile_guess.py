#!/usr/bin/env python3
"""Write a metadata-only profile guess report from an nx_extract manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-dir", type=Path, default=Path("vendor/nx2apple"))
    parser.add_argument("--exefs", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    backend = args.backend_dir.expanduser().resolve()
    sys.path.insert(0, str(backend / "dm" / "games"))
    import profile_guess as pg

    facts = pg.facts_of(args.exefs.expanduser().resolve(), args.manifest.expanduser().resolve())
    guess = pg.guess(facts)
    modules = {}
    for name, module in facts["mods"].items():
        modules[name] = {
            "build_id": module["bid"],
            "kind": module["kind"],
            "imports": len(module["imports"]),
            "exports": len(module["exports"]),
            "sizes": module["sizes"],
            "bss": module["bss"],
        }
    romfs = facts["romfs"]
    report = {
        "title_id": f"{facts['program']:016X}" if facts.get("program") else None,
        "sdk_versions": sorted(facts["sdkver"]),
        "markers": {key: sorted(value) for key, value in facts["markers"].items()},
        "main_markers": sorted(facts.get("main_markers", set())),
        "graphics_candidates": {
            "glslc_outputs_in_main": facts["glslc"],
            "glsl_sources": facts["glsl_src"],
            "spir_v_files": romfs["mags"].get("SPIR-V", 0),
        },
        "modules": modules,
        "romfs": {
            "files": romfs["n"],
            "bytes": romfs["bytes"],
            "top_level_files": dict(romfs["tops"]),
            "top_level_bytes": dict(romfs["topb"]),
            "extensions": dict(romfs["exts"]),
            "magic_headers": dict(romfs["mags"]),
            "largest_file": list(romfs["biggest"]),
        },
        "provisional_profile": {key: value[0] for key, value in guess.items()},
        "provisional_profile_reasons": {key: value[1] for key, value in guess.items() if value[1]},
    }
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "sdk": report["sdk_versions"], "romfs_bytes": romfs["bytes"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
