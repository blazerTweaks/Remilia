<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/ROADMAP.md) | [日本語](i18n/ja/ROADMAP.md) | [Español](i18n/es/ROADMAP.md)
<!-- /i18n:nav -->

# Roadmap & Status

This file is the project's record of completed tasks, pending tasks,
blockers, and decisions. Status values: `done`, `in progress`, `todo`,
`blocked`, `deferred` (postponed on purpose, work kept), and `static-verified`
(implemented and passed the static and tree checks, but not yet compiled or
tested in a running browser; never equivalent to `done`).

Last updated: 2026-11-26

## Current phase: 3a closed by static verification (2026-11-26). Phase 3b — Branding awaits the maintainer's explicit authorization.

## Working rules

1. **Isolated change categories.** Upstream, build fixes, security, privacy
   and branding are kept in separate files and patches, never mixed in one
   patch or commit, each traceable and individually reversible
   (ARCHITECTURE.md §10).
2. **A build is not a working browser.** A successful compilation only proves
   the build infrastructure. Nothing is called functional before the
   validation checklist passes and its results are recorded
   (ARCHITECTURE.md §11).
3. **The first full build is deferred, not abandoned.** REMILIA is developed
   first and compiled when branding, security and privacy are integrated
   enough to represent the project. Until then, phases close on
   static and tree checks, and their work is `static-verified`, not `done`.
4. **No automatic phase changes.** Moving to the next phase is a maintainer
   decision made after reviewing the recorded evidence.

## Sequence

1. Build infrastructure: fetch, verification, LibreWolf patches, toolchains,
   Docker, build and packaging scripts (Phase 2; the build itself is deferred).
2. Structure and configuration for REMILIA's own changes (Phase 3a).
3. Branding (Phase 3b).
4. Security (Phase 4a).
5. Privacy, including uBlock Origin integration (Phase 4b).
6. First integrated full build, packaging, and functional validation on
   Windows (Phase 5).
7. User experience, security testing, distribution (Phases 6–8).

## Validation strategy

Not every change needs a compilation. Each level below is run when it is
relevant, and lower levels always run before higher ones.

| Level | When | What | Needs |
|---|---|---|---|
| V0 Static | Every change | Fragment syntax; patch headers and `series` files; category boundaries; duplicate prefs or policies across categories; `python i18n/i18n.py check`; unit tests (`python -m unittest discover -s tests/layers`, `python -m unittest discover -s tests/validation`) | Python on the host. No Docker, no compilation |
| V1 Tree | Before closing each phase | Fresh preparation into a separate staging tree: every patch applies with zero fuzz and reverses cleanly; each category alone and all together; report of files touched by several categories; a tree with no categories is identical to the LibreWolf baseline | Docker, no compilation. Never touches the existing object directory |
| V2 Full build | Phase 5, when branding, security and privacy are integrated | `build.sh`, `package.sh`, sha256, provenance file | Docker, hours of compilation |
| V3 Functional | After the first V2 package | The [validation checklist](#validation-checklist) on Windows, results in `internal/evidence/<date>-<build>/` (local, not published) | The maintainer's Windows machine |

Rules:

- If a change can only be validated by compiling it, the reason is stated and
  approved before the build starts.
- V0 and V1 prove that changes apply, are consistent and are separable. They
  do not prove that anything works at run time. That is V2 and V3's job.
- Things that only V2/V3 can confirm: `mozconfig` options, that source patches
  compile, icons and resources inside the executables, the run-time effect of
  prefs and policies, sandboxing, uBlock Origin bundling.

## Blockers & open decisions

| ID | Item | Needed by | Owner |
|---|---|---|---|
| B1 | **Project domain** for update server, distribution ID (`--with-distribution-id`), support links | Phase 3b (branding), Phase 8 (updates) | Maintainer |
| B2 | **MAR update-signing key pair** generated and stored offline | Phase 4a; before any public build | Maintainer |
| B3 | **Safe Browsing API key**: obtain one, or accept the documented fallback (SECURITY.md §S3) | Phase 4a | Maintainer |
| B4 | **Windows code-signing (Authenticode) certificate.** Without it SmartScreen warns on the installer | Phase 8 | Maintainer |
| B5 | ~~License for REMILIA's own files~~ Resolved 2026-11-26: MPL-2.0 (`LICENSE`); inherited files keep their licenses | Phase 3a | Maintainer |
| B6 | Install **MozillaBuild** (needs an interactive installer and UAC) for build path B | Phase 5 (optional) | Maintainer |
| D1 | Default search engine | Phase 4b | Open |
| D2 | Sanitize-on-shutdown default (privacy vs. staying logged in) | Phase 4b | Open |
| D3 | DoH default (off vs. first-run choice) | Phase 4b | Open |
| D4 | Toolbar protection panel: uBO's popup vs. a REMILIA panel over uBO data | Phase 6 | Open |

## Phase 1 — Research `done`

- [x] Survey Firefox source: canonical repo is now `github.com/mozilla-firefox/firefox` (Git); release tarballs are GPG-signed.
- [x] Survey LibreWolf: `codeberg.org/librewolf/source` (patches, settings, build) and `bsys6` (packaging, Windows cross-compile).
- [x] Firefox Windows build requirements (MozillaBuild, `mach bootstrap`, 40 GB+, no spaces in paths).
- [x] How LibreWolf builds Windows binaries (Docker cross-compile on Debian).
- [x] Extension integration: how LibreWolf installs uBO; uBO managed-storage semantics verified in uBO source.
- [x] Privacy configuration review of `librewolf.cfg` v8.6 (privacy, networking, fingerprinting, security, extensions, updater sections).
- [x] Licensing: MPL-2.0 (Firefox, LibreWolf), GPL-3.0 (uBO), Firefox trademark, Touhou fan-work considerations.
- [x] Maintenance model (4-week cadence, chemspills).
- [x] Documentation set: README, ARCHITECTURE, PRIVACY, SECURITY, BUILD, UPSTREAM, ROADMAP, CONTRIBUTING.
- [x] Upstream pins recorded (`upstream/pins.env`).
- [x] Documentation translations (pt-BR, ja, es) with a synchronization checker (`i18n/i18n.py`).
- [ ] Not done: full read of `librewolf.cfg` UI/telemetry/region sections, and a line-by-line review of all 68 LibreWolf patches. Moved to Phases 4a/4b.

## Phase 2 — Build infrastructure `deferred`

Goal: build infrastructure able to produce a Windows x64 executable from the
LibreWolf 161.0-1 base. A standalone build of unmodified LibreWolf is no
longer a goal. The infrastructure is kept and its remaining steps
move to Phase 5.

- [x] Build-environment image `build/windows-cross.Dockerfile` (derived from bsys6, base image pinned by digest).
- [x] `scripts/fetch.sh`: Firefox tarball GPG-verified against the pinned Mozilla key; LibreWolf, l10n and bsys6 at pinned commits; tampered tarball rejected (tested).
- [x] `scripts/prepare.sh`: pristine copy → LibreWolf `patch.sh` (68 patches, 0 fuzz/rejects) → Windows cross-compile mozconfig.
- [x] l10n pinned to a commit of Mozilla's `firefox-l10n` (LibreWolf's mirror returned HTTP 502; same commit, same content).
- [x] `scripts/toolchains.sh`: clang, sysroots, Wine, NSIS, Windows SDK in the `remilia-mozbuild` volume (completion stamp present, 2026-11-26).
- [x] Build fixes found by running the build: work directory moved to `/builds/work` (clang-cl read `/work/...` as its `/wo` option); WSL2 VM given `memory=18GB`, `swap=24GB` after it ran out of memory; 6 parallel jobs.
- [x] Validation harness `tests/validation/validate_win64.py` written. Not yet run against a REMILIA build.
- [x] Build resource guard moved into the repository as `scripts/windows/guard-build.ps1` (guard v2 logic unchanged; thresholds and paths are parameters). Dry run on 2026-11-26; not yet used for a build from this location.
- [ ] `deferred` `scripts/build.sh` on unmodified LibreWolf: three attempts logged; the last one was stopped on purpose on 2026-11-26 at 260 of 1145 unified C++ files. The object directory (6.9 GB) and all logs are kept in the `remilia-builds` volume.
- [ ] `deferred` `scripts/package.sh`, measured build time and resources in BUILD.md, choice of the authoritative build path (to be documented in BUILD.md): moved to Phase 5.
- [ ] Diff LibreWolf `main` (ed92167b) vs tag `161.0-1` (e2baf325) to understand post-release changes.

Volumes `remilia-work`, `remilia-builds` and `remilia-mozbuild`, the downloads,
the logs and the toolchains are kept. Nothing is cleaned up.

## Phase 3a — Structure and configuration `static-verified`

No browser behaviour changes in this phase. It builds the mechanism that the
next phases fill. Its rules are described in `remilia/README.md` and
ARCHITECTURE.md §10. Every item below passed V0 and V1; the results are
recorded by the maintainer and not published. None of it is `done`: the
assembled files have not been read by a running browser yet (Phase 5).

Closed on 2026-11-26 by static verification (V0 + V1), after the maintainer
reviewed the results and the final audit. The items stay `static-verified`
until Phase 5 provides run-time evidence.

- [x] `static-verified` License: MPL-2.0 for REMILIA's own files (`LICENSE`, B5).
- [x] `static-verified` Category contract `remilia/README.md`: layout, patch headers, `prefs.cfg`, `policies.json`, `mozconfig`, `files/` + `replaces.txt`, `deviations.tsv`.
- [x] `static-verified` `scripts/remilia_layers.py`: V0 checks and deterministic assembly of `librewolf.cfg`, `policies.json` and `mozconfig`, with a header per category. Duplicates across categories and undeclared overrides of LibreWolf fail; an override must keep LibreWolf's function; a `lockPref` redefinition is marked `runtime-unverified`.
- [x] `static-verified` LibreWolf base snapshot `upstream/librewolf-base/`, checked against the prepared tree.
- [x] `static-verified` `prepare.sh`: `REMILIA_LAYERS`, patches at zero fuzz, overlays, assembly, provenance with versions, commits, categories and hashes; `--staging` trees isolated from the kept tree.
- [x] `static-verified` Exclusion list `upstream/librewolf-exclude.txt` (empty for 161.0-1).
- [x] `static-verified` V1 script `scripts/verify-tree.sh` (`docker.sh verify`), the build volume read-only except `staging/`.
- [x] `static-verified` Test fixtures `tests/layers/` (valid set, 12 invalid sets, 49 unit tests); never packaged.
- [x] `static-verified` LibreWolf identity inventory for Phase 3b (summary in UPSTREAM.md).
- [x] Gate (V1): the `REMILIA_LAYERS=none` tree is identical to the kept LibreWolf 161.0-1 tree except for 1110 entries that exist only in the kept tree and were created after its preparation (build by-products); every difference is listed in the results.
- [x] Maintainer review of the Phase 3a results and the final audit (approved 2026-11-26).

Known limitation carried into later phases: overrides are detected only
against `librewolf.cfg`, `policies.json` and `mozconfig`. Pref defaults set
elsewhere (default-pref files, static prefs, the branding pref file, code)
are not detected, and the identity inventory only covers text lines that
contain "librewolf" (`remilia/README.md`, "What the checks cover").

## Phase 3b — Branding `todo`

Category: branding only. No privacy or security changes in this phase.
Not started: awaiting the maintainer's explicit authorization.

- [ ] Name REMILIA: application name, remoting name, executable identity, profile directory (see UPSTREAM.md touch points). The internal `lw/` directory, `librewolf.cfg` name and `librewolf.*` pref namespace stay, so that security and privacy never depend on branding (`remilia/README.md`).
- [ ] Logo concept: symmetrical bat-wing pair around a scarlet diamond. SVG master, tested at 16/32/64/128/256 px.
- [ ] Variants: full colour, monochrome, light-background, dark-background, transparent.
- [ ] `.ico` generation for Windows; installer bitmaps.
- [ ] Branding directory replacing `--with-branding`.
- [ ] Browser theme with the palette from the brief (Firefox CSS, no framework).
- [ ] Start page (local, no remote content, every element optional).
- [ ] Pending from 3a: list the defaults in `browser/branding/librewolf/pref/firefox-branding.js` and the identity strings the inventory cannot see (remaining "Firefox" strings, binary assets); check every branding pref against them.
- [ ] Gate (V0 + V1): branding alone and with the other categories; results recorded. Run-time checks wait for Phase 5.

## Phase 4a — Security `todo`

Category: security only.

- [ ] Extension signing required (SECURITY.md S1).
- [ ] REMILIA updater identity: MAR keys, update host (S2; needs B1, B2).
- [ ] Certificates: review of the inherited settings (SECURITY.md).
- [ ] Sandboxing: inherited levels kept; differences from official Firefox checked in Phase 5.
- [ ] Safe Browsing decision (S3, B3) and restricted extension domains (S4).
- [ ] Line-by-line review of the security-relevant LibreWolf patches and `librewolf.cfg` sections.
- [ ] Run-time check of `runtime-unverified` prefs and policies (such as `lockPref` redefinitions) on an official LibreWolf 161.0-1 binary, for 4a and 4b (`remilia/README.md`).
- [ ] Pending from 3a: security-relevant pref defaults set outside `librewolf.cfg` (default-pref files and static prefs, including LibreWolf's patched values) are not detected by the checks; review them and decide whether the tool must cover them.
- [ ] Gate (V0 + V1): security alone and with all categories so far; results recorded.

## Phase 4b — Privacy `todo`

Category: privacy only.

- [ ] Privacy prefs with only the documented deviations; everything else inherited from LibreWolf: tracking protection, fingerprinting, telemetry, cookies and storage, DNS over HTTPS, WebRTC.
- [ ] Resolve D1–D3.
- [ ] Settings UI: clear explanations, exposing RFP side effects and toggles.
- [ ] uBlock Origin: pin the AMO-signed xpi (SHA-256) and bundle it in `distribution/extensions/`.
- [ ] REMILIA `assets.json` (uBO stock plus `spa-1`, the LibreWolf additions, Brazilian lists under evaluation), delivered via `assetsBootstrapLocation`.
- [ ] Pending from 3a: privacy-relevant pref defaults set outside `librewolf.cfg` are not detected by the checks; review them before setting privacy prefs, and decide whether the tool must cover them.
- [ ] Gate (V0 + V1): privacy alone and with all categories; results recorded.

## Phase 5 — First integrated build and validation `todo`

The first full build of REMILIA: Phase 2's infrastructure applied to the
integrated categories.

- [ ] V2: build, package, sha256, provenance. Record build time, disk and RAM use in BUILD.md.
- [ ] Choose the authoritative release build path and document it in BUILD.md. Optional: path B (native MozillaBuild, after B6) for debugging.
- [ ] V3: [validation checklist](#validation-checklist), results in `internal/evidence/<date>-<build>/` (format in `tests/validation/README.md`).
- [ ] Packet capture of a fresh profile: list every outbound connection in PRIVACY.md.
- [ ] uBlock Origin: first-run offline behaviour, AMO updates, established ad-block test pages; results recorded honestly.
- [ ] Items from Phases 3a–4b move from `static-verified` to `done` only with recorded evidence.

Phase 5 closes only when the maintainer has reviewed the recorded results.

## Phase 6 — User experience `todo`
Toolbar, tabs, address bar, downloads, bookmarks, settings, and decision D4
(build a panel only on real uBO data). These are largely Firefox's existing
features; REMILIA work is theming (branding) and configuration
(privacy/security), filed by category.

## Phase 7 — Security & testing `todo`
BrowserLeaks, EFF Cover Your Tracks, DNS and WebRTC leak tests, compatibility
suite, performance profiling. Results are recorded with dates and versions in
`internal/evidence/<date>-<build>/` (local, not published).

## Phase 8 — Distribution `todo`
NSIS installer and portable zip (both exist in LibreWolf's bsys6), MAR update
pipeline, update server, release documentation. Depends on B1, B2, B4.

## Validation checklist

Run on Windows 10 x64 (the maintainer machine) with a fresh profile. Each check
is recorded as passed, failed, or not applicable with the reason. Evidence is
collected by `tests/validation/validate_win64.py`; a person writes the verdicts.

| Check | How |
|---|---|
| Startup | Starts from the unzipped package; creates a profile; no crash; `about:support` opens |
| Real-site navigation | A fixed list of real sites (news, video, maps, webmail login page, a government site, a Brazilian bank's public page) loads and renders |
| JavaScript and web compatibility | JS-heavy sites work; a standard web-platform test page runs |
| Audio and video | HTML5 audio and video playback (open codecs and H.264); note DRM/EME state (disabled by LibreWolf policy) |
| Graphics acceleration | `about:support` → Graphics: compositor, WebRender, GPU acceleration status |
| Firefox extensions | Install a signed extension from addons.mozilla.org; enable, disable, remove |
| uBlock Origin | Present on first run; blocks on an ad-block test page; dashboard opens |
| Multiprocess | `about:support` multiprocess windows and Fission; `about:processes` shows separate content processes |
| Sandboxing | `about:support` sandbox levels equal those of official Firefox 161 on the same machine |
| Profile management | `about:profiles`: create, switch, delete a profile; data persists across restart as configured |
| Downloads | Download a file; progress, location, history, dangerous-file warning |
| Updates | Not applicable while the build has `--disable-updater` (LibreWolf's base mozconfig); applies once Phase 4a's updater identity exists |
| Package integrity | sha256 recorded; package re-extracts identically; `winchecksec` on `.exe`/`.dll` (ASLR, DEP, CFG) |

## Decisions in effect

| Decision | Explained in | Status |
|---|---|---|
| Overlay on a pinned LibreWolf release over Firefox Release | ARCHITECTURE.md §2 | Accepted |
| Inherit `librewolf.cfg`; deviations only with written reasons | PRIVACY.md, SECURITY.md, `remilia/README.md` | Accepted |
| Bundle signed uBO xpi; defaults via `assetsBootstrapLocation`, not `toOverwrite` | ARCHITECTURE.md §6 | Accepted |
| Isolated change categories: upstream, build fixes, security, privacy, branding | ARCHITECTURE.md §10 | Accepted |
| A successful build is not a working browser; validation gate before anything is called functional | ARCHITECTURE.md §11; Validation checklist (this file) | Accepted |
| Defer the first full build until branding, security and privacy are integrated; V0–V3 validation levels | ARCHITECTURE.md §11; Validation strategy (this file) | Accepted |
| Phase 3a decisions: MPL-2.0, AutoConfig assembly rules, isolated staging, internal `librewolf.*` names kept, fixtures, resource guard | `remilia/README.md`; CONTRIBUTING.md (licensing); BUILD.md (resource guard) | Accepted |
