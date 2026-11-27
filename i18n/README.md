# Remilia documentation translations

English is the canonical language. The English Markdown files in the
repository root are the single source of truth. This directory holds
translations of them, one subdirectory per locale:

```
i18n/
├── languages.json   # locale codes and display names, in navigation order
├── i18n.py          # status checker, navigation generator, stamping tool
├── pt-BR/           # Português (Brasil)
├── ja/              # 日本語
└── es/              # Español
```

A translation always has the same file name as its English source
(`i18n/ja/SECURITY.md` translates `SECURITY.md`). This is documentation
translation only. It has nothing to do with the browser's UI localization.

The tool needs Python 3.9+ and uses only the standard library. Run it from the
repository root.

## Translation metadata

Every translation starts with a metadata block, written exactly like this. The
field names stay in English so the tool can parse them:

```markdown
<!-- i18n:meta -->
> - **Translation status:** Current
> - **Language:** pt-BR
> - **Original language:** English
> - **Source:** [SECURITY.md](../../SECURITY.md)
> - **Source revision:** sha256:<64 hex characters>
<!-- /i18n:meta -->
```

| Status | Meaning |
|---|---|
| `Current` | Reviewed against the English source whose hash is recorded. |
| `Outdated` | The English source changed after the last review. The translation may be wrong. |
| `Draft` | Work in progress. Not yet a complete translation. |

**Source revision** is the SHA-256 of the English file's content, excluding
the language-navigation block. Hashing content rather than using a git
commit means the value is real even before anything is committed. Changing only
the navigation (for example, adding a language) does not change it. Never type
it by hand; `stamp` writes it.

## Language navigation

Each document, English and translated, starts with a generated block:

```markdown
<!-- i18n:nav -->
**English** | [Português (Brasil)](i18n/pt-BR/README.md) | [日本語](i18n/ja/README.md) | [Español](i18n/es/README.md)
<!-- /i18n:nav -->
```

Do not edit it by hand. Regenerate it with `python i18n/i18n.py nav`. It only
links to translations that exist.

## Commands

```sh
python i18n/i18n.py check                  # report status and validate everything
python i18n/i18n.py check --mark-outdated  # also flip stale "Current" translations to "Outdated"
python i18n/i18n.py nav                    # rewrite navigation blocks
python i18n/i18n.py stamp ja/SECURITY.md   # mark one reviewed translation as Current
python i18n/i18n.py stamp "ja/*"           # mark every translation of a locale as Current
```

`check` exit codes: `0` all translations current, `1` errors, `2` no errors but
some translations need review.

`check` verifies, for every English root document and every locale directory:

1. The translation exists and its metadata is complete and consistent.
2. The recorded source hash matches the current English file. If not, the
   translation is reported for review.
3. Heading levels, table rows and columns, list items (including checkbox
   state) are the same as the source.
4. Fenced code blocks are identical to the source.
5. Inline code (commands, prefs, file paths, identifiers) appears exactly as
   in the source.
6. Relative links resolve, including `#anchors`. Link targets match the source,
   and links between documents point to the translated sibling when it exists.
7. Links in the English documents resolve.

The tool never writes English text into a translation. It only edits
navigation blocks (`nav`) and metadata blocks (`stamp`, `--mark-outdated`).

## How to…

### Check translation status

Run `python i18n/i18n.py check`. The matrix at the end shows every document per
locale: `current`, `stale` (status says Current but the source changed),
`outdated`, `draft`, `missing` or `ERROR`.

### Update a translation after the English source changed

1. `python i18n/i18n.py check` lists it as `REVIEW … English source changed`.
2. See what changed in English (for example, `git diff` on the English file since
   the commit that last touched the translation).
3. Update the translation to match.
4. `python i18n/i18n.py stamp <locale>/<FILE>.md`. Stamping fails if the
   structure, code, or links don't match the source.

### Translate a document

1. Copy the English file to `i18n/<locale>/<FILE>.md` yourself.
2. Put the metadata block at the top with `Translation status: Draft` and
   `Source revision: pending`.
3. Translate the prose. Keep unchanged: code blocks, inline code, commands,
   configuration keys, file paths, URLs, and the names Remilia, SCARLET,
   LibreWolf, Firefox, Gecko, uBlock Origin. Keep headings, tables and lists
   structurally identical.
4. Fix links: links to other root documents stay as `OTHER.md` (they resolve to
   the translated sibling). Links to anything else in the repository get the
   `../../` prefix.
5. `python i18n/i18n.py nav`, then `python i18n/i18n.py stamp <locale>/<FILE>.md`.

### Add a language

1. Add an entry to `i18n/languages.json`: `{ "code": "fr", "name": "Français" }`.
   Its position sets its place in the navigation bar.
2. Create `i18n/<code>/` and translate documents as described above.
3. `python i18n/i18n.py nav` adds the new language to every document's
   navigation bar.

No code changes are needed. The tool discovers locale directories.

### Report a translation error

Open an issue titled `[i18n/<locale>] <FILE>.md: <short description>`, quoting
the translated passage and the English original. If the English text itself is
wrong, fix the English first. Every translation then shows up for review.
