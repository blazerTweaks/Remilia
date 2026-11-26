<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/BUILD.md) | [日本語](i18n/ja/BUILD.md) | [Español](i18n/es/BUILD.md)
<!-- /i18n:nav -->

# Building REMILIA

Status: **not yet buildable.** The fetch/patch/build scripts are Phase 2 work.
This document describes the verified requirements and the planned procedure.
Steps marked *(Phase 2)* have not been executed yet.

## Requirements

From Mozilla's Windows build guide (`docs/setup/windows_build.md`, mozilla-firefox/firefox `main`):

- Windows 10/11 x64.
- 8 GB+ RAM (4 GB minimum). 16–32 GB strongly recommended for optimized builds.
- **≥ 40 GB free disk** per source tree + object directory.
- No spaces in the path to the source or to MozillaBuild.
- Recommended: a **Dev Drive** (5–10% faster builds; Windows 11 only).
- Add the source directory and `%USERPROFILE%\.mozbuild` to Windows Defender exclusions (bootstrap offers to do this).

Reference machine (maintainer): Ryzen 5 3600 (6C/12T), 32 GB RAM, Windows 10 Pro
19045, Docker Desktop (WSL2), Visual Studio installed. Build times will be
recorded here after Phase 2 — none are claimed yet.

## Path A — Docker cross-compile (planned release path)

This mirrors how LibreWolf builds its published Windows binaries (`bsys6`,
`assets/Dockerfile.windows`): a Debian image with clang, Rust with the
`x86_64-pc-windows-msvc` target, the Windows SDK fetched by Mozilla's
`taskcluster/scripts/misc/get_vs.py`, Wine (`widl`), `fxc2`, and NSIS.

*(Phase 2)*

```sh
# inside WSL2 or any x86_64 Linux with Docker
./scripts/fetch.sh            # Firefox tarball + GPG verify, LibreWolf @ pinned commit
./scripts/prepare.sh          # apply LibreWolf, then REMILIA layers
./scripts/build.sh windows    # runs mach in the build container
```

Notes:
- Keep the work directory on the Linux filesystem (Docker volume or WSL ext4),
  **not** under `/mnt/c` or `/mnt/d`. Cross-filesystem I/O is very slow.
- Docker Desktop's WSL2 VM gets 50% of host RAM by default. Raise it in
  `%USERPROFILE%\.wslconfig` (`memory=24GB`) if linking runs out of memory.

## Path B — Native Windows with MozillaBuild (developer path)

*(Phase 2)*

1. Install MozillaBuild (latest), to `C:\mozilla-build`.
2. Open `C:\mozilla-build\start-shell.bat`.
3. In the prepared REMILIA tree: `./mach --no-interactive bootstrap --application-choice=browser`
   (downloads clang, Rust, Windows SDK; prompts UAC once for Defender exclusions).
4. `./mach build`, then `./mach run`.

Iteration tips: `./mach build faster` rebuilds front-end-only changes (JS/CSS/
XHTML/Fluent) in seconds; use it for UI and branding work.

## Verifying a build *(Phase 2)*

- `./mach run` launches with a temporary profile.
- `about:support` shows the version, `Multiprocess Windows`, `Fission` and
  `Sandbox` levels; each must equal the level reported by an official Firefox
  build of the same version on the same machine.
- `about:policies` shows REMILIA's policies as active.
- `about:config` → `general.config.filename` shows the REMILIA cfg.
