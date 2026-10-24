# Torchlight II bring-up gates

The project is complete only when every gate below has evidence from the
current build. A generated IPA alone is not proof that the game runs.

| Gate | Required evidence | Current state |
|---|---|---|
| Local archive identity | Base, update, and optional DLC title IDs match the local dump | Done on Windows |
| Input packaging | NSP/NSZ/DLC parts are <= 500,000,000 bytes; manifest and round-trip hashes verify | Done on Windows |
| NSZ normalization | Update NSZ decompresses to a temporary verified NSP for nx_extract | Done on Windows |
| Device resource packaging | NX2Apple ROMFSARC v2 index + shards, each <=512 MB | Real 1.88 GiB RomFS packed and verified on Windows |
| Native ROMFSARC reader | Patched C reader handles segmented files on Apple host | Pending hosted macOS clang test |
| Public tree hygiene | No game archives, extracted content, or keys are tracked | Done |
| Portable CI contract | Public tree, workflow, and split/restore checks pass on Ubuntu | Done |
| Runner input staging | Local part hashes verified before copying to runner temp | Done on Windows |
| IPA structure contract | Payload, Info.plist, Mach-O, and forbidden-file checks pass | Done for synthetic IPA |
| nxnative/NX2Apple survey | Mac runtime survey for title `010090400D366000` | Pending hosted macOS runner |
| Static survey | ExeFS modules, SDK, markers, RomFS inventory, rewrite census, and host import comparison | Done on Windows |
| Provisional profile | Generated profile, module census, SDK and graphics detection | Static keys done; runtime checks pending macOS |
| Mac boot | Host reaches the title screen with no fatal error | Pending |
| iOS packaging | NX2Apple slim IPA plus local ROMFSARC resource set | Pending |
| iPhone validation | iPhone 17 Pro Max launches, renders, accepts input, saves, and plays a short route | Pending |
| Verified profile | Any fixes are committed as public code/profile data without game assets | Pending |

The first Mac run should use `survey_only`. If the survey reaches extraction
and shader classification, keep its generated files in the local resource
directory and attach only sanitized logs to public issue discussions.
