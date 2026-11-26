#!/usr/bin/env python3
"""REMILIA documentation translation tool (stdlib only).

English Markdown files in the repository root are canonical. Translations live
in i18n/<locale>/<same file name>. This tool never writes English content into a
translation; it only edits the language-navigation block and the metadata
block of translation files.

Commands
  check [--mark-outdated]   Validate every translation and report its status.
  nav                       (Re)write the language-navigation block in every
                            English document and every existing translation.
  stamp <locale>/<FILE.md>… Mark translations as reviewed against the current
                            English source (status Current + source hash).
                            Refuses if the translation fails validation.
                            Use "<locale>/*" for every file of a locale.

Exit codes for `check`: 0 everything current, 1 errors, 2 no errors but some
translations need review (Outdated, Draft, or source changed).
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
I18N = ROOT / "i18n"
STATUSES = ("Current", "Outdated", "Draft")
META_KEYS = ("Translation status", "Language", "Original language", "Source", "Source revision")

NAV_RE = re.compile(r"<!-- i18n:nav -->\n.*?\n<!-- /i18n:nav -->\n\n?", re.S)
META_RE = re.compile(r"<!-- i18n:meta -->\n(.*?)<!-- /i18n:meta -->\n\n?", re.S)
FIELD_RE = re.compile(r"^>\s*-\s*\*\*(?P<k>[^*]+?):\*\*\s*(?P<v>.*?)\s*$")
LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)\)")
INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
FENCE_RE = re.compile(r"^\s*(```+|~~~+)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s+(\[[ xX]\]\s)?")


# ----------------------------------------------------------------- helpers

def read(path):
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def write(path, text):
    path.write_text(text, encoding="utf-8", newline="\n")


def rel(path):
    return Path(os.path.relpath(path, ROOT)).as_posix()


def strip_blocks(text):
    """Document body without the navigation and metadata blocks."""
    return META_RE.sub("", NAV_RE.sub("", text, count=1), count=1)


def source_hash(path):
    return hashlib.sha256(strip_blocks(read(path)).encode("utf-8")).hexdigest()


def load_languages():
    langs = json.loads(read(I18N / "languages.json"))
    canonical = [l for l in langs if l.get("canonical")]
    if len(canonical) != 1:
        sys.exit("languages.json must mark exactly one language as canonical")
    return langs, canonical[0]["code"]


def locales():
    return sorted(p.name for p in I18N.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))


def canonical_docs():
    return sorted(p.name for p in ROOT.glob("*.md"))


def github_slug(heading):
    s = re.sub(r"`|\*\*?|_", "", heading.strip().lower())
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


# ------------------------------------------------------- markdown analysis

def analyze(text):
    """Extract the structural elements that translations must preserve."""
    a = {"headings": [], "slugs": set(), "tables": [], "items": [], "fences": []}
    prose, buf, marker = [], None, None
    for line in text.split("\n"):
        if buf is not None:
            buf.append(line)
            if line.strip().startswith(marker) and line.strip().strip(marker[0]) == "":
                a["fences"].append("\n".join(buf))
                buf = None
            continue
        m = FENCE_RE.match(line)
        if m:
            buf, marker = [line], m.group(1)
            continue
        h = HEADING_RE.match(line)
        if h:
            a["headings"].append(len(h.group(1)))
            a["slugs"].add(github_slug(h.group(2)))
        if line.lstrip().startswith("|"):
            a["tables"].append(line.strip().strip("|").count("|") + 1)
        i = ITEM_RE.match(line)
        if i:
            a["items"].append((i.group(1) or "").strip())
        prose.append(line)
    if buf is not None:
        a["fences"].append("\n".join(buf) + "\n<UNTERMINATED>")
    prose = "\n".join(prose)
    a["code"] = Counter(m.group(2) for m in INLINE_CODE_RE.finditer(prose))
    a["links"] = [m.group(2) for m in LINK_RE.finditer(prose)]
    return a


def resolve_link(doc_path, target, problems, locale=None):
    """Return a canonical key for a link target; record broken links."""
    if re.match(r"^[a-z][a-z0-9+.-]*:", target):
        return target                                   # absolute URL / mailto
    path_part, _, anchor = target.partition("#")
    if not path_part:
        return "#"                                      # same-page anchor
    resolved = (doc_path.parent / path_part).resolve()
    if not resolved.exists():
        problems.append(f"broken link: {target}")
        return target
    if anchor and resolved.suffix == ".md":
        if github_slug(anchor) not in analyze(strip_blocks(read(resolved)))["slugs"]:
            problems.append(f"broken anchor: {target}")
    key = rel(resolved)
    if locale and key.startswith(f"i18n/{locale}/") and key.count("/") == 2:
        key = key.split("/", 2)[2]                      # translated sibling ≙ English doc
    return key


# ------------------------------------------------------------ metadata

def parse_meta(text):
    m = META_RE.search(text)
    if not m:
        return None
    fields = {}
    for line in m.group(1).splitlines():
        f = FIELD_RE.match(line)
        if f:
            fields[f.group("k").strip()] = f.group("v").strip()
    return fields


def render_meta(locale, doc, status, revision):
    return (
        "<!-- i18n:meta -->\n"
        f"> - **Translation status:** {status}\n"
        f"> - **Language:** {locale}\n"
        "> - **Original language:** English\n"
        f"> - **Source:** [{doc}](../../{doc})\n"
        f"> - **Source revision:** {revision}\n"
        "<!-- /i18n:meta -->\n\n"
    )


def set_meta(path, locale, doc, status, revision):
    text = read(path)
    block = render_meta(locale, doc, status, revision)
    if META_RE.search(text):
        text = META_RE.sub(lambda _: block, text, count=1)
    else:
        nav = NAV_RE.search(text)
        at = nav.end() if nav and nav.start() == 0 else 0
        text = text[:at] + block + text[at:]
    write(path, text)


# ------------------------------------------------------------ validation

def compare(src, tr):
    problems = []
    if src["headings"] != tr["headings"]:
        problems.append(f"heading structure differs: source {src['headings']} vs translation {tr['headings']}")
    if src["tables"] != tr["tables"]:
        problems.append(f"table rows/columns differ: source {src['tables']} vs translation {tr['tables']}")
    if src["items"] != tr["items"]:
        problems.append(f"list items differ: source {len(src['items'])} vs translation {len(tr['items'])} (or checkbox states)")
    if src["fences"] != tr["fences"]:
        problems.append("code blocks differ from the source (code blocks must be copied verbatim)")
    if src["code"] != tr["code"]:
        missing = src["code"] - tr["code"]
        extra = tr["code"] - src["code"]
        if missing:
            problems.append("inline code missing/changed: " + ", ".join(f"`{c}`" for c in sorted(missing)))
        if extra:
            problems.append("inline code not in source: " + ", ".join(f"`{c}`" for c in sorted(extra)))
    return problems


def validate_translation(locale, doc):
    """Return (problems, info) for one translation."""
    src_path, tr_path = ROOT / doc, I18N / locale / doc
    problems, info = [], {"status": None, "fresh": False}
    if not tr_path.exists():
        return [f"missing translation"], info
    text = read(tr_path)
    meta = parse_meta(text)
    if meta is None:
        return ["metadata block missing"], info
    for k in META_KEYS:
        if k not in meta:
            problems.append(f"metadata field missing: {k}")
    status = meta.get("Translation status")
    info["status"] = status
    if status not in STATUSES:
        problems.append(f"invalid status {status!r} (expected one of {', '.join(STATUSES)})")
    if meta.get("Language") != locale:
        problems.append(f"metadata Language is {meta.get('Language')!r}, directory is {locale!r}")
    if meta.get("Source") != f"[{doc}](../../{doc})":
        problems.append(f"metadata Source should be [{doc}](../../{doc})")
    revision = meta.get("Source revision", "")
    info["fresh"] = revision == f"sha256:{source_hash(src_path)}"
    if status in ("Current", "Outdated") and not re.fullmatch(r"sha256:[0-9a-f]{64}", revision):
        problems.append(f"Source revision must be sha256:<hash> for status {status}")

    src_body, tr_body = strip_blocks(read(src_path)), strip_blocks(text)
    problems += compare(analyze(src_body), analyze(tr_body))

    link_problems = []
    src_links = Counter(resolve_link(src_path, t, [], None) for t in analyze(src_body)["links"])
    tr_links = Counter(resolve_link(tr_path, t, link_problems, locale) for t in analyze(tr_body)["links"])
    problems += link_problems
    if src_links != tr_links:
        problems.append(
            "link targets differ from source: missing "
            f"{sorted((src_links - tr_links).elements())}, extra {sorted((tr_links - src_links).elements())}"
        )
    for t in analyze(tr_body)["links"]:
        if t.startswith("../../") and t[6:].split("#")[0] in canonical_docs() and (I18N / locale / t[6:].split("#")[0]).exists():
            problems.append(f"links to English {t} although a {locale} translation exists")
    return problems, info


# ---------------------------------------------------------------- commands

def cmd_check(args):
    langs, _ = load_languages()
    names = {l["code"] for l in langs}
    docs, locs = canonical_docs(), locales()
    errors, review = 0, 0
    out = []

    for loc in locs:
        if loc not in names:
            out.append(f"ERROR  i18n/{loc}/ has no entry in i18n/languages.json")
            errors += 1
    for loc in sorted(names):
        if loc != next(l["code"] for l in langs if l.get("canonical")) and loc not in locs:
            out.append(f"WARN   {loc} is listed in languages.json but i18n/{loc}/ does not exist")

    for doc in docs:                                     # English link validation
        problems = []
        for t in analyze(strip_blocks(read(ROOT / doc)))["links"]:
            resolve_link(ROOT / doc, t, problems)
        for p in problems:
            out.append(f"ERROR  {doc}: {p}")
            errors += 1

    for loc in locs:
        for extra in sorted(p.name for p in (I18N / loc).glob("*.md") if p.name not in docs):
            out.append(f"WARN   i18n/{loc}/{extra}: no English source with this name")
        for doc in docs:
            problems, info = validate_translation(loc, doc)
            label = f"i18n/{loc}/{doc}"
            status, fresh = info["status"], info["fresh"]
            if status == "Current" and not fresh:
                review += 1
                out.append(f"REVIEW {label}: English source changed since last sync")
                if args.mark_outdated:
                    path = I18N / loc / doc
                    meta = parse_meta(read(path))
                    set_meta(path, loc, doc, "Outdated", meta["Source revision"])
                    out.append(f"       -> status set to Outdated")
            elif status == "Outdated":
                review += 1
                out.append(f"REVIEW {label}: marked Outdated" + (" (source hash matches; run stamp after review)" if fresh else ""))
            elif status == "Draft":
                review += 1
                out.append(f"REVIEW {label}: Draft (translation incomplete)")
            for p in problems:
                level = "WARN  " if status == "Draft" else "ERROR "
                out.append(f"{level} {label}: {p}")
                errors += level == "ERROR "

    # Summary matrix
    width = max(len(d) for d in docs)
    out.append("")
    out.append("Document".ljust(width) + "  " + "  ".join(l.ljust(9) for l in locs))
    for doc in docs:
        cells = []
        for loc in locs:
            problems, info = validate_translation(loc, doc)
            if problems and info["status"] != "Draft":
                cell = "ERROR"
            elif info["status"] == "Current" and info["fresh"]:
                cell = "current"
            elif info["status"] == "Current":
                cell = "stale"
            else:
                cell = (info["status"] or "missing").lower()
            cells.append(cell.ljust(9))
        out.append(doc.ljust(width) + "  " + "  ".join(cells))
    out.append("")
    out.append(f"{len(docs)} English documents, {len(locs)} locales, {errors} error(s), {review} translation(s) needing review")
    print("\n".join(out))
    return 1 if errors else 2 if review else 0


def nav_line(langs, canonical, doc, current_file):
    parts = []
    for lang in langs:
        code = lang["code"]
        target = ROOT / doc if code == canonical else I18N / code / doc
        if target == current_file:
            parts.append(f"**{lang['name']}**")
        elif target.exists():
            link = Path(os.path.relpath(target, current_file.parent)).as_posix()
            parts.append(f"[{lang['name']}]({link})")
    return " | ".join(parts)


def cmd_nav(args):
    langs, canonical = load_languages()
    changed = 0
    for doc in canonical_docs():
        files = [ROOT / doc] + [I18N / loc / doc for loc in locales() if (I18N / loc / doc).exists()]
        for path in files:
            text = read(path)
            block = f"<!-- i18n:nav -->\n{nav_line(langs, canonical, doc, path)}\n<!-- /i18n:nav -->\n\n"
            new = NAV_RE.sub(lambda _: block, text, count=1) if NAV_RE.search(text) else block + text
            if new != text:
                write(path, new)
                changed += 1
                print(f"updated navigation: {rel(path)}")
    print(f"{changed} file(s) updated")
    return 0


def cmd_stamp(args):
    failed = 0
    targets = []
    for spec in args.files:
        loc, _, name = spec.replace("\\", "/").removeprefix("i18n/").partition("/")
        names = canonical_docs() if name == "*" else [name]
        targets += [(loc, n) for n in names]
    for loc, doc in targets:
        problems, _ = validate_translation(loc, doc)
        if problems:
            failed += 1
            print(f"REFUSED i18n/{loc}/{doc}:")
            for p in problems:
                print(f"   - {p}")
            continue
        set_meta(I18N / loc / doc, loc, doc, "Current", f"sha256:{source_hash(ROOT / doc)}")
        print(f"stamped i18n/{loc}/{doc} as Current")
    return 1 if failed else 0


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="validate translations and report status")
    c.add_argument("--mark-outdated", action="store_true",
                   help="set status to Outdated on translations whose English source changed")
    sub.add_parser("nav", help="rewrite language navigation blocks")
    s = sub.add_parser("stamp", help="mark reviewed translations as Current")
    s.add_argument("files", nargs="+", metavar="LOCALE/FILE.md")
    args = parser.parse_args()
    return {"check": cmd_check, "nav": cmd_nav, "stamp": cmd_stamp}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
