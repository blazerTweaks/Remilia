<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/ROADMAP.md) | [日本語](i18n/ja/ROADMAP.md) | [Español](i18n/es/ROADMAP.md)
<!-- /i18n:nav -->

# Roadmap & Status

This file is the project's record of completed tasks, pending tasks,
blockers, and decisions. Status values: `done`, `in progress`, `todo`, `blocked`.

Last updated: 2026-11-25

## Current phase: 2 — Browser foundation, step 1 (toolchain).

## Working rules

1. **Isolated change categories.** Upstream, build fixes, security, privacy
   and branding are kept in separate files and patches, never mixed in one
   patch or commit, each traceable and individually reversible
   (ARCHITECTURE.md §10, ADR 0004).
2. **A build is not a working browser.** A successful compilation only proves
   the build infrastructure. Nothing is called functional, and no phase is
   closed, before the validation checklist passes and its results are
   recorded (ARCHITECTURE.md §11, ADR 0005).

## Sequence

1. Finish the toolchain.
2. Build the original LibreWolf, without REMILIA changes.
3. Validate the produced executable.
4. Record the test results.
5. Establish the structure for REMILIA's own patches and configuration.
6. Start the branding changes.
7. Implement security and privacy configuration, in separate stages.
8. Validate each set of changes individually.

Steps 1–4 are Phase 2, step 5 is Phase 3a, step 6 is Phase 3b, step 7 is
Phases 4a, 4b and 5, and step 8 is the gate that closes each of those phases.

## Blockers & open decisions

| ID | Item | Needed by | Owner |
|---|---|---|---|
| B1 | **Project domain** for update server, distribution ID (`--with-distribution-id`), support links | Phase 3b (branding), Phase 8 (updates) | Maintainer |
| B2 | **MAR update-signing key pair** generated and stored offline | Phase 4a; before any public build | Maintainer |
| B3 | **Safe Browsing API key**: obtain one, or accept the documented fallback (SECURITY.md §S3) | Phase 4a | Maintainer |
| B4 | **Windows code-signing (Authenticode) certificate.** Without it SmartScreen warns on the installer | Phase 8 | Maintainer |
| B5 | **License for REMILIA's own files.** Recommendation: MPL-2.0, which patches to MPL files require anyway | Phase 3a | Maintainer |
| B6 | Install **MozillaBuild** (needs an interactive installer and UAC) for build path B | Phase 2 (optional) | Maintainer |
| D1 | Default search engine | Phase 4b | Open |
| D2 | Sanitize-on-shutdown default (privacy vs. staying logged in) | Phase 4b | Open |
| D3 | DoH default (off vs. first-run choice) | Phase 4b | Open |
| D4 | Toolbar protection panel: uBO's popup vs. a REMILIA panel over uBO data | Phase 5 | Open |

## Phase 1 — Research `done`

- [x] Survey Firefox source: canonical repo is now `github.com/mozilla-firefox/firefox` (Git); release tarballs are GPG-signed.
- [x] Survey LibreWolf: `codeberg.org/librewolf/source` (patches, settings, build) and `bsys6` (packaging, Windows cross-compile).
- [x] Firefox Windows build requirements (MozillaBuild, `mach bootstrap`, 40 GB+, no spaces in paths).
- [x] How LibreWolf builds Windows binaries (Docker cross-compile on Debian).
- [x] Extension integration: how LibreWolf installs uBO; uBO managed-storage semantics verified in uBO source.
- [x] Privacy configuration review of `librewolf.cfg` v8.6 (privacy, networking, fingerprinting, security, extensions, updater sections).
- [x] Licensing: MPL-2.0 (Firefox, LibreWolf), GPL-3.0 (uBO), Firefox trademark, Touhou fan-work considerations.
- [x] Maintenance model (4-week cadence, chemspills).
- [x] Documentation set: README, ARCHITECTURE, PRIVACY, SECURITY, BUILD, UPSTREAM, ROADMAP, CONTRIBUTING, ADRs.
- [x] Upstream pins recorded (`upstream/pins.env`).
- [x] Documentation translations (pt-BR, ja, es) with a synchronization checker (`i18n/i18n.py`).
- [ ] Not done: full read of `librewolf.cfg` UI/telemetry/region sections, and a line-by-line review of all 68 LibreWolf patches. Moved to Phases 4a/4b.

## Phase 2 — Browser foundation `in progress`

Goal: prove that the build infrastructure produces a valid Windows executable
from **unmodified LibreWolf 161.0-1**, and verify that executable. No REMILIA
changes are applied in this phase.

### Step 1 — Toolchain `in progress`

- [x] Build-environment image `build/windows-cross.Dockerfile` (derived from bsys6, base image pinned by digest).
- [x] `scripts/fetch.sh`: Firefox tarball GPG-verified against the pinned Mozilla key; LibreWolf, l10n and bsys6 at pinned commits; tampered tarball rejected (tested).
- [x] `scripts/prepare.sh`: pristine copy → LibreWolf `patch.sh` (68 patches, 0 fuzz/rejects) → Windows cross-compile mozconfig.
- [x] l10n pinned to a commit of Mozilla's `firefox-l10n` (LibreWolf's mirror returned HTTP 502; same commit, same content).
- [ ] `scripts/toolchains.sh`: clang, sysroots, Wine, NSIS, Windows SDK into the `remilia-mozbuild` volume.

### Step 2 — Build unmodified LibreWolf `todo`

- [ ] `scripts/build.sh` for Windows x64 (path A, Docker cross-compile). Record time, disk and RAM use.
- [ ] `scripts/package.sh`: en-US `.win64.zip` + sha256 + provenance file in `dist/`.

### Step 3 — Validate the executable `todo`

Run on Windows 10 x64 (the maintainer machine) with a fresh profile. Each check
is recorded as passed, failed, or not applicable with the reason.

| Check | How |
|---|---|
| Startup | Starts from the unzipped package; creates a profile; no crash; `about:support` opens |
| Real-site navigation | A fixed list of real sites (news, video, maps, webmail login page, a government site, a Brazilian bank's public page) loads and renders |
| JavaScript and web compatibility | JS-heavy sites work; a standard web-platform test page runs |
| Audio and video | HTML5 audio and video playback (open codecs and H.264); note DRM/EME state (disabled by LibreWolf policy) |
| Graphics acceleration | `about:support` → Graphics: compositor, WebRender, GPU acceleration status |
| Firefox extensions | Install a signed extension from addons.mozilla.org; enable, disable, remove |
| uBlock Origin | Installed by LibreWolf policy on first run; blocks on an ad-block test page; dashboard opens |
| Multiprocess | `about:support` multiprocess windows and Fission; `about:processes` shows separate content processes |
| Sandboxing | `about:support` sandbox levels equal those of official Firefox 161 on the same machine |
| Profile management | `about:profiles`: create, switch, delete a profile; data persists across restart as configured |
| Downloads | Download a file; progress, location, history, dangerous-file warning |
| Updates | Not applicable to this build: LibreWolf's base mozconfig has `--disable-updater`. Covered in Phase 4a |
| Package integrity | sha256 recorded; package re-extracts identically; `winchecksec` on `.exe`/`.dll` (ASLR, DEP, CFG) |

### Step 4 — Record results `todo`

- [ ] Write `tests/results/<date>-librewolf-161.0-1-win64.md` (ADR 0005 format).
- [ ] Update BUILD.md with measured build time and resource use, and the real commands.
- [ ] Choose the authoritative release build path (ADR).
- [ ] Optional: path B (native MozillaBuild, after B6) for debugging.
- [ ] Diff LibreWolf `main` (ed92167b) vs tag `161.0-1` (e2baf325) to understand post-release changes.

Phase 2 closes only when the maintainer has reviewed the recorded results.

## Phase 3a — REMILIA change structure `todo`

- [ ] Create `remilia/build-fixes/`, `remilia/security/`, `remilia/privacy/`, `remilia/branding/` as content arrives (ADR 0004).
- [ ] `prepare.sh`: apply categories in fixed order; assemble the AutoConfig file, `policies.json` and `mozconfig` with per-category headers; fail on duplicate prefs/policies; select subsets with `REMILIA_LAYERS`.
- [ ] `upstream/` exclusion list for LibreWolf patches, each with an ADR.
- [ ] Check: a tree prepared with no categories is identical to the Phase 2 tree.

## Phase 3b — Branding `todo`

Category: branding only. No privacy or security changes in this phase.

- [ ] Logo concept: symmetrical bat-wing pair around a scarlet diamond. SVG master, tested at 16/32/64/128/256 px.
- [ ] Variants: full colour, monochrome, light-background, dark-background, transparent.
- [ ] `.ico` generation for Windows; installer bitmaps.
- [ ] Branding directory replacing `--with-branding`; app name, remoting name, profile directory, cfg filename (see UPSTREAM.md touch points).
- [ ] Browser theme with the palette from the brief (Firefox CSS, no framework).
- [ ] Start page (local, no remote content, every element optional).
- [ ] Gate: validation checklist with branding alone; results recorded.

## Phase 4a — Security `todo`

Category: security only.

- [ ] Extension signing required (SECURITY.md S1).
- [ ] REMILIA updater identity: MAR keys, update host (S2; needs B1, B2).
- [ ] Safe Browsing decision (S3, B3) and restricted extension domains (S4).
- [ ] Gate: validation checklist with security alone, then with all categories so far; results recorded.

## Phase 4b — Privacy `todo`

Category: privacy only.

- [ ] Privacy prefs with only the documented deviations; everything else inherited from LibreWolf.
- [ ] Resolve D1–D3.
- [ ] Packet capture of a fresh profile: list every outbound connection in PRIVACY.md.
- [ ] Settings UI: clear explanations, exposing RFP side effects and toggles.
- [ ] Gate: validation checklist with privacy alone, then with all categories; results recorded.

## Phase 5 — Ad blocking `todo`

Category: privacy.

- [ ] Pin uBO (AMO-signed xpi, SHA-256) and bundle it in `distribution/extensions/`.
- [ ] REMILIA `assets.json` (uBO stock plus `spa-1`, the LibreWolf additions, Brazilian lists under evaluation); deliver it via `assetsBootstrapLocation`.
- [ ] Validate first-run offline behaviour and AMO updates.
- [ ] Resolve D4; build the panel only on real uBO data.
- [ ] Test against established ad-block test pages; record results honestly.
- [ ] Gate: validation checklist; results recorded.

## Phase 6 — User experience `todo`
Toolbar, tabs, address bar, downloads, bookmarks, settings. These are largely
Firefox's existing features; REMILIA work is theming (branding) and
configuration (privacy/security), filed by category.

## Phase 7 — Security & testing `todo`
BrowserLeaks, EFF Cover Your Tracks, DNS and WebRTC leak tests, compatibility
suite, performance profiling. Results go in `tests/results/` with dates and versions.

## Phase 8 — Distribution `todo`
NSIS installer and portable zip (both exist in LibreWolf's bsys6), MAR update
pipeline, update server, release documentation. Depends on B1, B2, B4.

## Decision log

| ADR | Decision | Status |
|---|---|---|
| 0001 | Overlay on a pinned LibreWolf release over Firefox Release | Accepted |
| 0002 | Inherit `librewolf.cfg`; deviations only with written reasons | Accepted |
| 0003 | Bundle signed uBO xpi; defaults via `assetsBootstrapLocation`, not `toOverwrite` | Accepted |
| 0004 | Isolated change categories: upstream, build fixes, security, privacy, branding | Accepted |
| 0005 | A successful build is not a working browser; validation gate per phase | Accepted |
