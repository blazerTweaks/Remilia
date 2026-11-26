<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/UPSTREAM.md) | [日本語](i18n/ja/UPSTREAM.md) | [Español](i18n/es/UPSTREAM.md)
<!-- /i18n:nav -->

# Upstream Synchronization

REMILIA is downstream of two projects. Staying current with them is the most
important ongoing maintenance task, because nearly all security fixes arrive
from upstream.

## Layers

| Layer | Source | Pinned in | REMILIA edits it? |
|---|---|---|---|
| 1. Firefox | `archive.mozilla.org/pub/firefox/releases/<ver>/source/` (GPG-signed tarball). Canonical repo: `github.com/mozilla-firefox/firefox` | `upstream/pins.env` → `FIREFOX_VERSION` | Never directly; only via layer-3 patches |
| 2. LibreWolf | `codeberg.org/librewolf/source` (patches, settings, build scripts) | `upstream/pins.env` → `LIBREWOLF_COMMIT` | Never; REMILIA overrides on top |
| 3. REMILIA build fixes, security, privacy | `remilia/build-fixes/`, `remilia/security/`, `remilia/privacy/` (one category each, ARCHITECTURE.md §10) | — | Yes |
| 4. REMILIA branding | `remilia/branding/` | — | Yes |

## Release cadence to track

- Firefox: major release every 4 weeks; dot releases for security issues, sometimes
  unscheduled ("chemspills"). Advisories: mozilla.org/security/advisories/.
- LibreWolf: tags `<firefox-version>-<lw-release>` (e.g. `161.0-1`), usually
  within days of Firefox.
- uBlock Origin: independent; updated through AMO, not tied to REMILIA releases.

## Update procedure *(scripts arrive in Phase 2)*

1. A new LibreWolf tag appears for a new Firefox version.
2. Update `upstream/pins.env`: `FIREFOX_VERSION`, `LIBREWOLF_COMMIT`, `LIBREWOLF_TAG`.
3. `./scripts/fetch.sh`, which verifies the Mozilla GPG signature and the commit hash.
4. `./scripts/prepare.sh`. If a REMILIA patch fails to apply:
   - refresh it against the new tree;
   - if the code it touched changed meaning, review the patch's purpose header
     and re-derive it. Do not force it.
5. Diff `librewolf.cfg` and `policies.json` between the old and new LibreWolf
   commits. Review every changed pref against PRIVACY.md and SECURITY.md,
   because REMILIA overrides may now conflict with or duplicate upstream.
6. Build, run the smoke-test checklist (`tests/`), package, sign, publish.
7. Release notes list the MFSA advisories included.

## Rules for REMILIA patches

- One concern and one category per patch (ARCHITECTURE.md §10). A header
  states: category, purpose, affected prefs/files, whether it could be
  upstreamed to LibreWolf or Mozilla, and what reverting it changes.
- Prefer, in order: pref in the category's `prefs.cfg` → policy in its
  `policies.json` → file overlay (copy) → source patch. Source patches are the
  last resort.
- Do not modify LibreWolf patches. If one is unwanted, exclude it through the
  `upstream/` exclusion list (Phase 3a) with an ADR.
- Fixes that are not REMILIA-specific are proposed upstream first.

## Rebranding a LibreWolf tree: known touch points

LibreWolf hardcodes its identity in several places that REMILIA must override.
Inventory to complete in Phase 3:

- `mozconfig`: `--with-app-name`, `--with-distribution-id`, `--with-branding`,
  `MOZ_APP_REMOTINGNAME`.
- `lw/` directory and `librewolf.cfg` filename (`lw-dir.patch`, `local-settings.js`).
- Profile directory naming (`profile-directory.patch`, `mozilla-dirs.patch`).
- `about:librewolf` page and preferences pane (`about-librewolf.patch`, `pref-pane/`).
- `librewolf.*` pref namespace (e.g. `librewolf.uBO.assetsBootstrapLocation`).
- Updater: `MOZ_APPUPDATE_HOST`, `release_primary.der`, `release_secondary.der`.
- Strings: `appstrings.properties` rewrite and l10n overlays.
- `policies.json` `SupportMenu`, `app.update.url.*`, `app.releaseNotesURL*`.
