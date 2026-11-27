<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/PRIVACY.md) | [日本語](i18n/ja/PRIVACY.md) | [Español](i18n/es/PRIVACY.md)
<!-- /i18n:nav -->

# REMILIA Browser — Privacy

Status: **design only.** Nothing in this document is built or tested yet.
Each item carries a status: `planned`, `implemented`, `verified` (tested, with
results in `tests/`). Today every item is `planned`.

## Principles

1. **Native mechanisms over custom code.** Firefox already ships Total Cookie
   Protection, ETP, RFP, HTTPS-Only, and DoH. REMILIA configures them.
2. **Inherit LibreWolf by default.** A deviation from `librewolf.cfg` needs a
   written reason, because every deviation is maintenance work and may make
   REMILIA users more distinguishable from the larger LibreWolf population.
3. **Breakage must buy privacy.** A setting that breaks sites without a
   meaningful privacy gain is not enabled by default.
4. **No overclaiming.** REMILIA reduces tracking and fingerprinting surface. It
   does not make anyone anonymous. DoH does not hide which sites you visit from
   the DoH provider, nor from the site operators or anyone observing TLS SNI
   unless ECH is used.

## What REMILIA protects against — and what it does not

| Protects (reduces) | Does **not** protect against |
|---|---|
| Cross-site cookies and storage tracking | Your ISP / network seeing destination IPs |
| Known tracker and ad domains | The site you visit identifying you after login |
| Many passive fingerprinting vectors | A determined, targeted adversary |
| Tracking query parameters in links | Malware on your computer |
| DNS snooping on the local network (when DoH is on) | The DoH provider seeing your DNS queries |
| Telemetry and background data collection by the browser | Anything you voluntarily submit to websites |

## Configuration baseline (from LibreWolf `librewolf.cfg` v8.6, Firefox 161)

Legend — **Keep**: inherit LibreWolf. **Change**: REMILIA deviates.
**Evaluate**: decide in Phase 4 with tests.

### Tracking & cookies

| Setting | LibreWolf | REMILIA | Notes |
|---|---|---|---|
| `browser.contentblocking.category` | `strict` | Keep | ETP Strict: Total Cookie Protection, strict lists, SmartBlock shims, query stripping. |
| Query stripping list | Brave's list | Keep | Removes `fbclid`, `gclid`, etc. |
| `privacy.sanitize.sanitizeOnShutdown` | `true` (cookies/cache cleared on exit) | **Evaluate** | Strong privacy, but logs users out every restart. Proposal: keep on, make site exceptions prominent in settings and onboarding. |
| Disk cache | disabled | Keep | Memory-only cache. Costs some repeat-visit performance. |
| `browser.formfill.enable` | `false` | Keep | |
| Bounce tracking protection | Firefox default | **Evaluate** | Confirm state under ETP Strict in Fx 161. |
| Global Privacy Control | on | Keep | |

### Fingerprinting

| Setting | LibreWolf | REMILIA | Notes |
|---|---|---|---|
| `privacy.resistFingerprinting` | `true` | Keep | Shared with Tor/Mullvad/LibreWolf, so users blend into a larger set. Side effects: UTC timezone reported, `en-US` locale reported, light theme reported to sites, rounded window size. All exposed as clear toggles in settings. |
| Letterboxing | off | Keep | |
| WebGL | enabled (RFP-protected) | Keep | Disabling WebGL breaks maps/3D and is itself a fingerprintable choice. |
| WebGPU | disabled | Keep | |
| Custom randomization | — | **Never** | Would make REMILIA users a distinct small population. |

Not claimed: complete fingerprinting protection. Font enumeration, screen size,
and hardware details are reduced by RFP, not eliminated.

### Telemetry & background connections

| Item | REMILIA |
|---|---|
| Telemetry | Disabled at compile time (`MOZ_TELEMETRY_REPORTING` empty) **and** by policy. |
| Studies / Normandy / Nimbus experiments | Disabled (`DisableFirefoxStudies`, `DisableRemoteImprovements`). |
| Pocket / sponsored tiles / sponsored suggestions / Firefox Suggest | Disabled. |
| Crash reporter | **Not built** (Mozilla's crash servers do not accept fork builds). No crash data is transmitted. A future opt-in, local-only crash dump option is a roadmap item, not a feature. |
| Default browser agent | Not built. |
| AI features (chatbot sidebar, smart tab groups, etc.) | Blocked by policy; OpenAI backend removed from source (inherited). |

Remaining expected network contacts, to be listed exactly in Phase 4 with a
packet capture: Remote Settings (certificate revocation/CRLite, security
blocklists), AMO extension updates, uBO filter-list updates, REMILIA update
checks. None of these sends browsing history.

### DNS & network

| Setting | LibreWolf | REMILIA | Notes |
|---|---|---|---|
| DoH (`network.trr.mode`) | `5` (off) | **Evaluate** | Off means the OS resolver is used. On (mode 2/3) moves trust to the provider. Proposal: off by default, a first-run choice offered. |
| DoH provider list | Quad9 ×2, LibreDNS ×2, Wikimedia, DNS4All | Keep + evaluate adding a Brazil-friendly provider | No provider is forced. |
| DNS prefetch / link prefetch / speculative connections | disabled | Keep | |
| `network.proxy.socks_remote_dns` | `true` | Keep | DNS goes through SOCKS5 proxy when one is set. |
| WebRTC | enabled, mDNS hides local IP; proxy-only when behind proxy | Keep | Disabling WebRTC breaks calls and is fingerprintable. A settings toggle to disable it will exist. |
| Cross-origin referrer trimming | `XOriginTrimmingPolicy=2` | Keep | |
| HTTPS-Only Mode | on (policy) | Keep | |
| `beacon.enabled` | `false` | Keep | |

## Search

- No default search provider is forced. Candidates offered: DuckDuckGo, Brave
  Search, Startpage, Mojeek (inherited), Google, Bing. Default choice to be
  decided (ROADMAP, open decision D1).
- Search suggestions are **off** by default. When enabled, keystrokes are sent
  to the chosen provider; the setting says so in plain text.
- The address bar does not send queries anywhere until the user submits.

## Data REMILIA never collects

REMILIA (the project) operates no analytics, no accounts, no sync service.
The update check sends the request that Mozilla's updater format requires
(version, build target, channel). That request is documented in
[SECURITY.md](SECURITY.md) once the update server exists.
