#!/usr/bin/env python3

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import release_notes  # noqa: E402

CHANGELOG = """# Изменения

## 1.3.0 — 2026-11-20

Свежие изменения.

### Добавлено

- Гейт версии.

## 1.2.0 — 2026-11-19

Прошлый релиз.
"""


class ExtractTests(unittest.TestCase):
    def test_section_found(self) -> None:
        section = release_notes.extract(CHANGELOG, "1.3.0")
        self.assertIn("Свежие изменения", section)
        self.assertNotIn("Прошлый релиз", section)

    def test_missing_section_is_none(self) -> None:
        self.assertIsNone(release_notes.extract(CHANGELOG, "9.9.9"))

    def test_version_prefix_is_not_a_match(self) -> None:
        self.assertIsNone(release_notes.extract(CHANGELOG, "1.3"))


class CliTests(unittest.TestCase):
    def test_cli_prints_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CHANGELOG.md"
            path.write_text(CHANGELOG, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "release_notes.py"), "--version", "1.3.0", "--changelog", str(path)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("## 1.3.0", result.stdout)

    def test_cli_fails_without_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CHANGELOG.md"
            path.write_text(CHANGELOG, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "release_notes.py"), "--version", "2.0.0", "--changelog", str(path)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("нет секции", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
