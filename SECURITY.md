<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/SECURITY.md) | [日本語](i18n/ja/SECURITY.md) | [Español](i18n/es/SECURITY.md)
<!-- /i18n:nav -->

# Remilia Browser — Security

Status: **design only.** No Remilia build exists yet.

Privacy and security are different. A privacy setting must never weaken
Firefox's security architecture. This file lists every security-relevant
modification Remilia makes or inherits, with justification.

## Reporting vulnerabilities

Until a dedicated channel exists, report privately to the maintainer. Do not
open public issues for vulnerabilities. Engine vulnerabilities belong upstream
(Mozilla Bugzilla, security group); Remilia will ship the fix when the upstream
release containing it is out.

## Preserved without change

- Gecko multiprocess architecture and **Fission** (site isolation).
- **Windows content-process sandbox** (`--enable-sandbox`, inherited from
  LibreWolf's Windows mozconfig). Never lowered to save memory.
- Certificate validation via NSS. **Never disabled.** No custom TLS or crypto.
- Mixed-content blocking, HSTS, HPKP-static pinning.
- Extension signature verification (see below — this is a deliberate
  difference from LibreWolf).
- Build hardening: `--enable-hardening`, `--enable-stl-hardening`,
  `-ftrivial-auto-var-init=zero`, `-fwrapv` (inherited).

## Inherited LibreWolf hardening — kept

| Setting | Effect |
|---|---|
| `security.pki.crlite_mode = 2` | CRLite revocation enforced locally. |
| `security.OCSP.enabled = 0` | No OCSP requests (privacy); relies on CRLite. |
| `security.cert_pinning.enforcement_level = 2` | Strict pinning. May conflict with antivirus TLS interception — documented in troubleshooting. |
| `security.ssl.require_safe_negotiation = true` | Rejects servers without RFC 5746. Rare breakage. |
| `security.tls.enable_0rtt_data = false` | No TLS 1.3 0-RTT (replay risk). |
| `security.enterprise_roots.enabled = false` | Windows certificate store roots not trusted automatically. |
| `network.IDN_show_punycode = true` | Homograph protection. |
| `pdfjs.enableScripting = false` | No JS in the PDF viewer. |

## Remilia deviations from LibreWolf (security-motivated)

| # | LibreWolf | Remilia (planned) | Reason |
|---|---|---|---|
| S1 | `MOZ_REQUIRE_SIGNING=` (empty): unsigned extensions can be enabled with a pref | Keep Mozilla's default: signing **required**, not overridable by pref | Prevents installing tampered or unsigned extensions. Developers can still load temporary add-ons through `about:debugging`. |
| S2 | Ships LibreWolf's MAR update-signing public keys; update host `update.librewolf.net` | Remilia's own MAR keys and update host | A Remilia binary must accept only Remilia-signed updates. Required before any public build. |
| S3 | Safe Browsing fully disabled | **Evaluate — see below** | Project requirements ask for Safe Browsing protection. |
| S4 | `extensions.webextensions.restrictedDomains = ""` (extensions may run on addons.mozilla.org etc.) | **Evaluate:** restore Firefox default | The restricted-domain list stops a compromised extension from manipulating the add-on store pages. |
| S5 | On Windows, AutoConfig also loads `%USERPROFILE%\.librewolf\librewolf.overrides.cfg`, so overrides written for an installed LibreWolf apply too | Reads only `%USERPROFILE%\.remilia\librewolf.overrides.cfg` (implemented, `static-verified`) | Another program's file must not change Remilia's prefs, including its security and privacy prefs. |

### S3 — Safe Browsing: open problem

Firefox's Safe Browsing downloads Google hash-prefix lists and checks URLs
locally, sending only hash prefixes on a partial match. It requires a **Google
Safe Browsing API key compiled into the build**. Mozilla's key cannot be used by
forks. Google restricts the Safe Browsing API to non-commercial use, and
commercial use requires the paid Web Risk API.

Options, to be decided in Phase 4:

1. Obtain a Remilia Safe Browsing API key (non-commercial project) and enable
   phishing/malware list checks. Remote *download* reputation checks
   (`browser.safebrowsing.downloads.remote.*`) send file metadata to Google and
   stay **off**.
2. If a key cannot be obtained: keep Safe Browsing off and rely on uBO's
   malware/phishing lists (`urlhaus-1`, `curben-phishing`, enabled by default)
   plus an optional malware-blocking DoH resolver. This must be described
   honestly as weaker than Safe Browsing.

Local download protections (dangerous-file-type warnings, Mark-of-the-Web) are
independent of Safe Browsing and stay on.

## Supply chain

- Firefox source: GPG-verified tarball from `archive.mozilla.org`.
- LibreWolf source: pinned commit hash in `upstream/pins.env`.
- uBlock Origin: AMO-signed `.xpi`, pinned version and SHA-256.
- Build toolchains: fetched by `mach` (Mozilla Taskcluster artifacts) or pinned
  container images.
- Release signing keys (MAR, Authenticode) are never committed to this
  repository.

## Security update policy

Firefox security releases are the highest priority. Target: a Remilia build
published within 72 hours of LibreWolf's corresponding release. Each release
note lists the Mozilla Security Advisories (MFSA) it includes.
