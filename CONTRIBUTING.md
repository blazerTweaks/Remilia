<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/CONTRIBUTING.md) | [日本語](i18n/ja/CONTRIBUTING.md) | [Español](i18n/es/CONTRIBUTING.md)
<!-- /i18n:nav -->

# Contributing to Remilia

## Ground rules

1. **No fake functionality.** No mockups standing in for features, and no
   placeholder statistics. If something is not implemented, the docs say so.
2. **Never weaken security for convenience or benchmarks.** Certificate
   validation, sandboxing, Fission and extension signing are not negotiable.
3. **Every privacy or security change is documented** in PRIVACY.md or
   SECURITY.md, with the reason, in the same change.
4. **Upstream first.** Prefer prefs, then policies, then file overlays, then
   source patches. See UPSTREAM.md.
5. **No new dependencies or frameworks** without a concrete reason, stated in
   the change and accepted by the maintainer. Browser UI uses Firefox's own
   front-end technologies.
6. **Never fabricate test results or benchmarks.** Record what was run, on which
   build and date, and what failed.

## Making a change

- Small commits, one concern and one category each (upstream, build fixes,
  security, privacy, branding; ARCHITECTURE.md §10). The message says *why*.
- New Remilia patch, pref or policy: put it in the directory of its single
  category, `remilia/<category>/`. A patch goes in that category's `patches/`
  and `series`, with a header (category, purpose, files and prefs touched,
  upstreamable?, effect of reverting it). A change spanning two categories is
  split into two. The exact formats are in `remilia/README.md`.
- A value that overrides LibreWolf gets an entry in the category's
  `deviations.tsv` and its reason in PRIVACY.md or SECURITY.md.
- Architecture-level choices are proposed to the maintainer before
  implementation, with context, decision and consequences. Once adopted, their
  effect is described in ARCHITECTURE.md.
- Update ROADMAP.md when a task changes status.

## Verifying

Every change: the static checks (V0 in ROADMAP.md, "Validation strategy").
Before a phase closes: the tree checks (V1).

```sh
python scripts/remilia_layers.py check        # V0: categories, duplicates, deviations
python -m unittest discover -s tests/layers   # V0: tests of the category tool
python -m unittest discover -s tests/validation  # V0: tests of the validation harness
python i18n/i18n.py check                     # V0: documentation translations
./scripts/docker.sh verify                    # V1: staging trees, no compilation
```

A full build is not required
after each change; the first one comes when branding, security and privacy are
integrated. If a change can only be validated by compiling, say why
before starting the build.

A successful build is not a working browser. Before calling any build
functional, run the [validation checklist](ROADMAP.md#validation-checklist)
and record the results in `internal/evidence/<date>-<build>/` (a local folder
ignored by Git; validation records are never committed). Work that passed only
V0 and V1 is `static-verified`, not `done`.

## Licensing

Remilia's own original files are MPL-2.0 ([LICENSE](LICENSE)).
Contributions touching Firefox or LibreWolf files are MPL-2.0 as well. Files
inherited from Firefox, LibreWolf and other third-party components keep their
own licenses and notices; do not change them.
