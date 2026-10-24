# Publish and build from a public GitHub repository

The local repository is ready to push, but it has no remote configured and no
GitHub credentials are available in this workspace. Create an empty **public**
repository, then push the source without adding `Gamedata/`, `resource-parts/`,
`.local/`, `prod.keys`, or `title.keys`:

```bash
git remote add origin https://github.com/<account>/<repository>.git
git push -u origin master
```

The workflow first runs its Ubuntu `portable` job. The IPA job then requires an
Apple Silicon self-hosted runner labeled `self-hosted`, `macOS`, `ARM64`, and
`torchlight2-local`. Before dispatching, place these files on that runner:

```text
$RUNNER_TEMP/torchlight2-resource-parts/manifest.json
$RUNNER_TEMP/torchlight2-resource-parts/<all part files>
$RUNNER_TEMP/torchlight2-prod.keys
```

Run `survey_only=true` first. Review the generated survey and provisional
profile. After that succeeds, run the normal build. The IPA is kept on the
self-hosted runner by default. `publish_ipa=true` is an explicit opt-in to
upload the IPA as a public Actions artifact; the IPA contains the packed game
files, so leave it false when the game data must stay local.
