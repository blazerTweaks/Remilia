#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""REMILIA change categories: check, assemble and apply (ARCHITECTURE.md §10).

The contract is remilia/README.md. Python 3.9+, standard library only, so the
same code runs on the Windows host (V0) and in the build container (V1).

Commands
  check      V0 static checks of a layer root (default: remilia/) against the
             LibreWolf base snapshot (upstream/librewolf-base/).
  apply      Apply categories to a prepared tree (called by prepare.sh).
  assemble   Assemble prefs/policies/mozconfig from base files into a
             directory, without a tree (V1 determinism and negative tests).
  exclude    Remove excluded LibreWolf patches from patches.txt and print the
             provenance lines that record them.
  snapshot   Copy the LibreWolf base files of a prepared tree.
  verify-base  Compare a prepared tree with the snapshot.
  hash       Print the content hash of each selected category.
  expected   Print the tree paths that applying categories may change.
  patch-targets  Print the paths a patch file touches.

Every check reports all problems it finds, then exits 1. Nothing is written
to a tree before all static checks of the selected categories have passed.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent

CATEGORIES = ("build-fixes", "security", "privacy", "branding")
PREFIX = {"build-fixes": "BF", "security": "SEC", "privacy": "PRIV", "branding": "BRAND"}
ALLOWED_ENTRIES = {
    "series", "patches", "prefs.cfg", "policies.json", "mozconfig",
    "files", "replaces.txt", "deviations.tsv", "README.md",
}
# Tree paths that categories may only change through fragments (or never).
CFG_PATH = "lw/librewolf.cfg"
POLICIES_PATH = "lw/policies.json"
MOZCONFIG_PATH = "mozconfig"
PROVENANCE_PATH = "REMILIA-PROVENANCE.txt"
FORBIDDEN_TARGETS = {CFG_PATH, POLICIES_PATH, MOZCONFIG_PATH, PROVENANCE_PATH}
BASE_FILES = {  # snapshot file name -> tree path
    "librewolf.cfg": CFG_PATH,
    "policies.json": POLICIES_PATH,
    "mozconfig": MOZCONFIG_PATH,
}
SNAPSHOT_FILES = ("librewolf.cfg", "policies.json", "mozconfig", "patches.txt")

ID_RE = r"(?:BF|SEC|PRIV|BRAND)-\d{3}"
VALUE_RE = r'"(?:[^"\\\n]|\\.)*"|-?\d+|true|false'
PREF_LINE = re.compile(
    r'^(pref|defaultPref|lockPref)\("((?:[^"\\\n]|\\.)+)", (' + VALUE_RE + r')\);'
    r'(?: // deviation: (' + ID_RE + r'))?$')
DEVIATION_TAIL = re.compile(r"^(.*?) # deviation: (" + ID_RE + r")$")
MOZ_AC = re.compile(r"^ac_add_options (--[A-Za-z0-9][A-Za-z0-9_.-]*)(?:=(\S.*))?$")
MOZ_MK = re.compile(r"^mk_add_options ([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
MOZ_EXPORT = re.compile(r"^export ([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
BASE_PREF_CALL = re.compile(
    r"\b(pref|defaultPref|lockPref|clearPref|unlockPref)\(\s*([\"'])((?:(?!\2)[^\\\n]|\\.)*)\2")
# LibreWolf patch exclusions: "<patch path as in patches.txt> <reason>".
EXCLUDE_PATH = r"patches/[A-Za-z0-9._/+-]+\.patch"
EXCLUDE_LINE = re.compile(r"^(" + EXCLUDE_PATH + r")[ \t]+(.*)$")
EXCLUDE_PATH_ONLY = re.compile(r"^(" + EXCLUDE_PATH + r")[ \t]*$")
LEGACY_DECISION_ID = re.compile(r"ADR-\d+", re.I)
INTERNAL_MENTION = re.compile(r"(?<![A-Za-z0-9_.-])internal[/\\]", re.I)
REASON_MIN, REASON_MAX = 10, 200

# deviations.tsv "reference": public documents only (exact, case-sensitive).
REFERENCE_DOCS = ("PRIVACY.md", "SECURITY.md")
FIXTURE_REFERENCE_DOCS = ("tests/layers/README.md",)  # only for layer roots other than remilia/


class Failure(Exception):
    """Raised when problems were found; the message lists them."""


class Problems:
    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, where: str, msg: str) -> None:
        self.items.append(f"{where}: {msg}")

    def raise_if_any(self, what: str) -> None:
        if self.items:
            raise Failure(f"{what}: {len(self.items)} problem(s)\n  " + "\n  ".join(self.items))


def display(path: Path) -> str:
    """Repository-relative POSIX path when possible (stable across host and container)."""
    try:
        return Path(path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return Path(path).as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path: Path, problems: Problems) -> str | None:
    """Strict text read: UTF-8, no CR, ends with a newline (unless empty)."""
    data = path.read_bytes()
    where = display(path)
    ok = True
    if b"\r" in data:
        problems.add(where, "contains a carriage return (CR); use LF line endings")
        ok = False
    if data and not data.endswith(b"\n"):
        problems.add(where, "does not end with a newline")
        ok = False
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as e:
        problems.add(where, f"not valid UTF-8 ({e})")
        return None
    return text  # problems (if any) are already recorded; parsing continues to report more


# --------------------------------------------------------------------------
# deviations.tsv references

_I18N = None


def heading_slugs(doc: Path) -> set[str]:
    """Anchors of a Markdown file, computed by i18n/i18n.py (the documentation checker)."""
    global _I18N
    if _I18N is None:
        path = REPO_ROOT / "i18n" / "i18n.py"
        if not path.is_file():
            raise Failure(f"{display(path)} not found: it is needed to check reference anchors")
        spec = importlib.util.spec_from_file_location("remilia_i18n", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["remilia_i18n"] = module
        spec.loader.exec_module(module)
        _I18N = module
    return set(_I18N.analyze(doc.read_text(encoding="utf-8"))["slugs"])


def is_fixture_root(layer_root: Path) -> bool:
    """True for every layer root except the repository's own remilia/.

    Fixtures live in tests/layers/, but V1 also prepares copies of them in
    staging (for example without one patch), so the location cannot be the
    test. prepare.sh accepts a layer root other than remilia/ only for staging
    trees, and package.sh refuses a tree prepared from one, so fixture
    references never reach a package."""
    try:
        return Path(layer_root).resolve() != (REPO_ROOT / "remilia").resolve()
    except OSError:
        return False


def check_reference(ref: str, layer_root: Path) -> list[str]:
    """Validate a deviations.tsv reference: '<document>' or '<document>#<anchor>'.

    The text is checked first, the file system only for documents on the
    allowed list, so the result is the same on Windows and Linux.
    """
    allowed = REFERENCE_DOCS + (FIXTURE_REFERENCE_DOCS if is_fixture_root(layer_root) else ())
    doc, sep, anchor = ref.partition("#")
    if any(ch.isspace() for ch in ref):
        return [f"reference {ref!r} must not contain spaces or other whitespace"]
    if "\\" in doc:
        return [f"reference {ref!r} must use '/' separators, not backslashes"]
    if ":" in doc:
        return [f"reference {ref!r} must be a repository path (no drive letter, URL or ':')"]
    if doc.startswith("/"):
        return [f"reference {ref!r} must be relative to the repository root, not absolute"]
    parts = doc.split("/")
    if any(p in ("", ".", "..") for p in parts):
        return [f"reference {ref!r} must not contain empty, '.' or '..' path segments"]
    if parts[0].lower() == "internal":
        return [f"reference {ref!r} points into internal/, which is not published"]
    if sep and not anchor:
        return [f"reference {ref!r} has an empty anchor"]
    if doc not in allowed:
        if doc in FIXTURE_REFERENCE_DOCS:
            return [f"reference {doc} is allowed only in test fixtures, not in remilia/; "
                    f"use one of: {', '.join(REFERENCE_DOCS)}"]
        return [f"reference {doc!r} is not an allowed document; use one of: {', '.join(allowed)}"]
    path = REPO_ROOT / doc
    try:
        st = os.lstat(path)
    except OSError:
        return [f"reference {doc} does not exist in the repository"]
    if not stat.S_ISREG(st.st_mode):
        return [f"reference {doc} is not a regular file"]
    if not path.resolve().is_relative_to(REPO_ROOT.resolve()):
        return [f"reference {doc} resolves outside the repository"]
    if anchor and anchor not in heading_slugs(path):
        return [f"reference {ref}: #{anchor} is not a heading anchor of {doc}"]
    return []


# --------------------------------------------------------------------------
# Data model

@dataclass
class Pref:
    category: str
    fn: str
    name: str
    value: str
    deviation: str | None
    where: str
    text: str


@dataclass
class MozLine:
    category: str
    key: str
    deviation: str | None
    where: str


@dataclass
class Deviation:
    id: str
    kind: str
    key: str
    reference: str
    where: str
    used: bool = False


@dataclass
class Patch:
    path: Path          # file on disk
    rel: str            # path relative to patches/
    targets: list[str]  # tree paths touched


@dataclass
class Category:
    name: str
    root: Path
    patches: list[Patch] = field(default_factory=list)
    prefs: list[Pref] = field(default_factory=list)
    prefs_text: str | None = None
    policies: dict | None = None
    moz: list[MozLine] = field(default_factory=list)
    moz_text: str | None = None
    files: dict[str, Path] = field(default_factory=dict)  # tree path -> source
    replaces: set[str] = field(default_factory=set)
    deviations: dict[str, Deviation] = field(default_factory=dict)


# --------------------------------------------------------------------------
# Parsing a category

def norm_tree_path(p: str) -> str | None:
    pp = PurePosixPath(p)
    if pp.is_absolute() or not p or any(part in ("..", "") for part in p.split("/")):
        return None
    return pp.as_posix()


def forbidden(path: str) -> bool:
    return path in FORBIDDEN_TARGETS or path.split("/", 1)[0].startswith("obj-")


def patch_targets(text: str) -> tuple[list[str], list[str]]:
    """Return (targets, errors) for a unified diff applied with -p1."""
    targets: list[str] = []
    errors: list[str] = []
    old_left = new_left = 0  # lines still expected in the current hunk
    for line in text.splitlines():
        if old_left > 0 or new_left > 0:
            tag = line[:1]
            if tag == "\\":
                continue
            if tag in (" ", ""):
                old_left, new_left = old_left - 1, new_left - 1
            elif tag == "-":
                old_left -= 1
            elif tag == "+":
                new_left -= 1
            else:
                errors.append(f"malformed hunk near {line[:60]!r}")
                old_left = new_left = 0
            continue
        m = re.match(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@", line)
        if m:
            old_left = int(m.group(1)) if m.group(1) is not None else 1
            new_left = int(m.group(2)) if m.group(2) is not None else 1
            continue
        if line.startswith("GIT binary patch") or line.startswith("Binary files "):
            errors.append("binary patches are not supported; put binary files in files/")
        if line.startswith("--- ") or line.startswith("+++ "):
            name = line[4:].split("\t", 1)[0].strip()
            if name == "/dev/null":
                continue
            parts = name.split("/", 1)
            if len(parts) != 2:
                errors.append(f"cannot strip one path component (-p1) from {name!r}")
                continue
            rel = norm_tree_path(parts[1])
            if rel is None:
                errors.append(f"unsafe path {name!r}")
            elif rel not in targets:
                targets.append(rel)
    return targets, errors


def patch_header(text: str) -> list[str]:
    head = []
    for line in text.splitlines():
        if line.startswith(("--- ", "diff ", "Index: ")):
            break
        head.append(line)
    return head


def load_category(name: str, root: Path, problems: Problems) -> Category:
    cat = Category(name=name, root=root)
    for entry in sorted(os.listdir(root)):
        if entry not in ALLOWED_ENTRIES:
            problems.add(display(root / entry), "not allowed in a category (see remilia/README.md)")

    # deviations.tsv first: other parsers reference it
    dev_file = root / "deviations.tsv"
    if dev_file.is_file():
        text = read_text(dev_file, problems) or ""
        keys_seen: set[tuple[str, str]] = set()
        for n, line in enumerate(text.splitlines(), 1):
            where = f"{display(dev_file)}:{n}"
            if not line.strip() or line.startswith("#"):
                continue
            cols = line.split("\t")
            if len(cols) != 4 or not all(c.strip() for c in cols):
                problems.add(where, "expected 4 tab-separated columns: id kind key reference")
                continue
            did, kind, key, ref = cols
            if not re.fullmatch(PREFIX[name] + r"-\d{3}", did):
                problems.add(where, f"id {did!r} must be {PREFIX[name]}-NNN in category {name}")
            if kind not in ("pref", "policy", "mozconfig"):
                problems.add(where, f"kind {kind!r} must be pref, policy or mozconfig")
            if did in cat.deviations:
                problems.add(where, f"duplicate id {did}")
            if (kind, key) in keys_seen:
                problems.add(where, f"duplicate entry for {kind} {key}")
            keys_seen.add((kind, key))
            for msg in check_reference(ref, root.parent):
                problems.add(where, msg)
            cat.deviations[did] = Deviation(did, kind, key, ref, where)

    # patches
    series = root / "series"
    pdir = root / "patches"
    if series.exists() != pdir.exists():
        problems.add(display(root), "series and patches/ must exist together")
    if series.is_file() and pdir.is_dir():
        listed: list[str] = []
        text = read_text(series, problems) or ""
        for n, line in enumerate(text.splitlines(), 1):
            where = f"{display(series)}:{n}"
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            rel = norm_tree_path(s)
            if rel is None or s != line:
                problems.add(where, f"invalid patch path {line!r}")
                continue
            if rel in listed:
                problems.add(where, f"{rel} listed twice")
                continue
            listed.append(rel)
        on_disk = sorted(p.relative_to(pdir).as_posix() for p in pdir.rglob("*") if p.is_file())
        for rel in on_disk:
            if rel not in listed:
                problems.add(display(pdir / rel), "not listed in series")
        for rel in listed:
            p = pdir / rel
            if not p.is_file():
                problems.add(display(series), f"{rel} does not exist in patches/")
                continue
            text = read_text(p, problems) or ""
            head = patch_header(text)
            cats = [h[len("Category: "):] for h in head if h.startswith("Category: ")]
            if cats != [name]:
                problems.add(display(p), f"header must contain exactly one 'Category: {name}' line")
            if not any(h.startswith("Summary: ") and h[9:].strip() for h in head):
                problems.add(display(p), "header must contain a 'Summary: ...' line")
            targets, errs = patch_targets(text)
            for e in errs:
                problems.add(display(p), e)
            if not targets and not errs:
                problems.add(display(p), "no file changes found")
            for t in targets:
                if forbidden(t):
                    problems.add(display(p), f"must not touch {t}; use the category fragments")
            cat.patches.append(Patch(p, rel, targets))

    # prefs.cfg
    pf = root / "prefs.cfg"
    if pf.is_file():
        text = read_text(pf, problems)
        cat.prefs_text = text
        names: set[str] = set()
        for n, line in enumerate((text or "").splitlines(), 1):
            where = f"{display(pf)}:{n}"
            if not line or line.startswith("//"):
                continue
            m = PREF_LINE.match(line)
            if not m:
                problems.add(where, "not a valid line: expected fn(\"name\", value); "
                             "[// deviation: ID] with fn pref/defaultPref/lockPref")
                continue
            fn, pname, value, dev = m.groups()
            if pname in names:
                problems.add(where, f"pref {pname} set twice in this category")
            names.add(pname)
            cat.prefs.append(Pref(name, fn, pname, value, dev, where, line))

    # policies.json
    pj = root / "policies.json"
    if pj.is_file():
        text = read_text(pj, problems)
        try:
            obj = json.loads(text or "")
        except json.JSONDecodeError as e:
            problems.add(display(pj), f"invalid JSON: {e}")
            obj = None
        if obj is not None:
            if not isinstance(obj, dict) or list(obj) != ["policies"] or not isinstance(obj["policies"], dict):
                problems.add(display(pj), 'must be an object whose only key is "policies" (an object)')
            elif not obj["policies"]:
                problems.add(display(pj), '"policies" is empty')
            else:
                for k, v in obj["policies"].items():
                    if isinstance(v, dict) and not v:
                        problems.add(display(pj), f"policy {k} is an empty object")
                cat.policies = obj["policies"]

    # mozconfig
    mf = root / "mozconfig"
    if mf.is_file():
        text = read_text(mf, problems)
        cat.moz_text = text
        keys: set[str] = set()
        for n, line in enumerate((text or "").splitlines(), 1):
            where = f"{display(mf)}:{n}"
            if not line or line.startswith("#"):
                continue
            m = DEVIATION_TAIL.match(line)
            body, dev = (m.group(1), m.group(2)) if m else (line, None)
            key = moz_key(body)
            if key is None:
                problems.add(where, "expected 'ac_add_options --opt[=v]', 'mk_add_options NAME=v' "
                             "or 'export NAME=v' [# deviation: ID]")
                continue
            if key in keys:
                problems.add(where, f"{key} set twice in this category")
            keys.add(key)
            cat.moz.append(MozLine(name, key, dev, where))

    # files/ and replaces.txt
    fdir = root / "files"
    if fdir.is_dir():
        for p in sorted(fdir.rglob("*")):
            rel = p.relative_to(fdir).as_posix()
            if p.is_symlink():
                problems.add(display(p), "symlinks are not allowed in files/")
            elif p.is_file():
                if forbidden(rel):
                    problems.add(display(p), f"must not write {rel}; use the category fragments")
                cat.files[rel] = p
    rf = root / "replaces.txt"
    if rf.is_file():
        text = read_text(rf, problems) or ""
        for n, line in enumerate(text.splitlines(), 1):
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            rel = norm_tree_path(s)
            where = f"{display(rf)}:{n}"
            if rel is None or s != line:
                problems.add(where, f"invalid path {line!r}")
            elif rel not in cat.files:
                problems.add(where, f"{rel} has no file in files/")
            else:
                cat.replaces.add(rel)
    return cat


def moz_key(body: str) -> str | None:
    m = MOZ_AC.match(body)
    if m:
        opt = m.group(1)[2:]
        for pos, neg, kind in (("enable-", "disable-", "enable"), ("with-", "without-", "with")):
            for pre in (pos, neg):
                if opt.startswith(pre) and len(opt) > len(pre):
                    return f"{kind}:{opt[len(pre):]}"
        return f"opt:{opt}"
    m = MOZ_MK.match(body)
    if m:
        return f"mk:{m.group(1)}"
    m = MOZ_EXPORT.match(body)
    if m:
        return f"env:{m.group(1)}"
    return None


# --------------------------------------------------------------------------
# LibreWolf base files

def strip_js_comments(src: str) -> str:
    """Blank out // and /* */ comments, keeping strings and newlines (line numbers)."""
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        if c in "\"'`":
            j = i + 1
            while j < n and src[j] != c:
                j += 2 if src[j] == "\\" else 1
            out.append(src[i:j + 1])
            i = j + 1
        elif src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i))
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j < 0 else j + 2
            out.append(re.sub(r"[^\n]", " ", src[i:j]))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def base_prefs(cfg_text: str) -> dict[str, list[tuple[str, int]]]:
    stripped = strip_js_comments(cfg_text)
    result: dict[str, list[tuple[str, int]]] = {}
    for m in BASE_PREF_CALL.finditer(stripped):
        line = stripped.count("\n", 0, m.start()) + 1
        result.setdefault(m.group(3), []).append((m.group(1), line))
    return result


def base_moz_keys(text: str) -> set[str]:
    keys = set()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        k = moz_key(s.split(" #", 1)[0].rstrip())
        if k:
            keys.add(k)
    return keys


@dataclass
class Base:
    cfg: str
    policies_raw: str
    policies: dict
    mozconfig: str
    origin: str

    @classmethod
    def load(cls, cfg: Path, policies: Path, mozconfig: Path, origin: str) -> "Base":
        pol_raw = policies.read_text(encoding="utf-8")
        return cls(cfg.read_text(encoding="utf-8"), pol_raw, json.loads(pol_raw),
                   mozconfig.read_text(encoding="utf-8"), origin)

    @classmethod
    def from_snapshot(cls, d: Path) -> "Base":
        return cls.load(d / "librewolf.cfg", d / "policies.json", d / "mozconfig", display(d))

    @classmethod
    def from_tree(cls, t: Path) -> "Base":
        return cls.load(t / CFG_PATH, t / POLICIES_PATH, t / MOZCONFIG_PATH, str(t))


# --------------------------------------------------------------------------
# Cross-category checks and assembly

@dataclass
class Plan:
    """Result of checking selected categories together (against a base or not)."""
    categories: list[Category]
    overrides: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    policy_mode: dict[str, str] = field(default_factory=dict)  # policy -> 'merge' | 'whole'


def check_together(cats: list[Category], base: Base | None, problems: Problems) -> Plan:
    plan = Plan(cats)
    bprefs = base_prefs(base.cfg) if base else {}
    bpol = base.policies.get("policies", {}) if base else {}
    bmoz = base_moz_keys(base.mozconfig) if base else set()

    def use_deviation(cat: Category, did: str | None, kind: str, key: str, where: str,
                      overrides: bool) -> None:
        if overrides:
            if did is None and kind != "policy":
                problems.add(where, f"overrides LibreWolf {kind} {key}: needs '{'//' if kind == 'pref' else '#'}"
                             f" deviation: <ID>' and a deviations.tsv entry")
                return
            # policies have no inline annotation: find the entry by key
            if kind == "policy":
                match = [d for d in cat.deviations.values() if d.kind == "policy" and d.key == key]
                if not match:
                    problems.add(where, f"overrides LibreWolf policy {key}: needs a deviations.tsv entry "
                                 f"(kind policy, key {key})")
                    return
                dev = match[0]
            else:
                dev = cat.deviations.get(did)
                if dev is None:
                    problems.add(where, f"deviation {did} is not registered in {cat.name}/deviations.tsv")
                    return
                if (dev.kind, dev.key) != (kind, key):
                    problems.add(where, f"deviation {did} is registered for {dev.kind} {dev.key}, not {kind} {key}")
                    return
            dev.used = True
            plan.overrides.append({"category": cat.name, "id": dev.id, "kind": kind, "key": key,
                                   "reference": dev.reference})
        elif did is not None and base is not None:
            problems.add(where, f"declares deviation {did} but {kind} {key} is not set by LibreWolf")
        elif did is not None:
            dev = cat.deviations.get(did)
            if dev is None:
                problems.add(where, f"deviation {did} is not registered in {cat.name}/deviations.tsv")
            else:
                dev.used = True  # cannot judge without a base

    # prefs
    owner: dict[str, Pref] = {}
    for cat in cats:
        for p in cat.prefs:
            if p.name in owner:
                problems.add(p.where, f"pref {p.name} is also set by category {owner[p.name].category} "
                             f"({owner[p.name].where}); one setting belongs to one category")
                continue
            owner[p.name] = p
            inherited = bprefs.get(p.name)
            if inherited:
                fns = {fn for fn, _ in inherited}
                lines = ", ".join(f"{fn}@{ln}" for fn, ln in inherited)
                if fns - {"pref", "defaultPref", "lockPref"}:
                    problems.add(p.where, f"LibreWolf clears or unlocks {p.name} ({lines}); "
                                 "overriding it needs a maintainer decision and a change to the tool")
                elif len(fns) > 1:
                    problems.add(p.where, f"LibreWolf sets {p.name} with different functions ({lines}); "
                                 "overriding it needs a maintainer decision")
                elif p.fn not in fns:
                    problems.add(p.where, f"LibreWolf sets {p.name} with {inherited[0][0]}() ({lines}); "
                                 f"keep the same function instead of {p.fn}()")
                use_deviation(cat, p.deviation, "pref", p.name, p.where, True)
                if p.fn == "lockPref" and "lockPref" in fns:
                    plan.notes.append(f"runtime-unverified: {cat.name} redefines lockPref {p.name} "
                                      f"(LibreWolf {lines}); effect must be confirmed in a running browser")
            else:
                use_deviation(cat, p.deviation, "pref", p.name, p.where, False)

    # policies
    definers: dict[str, list[Category]] = {}
    for cat in cats:
        for k in (cat.policies or {}):
            definers.setdefault(k, []).append(cat)
    for pol, dcats in definers.items():
        vals = [c.policies[pol] for c in dcats]
        merge = all(isinstance(v, dict) for v in vals) and (pol not in bpol or isinstance(bpol[pol], dict))
        plan.policy_mode[pol] = "merge" if merge else "whole"
        if merge:
            sub_owner: dict[str, str] = {}
            for c in dcats:
                for sub in c.policies[pol]:
                    unit = f"{pol}/{sub}"
                    where = f"{display(c.root / 'policies.json')}: {unit}"
                    if sub in sub_owner:
                        problems.add(where, f"policy unit {unit} is also set by category {sub_owner[sub]}")
                        continue
                    sub_owner[sub] = c.name
                    use_deviation(c, None, "policy", unit, where, pol in bpol and sub in bpol[pol])
        else:
            if len(dcats) > 1:
                problems.add(f"policy {pol}", "set by several categories: "
                             + ", ".join(c.name for c in dcats) + "; one setting belongs to one category")
                continue
            c = dcats[0]
            use_deviation(c, None, "policy", pol, f"{display(c.root / 'policies.json')}: {pol}", pol in bpol)

    # mozconfig
    mowner: dict[str, MozLine] = {}
    for cat in cats:
        for ml in cat.moz:
            if ml.key in mowner:
                problems.add(ml.where, f"{ml.key} is also set by category {mowner[ml.key].category} "
                             f"({mowner[ml.key].where})")
                continue
            mowner[ml.key] = ml
            use_deviation(cat, ml.deviation, "mozconfig", ml.key, ml.where, ml.key in bmoz)

    # files written by several categories
    fowner: dict[str, str] = {}
    for cat in cats:
        for rel in cat.files:
            if rel in fowner:
                problems.add(display(cat.files[rel]), f"{rel} is also written by category {fowner[rel]}")
            fowner.setdefault(rel, cat.name)

    # unused deviations (only meaningful with a base)
    if base is not None:
        for cat in cats:
            for d in cat.deviations.values():
                if not d.used:
                    problems.add(d.where, f"deviation {d.id} ({d.kind} {d.key}) is not used by any "
                                 "override of LibreWolf")
    return plan


def header(comment: str, cat: Category, frag: str, content: str, end: bool = False) -> str:
    if end:
        return f"{comment} ===== end of REMILIA category: {cat.name} =====\n"
    # Category-relative source path: the output must not depend on where the
    # layer root is (host, container, temporary copy). Provenance records the root.
    return (f"{comment} ===== REMILIA category: {cat.name} =====\n"
            f"{comment} Source: {cat.name}/{frag} "
            f"(sha256 {sha256_bytes(content.encode('utf-8'))})\n")


def assemble(plan: Plan, base: Base) -> dict[str, str | None]:
    """Return new contents for the three config files (None = leave unchanged)."""
    out: dict[str, str | None] = {CFG_PATH: None, POLICIES_PATH: None, MOZCONFIG_PATH: None}
    cfg_parts = [c for c in plan.categories if c.prefs_text is not None]
    if cfg_parts:
        text = base.cfg if base.cfg.endswith("\n") else base.cfg + "\n"
        for c in cfg_parts:
            text += "\n" + header("//", c, "prefs.cfg", c.prefs_text) + c.prefs_text \
                    + header("//", c, "prefs.cfg", "", end=True)
        out[CFG_PATH] = text
    moz_parts = [c for c in plan.categories if c.moz_text is not None]
    if moz_parts:
        text = base.mozconfig if base.mozconfig.endswith("\n") else base.mozconfig + "\n"
        for c in moz_parts:
            text += "\n" + header("#", c, "mozconfig", c.moz_text) + c.moz_text \
                    + header("#", c, "mozconfig", "", end=True)
        out[MOZCONFIG_PATH] = text
    pol_parts = [c for c in plan.categories if c.policies]
    if pol_parts:
        doc = json.loads(base.policies_raw)
        pols = doc.setdefault("policies", {})
        for c in pol_parts:
            for k, v in c.policies.items():
                if plan.policy_mode[k] == "merge":
                    target = pols.setdefault(k, {})
                    for sub, sv in v.items():
                        target[sub] = sv
                else:
                    pols[k] = v
        out[POLICIES_PATH] = json.dumps(doc, indent=4, ensure_ascii=False) + "\n"
    return out


# --------------------------------------------------------------------------
# Layer selection and loading

def present_categories(layer_root: Path, problems: Problems) -> list[str]:
    if not layer_root.is_dir():
        return []
    for entry in sorted(os.listdir(layer_root)):
        if entry not in CATEGORIES and entry != "README.md":
            problems.add(display(layer_root / entry), "unknown entry in the layer root; categories are "
                         + ", ".join(CATEGORIES))
    return [c for c in CATEGORIES if (layer_root / c).is_dir()]


def select(spec: str, layer_root: Path, problems: Problems) -> list[str]:
    present = present_categories(layer_root, problems)
    spec = spec.strip()
    if spec == "all":
        return present
    if spec == "none":
        return []
    wanted = [s.strip() for s in spec.split(",") if s.strip()]
    for w in wanted:
        if w not in CATEGORIES:
            problems.add("REMILIA_LAYERS", f"unknown category {w!r}; use all, none or "
                         + ",".join(CATEGORIES))
        elif w not in present:
            problems.add("REMILIA_LAYERS", f"category {w!r} has no directory in {display(layer_root)}")
    if len(set(wanted)) != len(wanted):
        problems.add("REMILIA_LAYERS", "a category is listed twice")
    return [c for c in CATEGORIES if c in wanted]


def load(layer_root: Path, spec: str, problems: Problems) -> list[Category]:
    names = select(spec, layer_root, problems)
    return [load_category(n, layer_root / n, problems) for n in names]


def category_hash(cat_root: Path) -> str:
    """sha256 over sorted (path, content hash) of everything applied (README.md excluded)."""
    h = hashlib.sha256()
    for p in sorted(cat_root.rglob("*"), key=lambda x: x.relative_to(cat_root).as_posix()):
        rel = p.relative_to(cat_root).as_posix()
        if p.is_file() and rel != "README.md":
            h.update(f"{rel}\0{sha256_file(p)}\n".encode())
    return h.hexdigest()


# --------------------------------------------------------------------------
# Applying to a tree

def run_patch(tree: Path, patch: Path, reverse: bool = False) -> subprocess.CompletedProcess:
    cmd = ["patch", "-p1", "--fuzz=0", "--batch", "--no-backup-if-mismatch",
           "--reject-file=-", "-i", str(patch)]
    cmd.insert(1, "--reverse" if reverse else "--forward")
    return subprocess.run(cmd, cwd=tree, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding="utf-8", errors="replace")


def verify_base(tree: Path, snapshot: Path, problems: Problems) -> None:
    for snap_name, tree_path in BASE_FILES.items():
        a, b = snapshot / snap_name, tree / tree_path
        if not a.is_file():
            problems.add(display(a), "missing from the snapshot")
        elif not b.is_file():
            problems.add(str(b), "missing from the tree")
        elif a.read_bytes() != b.read_bytes():
            problems.add(tree_path, f"differs from the snapshot {display(a)}; LibreWolf changed: review "
                         "and refresh it (remilia_layers.py snapshot, UPSTREAM.md step 5)")


def apply(tree: Path, layer_root: Path, spec: str, snapshot: Path | None, report: Path | None) -> dict:
    problems = Problems()
    cats = load(layer_root, spec, problems)
    problems.raise_if_any("category checks")
    if snapshot is not None:
        verify_base(tree, snapshot, problems)
        problems.raise_if_any("LibreWolf base snapshot")
    base = Base.from_tree(tree)
    plan = check_together(cats, base, problems)
    problems.raise_if_any("cross-category checks")
    new_configs = assemble(plan, base)

    touched: dict[str, list[str]] = {}
    written_by: dict[str, str] = {}
    log: list[str] = []
    for cat in cats:
        for p in cat.patches:
            r = run_patch(tree, p.path)
            log.append(f"[{cat.name}] {p.rel}\n{r.stdout}")
            if r.returncode != 0:
                raise Failure(f"{display(p.path)} does not apply with fuzz 0:\n{r.stdout}")
            for t in p.targets:
                touched.setdefault(t, []).append(cat.name)
        for rel, src in sorted(cat.files.items()):
            dest = tree / rel
            exists = dest.exists() or dest.is_symlink()
            if rel in written_by:
                raise Failure(f"{display(src)}: {rel} was already written by category {written_by[rel]}")
            if exists and rel not in cat.replaces:
                raise Failure(f"{display(src)}: {rel} exists in the tree; list it in replaces.txt to overwrite it")
            if not exists and rel in cat.replaces:
                raise Failure(f"{display(cat.root / 'replaces.txt')}: {rel} does not exist in the tree")
            if dest.is_symlink() or dest.is_dir():
                raise Failure(f"{rel} in the tree is a symlink or directory; refusing to overwrite it")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            if not exists:
                os.chmod(dest, 0o644)
            written_by[rel] = cat.name
            touched.setdefault(rel, []).append(cat.name)
    contributes = {
        CFG_PATH: lambda c: c.prefs_text is not None,
        MOZCONFIG_PATH: lambda c: c.moz_text is not None,
        POLICIES_PATH: lambda c: bool(c.policies),
    }
    for path, content in new_configs.items():
        if content is not None:
            (tree / path).write_bytes(content.encode("utf-8"))
            for c in cats:
                if contributes[path](c):
                    touched.setdefault(path, []).append(c.name)

    result = {
        "layer_root": display(layer_root),
        "requested": spec,
        "categories": [{"name": c.name, "sha256": category_hash(c.root),
                        "patches": len(c.patches), "files": len(c.files),
                        "prefs": len(c.prefs), "policies": len(c.policies or {}),
                        "mozconfig": len(c.moz)} for c in cats],
        "touched": dict(sorted(touched.items())),
        "overlaps": {k: v for k, v in sorted(touched.items()) if len(set(v)) > 1},
        "overrides": plan.overrides,
        "notes": plan.notes,
        "snapshot_verified": snapshot is not None,
    }
    if report:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        report.with_suffix(".patch-log.txt").write_text("".join(log), encoding="utf-8")
    return result


def provenance_lines(result: dict) -> list[str]:
    lines = [f"Layer root:  {result['layer_root']}",
             f"Layers:      {','.join(c['name'] for c in result['categories']) or '(none present)'}"
             f" (REMILIA_LAYERS={result['requested']})"]
    for c in result["categories"]:
        lines.append(f"Category {c['name']}: sha256 {c['sha256']} ({c['patches']} patches, "
                     f"{c['files']} files, {c['prefs']} prefs, {c['policies']} policies, "
                     f"{c['mozconfig']} mozconfig lines)")
    lines.append(f"Deviations from LibreWolf: {len(result['overrides'])}"
                 + (" (" + ", ".join(o["id"] for o in result["overrides"]) + ")" if result["overrides"] else ""))
    for n in result["notes"]:
        lines.append(f"Note: {n}")
    lines.append(f"Files touched by several categories: {len(result['overlaps'])}")
    return lines


# --------------------------------------------------------------------------
# Exclusions

EXCLUDE_FORMAT = (f"'<patch path as in patches.txt> <reason>' "
                  f"(reason: {REASON_MIN} to {REASON_MAX} characters, no commas)")
LEGACY_REASON_START = re.compile(r"ADR-\d+(?!\d)", re.I)


def reason_problem(reason: str) -> str | None:
    """Why an exclusion reason is not acceptable, or None. The reason is public:
    it is recorded in REMILIA-PROVENANCE.txt, which ships with the package."""
    if not reason:
        return f"missing reason; expected {EXCLUDE_FORMAT}"
    bad = sorted({c for c in reason if unicodedata.category(c) in ("Cc", "Zl", "Zp")})
    if bad:
        return ("reason contains control or line-break characters ("
                + ", ".join(f"U+{ord(c):04X}" for c in bad) + ")")
    if len(reason) < REASON_MIN:
        return f"reason is too short ({len(reason)} characters; minimum {REASON_MIN})"
    if len(reason) > REASON_MAX:
        return f"reason is too long ({len(reason)} characters; maximum {REASON_MAX})"
    if "," in reason:
        return "reason must not contain commas"
    if INTERNAL_MENTION.search(reason):
        return "reason must not refer to internal/ (internal documents are not published)"
    return None


def parse_excludes(path: Path, problems: Problems) -> list[tuple[str, str]]:
    """Entries '(patch path, reason)'. Lines are split on LF only, so a Unicode
    line separator inside a reason is reported instead of splitting the line."""
    entries: list[tuple[str, str]] = []
    text = read_text(path, problems) or ""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    for n, line in enumerate(lines, 1):
        where = f"{display(path)}:{n}"
        stripped = line.strip(" \t")
        if not stripped or stripped.startswith("#"):
            continue
        m = EXCLUDE_LINE.match(line)
        if not m:
            if EXCLUDE_PATH_ONLY.match(line):
                problems.add(where, f"missing reason; expected {EXCLUDE_FORMAT}")
            else:
                problems.add(where, f"expected {EXCLUDE_FORMAT}")
            continue
        patch, reason = m.group(1), m.group(2).strip(" \t")
        legacy = LEGACY_REASON_START.match(reason)
        if legacy:
            problems.add(where, f"old format: decision identifiers such as {legacy.group(0)} are no longer "
                                f"accepted; write the reason itself: {EXCLUDE_FORMAT}")
            continue
        msg = reason_problem(reason)
        if msg:
            problems.add(where, f"{patch}: {msg}")
            continue
        if patch in [e[0] for e in entries]:
            problems.add(where, f"{patch} excluded twice")
            continue
        entries.append((patch, reason))
    return entries


def exclusion_provenance_lines(entries: list[tuple[str, str]], list_sha256: str) -> list[str]:
    """REMILIA-PROVENANCE.txt lines for the exclusion list: a summary line, then
    one line per excluded patch. Patch paths never contain ':', and reasons
    contain no line breaks, so each line has one reading."""
    if not entries:
        return [f"LibreWolf patches excluded: none (list sha256 {list_sha256})"]
    return ([f"LibreWolf patches excluded: {len(entries)} (list sha256 {list_sha256})"]
            + [f"LibreWolf patch excluded: {patch}: {reason}" for patch, reason in entries])


def check_excludes(entries: list[tuple[str, str]], patches_txt: str, where: str, problems: Problems) -> None:
    lines = patches_txt.splitlines()
    for patch, _ in entries:
        n = lines.count(patch)
        if n != 1:
            problems.add(where, f"{patch} appears {n} times in LibreWolf's patches.txt (expected exactly once)")


def exclude(patches_txt: Path, exclude_file: Path) -> list[tuple[str, str]]:
    problems = Problems()
    entries = parse_excludes(exclude_file, problems)
    text = patches_txt.read_text(encoding="utf-8")
    check_excludes(entries, text, display(exclude_file), problems)
    problems.raise_if_any("LibreWolf patch exclusions")
    drop = {e[0] for e in entries}
    kept = [ln for ln in text.splitlines(keepends=True) if ln.rstrip("\n") not in drop]
    if entries:
        patches_txt.write_text("".join(kept), encoding="utf-8")
    return entries


# --------------------------------------------------------------------------
# Commands

def default_snapshot() -> Path | None:
    p = REPO_ROOT / "upstream" / "librewolf-base"
    return p if (p / "librewolf.cfg").is_file() else None


def cmd_check(a: argparse.Namespace) -> int:
    problems = Problems()
    layer_root = Path(a.layer_root)
    snapshot = Path(a.base) if a.base else default_snapshot()
    base = None
    if snapshot is not None:
        for f in SNAPSHOT_FILES:
            if not (snapshot / f).is_file():
                problems.add(display(snapshot / f), "missing from the snapshot")
        problems.raise_if_any("LibreWolf base snapshot")
        base = Base.from_snapshot(snapshot)
    cats = load(layer_root, "all", problems)
    plan = check_together(cats, base, problems)
    ex_file = Path(a.exclude_file) if a.exclude_file else REPO_ROOT / "upstream" / "librewolf-exclude.txt"
    n_ex = 0
    if ex_file.is_file():
        entries = parse_excludes(ex_file, problems)
        n_ex = len(entries)
        if snapshot is not None:
            check_excludes(entries, (snapshot / "patches.txt").read_text(encoding="utf-8"),
                           display(ex_file), problems)
    problems.raise_if_any("V0 check")
    print(f"V0 check passed: layer root {display(layer_root)}, categories: "
          f"{', '.join(c.name for c in cats) or 'none present'}; "
          f"base: {base.origin if base else 'none (deviations not checked against LibreWolf)'}; "
          f"overrides: {len(plan.overrides)}; LibreWolf patch exclusions: {n_ex}")
    for n in plan.notes:
        print(f"  note: {n}")
    if base is not None:
        for name, calls in sorted(base_prefs(base.cfg).items()):
            if len(calls) > 1:
                print(f"  LibreWolf itself sets {name} more than once: "
                      + ", ".join(f"{fn}() at line {ln}" for fn, ln in calls)
                      + " (an override of this pref is refused or must keep the same function)")
    return 0


def cmd_apply(a: argparse.Namespace) -> int:
    result = apply(Path(a.tree), Path(a.layer_root), a.layers,
                   Path(a.base) if a.base else None, Path(a.report) if a.report else None)
    text = "\n".join(provenance_lines(result)) + "\n"
    if a.provenance:
        Path(a.provenance).write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0


def cmd_assemble(a: argparse.Namespace) -> int:
    problems = Problems()
    cats = load(Path(a.layer_root), a.layers, problems)
    base = Base.from_snapshot(Path(a.base))
    plan = check_together(cats, base, problems)
    problems.raise_if_any("assembly")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    assembled = assemble(plan, base)
    for snap_name, tree_path in BASE_FILES.items():
        content = assembled[tree_path]
        src = content.encode("utf-8") if content is not None else (Path(a.base) / snap_name).read_bytes()
        (out / snap_name).write_bytes(src)
    for n in plan.notes:
        print(f"note: {n}")
    return 0


def cmd_exclude(a: argparse.Namespace) -> int:
    entries = exclude(Path(a.patches_txt), Path(a.exclude_file))
    lines = exclusion_provenance_lines(entries, sha256_file(Path(a.exclude_file)))
    sys.stdout.flush()
    sys.stdout.buffer.write(("\n".join(lines) + "\n").encode("utf-8"))
    sys.stdout.buffer.flush()
    return 0


def cmd_snapshot(a: argparse.Namespace) -> int:
    tree, out = Path(a.tree), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sources = {name: tree / path for name, path in BASE_FILES.items()}
    sources["patches.txt"] = Path(a.patches_txt)
    lines = [f"Verbatim copies of LibreWolf base files. Do not edit. Source: {a.source}",
             "These files belong to LibreWolf (codeberg.org/librewolf/source) and keep its license",
             "(MPL-2.0); mozconfig also contains REMILIA's Windows cross-compile block.",
             "Refresh: scripts/remilia_layers.py snapshot (see remilia/README.md).", ""]
    for name in SNAPSHOT_FILES:
        shutil.copyfile(sources[name], out / name)
        lines.append(f"{sha256_file(out / name)}  {name}")
    (out / "SOURCE.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


def cmd_verify_base(a: argparse.Namespace) -> int:
    problems = Problems()
    verify_base(Path(a.tree), Path(a.base), problems)
    if a.patches_txt:
        if Path(a.patches_txt).read_bytes() != (Path(a.base) / "patches.txt").read_bytes():
            problems.add("assets/patches.txt", "differs from the snapshot; review and refresh it")
    problems.raise_if_any("LibreWolf base snapshot")
    return 0


def cmd_hash(a: argparse.Namespace) -> int:
    problems = Problems()
    names = select(a.layers, Path(a.layer_root), problems)
    problems.raise_if_any("layer selection")
    for n in names:
        print(f"{n} {category_hash(Path(a.layer_root) / n)}")
    return 0


def cmd_expected(a: argparse.Namespace) -> int:
    """Paths that applying the selection may change (for V1 tree comparisons)."""
    problems = Problems()
    cats = load(Path(a.layer_root), a.layers, problems)
    problems.raise_if_any("category checks")
    paths: set[str] = set()
    for c in cats:
        if not a.no_patches:
            for p in c.patches:
                paths.update(p.targets)
        paths.update(c.files)
        if c.prefs_text is not None:
            paths.add(CFG_PATH)
        if c.policies:
            paths.add(POLICIES_PATH)
        if c.moz_text is not None:
            paths.add(MOZCONFIG_PATH)
    for p in sorted(paths):
        print(p)
    return 0


def cmd_patch_targets(a: argparse.Namespace) -> int:
    targets, errors = patch_targets(Path(a.patch).read_text(encoding="utf-8", errors="replace"))
    for e in errors:
        print(f"error: {e}", file=sys.stderr)
    for t in sorted(targets):
        print(t)
    return 1 if errors else 0


def cmd_patches(a: argparse.Namespace) -> int:
    """List the series of the selected categories in application order: '<category> <abs path>'."""
    problems = Problems()
    cats = load(Path(a.layer_root), a.layers, problems)
    problems.raise_if_any("category checks")
    for c in cats:
        for p in c.patches:
            print(f"{c.name} {p.path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    default_root = str(REPO_ROOT / "remilia")

    s = sub.add_parser("check", help="V0 static checks")
    s.add_argument("--layer-root", default=default_root)
    s.add_argument("--base", help="snapshot directory (default upstream/librewolf-base)")
    s.add_argument("--exclude-file")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("apply", help="apply categories to a prepared tree")
    s.add_argument("--tree", required=True)
    s.add_argument("--layer-root", default=default_root)
    s.add_argument("--layers", default="all")
    s.add_argument("--base", help="snapshot directory the tree must match")
    s.add_argument("--report")
    s.add_argument("--provenance")
    s.set_defaults(func=cmd_apply)

    s = sub.add_parser("assemble", help="assemble config files from a snapshot into a directory")
    s.add_argument("--base", required=True)
    s.add_argument("--layer-root", default=default_root)
    s.add_argument("--layers", default="all")
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_assemble)

    s = sub.add_parser("exclude", help="remove excluded LibreWolf patches from patches.txt")
    s.add_argument("--patches-txt", required=True)
    s.add_argument("--exclude-file", required=True)
    s.set_defaults(func=cmd_exclude)

    s = sub.add_parser("snapshot", help="copy LibreWolf base files from a prepared tree")
    s.add_argument("--tree", required=True)
    s.add_argument("--patches-txt", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--source", required=True, help="text recorded in SOURCE.txt")
    s.set_defaults(func=cmd_snapshot)

    s = sub.add_parser("verify-base", help="compare a prepared tree with the snapshot")
    s.add_argument("--tree", required=True)
    s.add_argument("--base", required=True)
    s.add_argument("--patches-txt")
    s.set_defaults(func=cmd_verify_base)

    for name, fn in (("hash", cmd_hash), ("expected", cmd_expected), ("patches", cmd_patches)):
        s = sub.add_parser(name)
        s.add_argument("--layer-root", default=default_root)
        s.add_argument("--layers", default="all")
        if name == "expected":
            s.add_argument("--no-patches", action="store_true", help="only files/ and config fragments")
        s.set_defaults(func=fn)

    s = sub.add_parser("patch-targets")
    s.add_argument("patch")
    s.set_defaults(func=cmd_patch_targets)

    a = ap.parse_args(argv)
    try:
        return a.func(a)
    except Failure as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
