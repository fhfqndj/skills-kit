#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import check_versions  # noqa: E402


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", *args],
        check=True, capture_output=True,
    )


def write_skill(repo: Path, name: str, version: str, body: str = "тело") -> None:
    path = repo / "skills" / name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nname: {name}\nversion: {version}\n---\n\n{body}\n", encoding="utf-8")


class VersionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        git(self.repo, "init", "-q", "-b", "master")
        write_skill(self.repo, "alpha", "1.0.0")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")
        self.addCleanup(self._tmp.cleanup)

    def commit(self, message: str) -> None:
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", message)

    def test_body_change_without_bump_is_error(self) -> None:
        write_skill(self.repo, "alpha", "1.0.0", "новое тело")
        self.commit("change")
        problems = check_versions.check(self.repo, "HEAD~1")
        self.assertTrue(any("не выросла" in p for p in problems), problems)

    def test_patch_bump_passes(self) -> None:
        write_skill(self.repo, "alpha", "1.0.1", "новое тело")
        self.commit("bump")
        self.assertEqual(check_versions.check(self.repo, "HEAD~1"), [])

    def test_version_only_change_passes(self) -> None:
        write_skill(self.repo, "alpha", "1.1.0")
        self.commit("bump only")
        self.assertEqual(check_versions.check(self.repo, "HEAD~1"), [])

    def test_new_skill_passes(self) -> None:
        write_skill(self.repo, "beta", "0.1.0")
        self.commit("new")
        self.assertEqual(check_versions.check(self.repo, "HEAD~1"), [])

    def test_deleted_skill_is_skipped(self) -> None:
        path = self.repo / "skills" / "alpha" / "SKILL.md"
        path.unlink()
        self.commit("delete")
        self.assertEqual(check_versions.check(self.repo, "HEAD~1"), [])

    def test_lower_version_is_error(self) -> None:
        write_skill(self.repo, "alpha", "0.9.9", "откат")
        self.commit("downgrade")
        problems = check_versions.check(self.repo, "HEAD~1")
        self.assertTrue(any("не выросла" in p for p in problems), problems)

    def test_missing_version_is_error(self) -> None:
        path = self.repo / "skills" / "alpha" / "SKILL.md"
        path.write_text("---\nname: alpha\n---\n\nтело\n", encoding="utf-8")
        self.commit("no version")
        problems = check_versions.check(self.repo, "HEAD~1")
        self.assertTrue(any("version пропала" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main(verbosity=2)
