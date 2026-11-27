<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/ARCHITECTURE.md) | [日本語](i18n/ja/ARCHITECTURE.md) | [Español](i18n/es/ARCHITECTURE.md)
<!-- /i18n:nav -->

# REMILIA Browser — Architecture

Project codename: **SCARLET**
Status: build infrastructure written and partly proven; first full build deferred
until REMILIA's categories are integrated, so that the first full build is of
REMILIA rather than unmodified LibreWolf. The category mechanism
exists (Phase 3a, `static-verified`), but no REMILIA change has been applied yet.
Last reviewed: 2026-11-26

This document records *what REMILIA is built from, how the layers fit together,
and why*.

---

## 1. Summary

REMILIA is a **downstream build of Firefox (Gecko)**, layered on top of
**LibreWolf's patch set and privacy configuration**, with a thin, separately
maintained layer of REMILIA patches, settings, and branding.

REMILIA does **not** contain a browser engine of its own, does not wrap a
WebView, and is not an Electron app. Every page is rendered by Gecko, every
request goes through Necko (Firefox's network stack), and every content process
runs inside Firefox's Windows sandbox.

```
┌───────────────────────────────────────────────────────────────┐
│ Layer 4  REMILIA branding & assets                            │
│          icons, wordmark, about pages, installer art, theme   │
├───────────────────────────────────────────────────────────────┤
│ Layer 3  REMILIA build-fixes, security, privacy               │
│          one directory per category: patches, prefs,          │
│          policies, mozconfig; applied/reverted separately     │
├───────────────────────────────────────────────────────────────┤
│ Layer 2  LibreWolf (pinned commit of librewolf/source)        │
│          68 patches, librewolf.cfg, policies, uBO assets      │
├───────────────────────────────────────────────────────────────┤
│ Layer 1  Upstream Firefox release source tarball              │
│          GPG-verified against Mozilla's release key           │
└───────────────────────────────────────────────────────────────┘
```

Each layer is applied **in order, by script, to a pristine tree**. Nothing in
layer 1 or 2 is edited by hand inside this repository. This is what makes
upstream security releases cheap to absorb (see [UPSTREAM.md](UPSTREAM.md)).

---

## 2. Foundation choice

### 2.1 Options considered

| Option | Verdict | Reason |
|---|---|---|
| Write an engine | Rejected | Not feasible; explicitly forbidden by project rules. |
| Chromium / CEF / Electron | Rejected | Project goal is a Gecko browser; Chromium base would lose Firefox extension compatibility, Total Cookie Protection and RFP, and offers no documented benefit for these goals. |
| Fork Firefox directly (mozilla-firefox/firefox) | Rejected as primary | Would require re-doing everything LibreWolf already maintains (telemetry removal, 68 patches, settings). Kept as the *upstream of the upstream*. |
| **Fork LibreWolf via git fork of `librewolf/source`** | Rejected | Merge conflicts every 4-week release; REMILIA changes would be interleaved with LibreWolf's history, making provenance unclear. |
| **Overlay on a pinned LibreWolf commit** | **Chosen** | LibreWolf's own build already works as "verified Firefox tarball + ordered patch list + copied files". REMILIA repeats the same pattern one level up. Clear 4-layer separation, small diffs, easy rebase. |
| Firefox ESR instead of Release | Rejected for now | LibreWolf tracks Release; following ESR would forfeit LibreWolf's maintenance. Revisit if REMILIA's maintainer capacity cannot keep a 4-week cadence (see §8). |

### 2.2 What LibreWolf actually is (verified 2026-11-25)

Source: `https://codeberg.org/librewolf/source`, `main` at commit
`ed92167b4c56` (Makefile `VERSION = 161.0`, `RELEASE = 1`). The released tag
`161.0-1` is commit `e2baf3254fc7`; REMILIA pins the tag, not `main`.

- **Build input:** `firefox-<ver>.source.tar.xz` from `archive.mozilla.org`,
  verified with `gpg --verify` against `assets/MOZILLA_PUBKEY.asc`.
- **`scripts/patch.sh`** then, inside the extracted tree:
  - copies `assets/mozconfig.new` → `mozconfig`;
  - copies branding (`themes/browser/branding/librewolf`), search config,
    `about:librewolf` page, and **LibreWolf's MAR update-signing public keys**
    into `toolkit/mozapps/update/updater/release_{primary,secondary}.der`;
  - copies `settings/librewolf.cfg`, `settings/distribution/policies.json`,
    `settings/defaults/pref/local-settings.js` into `lw/`;
  - applies every patch in `assets/patches.txt` in order (`patch -p1`);
  - removes the OpenAI ML backend, forces all Glean pings to follow the
    data-reporting pref, rewrites "Firefox" in `appstrings.properties`;
  - fetches Firefox l10n and overlays LibreWolf strings.
- **Settings:** `librewolf.cfg` (~1000 lines, AutoConfig, `lockPref`/`pref`/
  `defaultPref`) loaded through `general.config.filename` with the AutoConfig
  sandbox enabled; `policies.json` (enterprise policies).
- **uBlock Origin:** *not* bundled as a file. `policies.json` →
  `ExtensionSettings["uBlock0@raymondhill.net"]` with
  `installation_mode: normal_installed` and an AMO `install_url`; uBO is
  downloaded from addons.mozilla.org on first run. A Gecko patch
  (`custom-ubo-assets-bootstrap-location.patch`) injects
  `adminSettings.assetsBootstrapLocation` into uBO's managed storage so that
  uBO's default list selection comes from LibreWolf's `uBOAssets.json`.
- **Windows builds** are produced by `bsys6` by **cross-compiling on Debian in
  Docker** (clang, Rust MSVC targets, the Windows SDK fetched by Mozilla's
  `get_vs.py`, Wine for `widl`, `fxc2`, NSIS). LibreWolf's README states that
  *native* Windows builds are "not very well tested".
- **Updates:** bsys6 produces signed `.mar` files and an `update.xml`; the
  LibreWolf tree points `MOZ_APPUPDATE_HOST` to `update.librewolf.net`.

---

## 3. Repository layout (target)

```
REMILIA/
├── upstream/               # category "upstream": pins.env (Firefox, LibreWolf,
│                           #   l10n, bsys6, base image, Rust); librewolf-exclude.txt;
│                           #   librewolf-base/ (snapshot of LibreWolf's config files)
├── remilia/                # REMILIA changes, one directory per category
│   ├── README.md           # the category contract checked by the tools
│   ├── build-fixes/        # compile-only fixes, no behaviour change (layer 3)
│   ├── security/           # sandbox, certificates, signing, updates (layer 3)
│   ├── privacy/            # tracking, fingerprinting, cookies, DNS, telemetry,
│   │                       #   uBlock Origin (layer 3)
│   └── branding/           # logos, icons, colours, theme, names, UI (layer 4)
│       # each category holds only what it needs:
│       #   patches/ + series, prefs.cfg, policies.json, mozconfig, files/,
│       #   replaces.txt, deviations.tsv
├── build/                  # build-environment image (windows-cross.Dockerfile)
├── scripts/                # fetch, prepare, toolchains, build, package, docker,
│   │                       #   remilia_layers.py (categories), verify-tree.sh (V1)
│   └── windows/            # host-side tools (build resource guard)
├── i18n/                   # documentation translations
├── tests/                  # validation harness, category test fixtures
│                           #   (tests/layers/)
├── LICENSE                 # MPL-2.0, for REMILIA's own files
└── *.md                    # this documentation set
```

`remilia/` holds only its contract (`README.md`) for now. Each category
directory is created when it first gets real content (Phase 3b onwards), with
no empty scaffolding. Category rules are in §10.

---

## 4. Build pipeline

```
fetch   → firefox-161.0.source.tar.xz (+ .asc)      gpg --verify (Mozilla key)
        → librewolf/source @ <pinned commit>         git, commit hash checked
prepare → LibreWolf patch.sh on a pristine copy       = layer 2 applied
        → REMILIA patch series + file overlays        = layers 3 + 4 applied
build   → ./mach build   (mozconfig: LW base + REMILIA overrides)
package → ./mach package → zip → NSIS installer, .mar update files
```

### 4.1 Windows build host

Two paths, both legitimate; see [BUILD.md](BUILD.md):

1. **Release / reproducible path — Linux cross-compile in Docker.**
   Same method LibreWolf uses for its published Windows binaries, so it is the
   path that LibreWolf's patches are actually tested against. Runs on this
   machine via Docker Desktop (WSL2 backend).
2. **Developer path — native Windows with MozillaBuild.** Mozilla's documented
   and supported method. Better for debugging (WinDbg, `mach build faster`,
   incremental front-end changes). LibreWolf's shell scripts need the
   GNU tools that MozillaBuild ships.

Phase 5 will validate both and record which one is authoritative for releases.
Expectation: Docker cross-compile for releases, native for iteration.

---

## 5. Privacy architecture

Privacy is implemented with **Firefox's native mechanisms**, configured, never
re-implemented:

| Concern | Mechanism (native) |
|---|---|
| Cross-site tracking | ETP **Strict** (`browser.contentblocking.category=strict`): Total Cookie Protection (dFPI), strict tracking lists, SmartBlock shims, query-parameter stripping |
| Fingerprinting | `privacy.resistFingerprinting` (RFP) — the same mechanism used by Tor Browser and Mullvad Browser |
| Telemetry | Disabled at **compile time** (`MOZ_TELEMETRY_REPORTING` empty, crash reporter not built, Glean pings follow the data-reporting pref) and by policy |
| Content blocking | uBlock Origin (unmodified, AMO-signed) |
| DNS | Firefox TRR (DoH) — off by default, selectable providers |
| Transport | HTTPS-Only Mode on, CRLite enforced, 0-RTT off |

Full per-setting evaluation, including where REMILIA deliberately **differs**
from LibreWolf, is in [PRIVACY.md](PRIVACY.md). Security-relevant differences are
in [SECURITY.md](SECURITY.md).

---

## 6. Ad blocking architecture

- **Engine:** uBlock Origin, unmodified, the AMO-signed build. REMILIA never
  forks or repackages uBO's code, so its filtering engine, its popup with real
  per-site request counts, and its dashboard are all uBO's own.
- **Delivery:** the signed `.xpi` (pinned version + SHA-256) is placed in the
  application's `distribution/extensions/` so it is present **offline on first
  run**, *and* listed in `policies.json` `ExtensionSettings` so Firefox keeps it
  updated through AMO's normal signed-update channel. Signature verification
  stays mandatory.
- **Default lists:** set through uBO's supported
  `adminSettings.assetsBootstrapLocation` → a REMILIA `assets.json`.
  This only defines the *first-install defaults*; users keep full control.
  **Not** `toOverwrite.filterLists`: uBO's `restoreAdminSettings()` re-applies
  that on every launch (verified in `src/js/storage.js`), which would silently
  undo users' choices.
- **Brazil:** uBO's stock catalogue currently has no dedicated Brazilian list;
  the regional list covering pt-BR is `spa-1` (AdGuard Spanish/Portuguese).
  uBO auto-enables regional lists from `navigator.language`, but RFP spoofs
  that to `en-US`, so REMILIA must enable `spa-1` explicitly in its assets
  manifest. Additional Brazilian community lists will be evaluated in Phase 5.
- **Popup:** Phase 5 decides between (a) using uBO's own popup as the toolbar
  "protection" panel, or (b) a REMILIA panel that reads only data uBO exposes.
  Rule: no statistic is displayed that the blocker did not produce. Firefox's
  own ETP panel already reports real per-site tracker counts and stays.

---

## 7. Updates

REMILIA uses **Mozilla's own updater** (MAR files + `update.xml`), the same
mechanism LibreWolf now uses, with **REMILIA's own identity**:

- REMILIA MAR signing key pair; the public keys replace LibreWolf's in
  `release_primary.der` / `release_secondary.der`. **Building the LibreWolf tree
  unmodified would make REMILIA accept LibreWolf-signed updates and query
  `update.librewolf.net` — this must be overridden before any public build.**
- `MOZ_APPUPDATE_HOST` → a REMILIA-controlled host (domain not yet chosen —
  see ROADMAP blockers).
- Updates never touch the profile directory; user data is only migrated by
  Firefox's own profile-migration code.

Filter lists update through uBO; uBO itself updates through AMO.

---

## 8. Maintenance model

Firefox ships a major release every **4 weeks** plus unscheduled security
("chemspill") point releases. LibreWolf typically follows within days.
REMILIA's latency to users = LibreWolf latency + REMILIA rebase + build + publish.

Realistic requirements:

- **Per release:** bump pins, re-run patch series, fix rejects, full build
  (≈1.5–3 h on a 6-core Ryzen 5 3600 for an optimized build, to be measured in
  Phase 5), smoke tests, sign, publish.
- **Target:** security releases published within **72 hours** of LibreWolf's.
  If that cannot be met reliably, users must be told plainly; an outdated
  privacy browser is a security liability.
- **Patch budget:** keep REMILIA source patches few and small. Prefer prefs,
  policies, and file overlays over C++/JS diffs. Every patch has a header
  stating purpose, layer, and whether it is upstreamable.

Details: [UPSTREAM.md](UPSTREAM.md).

---

## 9. Explicit non-goals

- No custom rendering, networking, crypto, or sandboxing code.
- No custom fingerprinting "randomization" that would make REMILIA users a
  small, distinguishable population.
- No frontend frameworks or bundlers (no React, no Vite). Browser UI changes are
  made in Firefox's own XHTML/CSS/JS/Fluent front-end.
- No claims of anonymity.

---

## 10. Change categories

Every REMILIA change belongs to exactly one category. Categories are isolated
so that each can be reviewed, debugged, reverted and re-synchronized with
upstream on its own.

| Category | Covers | Location |
|---|---|---|
| Upstream | Firefox and LibreWolf, unmodified; pins; LibreWolf patches REMILIA excludes | `upstream/` |
| Build fixes | Changes needed only to compile; no behaviour change | `remilia/build-fixes/` |
| Security | Sandboxing, certificates, HTTPS validation, signatures, process protection, updates | `remilia/security/` |
| Privacy | Tracking protection, fingerprinting, cookies, DNS, telemetry, content blocking (uBlock Origin) | `remilia/privacy/` |
| Branding | Logos, icons, colours, theme, names, visual identity of the UI | `remilia/branding/` |

Rules:

- A patch, pref block, policy file or mozconfig fragment belongs to one
  category. A change that touches two categories is split into two.
- Classification follows the effect. UI that only changes appearance is
  branding; UI that changes behaviour belongs to that behaviour's category
  (a DoH settings control is privacy).
- Firefox reads one AutoConfig file, one `distribution/policies.json` and one
  `mozconfig`. `prepare.sh` assembles them from the category fragments, with a
  header per category, and fails if two categories set the same pref or policy.
- A value that overrides LibreWolf needs a registered deviation
  (`deviations.tsv`) pointing to its written reason, and must keep the
  function LibreWolf used (`pref`, `defaultPref`, `lockPref`). Redefining a
  pref LibreWolf locks is marked `runtime-unverified` until a running browser
  confirms its effect.
- Fixed application order: build-fixes → security → privacy → branding. Any
  subset can be applied, so each category can be built and validated alone,
  and a regression can be bisected to a category.
- Every patch header records: category, purpose, files and prefs touched,
  whether it can be upstreamed, and what reverting it changes.

Implementation (Phase 3a): `prepare.sh` with `REMILIA_LAYERS`, and
`scripts/remilia_layers.py` for the checks and the assembly. The contract is
`remilia/README.md`. Deviations are checked against a snapshot of LibreWolf's
configuration files in `upstream/librewolf-base/`, so the static checks run
without Docker.

---

## 11. Validation gates

A successful compilation proves that the build infrastructure works. It does
not make a usable browser. No build is described as functional until it passes
the validation checklist in [ROADMAP.md](ROADMAP.md#validation-checklist), with
the results recorded as described in `tests/validation/README.md`.
Validation records are kept locally by the maintainer and are not published
in this repository.

The first full build is deferred until branding, security and privacy are
integrated. Until then, changes are checked without compiling:
static checks on every change (V0) and a fresh, per-category tree preparation
before each phase closes (V1). V1 prepares separate staging trees in
`staging/` inside the build volume. The rest of the volume, with the preserved
tree and its object directory, is mounted read-only while V1 runs. Work that
passed only V0 and V1 is
`static-verified`, never `done`. The full build (V2) and the checklist (V3)
come in ROADMAP Phase 5. Whether each category also gets a full build of its
own there is a Phase 5 decision; `REMILIA_LAYERS` (§10) makes it possible.
