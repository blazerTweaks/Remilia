#!/usr/bin/env python3
# SPDX-License-Identifier: MPL-2.0
"""Unit tests for the --out rules of validate_win64.py (no browser, no selenium).

    python -m unittest discover -s tests/validation

Each test builds a throwaway Git repository with upstream/pins.env and a
.gitignore, so the real repository is only read (help text, refusal case).
"""
from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tests" / "validation" / "validate_win64.py"
spec = importlib.util.spec_from_file_location("validate_win64", SCRIPT)
vw = importlib.util.module_from_spec(spec)
sys.modules["validate_win64"] = vw
spec.loader.exec_module(vw)

HAVE_GIT = shutil.which("git") is not None


@unittest.skipUnless(HAVE_GIT, "git not available")
class ResolveOutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="remilia-validate-")).resolve()
        self.repo = self.tmp / "repo"
        (self.repo / "upstream").mkdir(parents=True)
        (self.repo / "upstream" / "pins.env").write_text("X=1\n", encoding="utf-8")
        (self.repo / "internal" / "evidence").mkdir(parents=True)
        (self.repo / "tests" / "validation").mkdir(parents=True)
        (self.repo / ".gitignore").write_text("/internal/\n/dist/\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.cwd = os.getcwd()

    def tearDown(self) -> None:
        os.chdir(self.cwd)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def out(self, arg, **kw) -> Path:
        return vw.resolve_out(arg, self.repo, **kw)

    def assertRefused(self, arg, fragment: str, **kw) -> None:
        with self.assertRaises(vw.OutputError) as cm:
            self.out(arg, **kw)
        self.assertIn(fragment, str(cm.exception))

    def test_w1_relative_from_the_root(self):
        os.chdir(self.repo)
        self.assertEqual(self.out("internal/evidence/2026-11-27-x"),
                         self.repo / "internal" / "evidence" / "2026-11-27-x")
        self.assertEqual(self.out("internal/evidence/2026-11-27-x/"),
                         self.repo / "internal" / "evidence" / "2026-11-27-x")

    def test_w2_same_destination_from_tests_validation(self):
        os.chdir(self.repo / "tests" / "validation")
        self.assertEqual(self.out("internal/evidence/2026-11-27-x"),
                         self.repo / "internal" / "evidence" / "2026-11-27-x")
        self.assertFalse((self.repo / "tests" / "validation" / "internal").exists())

    def test_w3_inside_the_repository_but_not_internal_evidence(self):
        for arg in ("tests/results/x", "dist/x", "x", "internal/x", "internal/evidence",
                    "internal/evidence/", "tests/validation/internal/evidence/x"):
            self.assertRefused(arg, "must be a directory inside internal/evidence/")

    def test_w4_dot_dot(self):
        self.assertRefused("internal/evidence/../../x", "must be a directory inside internal/evidence/")
        self.assertRefused("internal/evidence/../x", "must be a directory inside internal/evidence/")
        self.assertEqual(self.out("internal/evidence/a/../b"), self.repo / "internal" / "evidence" / "b")

    def test_w5_case_is_exact(self):
        for arg in ("Internal/Evidence/x", "internal/Evidence/x", "INTERNAL/evidence/x"):
            self.assertRefused(arg, "must be a directory inside internal/evidence/")

    def test_w6_absolute_inside_and_outside_the_repository(self):
        self.assertEqual(self.out(str(self.repo / "internal" / "evidence" / "abs")),
                         self.repo / "internal" / "evidence" / "abs")
        self.assertRefused(str(self.repo / "dist" / "x"), "must be a directory inside internal/evidence/")
        self.assertRefused(str(self.tmp / "elsewhere"), "is outside the repository")
        self.assertRefused(str(Path(tempfile.gettempdir()) / "remilia-out"), "is outside the repository")

    @unittest.skipUnless(os.name == "nt", "drive-relative paths exist only on Windows")
    def test_w6_drive_relative(self):
        self.assertRefused("C:internal/evidence/x", "drive-relative")

    def test_w7_no_repository_marker(self):
        with self.assertRaises(vw.OutputError) as cm:
            vw.resolve_out("internal/evidence/x", None)
        self.assertIn("repository root not found", str(cm.exception))
        lone = self.tmp / "lone" / "tests" / "validation" / "validate_win64.py"
        lone.parent.mkdir(parents=True)
        lone.write_text("", encoding="utf-8")
        self.assertIsNone(vw.find_repo_root(lone))
        script = self.repo / "tests" / "validation" / "validate_win64.py"
        script.write_text("", encoding="utf-8")
        self.assertEqual(vw.find_repo_root(script), self.repo)

    def test_w8_existing_destination(self):
        d = self.repo / "internal" / "evidence" / "run"
        d.mkdir()
        self.assertEqual(self.out("internal/evidence/run"), d)  # empty: accepted
        (d / "results.json").write_text("{}\n", encoding="utf-8")
        self.assertRefused("internal/evidence/run", "is not empty; pass --overwrite")
        self.assertEqual(self.out("internal/evidence/run", overwrite=True), d)
        f = self.repo / "internal" / "evidence" / "file"
        f.write_text("x", encoding="utf-8")
        self.assertRefused("internal/evidence/file", "exists and is not a directory")
        self.assertRefused("internal/evidence/file", "exists and is not a directory", overwrite=True)

    def test_destination_not_ignored_by_git(self):
        (self.repo / ".gitignore").write_text("/dist/\n", encoding="utf-8")
        self.assertRefused("internal/evidence/x", "is not ignored by Git (git check-ignore exit 1)")

    def test_destination_in_a_directory_that_is_not_a_git_repository(self):
        shutil.rmtree(self.repo / ".git")
        self.assertRefused("internal/evidence/x", "is not ignored by Git")

    def test_git_missing(self):
        self.assertRefused("internal/evidence/x", "git not found",
                           check_ignore=lambda root, rel: -1)

    def test_check_ignore_receives_the_repository_relative_directory(self):
        seen = []
        self.out("internal/evidence/a/b", check_ignore=lambda root, rel: seen.append((root, rel)) or 0)
        self.assertEqual(seen, [(self.repo, "internal/evidence/a/b/")])

    def test_symbolic_link_out_of_internal_evidence(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        try:
            os.symlink(outside, self.repo / "internal" / "evidence" / "link", target_is_directory=True)
        except (OSError, NotImplementedError) as e:
            self.skipTest(f"cannot create a symbolic link here: {e}")
        self.assertRefused("internal/evidence/link/x", "resolves outside internal/evidence/")

    def test_nothing_is_created_by_validation(self):
        for arg in ("internal/evidence/new-a", "tests/results/new-b"):
            try:
                self.out(arg)
            except vw.OutputError:
                pass
        self.assertFalse((self.repo / "internal" / "evidence" / "new-a").exists())
        self.assertFalse((self.repo / "tests" / "results").exists())


class PackageRulesTests(unittest.TestCase):
    """Package checks that do not need pefile or a build."""

    def test_essential_files_follow_the_exe_argument(self):
        self.assertEqual(vw.essential_files("remilia.exe")[0], "remilia.exe")
        self.assertNotIn("librewolf.exe", vw.essential_files("remilia.exe"))
        self.assertIn("librewolf.cfg", vw.essential_files("remilia.exe"))  # internal name kept
        self.assertEqual(vw.essential_files("x.exe")[1:], list(vw.ESSENTIAL_FILES))

    def test_no_executable_name_is_hard_coded(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("'librewolf.exe'", source)
        self.assertNotIn('"librewolf.exe"', source)

    def test_embedded_manifest_detection(self):
        class Entry:
            def __init__(self, id_):
                self.id = id_

        class Root:
            def __init__(self, ids):
                self.entries = [Entry(i) for i in ids]

        class PE:
            pass

        pe = PE()
        self.assertFalse(vw.has_embedded_manifest(pe))  # no resource directory at all
        pe.DIRECTORY_ENTRY_RESOURCE = Root([3, 14, 16])  # icons, group icon, version
        self.assertFalse(vw.has_embedded_manifest(pe))
        pe.DIRECTORY_ENTRY_RESOURCE = Root([3, 24])
        self.assertTrue(vw.has_embedded_manifest(pe))


class CommandLineTests(unittest.TestCase):
    def run_script(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *args], capture_output=True,
                              cwd=str(ROOT / "tests" / "validation"))

    def test_w9_help_keeps_line_breaks_and_states_the_rules(self):
        r = self.run_script("--help")
        self.assertEqual(r.returncode, 0)
        out = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")  # Windows console newlines
        self.assertIn("--exe remilia.exe \\\n      --geckodriver", out)
        self.assertIn("--out internal/evidence/<date>-<build>/", out)
        self.assertIn("A\nrelative --out is resolved against the repository root", out)
        self.assertIn("--overwrite", out)

    @unittest.skipUnless(HAVE_GIT, "git not available")
    def test_refusal_happens_before_anything_is_written(self):
        target = ROOT / "tests" / "results"
        self.assertFalse(target.exists(), "tests/results must not exist before this test")
        r = self.run_script("--app-dir", "none", "--exe", "none.exe", "--geckodriver", "none.exe",
                            "--out", "tests/results/selftest", "--only", "none")
        self.assertEqual(r.returncode, 2)
        self.assertIn(b"must be a directory inside internal/evidence/", r.stderr)
        self.assertFalse(target.exists())
        self.assertFalse((ROOT / "tests" / "validation" / "tests").exists())


if __name__ == "__main__":
    unittest.main()
