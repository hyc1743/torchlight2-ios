# Cloud macOS runner setup

The workflow uses GitHub?s hosted Apple Silicon `macos-26` runner. No local Mac or self-hosted runner is required.

Before dispatching, create the encrypted resource Release and configure the `TORCHLIGHT2_RESOURCE_KEY` and `TORCHLIGHT2_PROD_KEYS` Actions secrets as described in `docs/public-build.md`. Pass the Release tag through the `resource_release` workflow input.

Plaintext resources and keys exist only under the hosted runner?s temporary directory during the build.
