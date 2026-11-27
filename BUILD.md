<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/BUILD.md) | [日本語](i18n/ja/BUILD.md) | [Español](i18n/es/BUILD.md)
<!-- /i18n:nav -->

# Building REMILIA

Status: **build infrastructure written and partly proven; first full build
deferred.** The fetch, prepare and toolchain steps have run successfully. The
compile step ran up to 260 of 1145 unified C++ files of unmodified LibreWolf
161.0-1 and was then stopped on purpose: the first full build will be of
REMILIA, once branding, security and privacy are integrated (ROADMAP Phase 5).
Steps marked *(Phase 5)* have not been completed yet.

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
recorded here after the first full build (Phase 5) — none are claimed yet.

## Path A — Docker cross-compile (planned release path)

This mirrors how LibreWolf builds its published Windows binaries (`bsys6`,
`assets/Dockerfile.windows`): a Debian image with clang, Rust with the
`x86_64-pc-windows-msvc` target, the Windows SDK fetched by Mozilla's
`taskcluster/scripts/misc/get_vs.py`, Wine (`widl`), `fxc2`, and NSIS.

*(Phase 5 for `build` and `package`)*

```sh
# from the repository root, in Git Bash or any shell with Docker
./scripts/docker.sh image       # build-environment image
./scripts/docker.sh fetch       # Firefox tarball + GPG verify, LibreWolf @ pinned commit
./scripts/docker.sh prepare     # apply LibreWolf, then REMILIA layers
./scripts/docker.sh toolchains  # clang, Rust, Windows SDK, Wine, NSIS
./scripts/docker.sh build       # mach build
./scripts/docker.sh package     # .win64.zip + sha256 + provenance in dist/
```

Notes:
- Keep the work directory on the Linux filesystem (Docker volume or WSL ext4),
  **not** under `/mnt/c` or `/mnt/d`. Cross-filesystem I/O is very slow.
- Docker Desktop's WSL2 VM gets 50% of host RAM by default. On the reference
  machine the VM ran out of memory with the defaults; it builds with
  `memory=18GB` and `swap=24GB` in `%USERPROFILE%\.wslconfig` and 6 parallel
  jobs.
- `prepare.sh` refuses to overwrite an existing prepared tree, because the
  object directory lives inside it. `--force` deletes both. Never use it on the
  kept tree in the `remilia-builds` volume.
- `REMILIA_LAYERS` selects the REMILIA categories `prepare.sh` applies: `all`
  (default), `none` (unmodified LibreWolf), or a list such as
  `security,privacy`. See `remilia/README.md`.
- `prepare.sh --staging <name>` prepares a separate tree in
  `/builds/work/staging/<name>` and never touches the kept tree. Only staging
  trees accept another layer root or exclusion list (the test fixtures).

## Tree checks without compiling (V1)

```sh
./scripts/docker.sh verify
```

This prepares staging trees and compares them with the kept tree: no
categories, each fixture category alone and all together, patch reversal, a
LibreWolf patch exclusion. It never compiles. The `remilia-builds` volume is
mounted read-only except its `staging/` directory, so the kept tree, its object
directory and the logs cannot be modified. Each staging tree uses about 6 GB
while it exists and is deleted afterwards. The report goes to
`dist/verify-tree/<timestamp>/`.

## Resource guard (Windows host)

`scripts/windows/guard-build.ps1` samples Windows and WSL2 memory during a
build and stops the build with SIGINT when memory runs out (never by shutting
down WSL or Docker). Start it before the build container, which must be
started with `--name remilia-build-run` (or pass `-Container`):

```powershell
.\scripts\windows\guard-build.ps1 -Csv "$env:TEMP\guard.csv" -Events "$env:TEMP\guard-events.log"
```

Thresholds are parameters, or keys in a `.psd1` file passed with
`-ConfigFile`. The defaults are the values used during the Phase 2 builds.

## Path B — Native Windows with MozillaBuild (developer path)

*(Phase 5, optional)*

1. Install MozillaBuild (latest), to `C:\mozilla-build`.
2. Open `C:\mozilla-build\start-shell.bat`.
3. In the prepared REMILIA tree: `./mach --no-interactive bootstrap --application-choice=browser`
   (downloads clang, Rust, Windows SDK; prompts UAC once for Defender exclusions).
4. `./mach build`, then `./mach run`.

Iteration tips: `./mach build faster` rebuilds front-end-only changes (JS/CSS/
XHTML/Fluent) in seconds; use it for UI and branding work.

## Verifying a build *(Phase 5)*

- `./mach run` launches with a temporary profile.
- `about:support` shows the version, `Multiprocess Windows`, `Fission` and
  `Sandbox` levels; each must equal the level reported by an official Firefox
  build of the same version on the same machine.
- `about:policies` shows REMILIA's policies as active.
- `about:config` → `general.config.filename` shows the REMILIA cfg.
