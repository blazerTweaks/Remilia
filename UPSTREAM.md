<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/UPSTREAM.md) | [日本語](i18n/ja/UPSTREAM.md) | [Español](i18n/es/UPSTREAM.md)
<!-- /i18n:nav -->

# Upstream Synchronization

Remilia is downstream of two projects. Staying current with them is the most
important ongoing maintenance task, because nearly all security fixes arrive
from upstream.

## Layers

| Layer | Source | Pinned in | Remilia edits it? |
|---|---|---|---|
| 1. Firefox | `archive.mozilla.org/pub/firefox/releases/<ver>/source/` (GPG-signed tarball). Canonical repo: `github.com/mozilla-firefox/firefox` | `upstream/pins.env` → `FIREFOX_VERSION` | Never directly; only via layer-3 patches |
| 2. LibreWolf | `codeberg.org/librewolf/source` (patches, settings, build scripts) | `upstream/pins.env` → `LIBREWOLF_COMMIT` | Never; Remilia overrides on top |
| 3. Remilia build fixes, security, privacy | `remilia/build-fixes/`, `remilia/security/`, `remilia/privacy/` (one category each, ARCHITECTURE.md §10) | — | Yes |
| 4. Remilia branding | `remilia/branding/` | — | Yes |

## Release cadence to track

- Firefox: major release every 4 weeks; dot releases for security issues, sometimes
  unscheduled ("chemspills"). Advisories: mozilla.org/security/advisories/.
- LibreWolf: tags `<firefox-version>-<lw-release>` (e.g. `161.0-1`), usually
  within days of Firefox.
- uBlock Origin: independent; updated through AMO, not tied to Remilia releases.

## Update procedure

1. A new LibreWolf tag appears for a new Firefox version.
2. Update `upstream/pins.env`: `FIREFOX_VERSION`, `LIBREWOLF_COMMIT`, `LIBREWOLF_TAG`.
3. `./scripts/fetch.sh`, which verifies the Mozilla GPG signature and the commit hash.
4. `./scripts/prepare.sh`. It refuses to apply Remilia categories while
   `upstream/librewolf-base/` differs from the new LibreWolf files. If a
   Remilia patch fails to apply:
   - refresh it against the new tree;
   - if the code it touched changed meaning, review the patch's purpose header
     and re-derive it. Do not force it.
5. Refresh the LibreWolf base snapshot with `scripts/remilia_layers.py snapshot`
   and review its diff: `librewolf.cfg`, `policies.json`, `mozconfig` and
   `patches.txt`. Review every changed pref against PRIVACY.md and
   SECURITY.md, because Remilia overrides may now conflict with or duplicate
   upstream. Then run `python scripts/remilia_layers.py check`.
6. Tree checks (`./scripts/docker.sh verify`), then build, run the validation
   checklist, package, sign, publish.
7. Release notes list the MFSA advisories included.

## Rules for Remilia patches

- One concern and one category per patch (ARCHITECTURE.md §10). A header
  states: category, purpose, affected prefs/files, whether it could be
  upstreamed to LibreWolf or Mozilla, and what reverting it changes. The
  exact format is in `remilia/README.md`.
- Prefer, in order: pref in the category's `prefs.cfg` → policy in its
  `policies.json` → file overlay (copy) → source patch. Source patches are the
  last resort.
- Do not modify LibreWolf patches. If one is unwanted, exclude it through
  `upstream/librewolf-exclude.txt`, one line per patch: the path as written in
  LibreWolf's `patches.txt`, then the reason. The reason is required and
  public, because it is copied into `REMILIA-PROVENANCE.txt`: 10 to 200
  characters, no commas, no control characters and no references to internal
  documents. `scripts/remilia_layers.py` checks the path, that it appears
  exactly once in `patches.txt`, and the reason; a line in the old format, with
  a decision identifier instead of a reason, is refused. The list is empty for
  LibreWolf 161.0-1.
- Fixes that are not Remilia-specific are proposed upstream first.

## Rebranding a LibreWolf tree: touch points

Inventory of the prepared LibreWolf 161.0-1 tree, made in Phase 3a. It found
4018 lines that contain "librewolf"; the full line-by-line list is not
published. 3605 of them
are LibreWolf's own UI string overlays in `lw/l10n/` (504 files).

What the inventory covers: every line of a text file in the prepared tree
(object directory excluded) that contains "librewolf" in any case. What it
does not cover:

- binary files line by line (icons and bitmaps are listed by directory);
- identity that does not contain that word, such as remaining "Firefox"
  strings or Mozilla URLs;
- pref defaults set outside `librewolf.cfg`, such as `browser/app/profile/firefox.js`,
  `modules/libpref/init/all.js`, `modules/libpref/init/StaticPrefList.yaml`
  and `browser/branding/librewolf/pref/firefox-branding.js`. The category
  checks do not detect overrides of those either (`remilia/README.md`,
  "What the checks cover"). This is pending work for Phases 3b, 4a and 4b.

Phase 3b changes the identity the user sees to Remilia: name, icons, UI,
executables and profile. The internal names stay: the `lw/` directory, the
`librewolf.cfg` file name and the `librewolf.*` pref namespace. Renaming them
would make security and privacy depend on branding.

| Touch point | Where | Category | Phase |
|---|---|---|---|
| Application name, branding directory, remoting name | `mozconfig` lines 21, 23, 30; `browser/branding/librewolf/configure.sh` lines 8–11; vendor and app-name defaults in `toolkit/moz.configure` lines 23, 37 | Branding (`mozconfig` deviations) | 3b |
| Distribution ID `net.librewolf` | `mozconfig` line 22 | Branding | 3b, needs B1 |
| Branding directory: icons (`.ico`, `.png`, `.icns`, `.bmp`), wordmark, `brand.ftl`, `brand.dtd`, `brand.properties`, `branding.nsi` | `browser/branding/librewolf/` (42 entries, copied by `patch.sh` from LibreWolf's `themes/`) | Branding: a new Remilia branding directory, LibreWolf's is not edited | 3b |
| Executable manifest | `browser/app/librewolf.exe.manifest` lines 6, 9 | Branding | 3b |
| Profile and data directory names | `toolkit/xre/nsXREDirProvider.cpp` lines 337, 430, 432, 1010, 1307, 1317 (`profile-directory.patch`, `mozilla-dirs.patch`); backup folder `browser/components/backup/BackupService.sys.mjs` line 661 | Branding | 3b |
| User override file `librewolf.overrides.cfg` read from the profile | `extensions/pref/autoconfig/src/prefcalls.js` lines 25–54 | Open: user-visible file name inside the internal AutoConfig mechanism | 3b decision |
| About dialog and `about:librewolf` page | `browser/base/content/aboutDialog.xhtml` lines 38, 44, 45; `toolkit/content/librewolf.html`; `toolkit/locales/en-US/toolkit/about/aboutLibreWolf.ftl`; `docshell/build/components.conf` line 18 | Branding (visible text); the `about:` address is an open 3b decision | 3b |
| Settings pane | `browser/components/preferences/librewolf.js`, `librewolf.inc.xhtml`; `browser/locales/en-US/browser/preferences/preferences.ftl` (46 lines) | Branding for names and icons; behaviour of each control stays in its own category | 3b |
| Hard-coded strings | `appstrings.properties` (rewritten by `patch.sh`, 12 lines); `dom/locales/en-US/chrome/appstrings.properties`; `lw/l10n/` overlays (1545 lines with the visible name) | Branding | 3b |
| Developer tools logo | `devtools/client/aboutdebugging/src/actions/runtimes.js` line 74 (`lw-logo-devtools.patch`) | Branding | 3b |
| Support and release-notes links | `lw/librewolf.cfg` lines 582–586 and 648 (`app.update.url.*`, `app.releaseNotesURL*`, `app.support.baseURL`); `lw/policies.json` lines 93–94 (`SupportMenu`) and 60 (language-pack message) | Branding (pref and policy deviations) | 3b, needs B1 |
| Update host and MAR keys | `build/moz.build` line 95 (`MOZ_APPUPDATE_HOST`); `release_primary.der`, `release_secondary.der` copied by `patch.sh` | Security, not branding: they decide which updates the browser accepts | 4a, needs B1, B2 |
| uBlock Origin asset list location | `lw/librewolf.cfg` lines 996–999 (`librewolf.uBO.assetsBootstrapLocation`) | Privacy | 4b |
| Version check against LibreWolf's server (off by default) | `browser/base/content/aboutDialog.js` lines 42–72 | Privacy (network request); stays off | 4b |
| Search engines | `services/settings/dumps/main/search-config-v2.json` (copied by `patch.sh`) | Privacy (D1) | 4b |
| Windows installer names | `browser/branding/librewolf/branding.nsi` lines 11–13 | Branding | 8 |
| Internal names kept | `librewolf.*` prefs (`modules/libpref/init/StaticPrefList.yaml` lines 12433–12446 and about 40 code sites); `lw/` and `librewolf.cfg` (`browser/installer/package-manifest.in` line 279, `lw/local-settings.js`) | None: kept on purpose | — |
