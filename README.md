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

## Build without a local Mac

NX2Apple needs Xcode, the Metal toolchain, .NET, and its documented Homebrew
and Python dependencies, plus `zstandard`, `pycryptodome`, and `enlighten` for
NSZ normalization. The public GitHub Actions workflow builds on GitHub?s `macos-26` runner. Encrypt the local resource parts with `scripts/encrypt_resource_release.py`, upload them to a private Release, and configure the `TORCHLIGHT2_RESOURCE_KEY` and `TORCHLIGHT2_PROD_KEYS` Actions secrets. Dispatch the workflow with the Release tag in `resource_release`. For local development on a Mac, the wrapper can still be run directly:

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

The workflow downloads encrypted Release assets, decrypts them in `$RUNNER_TEMP`, and never places plaintext game resources in Git. See `docs/public-build.md` for the exact Release and secret setup. The `publish_ipa` input defaults to uploading the slim IPA together with the separately packaged ROMFSARC files as an Actions artifact; copy those files into the installed app?s `Documents/romfs/` directory.

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
