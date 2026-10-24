# Torchlight II iOS build wrapper

This repository contains the public build wrapper and resource handling tools
for a **user-owned** Nintendo Switch copy of *Torchlight II*. It follows the
native-execution path used by `d2r-mobile` and `nxnative`, with the
ROMFSARC/slim-IPA resource path from `NX2Apple`. All game data and Switch keys
remain outside version control.

The target device is an iPhone 17 Pro Max. The upstream runtime currently
requires iOS/iPadOS 26 or later and an Apple chip in the supported class. The
Torchlight II title IDs in the local dump are:

- base: `010090400D366000`
- update 1.0.5: `010090400D366800`
- DLC: `010090400D367000`

Torchlight II does not have a verified upstream game profile yet. The first
build therefore must run the upstream survey and provisional profile flow on a
Mac. A provisional IPA is an experiment and may fail to boot until the game's
memory, graphics, input, audio, and shader behavior are brought up.

## Repository and data boundary

The public repository contains only source code, scripts, documentation, and
the pinned upstream dependency. Do not commit any of the following:

- NSP/NSZ/XCI/NCA files or extracted RomFS/ExeFS data
- `prod.keys`, `title.keys`, tickets, certificates, or title keys
- generated IPAs, shader caches, saves, or logs containing game data

The local splitter writes the original NSP/NSZ/DLC inputs to `resource-parts/`
with a manifest containing sizes and SHA-256 digests. The default part size is
**500,000,000 bytes**, so every input part stays below both decimal 512 MB and
binary 512 MiB. After the Mac extracts the merged RomFS, the NX2Apple ROMFSARC
packer writes the device resource set as `romfs.idx` plus shards; the workflow
uses 200 MiB shards, also below the 512 MB limit.

## Local resource flow

On the machine that owns the game dump:

```powershell
python scripts/split_resources.py Gamedata --output resource-parts
python scripts/inspect_nsp_set.py Gamedata
python scripts/assemble_resources.py resource-parts/manifest.json --output-dir .local/Gamedata
python scripts/normalize_switch_inputs.py --resources .local/Gamedata --output .local/Normalized --keys prod.keys
```

The manifest does not contain key material. It only records the source file
names, part names, sizes, and hashes. `assemble_resources.py` refuses path
traversal and verifies every part before writing a reconstructed file.
`normalize_switch_inputs.py` converts NSZ updates to temporary NSP files because
`nx_extract` consumes NSP/XCI inputs.

To prepare a self-hosted runner without printing key contents:

```bash
python scripts/stage_runner_inputs.py \
  --parts /path/to/resource-parts \
  --keys /path/to/prod.keys \
  --runner-temp "$RUNNER_TEMP"
```

## Build on a Mac

NX2Apple needs Xcode, the Metal toolchain, .NET, and its documented Homebrew
and Python dependencies, plus `zstandard`, `pycryptodome`, and `enlighten` for
NSZ normalization. On a Mac, either use the public GitHub Actions
workflow with a **self-hosted macOS runner** that has the local data mounted,
or run the wrapper directly:

```bash
python scripts/build_local_ipa.py \
  --resources /path/to/Normalized \
  --keys /path/to/prod.keys \
  --out /path/to/TorchlightIIMobile.ipa
```

The default backend invokes `vendor/nx2apple/scripts/build_ipa_from_nsp.py` and
produces a slim IPA with no RomFS in the bundle. The app reads a plain RomFS
directory or ROMFSARC archive from `Documents/romfs`. Torchlight II has no
verified profile, so the survey and provisional profile remain a best-effort
bring-up; `--survey-only` should run before spending time on IPA packing.

After a successful Mac build, create the local device resource set with:

```bash
python scripts/pack_romfs_for_iphone.py \
  --romfs /path/to/extracted/RomFS \
  --output /path/to/romfs-parts \
  --shard-mib 200
```

Copy `romfs.idx`, `romfs.00`, `romfs.01`, and the remaining generated shards
into the installed app's `Documents/romfs/` directory. The archive packer
verifies every source file before producing its manifest.

## Public GitHub Actions workflow

The workflow in `.github/workflows/build-ipa.yml` runs only on a self-hosted
macOS runner. Before dispatching it, place the local split directory and keys
on that runner. The workflow expects these local paths:

- `$RUNNER_TEMP/torchlight2-resource-parts`: a copy of the local
  `resource-parts/` directory containing `manifest.json` and all parts
- `$RUNNER_TEMP/torchlight2-prod.keys`: the user's local `prod.keys`

The job reconstructs the archives inside the runner's temporary directory and
never uploads the split paths or their contents. The `publish_ipa` input
defaults to uploading the slim IPA as a public Actions artifact; set it to
`false` to keep the executable local. The generated ROMFSARC shards stay on
the runner. Do not replace this with a hosted runner
plus an uploaded game archive: that would publish proprietary game resources
outside the local boundary.

Every workflow dispatch first runs the portable Ubuntu validation job. It
checks the public tree, the workflow contract, and a synthetic split/restore
round trip before the macOS job is allowed to use the local dump.
After an IPA build, the workflow validates its ZIP/Payload layout, Info.plist,
Mach-O executable, and rejects embedded NSP/NSZ/key files before any optional
artifact upload.

## Technical path from the reference projects

- `d2r-mobile`: native execution on Apple silicon, iOS shell, and host-side
  Horizon service replacements.
- `nxnative`: NSO/module rewriting, Horizon service emulation, NVN/Vulkan/GL
  translation, shader preparation, and Xcode/IPA generation.
- `NX2Apple`: the ROMFSARC reader and packer used here. It keeps the IPA slim
  and serves RomFS files from `Documents/romfs` through the host filesystem
  layer, opening shards lazily.

## References

- [nxnative](https://github.com/seedds/nxnative)
- [NX2Apple](https://github.com/LNPANDY/NX2Apple)
- [d2r-mobile](https://github.com/jhaizhou-ops/d2r-mobile)

Those projects are references and upstream dependencies; their own licenses
remain applicable.
