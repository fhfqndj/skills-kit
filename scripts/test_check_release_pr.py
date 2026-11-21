#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def pull(*, number: int = 50, base: str = "master", merged: bool = True) -> dict[str, object]:
    return {
        "number": number,
        "base": {"ref": base},
        "merged_at": "2026-11-21T12:00:00Z" if merged else None,
    }


class CliTests(unittest.TestCase):
    def run_cli(self, payload: object) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pulls.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPTS / "check_release_pr.py"), str(path)],
                capture_output=True, text=True, check=False,
            )

    def test_merged_pr_into_master_passes(self) -> None:
        result = self.run_cli([pull()])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("влит в master", result.stdout)

    def test_unmerged_pr_fails(self) -> None:
        result = self.run_cli([pull(merged=False)])
        self.assertEqual(result.returncode, 1)
        self.assertIn("влитого в master", result.stderr)

    def test_pr_into_other_base_fails(self) -> None:
        result = self.run_cli([pull(base="develop")])
        self.assertEqual(result.returncode, 1)
        self.assertIn("влитого в master", result.stderr)

    def test_empty_list_fails(self) -> None:
        result = self.run_cli([])
        self.assertEqual(result.returncode, 1)
        self.assertIn("ни одного PR", result.stderr)

    def test_broken_json_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "pulls.json"
            path.write_text("{не json", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "check_release_pr.py"), str(path)],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("битый JSON", result.stderr)

    def test_missing_file_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "check_release_pr.py"), str(Path(tmp) / "nope.json")],
                capture_output=True, text=True, check=False,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("нет файла", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
