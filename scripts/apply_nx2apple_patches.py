#!/usr/bin/env python3
"""Apply the repository's NX2Apple ROMFSARC segment patch idempotently."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend-dir", type=Path, default=Path("vendor/nx2apple"))
    parser.add_argument("--patch", type=Path, action="append")
    parser.add_argument("--debug-jumptable", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    backend = args.backend_dir.expanduser().resolve()
    if not (backend / ".git").exists():
        raise SystemExit(f"NX2Apple checkout is missing: {backend}")
    patches = [Path("patches/nx2apple-romfsarc-segments.patch")]
    if args.patch: patches.extend(args.patch)
    for patch_arg in patches:
        patch = patch_arg.expanduser().resolve()
        if not patch.is_file(): raise SystemExit(f"NX2Apple patch is missing: {patch}")
        check = subprocess.run(["git", "-C", str(backend), "apply", "--check", str(patch)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if check.returncode == 0:
            subprocess.run(["git", "-C", str(backend), "apply", str(patch)], check=True)
            print(f"applied {patch.name}"); continue
        if patch.name == "nx2apple-romfsarc-segments.patch" and "VERSION = 2" in (backend / "dm/tools/romfs_arc.py").read_text(encoding="utf-8"):
            print(f"already applied {patch.name}"); continue
        if patch.name == "nx2apple-jumptable.patch" and "def jump_offsets_base_copy" in (backend / "dm/tools/patch_nso.py").read_text(encoding="utf-8"):
            print(f"already applied {patch.name}"); continue
        if patch.name == "nx2apple-drawtexture-nop.patch" and '    "nvnCommandBufferDrawTexture",' in (backend / "dm/gfx/nvn/hle_nvn.c").read_text(encoding="utf-8"):
            print(f"already applied {patch.name}"); continue
        reverse = subprocess.run(["git", "-C", str(backend), "apply", "--reverse", "--check", str(patch)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if reverse.returncode == 0: print(f"already applied {patch.name}"); continue
        sys.stderr.write(check.stderr or reverse.stderr)
        raise SystemExit(f"NX2Apple patch does not apply cleanly: {patch.name}")
    if args.debug_jumptable:
        target = backend / "dm/tools/patch_nso.py"
        raw = target.read_bytes()
        marker = b"                assert tgt, f'jump table {ins.address:x}'"
        addition = b"                if not tgt:\n                    lines = [f'UNRECOGNIZED_JUMPTABLE {ins.address:x} function {fa:x}..{fb:x}']\n                    lines += [f'  {q.address:x}: {q.mnemonic} {q.op_str}' for q in insl[max(0, j - 40):j + 1]]\n                    print('\\n'.join(lines), file=sys.stderr)\n                    try: open(os.environ.get('TL2_JUMPTABLE_LOG', '/tmp/torchlight2-jumptable.log'), 'a').write('\\n'.join(lines) + '\\n')\n                    except OSError: pass\n"
        if marker in raw and addition not in raw:
            target.write_bytes(raw.replace(marker, addition + marker, 1))
            print("applied jump-table diagnostics")


if __name__ == "__main__":
    raise SystemExit(main())
