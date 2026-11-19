#!/usr/bin/env python3

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import smoke_examples  # noqa: E402


class SmokeTests(unittest.TestCase):
    def run_cases(self, cases) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            return smoke_examples.execute(cases, Path(tmp))

    def test_passing_case(self) -> None:
        report = self.run_cases([smoke_examples.Case("true", ["true"], 0)])
        self.assertEqual(report, ["ok true"])

    def test_failing_case_reports_exit(self) -> None:
        report = self.run_cases([smoke_examples.Case("false", ["false"], 0)])
        self.assertTrue(report[0].startswith("FAIL false: exit 1"))

    def test_expected_nonzero_is_not_failure(self) -> None:
        report = self.run_cases([smoke_examples.Case("guard", ["sh", "-c", "exit 1"], 1)])
        self.assertEqual(report, ["ok guard"])

    def test_missing_tool_is_skipped(self) -> None:
        case = smoke_examples.Case("x", ["true"], 0, "tool-that-does-not-exist-42")
        report = self.run_cases([case])
        self.assertEqual(report, ["skipped x (tool-that-does-not-exist-42 not installed)"])

    def test_signal_is_normalized_to_shell_code(self) -> None:
        self.assertEqual(smoke_examples.normalize(-14), 142)
        self.assertEqual(smoke_examples.normalize(0), 0)

    def test_real_cases_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = smoke_examples.execute(smoke_examples.CASES, Path(tmp))
        self.assertFalse([line for line in report if line.startswith("FAIL")], report)
