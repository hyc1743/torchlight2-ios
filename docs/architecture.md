# Build and data architecture

```mermaid
flowchart LR
  A[Local NSP/NSZ/DLC] --> B[split_resources.py]
  B --> C[Local parts <= 500,000,000 bytes]
  C --> D[assemble_resources.py]
  D --> E[Local Gamedata]
  K[Local prod.keys] --> F[build_local_ipa.py]
  E --> F
  U[Public nxnative submodule] --> F
  F --> G[Survey / provisional profile / IPA]
  G --> H[Self hosted macOS GitHub runner]
  H --> I[User sideloads IPA to iPhone]
```

The public repository is a build recipe and wrapper. The archive contents and
keys stay on the user's own storage. The first Torchlight II build is an
upstream provisional-profile experiment because no verified profile is present
yet; a playable build requires iterative bring-up on macOS and then testing on
the iPhone.
