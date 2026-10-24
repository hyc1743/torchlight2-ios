# Publish and build from a public GitHub repository

The repository builds the iOS host on GitHub's Apple Silicon `macos-26`
runner, so the local Windows machine does not need a Mac. Game inputs stay
outside Git: split parts are encrypted locally and uploaded as assets of a
private Release, while the production key and resource key are stored as
Actions secrets.

Push the source without adding `Gamedata/`, `resource-parts/`, `.local/`,
`prod.keys`, or `title.keys`:

```bash
git remote add origin https://github.com/<account>/<repository>.git
git push -u origin master
```

Generate a local resource key and encrypt every verified split part:

```powershell
python scripts/encrypt_resource_release.py seal resource-parts .local/cloud-resources
Get-Content .local/torchlight2-resource.key
```

Store that value as the repository Actions secret `TORCHLIGHT2_RESOURCE_KEY`.
Store the contents of `prod.keys` as `TORCHLIGHT2_PROD_KEYS`. Create a private
Release (for example tag `resources-v1`) and upload every file in
`.local/cloud-resources`, including `cloud-manifest.json`:

```powershell
gh release create resources-v1 .local/cloud-resources/* --repo <owner>/<repo> --title "Torchlight II resources v1" --notes "Encrypted owner-local build inputs"
```

The encrypted assets contain no plaintext game data. The workflow downloads
and decrypts them only inside `$RUNNER_TEMP`, then builds the slim IPA and
packs the local ROMFS archive.

Dispatch `.github/workflows/build-ipa.yml` with `resource_release=resources-v1`.
Run `survey_only=true` first and review the generated survey and provisional
profile. After that succeeds, run the normal build. The workflow uses the
NX2Apple backend, so the IPA is slim and the merged RomFS is packed as local
ROMFSARC shards. Copy `romfs.idx` and the numbered shards into the installed
app's `Documents/romfs/` directory.

`publish_ipa` defaults to uploading the slim IPA and the separately packaged
ROMFSARC files as an Actions artifact. After downloading and extracting the
artifact, copy `romfs.idx` and every `romfs.00`, `romfs.01`, ... file into the
app's `Documents/romfs/` directory. The IPA remains slim and does not contain
the game data.
