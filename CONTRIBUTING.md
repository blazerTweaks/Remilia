<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/CONTRIBUTING.md) | [日本語](i18n/ja/CONTRIBUTING.md) | [Español](i18n/es/CONTRIBUTING.md)
<!-- /i18n:nav -->

# Contributing to REMILIA

## Ground rules

1. **No fake functionality.** No mockups standing in for features, and no
   placeholder statistics. If something is not implemented, the docs say so.
2. **Never weaken security for convenience or benchmarks.** Certificate
   validation, sandboxing, Fission and extension signing are not negotiable.
3. **Every privacy or security change is documented** in PRIVACY.md or
   SECURITY.md, with the reason, in the same change.
4. **Upstream first.** Prefer prefs, then policies, then file overlays, then
   source patches. See UPSTREAM.md.
5. **No new dependencies or frameworks** without a concrete reason recorded in
   an ADR. Browser UI uses Firefox's own front-end technologies.
6. **Never fabricate test results or benchmarks.** Record what was run, on which
   build and date, and what failed.

## Making a change

- Small commits, one concern and one category each (upstream, build fixes,
  security, privacy, branding; ARCHITECTURE.md §10). The message says *why*.
- New REMILIA patch, pref or policy: put it in the directory of its single
  category, `remilia/<category>/`. A patch goes in that category's `patches/`
  and `series`, with a header (category, purpose, files and prefs touched,
  upstreamable?, effect of reverting it). A change spanning two categories is
  split into two.
- Architecture-level choices get an architecture decision record (ADR):
  Context, Decision, Consequences, Status.
- Update ROADMAP.md when a task changes status.

## Verifying

After any change that touches the build: a full build, then the smoke checklist in
BUILD.md ("Verifying a build"). After a privacy-pref change: re-run the
relevant tests in `tests/` and update results.

A successful build is not a working browser. Before calling any build
functional, run the validation checklist (ROADMAP.md, Phase 2, step 3) and
record the results in `tests/results/` (ADR 0005).

## Licensing

Contributions touching Firefox or LibreWolf files are MPL-2.0. The licence for
REMILIA-original files is pending (ROADMAP B5).
