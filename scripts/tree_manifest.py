#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Content manifests of source trees, for the V1 tree checks (verify-tree.sh).

  build  TREE OUT [--exclude-top GLOB ...]
         One line per entry, sorted: kind, mode, size, sha256 (files) or link
         target (symlinks), path. Timestamps are ignored: two trees are equal
         when their entries, types, permissions and bytes are equal.
  diff   A B [--json OUT] [--expect FILE]
         Compare two manifests. Exit 0 when identical (or, with --expect, when
         the changed paths are exactly the paths listed in FILE), 1 otherwise.
  classify DIFF.json TREE PREPARED
         List and classify every difference between a kept tree (A) and a
         fresh tree (B); exit 0 only if each is an entry of A alone created
         after A was prepared (build by-products).
  stat   DIR OUT
         Path, kind, size and mtime (ns) of every entry, no hashing: proves an
         object directory was not touched without reading 7 GB.

Python 3.9+, standard library only.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import stat
import sys


def esc(path: str) -> str:
    return path.replace("\\", "\\\\").replace("\t", "\\t").replace("\n", "\\n")


def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk(root: str, excludes: list[str]):
    """Yield (relpath, lstat) for every entry below root, without following symlinks."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        rel_dir = os.path.relpath(dirpath, root)
        top = rel_dir == "."
        for name in sorted(dirnames + filenames):
            if top and any(fnmatch.fnmatch(name, g) for g in excludes):
                if name in dirnames:
                    dirnames.remove(name)
                continue
            rel = name if top else os.path.join(rel_dir, name)
            yield rel.replace(os.sep, "/"), os.lstat(os.path.join(dirpath, name))
        dirnames[:] = sorted(d for d in dirnames if not os.path.islink(os.path.join(dirpath, d)))


def cmd_build(a) -> int:
    lines = []
    for rel, st in walk(a.tree, a.exclude_top):
        full = os.path.join(a.tree, rel)
        mode = f"{stat.S_IMODE(st.st_mode):o}"
        if stat.S_ISLNK(st.st_mode):
            lines.append(f"l\t{mode}\t-\t{esc(os.readlink(full))}\t{esc(rel)}")
        elif stat.S_ISDIR(st.st_mode):
            lines.append(f"d\t{mode}\t-\t-\t{esc(rel)}")
        elif stat.S_ISREG(st.st_mode):
            lines.append(f"f\t{mode}\t{st.st_size}\t{file_sha256(full)}\t{esc(rel)}")
        else:
            lines.append(f"o\t{mode}\t-\t-\t{esc(rel)}")
    lines.sort(key=lambda l: l.rsplit("\t", 1)[1])
    with open(a.out, "w", encoding="utf-8", errors="surrogateescape", newline="\n") as f:
        f.write("".join(l + "\n" for l in lines))
    print(f"{a.out}: {len(lines)} entries")
    return 0


def load(path: str) -> dict[str, str]:
    entries = {}
    with open(path, encoding="utf-8", errors="surrogateescape") as f:
        for line in f:
            body, rel = line.rstrip("\n").rsplit("\t", 1)
            entries[rel] = body
    return entries


def describe(a: str | None, b: str | None) -> str:
    if a is None:
        return "added"
    if b is None:
        return "removed"
    ka, ma, sa, ha = a.split("\t")
    kb, mb, sb, hb = b.split("\t")
    what = []
    if ka != kb:
        what.append(f"type {ka}->{kb}")
    if ma != mb:
        what.append(f"mode {ma}->{mb}")
    if (sa, ha) != (sb, hb):
        what.append("content")
    return ", ".join(what)


def cmd_diff(a) -> int:
    x, y = load(a.a), load(a.b)
    changed = {p: describe(x.get(p), y.get(p)) for p in sorted(set(x) | set(y)) if x.get(p) != y.get(p)}
    result = {"a": a.a, "b": a.b, "entries_a": len(x), "entries_b": len(y), "differences": changed}
    ok = not changed
    if a.expect:
        with open(a.expect, encoding="utf-8") as f:
            expected = {l.strip() for l in f if l.strip()}
        # A changed file may also add its parent directories (new files only).
        unexpected = {p: d for p, d in changed.items()
                      if p not in expected and not (d == "added" and y[p].startswith("d\t")
                                                    and any(e.startswith(p + "/") for e in expected))}
        missing = sorted(expected - set(changed))
        result.update(expected=sorted(expected), unexpected=unexpected, missing=missing)
        ok = not unexpected and not missing
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
            f.write("\n")
    print(f"{len(changed)} difference(s) between {a.a} ({len(x)} entries) and {a.b} ({len(y)} entries)")
    for p, d in list(changed.items())[:200]:
        print(f"  {d}: {p}")
    if len(changed) > 200:
        print(f"  ... {len(changed) - 200} more (see JSON)")
    if a.expect:
        print(f"expected changes: {len(result['expected'])}; unexpected: {len(result['unexpected'])}; "
              f"expected but unchanged: {len(result['missing'])}")
        for p in result["missing"]:
            print(f"  expected but unchanged: {p}")
    return 0 if ok else 1


def cmd_classify(a) -> int:
    """Classify a diff JSON (A = kept tree, B = fresh tree). Every difference is
    listed. Exit 0 only if each one exists in A alone and is newer than A's
    preparation time (a by-product of using A after it was prepared)."""
    import datetime
    with open(a.diff_json, encoding="utf-8") as f:
        diffs = json.load(f)["differences"]
    prepared = datetime.datetime.strptime(a.prepared, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=datetime.timezone.utc).timestamp()
    groups: dict[str, list[str]] = {"build by-product: __pycache__ / .pyc": [],
                                    "other entry only in the kept tree, created after preparation": [],
                                    "NOT EXPLAINED": []}
    for p, what in diffs.items():
        full = os.path.join(a.tree, p)
        newer = what == "removed" and os.path.lexists(full) and os.lstat(full).st_mtime >= prepared
        if not newer:
            groups["NOT EXPLAINED"].append(f"{what}: {p}")
        elif "__pycache__" in p.split("/") or p.endswith(".pyc"):
            groups["build by-product: __pycache__ / .pyc"].append(p)
        else:
            mtime = datetime.datetime.fromtimestamp(os.lstat(full).st_mtime, datetime.timezone.utc)
            groups["other entry only in the kept tree, created after preparation"].append(
                f"{p} (mtime {mtime:%Y-%m-%dT%H:%M:%SZ})")
    bad = len(groups["NOT EXPLAINED"])
    print(f"{len(diffs)} difference(s): " + "; ".join(f"{len(v)} {k}" for k, v in groups.items())
          + f" (kept tree prepared {a.prepared})")
    for k, v in groups.items():
        print(f"\n## {k}: {len(v)}")
        for line in v:
            print(f"  {line}")
    return 1 if bad else 0


def cmd_stat(a) -> int:
    lines = []
    total = 0
    for rel, st in walk(a.dir, []):
        kind = "l" if stat.S_ISLNK(st.st_mode) else "d" if stat.S_ISDIR(st.st_mode) else "f"
        size = st.st_size if kind == "f" else 0
        total += size
        lines.append(f"{kind}\t{size}\t{st.st_mtime_ns}\t{esc(rel)}")
    lines.sort(key=lambda l: l.rsplit("\t", 1)[1])
    with open(a.out, "w", encoding="utf-8", errors="surrogateescape", newline="\n") as f:
        f.write(f"# entries {len(lines)} bytes {total}\n")
        f.write("".join(l + "\n" for l in lines))
    print(f"{a.out}: {len(lines)} entries, {total} bytes")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("build")
    s.add_argument("tree")
    s.add_argument("out")
    s.add_argument("--exclude-top", action="append", default=[])
    s.set_defaults(func=cmd_build)
    s = sub.add_parser("diff")
    s.add_argument("a")
    s.add_argument("b")
    s.add_argument("--json")
    s.add_argument("--expect")
    s.set_defaults(func=cmd_diff)
    s = sub.add_parser("classify")
    s.add_argument("diff_json")
    s.add_argument("tree")
    s.add_argument("prepared", help="preparation time of the tree, YYYY-MM-DDTHH:MM:SSZ")
    s.set_defaults(func=cmd_classify)
    s = sub.add_parser("stat")
    s.add_argument("dir")
    s.add_argument("out")
    s.set_defaults(func=cmd_stat)
    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
