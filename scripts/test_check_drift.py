#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
SCRIPT = SCRIPTS / "check_drift.py"
sys.path.insert(0, str(SCRIPTS))
import check_drift  # noqa: E402


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def skill(
    root: Path, name: str, body: str = "тело\n", extra: str | None = None,
    nested: bool = True,
) -> Path:
    directory = root / "skills" / name if nested else root / name
    write(directory / "SKILL.md", f"---\nname: {name}\n---\n\n{body}")
    if extra:
        write(directory / extra, "файл\n")
    return directory


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class CompareTests(unittest.TestCase):
    def test_identical_tree_is_clean(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, library = Path(tmp) / "repo", Path(tmp) / "lib"
            skill(repo, "plan")
            skill(library, "plan", nested=False)
            report = check_drift.compare(repo, library)
            self.assertEqual(report.same, ["plan"])
            self.assertEqual(report.drifted, [])

    def test_drift_counts_changed_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, library = Path(tmp) / "repo", Path(tmp) / "lib"
            skill(repo, "plan", "одна строк\n")
            skill(library, "plan", "другая строка\n", nested=False)
            report = check_drift.compare(repo, library)
            self.assertEqual([name for name, _ in report.drifted], ["plan"])
            self.assertGreater(report.drifted[0][1], 0)

    def test_extra_file_counts_as_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, library = Path(tmp) / "repo", Path(tmp) / "lib"
            skill(repo, "plan", extra="references/тема.md")
            skill(library, "plan", nested=False)
            report = check_drift.compare(repo, library)
            self.assertEqual(len(report.drifted), 1)

    def test_only_repo_and_only_library(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, library = Path(tmp) / "repo", Path(tmp) / "lib"
            skill(repo, "plan")
            skill(library, "office", nested=False)
            report = check_drift.compare(repo, library)
            self.assertEqual(report.only_repo, ["plan"])
            self.assertEqual(report.only_library, ["office"])
            self.assertEqual(report.same, [])


class CliTests(unittest.TestCase):
    def test_clean_tree_exits_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, library = Path(tmp) / "repo", Path(tmp) / "lib"
            skill(repo, "plan")
            skill(library, "plan", nested=False)
            result = run("--repo", str(repo), "--library", str(library))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("совпадает: 1", result.stdout)

    def test_drift_exits_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, library = Path(tmp) / "repo", Path(tmp) / "lib"
            skill(repo, "plan", "одна строка\n")
            skill(library, "plan", "другая строка\n", nested=False)
            result = run("--repo", str(repo), "--library", str(library))
            self.assertEqual(result.returncode, 1)
            self.assertIn("разъехалось  plan", result.stdout)

    def test_missing_library_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            skill(repo, "plan")
            result = run("--repo", str(repo), "--library", str(Path(tmp) / "нет"))
            self.assertEqual(result.returncode, 2)
            self.assertIn("не найдена", result.stderr)

    def test_verbose_lists_library_only_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo, library = Path(tmp) / "repo", Path(tmp) / "lib"
            skill(repo, "plan")
            skill(library, "plan", nested=False)
            skill(library, "office", nested=False)
            result = run("--repo", str(repo), "--library", str(library), "-v")
            self.assertIn("только в библ office", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
