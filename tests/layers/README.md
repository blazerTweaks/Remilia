# Category test fixtures

Test data for `scripts/remilia_layers.py` and the V1 tree checks
(`scripts/verify-tree.sh`). **These are not Remilia changes.** They are never
applied to the baseline tree and never packaged:

- `prepare.sh` accepts a layer root other than `remilia/`, or an exclusion list
  other than `upstream/librewolf-exclude.txt`, only with `--staging`.
- `package.sh` refuses a tree whose provenance records a different layer root.
- Every fixture patch says `TEST FIXTURE` in its header. Fixture values use
  `remilia.fixture.*`, `*@remilia.invalid` or `remilia-fixture` names.

The deviations registered in the fixtures point to this file. They are
fictional: they exist only to exercise the deviation rules.

| Path | What it is |
|---|---|
| `test_layers.py` | Unit tests (V0, host): `python -m unittest discover -s tests/layers` |
| `valid/` | A complete valid category set for the real LibreWolf 161.0-1 tree |
| `invalid/<case>/` | One mistake each. `EXPECT` holds part of the error the checks must report |
| `exclude-msix.txt` | Excludes LibreWolf's `patches/msix.patch`, which no other patch depends on |
| `exclude-unknown.txt` | Excludes a patch that does not exist: preparation must stop |

## What `valid/` exercises

| Category | Content | Purpose |
|---|---|---|
| build-fixes | Patch to `AUTHORS`; new `mozconfig` variable | A category with a patch and a fragment |
| security | Two patches (`README.md` top, `CODE_OF_CONDUCT.md`); new pref; `lockPref` redefinition of `app.update.service.enabled` (SEC-001); new `ExtensionSettings` entry | Removal test (`0001` is removed from `series` in V1); `runtime-unverified` marking |
| privacy | Patch to `README.md` bottom; new pref; override of `network.trr.mode` (PRIV-001); new `ExtensionSettings` entry and override of LibreWolf's uBlock Origin entry (PRIV-002) | Overlap report (same file as security `0001`); second-level policy merge |
| branding | New file; replacement of LibreWolf's `brand.ftl` (`replaces.txt`); override of `--with-app-name` (BRAND-001) with the matching `browser/app/remilia-fixture.exe.manifest` | Overlays, `mozconfig` deviations, executable manifest rule |
