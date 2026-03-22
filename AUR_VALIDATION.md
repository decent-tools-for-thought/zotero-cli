# AUR Validation Routine

`zotero-cli` does not keep the Arch packaging files in this repository, but the release routine should still follow a fixed validation checklist whenever the AUR package is updated.

## Required state

- Keep source hashes pinned in `PKGBUILD`.
- Regenerate `.SRCINFO` after every packaging change.
- Install the `LICENSE` file explicitly in the package.

## Validation commands

Run these from the AUR packaging checkout after updating the release version and checksums:

```bash
makepkg --printsrcinfo > .SRCINFO
namcap PKGBUILD
extra-x86_64-build
namcap ./*.pkg.tar.*
```

If `extra-x86_64-build` is not available, use the current `devtools` clean-chroot equivalent for the target architecture.
