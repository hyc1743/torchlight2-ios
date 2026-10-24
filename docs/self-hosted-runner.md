# Self-hosted macOS runner setup

The upstream toolchain needs macOS, Xcode, and Metal. A public GitHub-hosted
runner cannot access the user's local game files, so this repository uses a
self-hosted runner label and stages only local files on that machine.

1. Install a current Xcode and command line tools, Homebrew, Python 3, and the
   GitHub Actions runner on an Apple Silicon Mac.
2. Register the runner with labels `self-hosted`, `macOS`, `ARM64`, and
   `torchlight2-local`.
3. Copy the local `resource-parts/` directory to the runner's `$RUNNER_TEMP`
   as `torchlight2-resource-parts/`. Copy `prod.keys` to
   `$RUNNER_TEMP/torchlight2-prod.keys`. Do this through local storage or a
   private encrypted transport; do not commit either path.
4. Start the workflow manually. The first run should select `survey_only` so
   you can review the generated profile and logs before building an IPA.

The workflow reassembles the archives locally, runs the upstream nxnative
survey/provisional profile flow, and keeps the IPA on the runner unless the
`publish_ipa` input is deliberately enabled. No key values are printed.
