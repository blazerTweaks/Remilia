# REMILIA change categories — contract

This directory holds REMILIA's own changes to the LibreWolf tree, split into
isolated categories (ARCHITECTURE.md §10). This file is the
contract that `scripts/remilia_layers.py` enforces. When this file and the
tool disagree, the tool is wrong.

License: REMILIA's original files are MPL-2.0 (see `LICENSE` at the
repository root). Files copied or derived from Firefox or LibreWolf keep
their original license and notices.

## Categories and order

| Category | Directory | Deviation ID prefix |
|---|---|---|
| Build fixes | `remilia/build-fixes/` | `BF-` |
| Security | `remilia/security/` | `SEC-` |
| Privacy | `remilia/privacy/` | `PRIV-` |
| Branding | `remilia/branding/` | `BRAND-` |

Categories are always applied in this order, whatever order
`REMILIA_LAYERS` lists them in. A category directory is created only when
it has real content. Empty scaffolding is not committed.

Upstream (the fifth category, ARCHITECTURE.md §10) lives in `upstream/`, not here:
`pins.env`, the LibreWolf patch exclusion list `librewolf-exclude.txt`, and
the LibreWolf base snapshot `librewolf-base/`.

## Selecting categories: `REMILIA_LAYERS`

| Value | Effect |
|---|---|
| `all` (default) | Every category directory that exists, plus the upstream exclusion list |
| `none` | Nothing REMILIA-owned: no exclusions, no categories. The tree is unmodified LibreWolf |
| `security,privacy` | Only these categories (still in the fixed order), plus the exclusion list |

An unknown name, or a requested category whose directory does not exist, is
an error.

## What a category may contain

Only these entries. Anything else is a V0 error.

| Entry | Purpose |
|---|---|
| `series` + `patches/` | Source patches, applied in `series` order |
| `prefs.cfg` | Preferences appended to the AutoConfig file `lw/librewolf.cfg` |
| `policies.json` | Enterprise policies merged into `lw/policies.json` |
| `mozconfig` | Build options appended to the tree's `mozconfig` |
| `files/` | Files copied into the tree at the same relative path |
| `replaces.txt` | The inherited files that `files/` is allowed to overwrite |
| `deviations.tsv` | Registry of every value that overrides LibreWolf |
| `README.md` | Optional notes for maintainers. Never applied |

Preference order (UPSTREAM.md): pref → policy → file overlay → source patch.
Source patches are the last resort.

All text files are UTF-8 with LF line endings and end with a newline. A
carriage return anywhere is an error.

## Application order inside `prepare.sh`

1. LibreWolf's `patch.sh`, with excluded patches removed from its list.
2. The Windows cross-compile `mozconfig` block.
3. The LibreWolf base snapshot is compared with the tree (see below).
4. For each selected category, in the fixed order: its patches in `series`
   order, then its `files/`.
5. Assembly: every selected category's `prefs.cfg`, `policies.json` and
   `mozconfig` are checked together, then written into the tree.
6. `REMILIA-PROVENANCE.txt` records versions, commits, categories and hashes.

## Patches

- `series` lists patch paths relative to `patches/`, one per line. Blank
  lines and lines starting with `#` are ignored. Every file in `patches/` is
  listed exactly once.
- Applied with `patch -p1 --fuzz=0 --forward`. A patch that needs fuzz, or
  that looks already applied, fails the preparation. Line offsets are
  accepted, as in quilt.
- Each patch starts with a header before the diff:

  ```
  Category: security
  Summary: one line saying what the patch changes and why
  ```

  `Category` must match the directory. More free text may follow.
- A patch must not touch `lw/librewolf.cfg`, `lw/policies.json`, `mozconfig`
  or `REMILIA-PROVENANCE.txt`. Use the fragments instead.
- Git binary patches are not supported. Binary files go in `files/`.
- Removing a patch from `series` must produce the same tree as reverse-applying
  it. V1 checks this.

## `prefs.cfg`

One call per line, starting in column 0:

```
defaultPref("remilia.example", true);
lockPref("privacy.example", 2); // deviation: PRIV-001
```

- Allowed functions: `pref`, `defaultPref`, `lockPref`.
- Allowed values: a double-quoted string, an integer, `true` or `false`.
- Other allowed lines: blank lines and `//` comment lines.
- A pref may appear only once in a category, and in only one category.
  Duplicates across categories stop the preparation.
- **Overriding LibreWolf.** If the pref is also set in LibreWolf's
  `librewolf.cfg`, the line must end with `// deviation: <ID>`, the ID must be
  registered in `deviations.tsv`, and the function must be the one LibreWolf
  used (`pref`, `defaultPref` or `lockPref`). Changing the function is an
  error. If LibreWolf sets the same pref with different functions, or clears
  it with `clearPref`, the override is refused; allowing it needs a maintainer
  decision and a change to the tool.
- **`lockPref` is not assumed to work twice.** Redefining a pref that
  LibreWolf already locks is accepted only with a deviation, and the assembly
  report and the provenance file mark it `runtime-unverified`. Its effect is
  confirmed only by running the browser (validation level V3, or the Phase 4
  checks on an official LibreWolf binary).
- Only `librewolf.cfg` is compared. Defaults set anywhere else are not
  detected: see "What the checks cover" below.

The fragments are appended to the end of `lw/librewolf.cfg`, each under a
header naming its category. The `lw/` directory, the `librewolf.cfg` file name
and the `librewolf.*` pref namespace stay as they are: branding never renames
them, so that security and privacy never depend on branding.

## `policies.json`

```json
{
  "policies": {
    "ExtensionSettings": {
      "example@remilia.invalid": { "installation_mode": "blocked" }
    }
  }
}
```

- The only top-level key is `policies`, an object.
- Conflicts are checked per unit. When both sides are JSON objects, the unit
  is `Policy/key` (second level): two categories may add different keys to
  `ExtensionSettings`. Otherwise the unit is the whole policy.
- The same unit in two categories is an error.
- A unit that exists in LibreWolf's `policies.json` is an override and needs a
  `deviations.tsv` entry with kind `policy` and key `Policy` or `Policy/key`.
- The merged file keeps LibreWolf's key order and is rewritten with 4-space
  indentation. It is rewritten only when at least one selected category has a
  `policies.json`.

## `mozconfig`

```
ac_add_options --enable-example
mk_add_options EXAMPLE=1
export EXAMPLE_VAR=1 # deviation: BF-001
```

- One `ac_add_options`, `mk_add_options` or `export` per line, plus blank
  lines and `#` comments.
- Each line has a key: `--enable-x` and `--disable-x` are both `enable:x`;
  `--with-x` and `--without-x` are both `with:x`; any other option is
  `opt:name`; `mk_add_options NAME=` is `mk:NAME`; `export NAME=` is
  `env:NAME`.
- The same key in two categories is an error. A key that LibreWolf's
  `mozconfig` (including the Windows cross-compile block) already sets needs
  `# deviation: <ID>` at the end of the line and a `deviations.tsv` entry.
- Fragments are appended after the Windows cross-compile block, so they are
  read last.
- A `mozconfig` change can only be confirmed by a full build (V2).

## `files/` and `replaces.txt`

- `files/<path>` is copied to `<tree>/<path>`. Symlinks are refused.
- Creating a new file needs nothing else.
- Overwriting a file that exists in the LibreWolf tree needs the path in
  `replaces.txt` (one path per line, `#` comments allowed). A listed path
  that does not exist in the tree is an error.
- A file written by an earlier REMILIA category can never be overwritten.
- The same forbidden paths as for patches apply.

## `deviations.tsv`

Every value that overrides LibreWolf has one line, tab-separated:

```
# id	kind	key	reference
PRIV-001	pref	privacy.example	PRIVACY.md#tracking--cookies
SEC-002	policy	ExtensionSettings/uBlock0@raymondhill.net	SECURITY.md
```

- `id`: the category's prefix, a dash and three digits. IDs are never reused.
- `kind`: `pref`, `policy` or `mozconfig`.
- `key`: the pref name, policy unit or mozconfig key it overrides.
- `reference`: where the reason is written, as `<document>` or
  `<document>#<anchor>`. Allowed documents: `PRIVACY.md` and `SECURITY.md`.
  `tests/layers/README.md` is also allowed, but never in `remilia/`: only in
  the test fixtures, that is, any other layer root, including the copies of
  `tests/layers/` that V1 prepares in staging. `prepare.sh` accepts another
  layer root only for staging trees, and `package.sh` refuses to package one.
  `scripts/remilia_layers.py` checks, in this order:
  - the text, before the file system is consulted: no spaces or other
    whitespace, no `\`, no `:` (drive letters, URLs), no leading `/`
    (absolute paths), no empty, `.` or `..` segments (traversal), nothing
    under `internal/` (not published);
  - the document name, compared exactly with the allowed list, case
    included: `privacy.md` is refused on every system, and so is any other
    document, such as `ROADMAP.md`;
  - the file: a regular file inside the repository, not a symbolic link;
  - the anchor, which is optional: when present, it must be the anchor of a
    heading of that document, computed by `i18n/i18n.py` (the documentation
    checker, GitHub style).
  The allowed list is fixed in the tool; adding a document is a change to the
  tool.
- An entry that no fragment uses, or that does not override anything in the
  LibreWolf base, is an error. So is an override without an entry.

## LibreWolf base snapshot

`upstream/librewolf-base/` holds verbatim copies of the four LibreWolf files
the checks compare against: `librewolf.cfg`, `policies.json`, `mozconfig`
(after the Windows block) and `patches.txt`. They let V0 detect deviations on
the host without Docker. `prepare.sh` refuses to apply categories if the
snapshot differs from the tree it prepared. After a LibreWolf update, refresh
the snapshot with `scripts/remilia_layers.py snapshot` and review its diff
(UPSTREAM.md, step 5).

## What the checks cover

An override of LibreWolf is detected only where LibreWolf's value is in one of
the three snapshot files:

| Detected | Source |
|---|---|
| Prefs set by a literal `pref`, `defaultPref`, `lockPref`, `clearPref` or `unlockPref` call | `lw/librewolf.cfg` |
| Policies, at the unit level described above | `lw/policies.json` (LibreWolf 161.0-1 has no `Preferences` policy) |
| `ac_add_options`, `mk_add_options` and `export` keys | `mozconfig` (LibreWolf's, plus the Windows cross-compile block) |

**Not detected.** A REMILIA pref can silently override a default set in any of
these places. It then passes V0 and V1 with no deviation required:

- Firefox and LibreWolf default-pref files, such as
  `browser/app/profile/firefox.js` and `modules/libpref/init/all.js`,
  including the values LibreWolf patches into them.
- Static prefs in `modules/libpref/init/StaticPrefList.yaml` (LibreWolf adds
  `librewolf.*` entries with `lw-staticprefs.patch`).
- The branding pref file `browser/branding/*/pref/firefox-branding.js`.
- `lw/local-settings.js` (the AutoConfig loader prefs).
- Prefs computed in code (JavaScript or C++) or set by a policy at run time.
- Prefs a user sets in a profile (`prefs.js`, `user.js`, `librewolf.overrides.cfg`).

The identity inventory (UPSTREAM.md) has a separate scope: it lists every
line of a text file that contains `librewolf`. It does not list binary files
line by line (icons are listed by directory), identity that does not contain
that word, or pref defaults.

Until these gaps are closed, every category change that sets a pref must be
checked by hand against those sources. Closing them is pending work for
Phase 3b (branding prefs) and Phases 4a and 4b (security and privacy
defaults), as listed in ROADMAP.md.

## Checks

| Command | Level | Where |
|---|---|---|
| `python scripts/remilia_layers.py check` | V0 | Host. Contract, duplicates, deviations against the snapshot |
| `python -m unittest discover -s tests/layers` | V0 | Host. Tests of the tool itself |
| `python -m unittest discover -s tests/validation` | V0 | Host. Tests of the `--out` rules of the validation harness |
| `scripts/docker.sh verify` | V1 | Container. Staging trees, no compilation |

Test fixtures live in `tests/layers/`. They are never applied to the
baseline tree and never packaged: `prepare.sh` accepts another layer root
only when it prepares a staging tree.
