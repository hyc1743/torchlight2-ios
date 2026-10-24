# Torchlight II iOS build wrapper

This repository contains the public build wrapper and resource handling tools
for a **user-owned** Nintendo Switch copy of *Torchlight II*. It uses the
open-source `nxnative` toolchain as a pinned submodule and keeps all game data
and Switch keys outside version control.

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

The local splitter writes parts to `resource-parts/` and a manifest containing
sizes and SHA-256 digests. The default part size is **500,000,000 bytes**, so
every part stays below both decimal 512 MB and binary 512 MiB.

## Local resource flow

On the machine that owns the game dump:

```powershell
python scripts/split_resources.py Gamedata --output resource-parts
python scripts/assemble_resources.py resource-parts/manifest.json --output-dir .local/Gamedata
```

The manifest does not contain key material. It only records the source file
names, part names, sizes, and hashes. `assemble_resources.py` refuses path
traversal and verifies every part before writing a reconstructed file.

## Build on a Mac

`nxnative` needs Xcode, the Metal toolchain, .NET, and its documented Homebrew
and Python dependencies. On a Mac, either use the public GitHub Actions
workflow with a **self-hosted macOS runner** that has the local data mounted,
or run the wrapper directly:

```bash
python scripts/build_local_ipa.py \
  --resources /path/to/Gamedata \
  --keys /path/to/prod.keys \
  --out /path/to/TorchlightIIMobile.ipa
```

The wrapper invokes `vendor/nxnative/scripts/build_ipa_from_nsp.py`. Because
Torchlight II has no verified profile, it keeps the survey and provisional
profile under the local resource directory and labels the resulting IPA as
best effort. The `--survey-only` mode is useful before spending time on IPA
packing.

## Public GitHub Actions workflow

The workflow in `.github/workflows/build-ipa.yml` runs only on a self-hosted
macOS runner. It expects the runner to expose two local environment variables:

- `TORCHLIGHT2_RESOURCES`: a directory containing the base NSP, update NSZ,
  and optional DLC NSP
- `TORCHLIGHT2_KEYS`: a path to the user's local `prod.keys`

The job never uploads those paths or their contents. By default the IPA also
stays on the self-hosted runner; the workflow prints its local path. A separate
`publish_ipa` input can upload the IPA as a public Actions artifact only when
you explicitly accept that the IPA contains game data. Do not replace this
with a hosted runner plus an uploaded game archive: that would publish
proprietary game resources outside the local boundary.

## References

- [nxnative](https://github.com/seedds/nxnative)
- [NX2Apple](https://github.com/LNPANDY/NX2Apple)
- [d2r-mobile](https://github.com/jhaizhou-ops/d2r-mobile)

Those projects are references and upstream dependencies; their own licenses
remain applicable.
