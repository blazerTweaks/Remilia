<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/README.md) | [日本語](i18n/ja/README.md) | [Español](i18n/es/README.md)
<!-- /i18n:nav -->

# Remilia Browser

**Project SCARLET** — a privacy-focused desktop browser built on Firefox (Gecko)
and LibreWolf, with its own identity inspired by Remilia Scarlet.

> **Status: in development.** Research is done and the build infrastructure
> exists, but there is no Remilia build yet: the first full build is planned
> once branding, security and privacy are integrated. Nothing below is a
> shipped feature. Progress is tracked in [ROADMAP.md](ROADMAP.md).

## What Remilia is

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

## What Remilia is not

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

Remilia is built on Mozilla Firefox (MPL-2.0) and LibreWolf (MPL-2.0), and
bundles uBlock Origin (GPL-3.0, distributed unmodified). "Firefox" is a Mozilla
trademark and is not used in Remilia's name or branding.

Remilia's own original files are licensed under the Mozilla Public License 2.0
([LICENSE](LICENSE)). Files inherited from Firefox, LibreWolf and other
third-party components keep their own licenses and notices, which Remilia does
not change.

Touhou Project and Remilia Scarlet are creations of ZUN / Team Shanghai Alice.
Remilia is an independent fan-inspired project. It uses no official artwork, and
all Remilia visual assets are original.
