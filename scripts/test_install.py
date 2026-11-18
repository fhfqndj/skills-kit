#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INSTALL = "./scripts/install.sh"
ALL_SKILLS = 27
CORE_SKILLS = 15
GIT_SKILLS = 8
CODE_SKILLS = 4
SENTINEL = "# sentinel: не перезаписывать без --force\n"


class InstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.addCleanup(self._tmp.cleanup)

    def install(self, *args: object) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        return subprocess.run(
            [INSTALL, *(str(arg) for arg in args)],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def target(self, name: str) -> Path:
        return self.root / name / "skills"

    @staticmethod
    def skill_dirs(target: Path) -> list[Path]:
        if not target.is_dir():
            return []
        return sorted(
            path for path in target.iterdir() if (path / "SKILL.md").is_file()
        )

    def test_target_list_shows_groups(self) -> None:
        result = self.install("--target", "list")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"core ({CORE_SKILLS})", result.stdout)
        self.assertIn(f"git ({GIT_SKILLS})", result.stdout)
        self.assertIn(f"code ({CODE_SKILLS})", result.stdout)

    def test_dry_run_does_not_create_target(self) -> None:
        target = self.target("dry")
        result = self.install("--target", target, "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(target.exists())
        self.assertIn("[dry-run]", result.stdout)

    def test_install_all_skills(self) -> None:
        target = self.target("all")
        result = self.install("--target", target)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.skill_dirs(target)), ALL_SKILLS)

    def test_pack_core(self) -> None:
        target = self.target("core")
        result = self.install("--target", target, "--pack", "core")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(len(self.skill_dirs(target)), CORE_SKILLS)

    def test_pack_core_verify_checks_installed_only(self) -> None:
        target = self.target("core-verify")
        result = self.install("--target", target, "--pack", "core", "--verify")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(self.skill_dirs(target)), CORE_SKILLS)
        self.assertIn("итог: OK", result.stdout)

    def test_pack_unknown_group_lists_available(self) -> None:
        target = self.target("ghost")
        result = self.install("--target", target, "--pack", "ghost")
        self.assertEqual(result.returncode, 2)
        self.assertIn("неизвестная группа: ghost", result.stderr)
        self.assertIn("доступные группы:", result.stderr)
        for group in ("core", "git", "code"):
            self.assertIn(group, result.stderr)

    def test_conflict_without_force_keeps_existing(self) -> None:
        target = self.target("conflict")
        sentinel = target / "plan" / "SKILL.md"
        sentinel.parent.mkdir(parents=True)
        sentinel.write_text(SENTINEL, encoding="utf-8")
        result = self.install("--target", target, "--pack", "core")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), SENTINEL)
        self.assertIn("занято", result.stderr)

    def test_force_overwrites_conflict(self) -> None:
        target = self.target("conflict-force")
        sentinel = target / "plan" / "SKILL.md"
        sentinel.parent.mkdir(parents=True)
        sentinel.write_text(SENTINEL, encoding="utf-8")
        result = self.install("--target", target, "--pack", "core", "--force")
        self.assertEqual(result.returncode, 0, result.stderr)
        text = sentinel.read_text(encoding="utf-8")
        self.assertNotEqual(text, SENTINEL)
        self.assertIn("name: plan", text)

    def test_unknown_target_is_usage_error(self) -> None:
        result = self.install("--target", "nope")
        self.assertEqual(result.returncode, 2)
        self.assertIn("неизвестная цель: nope", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
