# SPDX-License-Identifier: MPL-2.0
"""Unit tests for scripts/remilia_layers.py (V0: host, no Docker, no compilation).

Run from the repository root:
    python -m unittest discover -s tests/layers

Most tests build small synthetic category sets in a temporary directory.
Tests marked "real base" check against the LibreWolf base snapshot in
upstream/librewolf-base/. Tests that apply patches need GNU patch on PATH
(Git Bash and the build container have it) and are skipped otherwise.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import remilia_layers as rl  # noqa: E402

SNAPSHOT = ROOT / "upstream" / "librewolf-base"
HAVE_PATCH = shutil.which("patch") is not None

BASE_CFG = textwrap.dedent("""\

    /** comment with pref("commented.out", 1); */
    defaultPref("base.default", 1);
    lockPref("base.locked", true);
    pref("base.user", "x"); // trailing comment
    clearPref("base.cleared");
    defaultPref("base.mixed", 1);
    lockPref("base.mixed", 2);
    """)
BASE_POLICIES = json.dumps({"policies": {
    "ExtensionSettings": {"*": {"installation_mode": "allowed"}, "ubo@x": {"installation_mode": "normal_installed"}},
    "DisableTelemetry": True,
}}, indent=4) + "\n"
BASE_MOZCONFIG = "ac_add_options --with-app-name=librewolf\nexport MOZ_REQUIRE_SIGNING=\nmk_add_options MOZ_X=0\n"


def write(path: Path, text: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_bytes(text.encode("utf-8"))


def make_patch(category: str, target: str, old: list[str], new: list[str], start: int = 1,
               summary: str = "test patch") -> str:
    body = "".join(f"-{l}\n" for l in old) + "".join(f"+{l}\n" for l in new)
    return (f"Category: {category}\nSummary: {summary}\n\n"
            f"--- a/{target}\n+++ b/{target}\n"
            f"@@ -{start},{len(old)} +{start},{len(new)} @@\n{body}")


class Workspace(unittest.TestCase):
    """Creates a temp dir with layers/, base/ (snapshot) and tree/."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="remilia-layers-"))
        self.layers = self.tmp / "layers"
        self.base = self.tmp / "base"
        self.tree = self.tmp / "tree"
        self.layers.mkdir()
        write(self.base / "librewolf.cfg", BASE_CFG)
        write(self.base / "policies.json", BASE_POLICIES)
        write(self.base / "mozconfig", BASE_MOZCONFIG)
        write(self.base / "patches.txt", "patches/a.patch\npatches/b.patch\n")
        for name, path in rl.BASE_FILES.items():
            write(self.tree / path, (self.base / name).read_bytes())
        write(self.tree / "src/one.txt", "".join(f"line {i}\n" for i in range(1, 21)))
        write(self.tree / "src/two.txt", "alpha\nbeta\ngamma\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cat(self, name: str, **files: str | bytes) -> Path:
        root = self.layers / name
        root.mkdir(parents=True, exist_ok=True)
        for rel, content in files.items():
            write(root / rel.replace("__", "/"), content)
        return root

    def check(self, spec: str = "all", base: bool = True) -> tuple[rl.Plan, rl.Problems]:
        problems = rl.Problems()
        cats = rl.load(self.layers, spec, problems)
        plan = rl.check_together(cats, rl.Base.from_snapshot(self.base) if base else None, problems)
        return plan, problems

    def assertProblem(self, problems: rl.Problems, fragment: str) -> None:
        joined = "\n".join(problems.items)
        self.assertIn(fragment, joined, f"expected a problem containing {fragment!r}, got:\n{joined}")

    def assertClean(self, problems: rl.Problems) -> None:
        self.assertEqual(problems.items, [], "\n".join(problems.items))


class SelectionTests(Workspace):
    def test_fixed_order_regardless_of_spec(self):
        for c in ("branding", "security", "privacy"):
            self.cat(c, **{"prefs.cfg": f'defaultPref("remilia.{c}", true);\n'})
        p = rl.Problems()
        self.assertEqual(rl.select("branding,security", self.layers, p), ["security", "branding"])
        self.assertEqual(rl.select("all", self.layers, p), ["security", "privacy", "branding"])
        self.assertEqual(rl.select("none", self.layers, p), [])
        self.assertClean(p)

    def test_unknown_and_missing_categories(self):
        self.cat("security", **{"prefs.cfg": 'defaultPref("a.b", 1);\n'})
        p = rl.Problems()
        rl.select("secrity", self.layers, p)
        self.assertProblem(p, "unknown category 'secrity'")
        p = rl.Problems()
        rl.select("privacy", self.layers, p)
        self.assertProblem(p, "category 'privacy' has no directory")

    def test_unknown_entries(self):
        self.cat("security", **{"prefs.cfg": 'defaultPref("a.b", 1);\n', "notes.txt": "x\n"})
        (self.layers / "misc").mkdir()
        _, p = self.check()
        self.assertProblem(p, "notes.txt: not allowed in a category")
        self.assertProblem(p, "misc: unknown entry in the layer root")


class PrefTests(Workspace):
    def test_valid_new_prefs(self):
        self.cat("security", **{"prefs.cfg": '// c\n\ndefaultPref("remilia.a", true);\nlockPref("remilia.b", "s");\n'})
        self.cat("privacy", **{"prefs.cfg": 'pref("remilia.c", -3);\n'})
        _, p = self.check()
        self.assertClean(p)

    def test_duplicate_across_categories_is_an_error(self):
        self.cat("security", **{"prefs.cfg": 'defaultPref("remilia.dup", 1);\n'})
        self.cat("privacy", **{"prefs.cfg": 'defaultPref("remilia.dup", 2);\n'})
        _, p = self.check()
        self.assertProblem(p, "pref remilia.dup is also set by category security")

    def test_duplicate_within_category(self):
        self.cat("security", **{"prefs.cfg": 'defaultPref("remilia.dup", 1);\ndefaultPref("remilia.dup", 1);\n'})
        _, p = self.check()
        self.assertProblem(p, "set twice in this category")

    def test_syntax_is_strict(self):
        bad = ['user_pref("a", 1);', 'defaultPref("a", 1)', '  defaultPref("a", 1);',
               'defaultPref("a", x);', 'defaultPref("a", 1); // other comment', '/* block */']
        self.cat("security", **{"prefs.cfg": "\n".join(bad) + "\n"})
        _, p = self.check()
        self.assertEqual(len([i for i in p.items if "not a valid line" in i]), len(bad))

    def test_override_requires_deviation(self):
        self.cat("privacy", **{"prefs.cfg": 'defaultPref("base.default", 2);\n'})
        _, p = self.check()
        self.assertProblem(p, "overrides LibreWolf pref base.default")

    def test_override_with_registered_deviation(self):
        self.cat("privacy", **{
            "prefs.cfg": 'defaultPref("base.default", 2); // deviation: PRIV-001\n',
            "deviations.tsv": "PRIV-001\tpref\tbase.default\tPRIVACY.md\n"})
        plan, p = self.check()
        self.assertClean(p)
        self.assertEqual([o["id"] for o in plan.overrides], ["PRIV-001"])

    def test_override_must_keep_function(self):
        self.cat("privacy", **{
            "prefs.cfg": 'lockPref("base.default", 2); // deviation: PRIV-001\n',
            "deviations.tsv": "PRIV-001\tpref\tbase.default\tPRIVACY.md\n"})
        _, p = self.check()
        self.assertProblem(p, "keep the same function instead of lockPref()")

    def test_lockpref_redefinition_is_marked_runtime_unverified(self):
        self.cat("security", **{
            "prefs.cfg": 'lockPref("base.locked", false); // deviation: SEC-001\n',
            "deviations.tsv": "SEC-001\tpref\tbase.locked\tSECURITY.md\n"})
        plan, p = self.check()
        self.assertClean(p)
        self.assertTrue(any(n.startswith("runtime-unverified") and "base.locked" in n for n in plan.notes))

    def test_cleared_or_mixed_base_prefs_are_refused(self):
        self.cat("security", **{
            "prefs.cfg": 'defaultPref("base.cleared", 1); // deviation: SEC-001\n'
                         'lockPref("base.mixed", 3); // deviation: SEC-002\n',
            "deviations.tsv": "SEC-001\tpref\tbase.cleared\tSECURITY.md\nSEC-002\tpref\tbase.mixed\tSECURITY.md\n"})
        _, p = self.check()
        self.assertProblem(p, "LibreWolf clears or unlocks base.cleared")
        self.assertProblem(p, "LibreWolf sets base.mixed with different functions")

    def test_commented_out_base_pref_is_not_a_base_pref(self):
        self.cat("security", **{"prefs.cfg": 'pref("commented.out", 2);\n'})
        _, p = self.check()
        self.assertClean(p)

    def test_deviation_without_override(self):
        self.cat("privacy", **{
            "prefs.cfg": 'defaultPref("remilia.new", 2); // deviation: PRIV-001\n',
            "deviations.tsv": "PRIV-001\tpref\tremilia.new\tPRIVACY.md\n"})
        _, p = self.check()
        self.assertProblem(p, "declares deviation PRIV-001 but pref remilia.new is not set by LibreWolf")

    def test_unregistered_wrong_prefix_and_unused_ids(self):
        self.cat("privacy", **{
            "prefs.cfg": 'defaultPref("base.default", 2); // deviation: PRIV-009\n',
            "deviations.tsv": "SEC-001\tpref\tbase.default\tPRIVACY.md\n"
                              "PRIV-002\tpref\tbase.user\tPRIVACY.md\n"})
        _, p = self.check()
        self.assertProblem(p, "id 'SEC-001' must be PRIV-NNN")
        self.assertProblem(p, "deviation PRIV-009 is not registered")
        self.assertProblem(p, "deviation PRIV-002 (pref base.user) is not used")

    def test_registry_reference_must_exist(self):
        self.cat("privacy", **{
            "prefs.cfg": 'defaultPref("base.default", 2); // deviation: PRIV-001\n',
            "deviations.tsv": "PRIV-001\tpref\tbase.default\tNOPE.md#x\n"})
        _, p = self.check()
        # NOPE.md is refused before the file system is consulted: it is not an allowed document.
        # A missing allowed document is covered by ReferenceTests.test_allowed_document_missing.
        self.assertProblem(p, "deviations.tsv:1: reference 'NOPE.md' is not an allowed document")

    def test_carriage_return_and_missing_newline(self):
        self.cat("security", **{"prefs.cfg": b'defaultPref("remilia.a", 1);\r\n'})
        self.cat("privacy", **{"prefs.cfg": b'defaultPref("remilia.b", 1);'})
        _, p = self.check()
        self.assertProblem(p, "carriage return")
        self.assertProblem(p, "does not end with a newline")


class PolicyAndMozconfigTests(Workspace):
    def test_second_level_merge_and_collisions(self):
        self.cat("security", **{"policies.json": json.dumps(
            {"policies": {"ExtensionSettings": {"a@x": {"installation_mode": "blocked"}}}}) + "\n"})
        self.cat("privacy", **{"policies.json": json.dumps(
            {"policies": {"ExtensionSettings": {"b@x": {"installation_mode": "blocked"}}}}) + "\n"})
        plan, p = self.check()
        self.assertClean(p)
        out = rl.assemble(plan, rl.Base.from_snapshot(self.base))[rl.POLICIES_PATH]
        es = json.loads(out)["policies"]["ExtensionSettings"]
        self.assertEqual(list(es), ["*", "ubo@x", "a@x", "b@x"])

    def test_same_unit_in_two_categories(self):
        for c in ("security", "privacy"):
            self.cat(c, **{"policies.json": json.dumps(
                {"policies": {"ExtensionSettings": {"same@x": {"installation_mode": "blocked"}}}}) + "\n"})
        _, p = self.check()
        self.assertProblem(p, "policy unit ExtensionSettings/same@x is also set by category security")

    def test_whole_policy_conflict(self):
        for c in ("security", "privacy"):
            self.cat(c, **{"policies.json": json.dumps({"policies": {"NewPolicy": True}}) + "\n"})
        _, p = self.check()
        self.assertProblem(p, "set by several categories: security, privacy")

    def test_policy_override_needs_registry(self):
        self.cat("privacy", **{"policies.json": json.dumps(
            {"policies": {"ExtensionSettings": {"ubo@x": {"installation_mode": "force_installed"}},
                          "DisableTelemetry": False}}) + "\n"})
        _, p = self.check()
        self.assertProblem(p, "overrides LibreWolf policy ExtensionSettings/ubo@x")
        self.assertProblem(p, "overrides LibreWolf policy DisableTelemetry")
        write(self.layers / "privacy" / "deviations.tsv",
              "PRIV-001\tpolicy\tExtensionSettings/ubo@x\tPRIVACY.md\nPRIV-002\tpolicy\tDisableTelemetry\tPRIVACY.md\n")
        plan, p = self.check()
        self.assertClean(p)
        doc = json.loads(rl.assemble(plan, rl.Base.from_snapshot(self.base))[rl.POLICIES_PATH])
        self.assertEqual(list(doc["policies"]), ["ExtensionSettings", "DisableTelemetry"])  # order kept
        self.assertEqual(doc["policies"]["ExtensionSettings"]["ubo@x"]["installation_mode"], "force_installed")

    def test_policies_shape(self):
        self.cat("security", **{"policies.json": '{"policies": {}, "extra": 1}\n'})
        self.cat("privacy", **{"policies.json": "{not json\n"})
        _, p = self.check()
        self.assertProblem(p, 'only key is "policies"')
        self.assertProblem(p, "invalid JSON")

    def test_mozconfig_keys_conflicts_and_deviations(self):
        self.assertEqual(rl.moz_key("ac_add_options --disable-updater"), "enable:updater")
        self.assertEqual(rl.moz_key("ac_add_options --without-foo"), "with:foo")
        self.assertEqual(rl.moz_key("ac_add_options --target=x"), "opt:target")
        self.assertEqual(rl.moz_key("export A=1"), "env:A")
        self.cat("security", **{"mozconfig": "ac_add_options --enable-foo\nexport MOZ_REQUIRE_SIGNING=1\n"})
        self.cat("privacy", **{"mozconfig": "ac_add_options --disable-foo\nbogus line\n"})
        _, p = self.check()
        self.assertProblem(p, "enable:foo is also set by category security")
        self.assertProblem(p, "overrides LibreWolf mozconfig env:MOZ_REQUIRE_SIGNING")
        self.assertProblem(p, "expected 'ac_add_options")

    def test_mozconfig_deviation_ok(self):
        self.cat("branding", **{"mozconfig": "ac_add_options --with-app-name=remilia # deviation: BRAND-001\n",
                                "deviations.tsv": "BRAND-001\tmozconfig\twith:app-name\tSECURITY.md\n"})
        plan, p = self.check()
        self.assertClean(p)
        out = rl.assemble(plan, rl.Base.from_snapshot(self.base))[rl.MOZCONFIG_PATH]
        self.assertTrue(out.startswith(BASE_MOZCONFIG))
        self.assertIn("# ===== REMILIA category: branding =====", out)


class AssemblyTests(Workspace):
    def build_valid(self):
        self.cat("security", **{"prefs.cfg": 'lockPref("remilia.s", 1);\n',
                                "mozconfig": "export REMILIA_S=1\n"})
        self.cat("privacy", **{"prefs.cfg": 'defaultPref("remilia.p", "x");\n',
                               "policies.json": '{"policies": {"NewOne": true}}\n'})

    def test_deterministic_and_ordered(self):
        self.build_valid()
        plan1, p1 = self.check()
        plan2, p2 = self.check("privacy,security")
        self.assertClean(p1)
        self.assertClean(p2)
        base = rl.Base.from_snapshot(self.base)
        a, b = rl.assemble(plan1, base), rl.assemble(plan2, base)
        self.assertEqual(a, b)
        cfg = a[rl.CFG_PATH]
        self.assertTrue(cfg.startswith(BASE_CFG))
        self.assertLess(cfg.index("REMILIA category: security"), cfg.index("REMILIA category: privacy"))
        self.assertIn("end of REMILIA category: privacy", cfg)

    def test_nothing_rewritten_without_fragments(self):
        self.cat("security", **{"files__new/file.txt": "x\n"})
        plan, p = self.check()
        self.assertClean(p)
        self.assertEqual(rl.assemble(plan, rl.Base.from_snapshot(self.base)),
                         {rl.CFG_PATH: None, rl.POLICIES_PATH: None, rl.MOZCONFIG_PATH: None})


class PatchFileTests(Workspace):
    def test_series_and_headers(self):
        self.cat("security", **{
            "series": "a.patch\nmissing.patch\n",
            "patches__a.patch": make_patch("privacy", "src/two.txt", ["beta"], ["BETA"], 2),
            "patches__extra.patch": make_patch("security", "src/two.txt", ["beta"], ["B"], 2),
            "patches__nosum.patch": "Category: security\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n"})
        _, p = self.check()
        self.assertProblem(p, "extra.patch: not listed in series")
        self.assertProblem(p, "missing.patch does not exist")
        self.assertProblem(p, "a.patch: header must contain exactly one 'Category: security'")

    def test_forbidden_targets_and_binary(self):
        self.cat("security", **{
            "series": "a.patch\nb.patch\n",
            "patches__a.patch": make_patch("security", "lw/librewolf.cfg", ["x"], ["y"]),
            "patches__b.patch": "Category: security\nSummary: s\n--- a/i.png\n+++ b/i.png\nGIT binary patch\n"})
        _, p = self.check()
        self.assertProblem(p, "must not touch lw/librewolf.cfg")
        self.assertProblem(p, "binary patches are not supported")

    def test_hunk_aware_targets(self):
        text = ("Category: x\nSummary: y\n--- a/sql/t.sql\n+++ b/sql/t.sql\n@@ -1,2 +1,1 @@\n"
                "--- a removed SQL comment\n keep\n")
        targets, errors = rl.patch_targets(text)
        self.assertEqual(targets, ["sql/t.sql"])
        self.assertEqual(errors, [])


class FilesTests(Workspace):
    def test_two_categories_same_file(self):
        self.cat("security", **{"files__new/x.txt": "a\n"})
        self.cat("branding", **{"files__new/x.txt": "b\n"})
        _, p = self.check()
        self.assertProblem(p, "new/x.txt is also written by category security")

    def test_replaces_without_file_and_forbidden(self):
        self.cat("branding", **{"files__mozconfig": "x\n", "replaces.txt": "src/one.txt\n"})
        _, p = self.check()
        self.assertProblem(p, "must not write mozconfig")
        self.assertProblem(p, "src/one.txt has no file in files/")


class PolicyBytesTests(Workspace):
    """policies.json: byte-exact when no category changes policies, semantically
    equivalent (plus the intended changes) when one does."""

    # Deliberately NOT the tool's own json.dumps(indent=4) layout: compact
    # objects, a one-line list, extra spaces, a comment key. Byte identity
    # can then only come from not rewriting the file.
    COMPACT = ('{\n  "__COMMENT__ x": "kept",\n  "policies": {\n'
               '    "ContentAnalysis": { "Enabled": false, "Points": { "Print": { "Enabled": false } } },\n'
               '    "ExtensionSettings": {\n'
               '      "*": { "installation_mode": "allowed", "allowed_types": ["extension", "theme"] },\n'
               '      "ubo@x": { "installation_mode": "normal_installed" }\n'
               '    },\n'
               '    "DisableTelemetry":   true,\n'
               '    "SupportMenu": { "Title": "Ünïcode", "URL": "https://example.invalid" }\n'
               '  }\n}\n')

    def setUp(self) -> None:
        super().setUp()
        write(self.base / "policies.json", self.COMPACT)
        write(self.tree / rl.POLICIES_PATH, self.COMPACT)

    def snapshot_bytes(self) -> dict[str, bytes]:
        return {p: (self.tree / p).read_bytes() for p in rl.BASE_FILES.values()}

    def test_none_selection_keeps_every_byte(self):
        self.cat("privacy", **{"policies.json": '{"policies": {"NewOne": true}}\n'})
        before = self.snapshot_bytes()
        res = rl.apply(self.tree, self.layers, "none", self.base, None)
        self.assertEqual(res["categories"], [])
        self.assertEqual(self.snapshot_bytes(), before)
        out = self.tmp / "assembled-none"
        self.assertEqual(rl.main(["assemble", "--base", str(self.base), "--layer-root", str(self.layers),
                                  "--layers", "none", "--out", str(out)]), 0)
        for name in rl.BASE_FILES:
            self.assertEqual((out / name).read_bytes(), (self.base / name).read_bytes(), name)

    @unittest.skipUnless(HAVE_PATCH, "GNU patch not on PATH")
    def test_categories_without_policies_keep_policies_bytes(self):
        self.cat("security", **{"prefs.cfg": 'defaultPref("remilia.s", 1);\n',
                                "mozconfig": "export REMILIA_S=1\n"})
        self.cat("branding", **{"files__new/x.txt": "x\n"})
        before = (self.tree / rl.POLICIES_PATH).read_bytes()
        rl.apply(self.tree, self.layers, "all", self.base, None)
        self.assertEqual((self.tree / rl.POLICIES_PATH).read_bytes(), before)
        self.assertNotEqual((self.tree / rl.CFG_PATH).read_bytes(), (self.base / "librewolf.cfg").read_bytes())

    def test_policy_change_is_semantically_equivalent(self):
        self.cat("security", **{"policies.json": json.dumps({"policies": {
            "ExtensionSettings": {"new@x": {"installation_mode": "blocked"}}}}) + "\n"})
        self.cat("privacy", **{
            "policies.json": json.dumps({"policies": {"DisableTelemetry": False, "NewOne": True}}) + "\n",
            "deviations.tsv": "PRIV-001\tpolicy\tDisableTelemetry\tPRIVACY.md\n"})
        plan, p = self.check()
        self.assertClean(p)
        merged_text = rl.assemble(plan, rl.Base.from_snapshot(self.base))[rl.POLICIES_PATH]
        merged = json.loads(merged_text)
        # Independent expectation: the base document plus exactly the intended changes.
        expected = json.loads(self.COMPACT)
        expected["policies"]["ExtensionSettings"]["new@x"] = {"installation_mode": "blocked"}
        expected["policies"]["DisableTelemetry"] = False
        expected["policies"]["NewOne"] = True
        self.assertEqual(merged, expected)
        self.assertEqual(list(merged), ["__COMMENT__ x", "policies"])
        self.assertEqual(list(merged["policies"]),
                         ["ContentAnalysis", "ExtensionSettings", "DisableTelemetry", "SupportMenu", "NewOne"])
        self.assertEqual(list(merged["policies"]["ExtensionSettings"]), ["*", "ubo@x", "new@x"])
        self.assertIn("Ünïcode", merged_text)  # not escaped to \u sequences
        self.assertTrue(merged_text.endswith("}\n"))
        # Deterministic: same bytes on a second assembly.
        plan2, _ = self.check("privacy,security")
        self.assertEqual(rl.assemble(plan2, rl.Base.from_snapshot(self.base))[rl.POLICIES_PATH], merged_text)


@unittest.skipUnless(HAVE_PATCH, "GNU patch not on PATH")
class ApplyTests(Workspace):
    def test_apply_patches_files_and_configs(self):
        self.cat("security", **{"series": "a.patch\n",
                                "patches__a.patch": make_patch("security", "src/one.txt", ["line 2"], ["SEC 2"], 2),
                                "prefs.cfg": 'defaultPref("remilia.s", 1);\n'})
        self.cat("privacy", **{"series": "b.patch\n",
                               "patches__b.patch": make_patch("privacy", "src/one.txt", ["line 15"], ["PRIV 15"], 15)})
        self.cat("branding", **{"files__src/two.txt": "replaced\n", "replaces.txt": "src/two.txt\n",
                                "files__new/logo.txt": "logo\n"})
        res = rl.apply(self.tree, self.layers, "all", self.base, self.tmp / "report.json")
        one = (self.tree / "src/one.txt").read_text()
        self.assertIn("SEC 2", one)
        self.assertIn("PRIV 15", one)
        self.assertEqual((self.tree / "src/two.txt").read_text(), "replaced\n")
        self.assertEqual((self.tree / "new/logo.txt").read_text(), "logo\n")
        self.assertEqual(res["overlaps"]["src/one.txt"], ["security", "privacy"])
        self.assertIn("REMILIA category: security", (self.tree / rl.CFG_PATH).read_text())
        self.assertEqual((self.tree / rl.POLICIES_PATH).read_text(), BASE_POLICIES)  # untouched
        self.assertFalse(list(self.tree.rglob("*.orig")) + list(self.tree.rglob("*.rej")))
        lines = rl.provenance_lines(res)
        self.assertTrue(any(l.startswith("Category security: sha256 ") for l in lines))

    def test_fuzz_is_refused(self):
        # Context line 1 is wrong: applying would need fuzz 1.
        bad = ("Category: security\nSummary: s\n--- a/src/one.txt\n+++ b/src/one.txt\n"
               "@@ -1,3 +1,3 @@\n WRONG CONTEXT\n-line 2\n+X\n line 3\n")
        self.cat("security", **{"series": "a.patch\n", "patches__a.patch": bad})
        with self.assertRaises(rl.Failure) as cm:
            rl.apply(self.tree, self.layers, "all", self.base, None)
        self.assertIn("does not apply with fuzz 0", str(cm.exception))

    def test_overwrite_needs_replaces(self):
        self.cat("branding", **{"files__src/two.txt": "replaced\n"})
        with self.assertRaises(rl.Failure) as cm:
            rl.apply(self.tree, self.layers, "all", self.base, None)
        self.assertIn("list it in replaces.txt", str(cm.exception))
        self.assertEqual((self.tree / "src/two.txt").read_text(), "alpha\nbeta\ngamma\n")

    def test_static_problems_stop_before_tree_changes(self):
        self.cat("security", **{"series": "a.patch\n",
                                "patches__a.patch": make_patch("security", "src/one.txt", ["line 2"], ["S"], 2),
                                "prefs.cfg": 'defaultPref("dup", 1);\n'})
        self.cat("privacy", **{"prefs.cfg": 'defaultPref("dup", 1);\n'})
        before = (self.tree / "src/one.txt").read_bytes()
        with self.assertRaises(rl.Failure):
            rl.apply(self.tree, self.layers, "all", self.base, None)
        self.assertEqual((self.tree / "src/one.txt").read_bytes(), before)

    def test_snapshot_mismatch_stops(self):
        write(self.tree / rl.CFG_PATH, BASE_CFG + 'defaultPref("upstream.changed", 1);\n')
        self.cat("security", **{"prefs.cfg": 'defaultPref("remilia.s", 1);\n'})
        with self.assertRaises(rl.Failure) as cm:
            rl.apply(self.tree, self.layers, "all", self.base, None)
        self.assertIn("differs from the snapshot", str(cm.exception))

    def test_removing_from_series_equals_reverse_apply(self):
        pa = make_patch("security", "src/one.txt", ["line 2"], ["SEC 2"], 2)
        pb = make_patch("security", "src/one.txt", ["line 10"], ["SEC 10"], 10)
        self.cat("security", **{"series": "a.patch\nb.patch\n", "patches__a.patch": pa, "patches__b.patch": pb})
        pristine = (self.tree / "src/one.txt").read_bytes()
        rl.apply(self.tree, self.layers, "all", self.base, None)
        r = rl.run_patch(self.tree, self.layers / "security/patches/a.patch", reverse=True)
        self.assertEqual(r.returncode, 0, r.stdout)
        reversed_a = (self.tree / "src/one.txt").read_bytes()
        write(self.tree / "src/one.txt", pristine)
        write(self.layers / "security/series", "b.patch\n")
        (self.layers / "security/patches/a.patch").unlink()
        rl.apply(self.tree, self.layers, "all", self.base, None)
        self.assertEqual((self.tree / "src/one.txt").read_bytes(), reversed_a)


class ExcludeTests(Workspace):
    def test_exclude(self):
        pt = self.tmp / "patches.txt"
        write(pt, "patches/a.patch\npatches/b.patch\npatches/c.patch\n")
        ex = self.tmp / "exclude.txt"
        write(ex, "# comment\npatches/b.patch reason text for the test\n")
        self.assertEqual(rl.exclude(pt, ex), [("patches/b.patch", "reason text for the test")])
        self.assertEqual(pt.read_text(), "patches/a.patch\npatches/c.patch\n")

    def test_exclude_errors(self):
        pt = self.tmp / "patches.txt"
        write(pt, "patches/a.patch\n")
        ex = self.tmp / "exclude.txt"
        for content, msg in (("patches/zzz.patch reason for the test\n", "appears 0 times"),
                             ("patches/a.patch\n", "expected '<patch path"),
                             ("patches/a.patch reason for the test\npatches/a.patch another reason here\n",
                              "excluded twice")):
            write(ex, content)
            with self.assertRaises(rl.Failure) as cm:
                rl.exclude(pt, ex)
            self.assertIn(msg, str(cm.exception))
            self.assertEqual(pt.read_text(), "patches/a.patch\n")

    def test_empty_exclude_file_changes_nothing(self):
        pt = self.tmp / "patches.txt"
        write(pt, "patches/a.patch\n")
        ex = self.tmp / "exclude.txt"
        write(ex, "# nothing excluded\n")
        self.assertEqual(rl.exclude(pt, ex), [])
        self.assertEqual(pt.read_text(), "patches/a.patch\n")


class ExcludeFormatTests(Workspace):
    """Exclusion line format '<patch path> <reason>' (E1-E16 of the plan)."""

    def parse(self, content: str | bytes) -> tuple[list[tuple[str, str]], rl.Problems]:
        ex = self.tmp / "exclude.txt"
        write(ex, content)
        problems = rl.Problems()
        return rl.parse_excludes(ex, problems), problems

    def assertRejected(self, content: str | bytes, fragment: str) -> None:
        entries, p = self.parse(content)
        self.assertEqual(entries, [], f"{content!r} must not produce an entry")
        self.assertProblem(p, fragment)

    def test_e1_missing_reason(self):
        self.assertRejected("patches/a.patch\n", "missing reason")

    def test_e2_empty_reason(self):
        for line in ("patches/a.patch   \n", "patches/a.patch\t\n", "patches/a.patch \t \n"):
            self.assertRejected(line, "missing reason")

    def test_e3_old_identifier_is_a_migration_error(self):
        for line in ("patches/a.patch ADR-0007 reason text for it\n", "patches/a.patch ADR-0007\n",
                     "patches/a.patch adr-12 something long enough\n", "patches/a.patch\tADR-0001\treason here ok\n",
                     "patches/a.patch ADR-0001: reason text for it\n"):
            self.assertRejected(line, "old format: decision identifiers such as")

    def test_e3_identifier_inside_a_reason_is_not_the_old_format(self):
        entries, p = self.parse("patches/a.patch replaces what ADR-0001 used to say\n")
        self.assertClean(p)
        self.assertEqual(entries, [("patches/a.patch", "replaces what ADR-0001 used to say")])

    def test_e4_valid(self):
        entries, p = self.parse("patches/a.patch MSIX is not shipped\n")
        self.assertClean(p)
        self.assertEqual(entries, [("patches/a.patch", "MSIX is not shipped")])

    def test_e5_tab_separator_and_outer_spaces(self):
        entries, p = self.parse("patches/a.patch\t  MSIX is not shipped  \t\n")
        self.assertClean(p)
        self.assertEqual(entries, [("patches/a.patch", "MSIX is not shipped")])

    def test_e6_special_characters_are_kept_verbatim(self):
        reason = 'Uses # : " \' ` $(echo x) $HOME \\ acentuação 日本語 (ok)'
        entries, p = self.parse(f"patches/a.patch {reason}\n")
        self.assertClean(p)
        self.assertEqual(entries, [("patches/a.patch", reason)])

    def test_e7_control_and_line_break_characters(self):
        for bad in ("\x00", "\x1b", "\t", "\x0b", "\x0c", "\x85", "\u2028", "\u2029"):
            self.assertRejected(f"patches/a.patch reason with{bad}a control char\n",
                                "reason contains control or line-break characters")

    def test_e8_carriage_return(self):
        self.assertRejected(b"patches/a.patch some reason here\r\n", "contains a carriage return")

    def test_e9_length_limits_after_trimming(self):
        for reason in ("a" * 10, "a" * 200, "  " + "a" * 10 + "  "):
            entries, p = self.parse(f"patches/a.patch {reason}\n")
            self.assertClean(p)
            self.assertEqual(entries, [("patches/a.patch", reason.strip())])
        self.assertRejected("patches/a.patch " + "a" * 9 + "\n", "reason is too short (9 characters; minimum 10)")
        self.assertRejected("patches/a.patch    " + "a" * 9 + "    \n", "reason is too short (9 characters")
        self.assertRejected("patches/a.patch " + "a" * 201 + "\n", "reason is too long (201 characters; maximum 200)")

    def test_e9_length_counts_characters_not_bytes(self):
        entries, p = self.parse("patches/a.patch " + "日" * 200 + "\n")
        self.assertClean(p)
        self.assertEqual(len(entries[0][1]), 200)

    def test_reason_with_comma(self):
        self.assertRejected("patches/a.patch not used, not needed\n", "reason must not contain commas")
        self.assertRejected("patches/a.patch not used，fullwidth is fine but this, is not\n",
                            "reason must not contain commas")

    def test_e10_reason_mentioning_internal(self):
        for reason in ("see internal/decisions/0007.md here", "see Internal/notes for this",
                       "see internal\\evidence for this", "(internal/reports) explains it"):
            self.assertRejected(f"patches/a.patch {reason}\n", "must not refer to internal/")
        entries, p = self.parse("patches/a.patch an internal detail of the patch\n")
        self.assertClean(p)
        self.assertEqual(len(entries), 1)

    def test_e11_invalid_paths(self):
        for line in ("patches\\a.patch some reason here\n", "a.patch some reason here ok\n",
                     "patches/a.diff some reason here ok\n", " patches/a.patch leading space reason\n",
                     "patches/a b.patch reason with a space path\n", "patches/a.patch:x reason text here\n"):
            self.assertRejected(line, "expected '<patch path as in patches.txt> <reason>'")

    def test_e12_duplicates(self):
        _, p = self.parse("patches/a.patch first reason here\npatches/a.patch second reason here\n")
        self.assertProblem(p, "patches/a.patch excluded twice")

    def test_e14_comments_with_leading_whitespace_and_blank_lines(self):
        entries, p = self.parse("# note\n   # indented note\n\t# tabbed note\n\n   \n\t\n")
        self.assertClean(p)
        self.assertEqual(entries, [])

    def test_e15_repository_exclusion_list(self):
        problems = rl.Problems()
        self.assertEqual(rl.parse_excludes(ROOT / "upstream" / "librewolf-exclude.txt", problems), [])
        self.assertClean(problems)

    def test_e16_fixture_lists_parse(self):
        for name, patch in (("exclude-msix.txt", "patches/msix.patch"),
                            ("exclude-unknown.txt", "patches/does-not-exist.patch")):
            problems = rl.Problems()
            entries = rl.parse_excludes(ROOT / "tests" / "layers" / name, problems)
            self.assertClean(problems)
            self.assertEqual([e[0] for e in entries], [patch])

    @unittest.skipUnless((SNAPSHOT / "patches.txt").is_file(), "no LibreWolf base snapshot")
    def test_e13_e16_fixtures_against_real_patches_txt(self):
        # The same calls prepare.sh makes in V1 (staging), on a copy of the real list.
        pt = self.tmp / "patches.txt"
        write(pt, (SNAPSHOT / "patches.txt").read_bytes())
        self.assertEqual(len(rl.exclude(pt, ROOT / "tests" / "layers" / "exclude-msix.txt")), 1)
        lines = pt.read_text().splitlines()
        self.assertEqual(len(lines), 67)
        self.assertNotIn("patches/msix.patch", lines)
        write(pt, (SNAPSHOT / "patches.txt").read_bytes())
        with self.assertRaises(rl.Failure) as cm:
            rl.exclude(pt, ROOT / "tests" / "layers" / "exclude-unknown.txt")
        self.assertIn("appears 0 times", str(cm.exception))  # what verify-tree.sh looks for
        self.assertEqual(pt.read_bytes(), (SNAPSHOT / "patches.txt").read_bytes())


class ExclusionProvenanceTests(Workspace):
    """REMILIA-PROVENANCE.txt lines for exclusions (P1-P7 of the plan)."""

    def test_p2_none_is_unchanged(self):
        self.assertEqual(rl.exclusion_provenance_lines([], "abc"),
                         ["LibreWolf patches excluded: none (list sha256 abc)"])

    def test_p2_one_line_per_exclusion(self):
        entries = [("patches/a.patch", "first reason here"), ("patches/b.patch", "reason: with colon $(x) 日本")]
        self.assertEqual(rl.exclusion_provenance_lines(entries, "abc"), [
            "LibreWolf patches excluded: 2 (list sha256 abc)",
            "LibreWolf patch excluded: patches/a.patch: first reason here",
            "LibreWolf patch excluded: patches/b.patch: reason: with colon $(x) 日本",
        ])

    def test_p2_lines_have_one_reading(self):
        entries = [("patches/a.patch", "reason: one: two")]
        line = rl.exclusion_provenance_lines(entries, "x")[1]
        body = line[len("LibreWolf patch excluded: "):]
        path, _, reason = body.partition(": ")
        self.assertEqual((path, reason), entries[0])

    def test_p2_exclude_command_prints_provenance_lines_in_utf8(self):
        pt = self.tmp / "patches.txt"
        write(pt, "patches/a.patch\npatches/b.patch\n")
        ex = self.tmp / "exclude.txt"
        write(ex, "# list\npatches/b.patch não usado no REMILIA 日本語\n")
        r = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "remilia_layers.py"), "exclude",
                            "--patches-txt", str(pt), "--exclude-file", str(ex)], capture_output=True)
        self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", "replace"))
        self.assertEqual(r.stdout.decode("utf-8").splitlines(), [
            f"LibreWolf patches excluded: 1 (list sha256 {rl.sha256_file(ex)})",
            "LibreWolf patch excluded: patches/b.patch: não usado no REMILIA 日本語",
        ])
        self.assertEqual(pt.read_text(), "patches/a.patch\n")

    def test_p2_exclude_command_without_entries(self):
        pt = self.tmp / "patches.txt"
        write(pt, "patches/a.patch\n")
        ex = self.tmp / "exclude.txt"
        write(ex, "# nothing\n")
        r = subprocess.run([sys.executable, "-B", str(ROOT / "scripts" / "remilia_layers.py"), "exclude",
                            "--patches-txt", str(pt), "--exclude-file", str(ex)], capture_output=True)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout.decode("utf-8").splitlines(),
                         [f"LibreWolf patches excluded: none (list sha256 {rl.sha256_file(ex)})"])

    def test_p5_package_layer_root_check_is_not_affected(self):
        # package.sh greps '^Layer root:'; exclusion lines must never look like that line.
        lines = rl.exclusion_provenance_lines([("patches/a.patch", "Layer root:  remilia trick")], "x")
        self.assertFalse(any(l.startswith("Layer root:") for l in lines))
        self.assertIn("grep -q '^Layer root:'", (ROOT / "scripts" / "package.sh").read_text())

    def test_p7_only_prepare_and_the_tool_know_the_exclusion_lines(self):
        markers = ("LibreWolf patches excluded:", "LibreWolf patch excluded:")
        users = sorted(p.name for p in (ROOT / "scripts").iterdir()
                       if p.suffix in (".sh", ".py")
                       and any(m in p.read_text(encoding="utf-8") for m in markers))
        self.assertEqual(users, ["prepare.sh", "remilia_layers.py"])
        prepare = (ROOT / "scripts" / "prepare.sh").read_text(encoding="utf-8")
        self.assertIn('excluded="LibreWolf patches excluded: none (REMILIA_LAYERS=none)"', prepare)
        self.assertIn('excluded="LibreWolf patches excluded: none"', prepare)
        self.assertIn("\n$excluded\n", prepare)


class ReferenceTests(Workspace):
    """deviations.tsv 'reference' validation (F1-F15 of the plan)."""

    FIXTURE_ROOT = ROOT / "tests" / "layers" / "valid"

    PRODUCTION_ROOT = rl.REPO_ROOT / "remilia"

    def ref(self, ref: str, fixture: bool = False) -> list[str]:
        return rl.check_reference(ref, self.FIXTURE_ROOT if fixture else self.PRODUCTION_ROOT)

    def assertRefOk(self, ref: str, fixture: bool = False) -> None:
        self.assertEqual(self.ref(ref, fixture), [], ref)

    def assertRefBad(self, ref: str, fragment: str, fixture: bool = False) -> None:
        msgs = self.ref(ref, fixture)
        self.assertTrue(msgs, f"{ref!r} must be refused")
        self.assertIn(fragment, "\n".join(msgs))

    def test_f1_allowed_documents(self):
        for ref in ("PRIVACY.md", "SECURITY.md"):
            self.assertRefOk(ref)
            self.assertRefOk(ref, fixture=True)

    def test_f2_existing_anchors_and_f15_same_slugs_as_i18n(self):
        for doc in ("PRIVACY.md", "SECURITY.md"):
            slugs = rl.heading_slugs(ROOT / doc)
            self.assertTrue(slugs)
            for s in slugs:
                self.assertRefOk(f"{doc}#{s}")
        self.assertEqual(Path(rl._I18N.__file__).resolve(), (ROOT / "i18n" / "i18n.py").resolve())
        # Heading with an em dash: the slug keeps two hyphens, as GitHub and i18n.py do.
        self.assertRefOk("PRIVACY.md#what-remilia-protects-against--and-what-it-does-not")

    def test_f3_missing_or_empty_anchor(self):
        self.assertRefBad("PRIVACY.md#no-such-anchor", "#no-such-anchor is not a heading anchor of PRIVACY.md")
        self.assertRefBad("PRIVACY.md#Search", "is not a heading anchor")  # slugs are lower case
        self.assertRefBad("PRIVACY.md#", "has an empty anchor")

    def test_f4_internal_is_refused(self):
        for ref in ("internal/decisions/example.md", "Internal/x.md",
                    "internal/evidence/x.md#a"):
            self.assertRefBad(ref, "points into internal/, which is not published")
            self.assertRefBad(ref, "points into internal/", fixture=True)

    def test_f5_f6_documents_outside_the_list(self):
        for ref in ("NOPE.md", "ROADMAP.md", "README.md", "ARCHITECTURE.md", "remilia/README.md"):
            self.assertRefBad(ref, "is not an allowed document; use one of: PRIVACY.md, SECURITY.md")

    def test_f7_absolute_paths_inside_and_outside_the_repository(self):
        inside = (ROOT / "PRIVACY.md").as_posix()
        outside = (self.tmp / "x.md").as_posix()
        for ref in ("/PRIVACY.md", "//server/share/x.md", "/etc/x.md"):
            self.assertRefBad(ref, "not absolute")
        for ref in ("C:/x/PRIVACY.md", "C:PRIVACY.md", "https://example.org/x.md"):
            self.assertRefBad(ref, "no drive letter, URL or ':'")
        for ref in (inside, outside):
            self.assertTrue(self.ref(ref), f"{ref} must be refused")

    def test_f8_traversal_and_dot_segments(self):
        for ref in ("../REMILIA/PRIVACY.md", "./PRIVACY.md", "docs/../PRIVACY.md", "PRIVACY.md/..",
                    "a//PRIVACY.md", "PRIVACY.md/"):
            self.assertRefBad(ref, "must not contain empty, '.' or '..' path segments")

    def test_f9_backslashes(self):
        for ref in ("docs\\PRIVACY.md", "PRIVACY.md\\", "..\\PRIVACY.md"):
            self.assertRefBad(ref, "must use '/' separators")

    def test_f10_case_is_exact_on_every_system(self):
        for ref in ("privacy.md", "PRIVACY.MD", "Privacy.md", "security.md"):
            self.assertRefBad(ref, "is not an allowed document")

    def test_f11_whitespace(self):
        for ref in ("PRIVACY.md ", " PRIVACY.md", "PRIVACY .md", "PRIVACY.md\t", "PRIVACY.md#a b", "PRIVACY.md\u00a0"):
            self.assertRefBad(ref, "must not contain spaces or other whitespace")

    def test_f12_identifiers_and_other_separators(self):
        for ref in ("ADR-0007", "PRIVACY.md;x", "PRIVACY.md?x", "PRIVACY"):
            self.assertRefBad(ref, "is not an allowed document")

    def test_f13_fixture_document_never_in_remilia(self):
        self.assertRefOk("tests/layers/README.md", fixture=True)
        self.assertRefBad("tests/layers/README.md", "is allowed only in test fixtures, not in remilia/")
        self.assertFalse(rl.is_fixture_root(rl.REPO_ROOT / "remilia"))
        self.assertFalse(rl.is_fixture_root(rl.REPO_ROOT / "tests" / ".." / "remilia"))
        self.assertTrue(rl.is_fixture_root(rl.REPO_ROOT / "tests" / "layers" / "invalid" / "crlf" / "layers"))
        self.assertTrue(rl.is_fixture_root(self.layers))  # staging copies, as in V1 fx-minus-one

    @unittest.skipUnless((SNAPSHOT / "librewolf.cfg").is_file(), "no LibreWolf base snapshot")
    def test_fixture_copy_outside_tests_layers_passes(self):
        # Regression (V1 2026-11-27, prepare-fx-minus-one): a copy of the valid
        # fixtures outside tests/layers/, without one patch, must still pass.
        copy = self.tmp / "layers-minus-one" / "layers"
        shutil.copytree(self.FIXTURE_ROOT, copy)
        (copy / "security" / "patches" / "0001-readme-top.patch").unlink()
        series = copy / "security" / "series"
        series.write_bytes(series.read_bytes().replace(b"0001-readme-top.patch\n", b""))
        problems = rl.Problems()
        cats = rl.load(copy, "all", problems)
        rl.check_together(cats, rl.Base.from_snapshot(SNAPSHOT), problems)
        self.assertClean(problems)

    def test_allowed_document_missing(self):
        fake = self.tmp / "repo"
        fake.mkdir()
        with mock.patch.object(rl, "REPO_ROOT", fake):
            self.assertEqual(rl.check_reference("PRIVACY.md", self.layers),
                             ["reference PRIVACY.md does not exist in the repository"])

    def test_f14_not_a_regular_file(self):
        fake = self.tmp / "repo"
        (fake / "PRIVACY.md").mkdir(parents=True)
        with mock.patch.object(rl, "REPO_ROOT", fake):
            self.assertEqual(rl.check_reference("PRIVACY.md", self.layers),
                             ["reference PRIVACY.md is not a regular file"])

    def test_f14_symbolic_link_out_of_the_repository(self):
        fake = self.tmp / "repo"
        fake.mkdir()
        target = self.tmp / "outside.md"
        write(target, "# Outside\n")
        try:
            os.symlink(target, fake / "PRIVACY.md")
        except (OSError, NotImplementedError) as e:
            self.skipTest(f"cannot create a symbolic link here: {e}")
        with mock.patch.object(rl, "REPO_ROOT", fake):
            self.assertEqual(rl.check_reference("PRIVACY.md", self.layers),
                             ["reference PRIVACY.md is not a regular file"])

    def test_problem_reported_with_file_and_line(self):
        self.cat("privacy", **{
            "prefs.cfg": 'defaultPref("base.default", 2); // deviation: PRIV-001\n',
            "deviations.tsv": "# id\tkind\tkey\treference\nPRIV-001\tpref\tbase.default\t"
                              "internal/decisions/example.md\n"})
        _, p = self.check()
        self.assertProblem(p, "privacy/deviations.tsv:2: reference "
                              "'internal/decisions/example.md' points into internal/")

    def test_text_is_checked_before_the_file_system(self):
        # In an empty repository nothing exists: if the file system were consulted first,
        # these would all say "does not exist". They must report the text rule instead.
        fake = self.tmp / "repo"
        fake.mkdir()
        cases = {"internal/x.md": "points into internal/", "../PRIVACY.md": "'..' path segments",
                 "/PRIVACY.md": "not absolute", "privacy.md": "is not an allowed document",
                 "ADR-0007": "is not an allowed document", "PRIVACY.md ": "whitespace",
                 "docs\\PRIVACY.md": "backslashes", "C:/PRIVACY.md": "no drive letter"}
        with mock.patch.object(rl, "REPO_ROOT", fake):
            for ref, fragment in cases.items():
                msgs = rl.check_reference(ref, self.layers)
                self.assertEqual(len(msgs), 1, ref)
                self.assertIn(fragment, msgs[0])
                self.assertNotIn("does not exist", msgs[0])


@unittest.skipUnless((SNAPSHOT / "librewolf.cfg").is_file(), "no LibreWolf base snapshot")
class RealBaseTests(unittest.TestCase):
    """Checks against the real LibreWolf 161.0-1 base snapshot."""

    def test_all_base_pref_calls_found(self):
        cfg = (SNAPSHOT / "librewolf.cfg").read_text(encoding="utf-8")
        import re
        line_starts = len(re.findall(r"^\s*(?:pref|defaultPref|lockPref|clearPref|unlockPref)\(", cfg, re.M))
        found = sum(len(v) for v in rl.base_prefs(cfg).values())
        self.assertEqual(found, line_starts)

    def test_repository_layers_pass_v0(self):
        self.assertEqual(rl.main(["check"]), 0)

    def test_valid_fixture_set_passes_v0(self):
        fixture = ROOT / "tests" / "layers" / "valid"
        if not fixture.is_dir():
            self.skipTest("no valid fixture set")
        self.assertEqual(rl.main(["check", "--layer-root", str(fixture)]), 0)

    def test_real_policies_bytes_kept_without_policy_fragments(self):
        """none, and categories without policies.json, leave LibreWolf's real file byte-identical."""
        fixture = ROOT / "tests" / "layers" / "valid"
        with tempfile.TemporaryDirectory() as tmp:
            for spec in ("none", "build-fixes,branding"):
                out = Path(tmp) / spec.replace(",", "_")
                self.assertEqual(rl.main(["assemble", "--base", str(SNAPSHOT), "--layer-root", str(fixture),
                                          "--layers", spec, "--out", str(out)]), 0)
                self.assertEqual((out / "policies.json").read_bytes(),
                                 (SNAPSHOT / "policies.json").read_bytes(), spec)
                if spec == "none":
                    for name in rl.BASE_FILES:
                        self.assertEqual((out / name).read_bytes(), (SNAPSHOT / name).read_bytes(), name)

    def test_real_policies_merge_is_semantically_equivalent(self):
        """With policy fragments, every LibreWolf policy not targeted stays equal (as JSON)."""
        fixture = ROOT / "tests" / "layers" / "valid"
        base = json.loads((SNAPSHOT / "policies.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "all"
            self.assertEqual(rl.main(["assemble", "--base", str(SNAPSHOT), "--layer-root", str(fixture),
                                      "--layers", "all", "--out", str(out)]), 0)
            merged = json.loads((out / "policies.json").read_text(encoding="utf-8"))
        expected = json.loads(json.dumps(base))
        es = expected["policies"]["ExtensionSettings"]
        for c in ("security", "privacy"):
            frag = json.loads((fixture / c / "policies.json").read_text(encoding="utf-8"))["policies"]
            es.update(frag["ExtensionSettings"])
        self.assertEqual(merged, expected)
        self.assertEqual(list(merged), list(base))
        self.assertEqual(list(merged["policies"]), list(base["policies"]))

    def test_invalid_fixture_sets_fail_with_expected_message(self):
        invalid = ROOT / "tests" / "layers" / "invalid"
        if not invalid.is_dir():
            self.skipTest("no invalid fixture sets")
        cases = sorted(p for p in invalid.iterdir() if p.is_dir())
        self.assertTrue(cases)
        for case in cases:
            with self.subTest(case=case.name):
                expect = (case / "EXPECT").read_text(encoding="utf-8").strip()
                problems = rl.Problems()
                cats = rl.load(case / "layers", "all", problems)
                rl.check_together(cats, rl.Base.from_snapshot(SNAPSHOT), problems)
                self.assertIn(expect, "\n".join(problems.items))


if __name__ == "__main__":
    unittest.main()
