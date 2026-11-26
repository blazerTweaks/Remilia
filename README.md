<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/README.md) | [日本語](i18n/ja/README.md) | [Español](i18n/es/README.md)
<!-- /i18n:nav -->

# REMILIA Browser

**Project SCARLET** — a privacy-focused desktop browser built on Firefox (Gecko)
and LibreWolf, with its own identity inspired by Remilia Scarlet.

> **Status: Phase 1 (research & architecture).** There is no REMILIA build
> yet. Nothing below is a shipped feature. Progress is tracked in
> [ROADMAP.md](ROADMAP.md).

## What REMILIA is

- A **real browser**: Gecko rendering, Firefox networking, multiprocess and
  site isolation, the Windows sandbox, and Firefox extension compatibility, all
  unmodified.
- **LibreWolf's privacy foundation**: telemetry removed at build time,
  Enhanced Tracking Protection Strict, Total Cookie Protection,
  resistFingerprinting, HTTPS-Only Mode.
- **uBlock Origin built in**: the real, AMO-signed extension, preinstalled,
  with sensible default lists including regional coverage for Brazil.
- **Its own identity**: original gothic, scarlet-accented branding. The
  reference is subtle, and the UI looks professional to people who have
  never heard of Touhou.

## What REMILIA is not

Not a WebView wrapper, not Electron, not a new engine, and not an anonymity tool.
See [PRIVACY.md](PRIVACY.md) for what it does and does not protect against.

## Documentation

| Document | Contents |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Foundation choice, layer model, build pipeline, ad-block and update design |
| [PRIVACY.md](PRIVACY.md) | Per-setting privacy evaluation, deviations from LibreWolf |
| [SECURITY.md](SECURITY.md) | Security model, deviations, supply chain, open problems |
| [BUILD.md](BUILD.md) | Requirements and build procedure (Windows x64) |
| [UPSTREAM.md](UPSTREAM.md) | Tracking Firefox and LibreWolf releases |
| [ROADMAP.md](ROADMAP.md) | Phases, task status, blockers |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to work on the project |

## Credits and licensing

REMILIA is built on Mozilla Firefox (MPL-2.0) and LibreWolf (MPL-2.0), and
bundles uBlock Origin (GPL-3.0, distributed unmodified). "Firefox" is a Mozilla
trademark and is not used in REMILIA's name or branding.

Touhou Project and Remilia Scarlet are creations of ZUN / Team Shanghai Alice.
REMILIA is an independent fan-inspired project. It uses no official artwork, and
all REMILIA visual assets are original.
