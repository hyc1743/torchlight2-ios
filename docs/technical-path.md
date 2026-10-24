# Technical path selected from the reference projects

The project uses the references for their implementation boundaries:

1. **Native execution:** the Switch AArch64 guest modules are rewritten and
   linked into an Apple host. This comes from `nxnative` and the earlier
   `d2r-mobile` native runtime, rather than emulating a whole Switch console.
2. **Horizon compatibility:** the host supplies the file, thread, memory,
   input, audio, and graphics service behavior expected by the guest. The
   guest's own code remains the execution entry point.
3. **Graphics:** NVN/Vulkan/GL shader inputs are prepared for Metal by the
   upstream toolchain; Torchlight II still needs a survey to determine its
   exact graphics path and profile settings.
4. **External RomFS:** `NX2Apple` adds `dm/tools/romfs_arc.py`,
   `dm/host/romfs_arc.c/.h`, and filesystem routing in `hle_fs.c`. The iOS
   entry point accepts `Documents/romfs/romfs.idx` plus numbered shards, and
   `build_ipa.sh` produces a slim IPA unless `DM_FULL_ROMFS=1` is set.
   The local patch extends ROMFSARC to version 2 so one logical file can span
   multiple shards; this is required because Torchlight II's `PAKS/DATA.PAK`
   is about 1.15 GiB while each delivery shard must stay below 512 MB.

This repository therefore pins both the upstream `nxnative` fallback and the
`NX2Apple` backend. `scripts/build_local_ipa.py` selects NX2Apple by default;
`--backend nxnative` remains available for comparison. The local Mac workflow
uses the NX2Apple backend, then runs `scripts/pack_romfs_for_iphone.py` with
200 MiB shards and verifies the archive against the extracted RomFS.

The local dump contains an NSZ update, so the workflow first runs
`scripts/normalize_switch_inputs.py` (the pinned `nsz` tool) to produce a
temporary NSP. The original NSZ remains untouched and stays in local storage.

The profile and runtime bring-up remain game-specific. No profile is invented
for Torchlight II before its Mac survey identifies the actual modules, SDK,
graphics API, memory partition, and shader sources.

The Windows static preflight has now identified the base/update pair as SDK
8.2.0 with NVN + FMOD, modules `main/subsdk0/sdk`, and a 257-file 1.88 GiB
RomFS. It suggests a 3,328 MiB heap and no virtual-address system resource;
these values remain provisional until the Mac runtime survey and heap check.
