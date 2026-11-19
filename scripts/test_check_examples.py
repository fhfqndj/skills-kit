#!/usr/bin/env python3

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import check_examples  # noqa: E402


def write_skill(root: Path, text: str) -> None:
    path = root / "skills" / "demo" / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_on(text: str) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        write_skill(root, text)
        return check_examples.run(root).violations


SHELL = "```bash\n{}\n```\n"


class ShellRuleTests(unittest.TestCase):
    def test_python_without_three_is_error(self) -> None:
        self.assertTrue(run_on(SHELL.format("python -c \"print(1)\"")))
        self.assertTrue(run_on(SHELL.format("python -m pytest -q")))

    def test_python3_is_clean(self) -> None:
        self.assertEqual(run_on(SHELL.format("python3 -c \"print(1)\"")), [])

    def test_python_inside_json_is_not_a_command(self) -> None:
        self.assertEqual(
            run_on(SHELL.format("-d '{\"names\": [\"machine-learning\", \"python\"]}'")), []
        )

    def test_timeout_is_error(self) -> None:
        self.assertTrue(run_on(SHELL.format("echo x | timeout 20 gh auth login")))

    def test_perl_alarm_is_clean(self) -> None:
        self.assertEqual(
            run_on(SHELL.format("echo x | perl -e 'alarm 20; exec @ARGV' gh auth login")), []
        )

    def test_bsd_sed_is_error(self) -> None:
        self.assertTrue(run_on(SHELL.format("sed -i '' 's/a/b/g' README.md")))

    def test_perl_pi_is_clean(self) -> None:
        self.assertEqual(run_on(SHELL.format("perl -pi -e 's/a/b/g' README.md")), [])

    def test_bare_assert_is_error(self) -> None:
        self.assertTrue(run_on(SHELL.format("assert \"$(git rev-parse HEAD)\" = \"x\"")))

    def test_shell_test_is_clean(self) -> None:
        self.assertEqual(
            run_on(SHELL.format('[ "$a" = "$b" ] || { echo no; exit 1; }')), []
        )


class GlobalRuleTests(unittest.TestCase):
    def test_secret_placeholder_is_error(self) -> None:
        self.assertTrue(run_on(SHELL.format('curl -H "Authorization: token ***" https://api.github.com')))

    def test_token_variable_is_clean(self) -> None:
        self.assertEqual(
            run_on(SHELL.format('curl -H "Authorization: token $TOKEN" https://api.github.com')), []
        )

    def test_filter_branch_is_error(self) -> None:
        self.assertTrue(run_on("Использовать `git filter-branch` не стоит."))

    def test_filter_repo_is_clean(self) -> None:
        self.assertEqual(run_on("Использовать `git filter-repo --mailmap`."), [])


class ScopeTests(unittest.TestCase):
    def test_non_shell_block_is_ignored(self) -> None:
        self.assertEqual(run_on("```text\npython -c \"print(1)\"\n```\n"), [])

    def test_prose_is_ignored(self) -> None:
        self.assertEqual(run_on("В тексте слово python встречается как название языка.\n"), [])

    def test_real_repo_is_clean(self) -> None:
        report = check_examples.run(SCRIPTS.parent)
        self.assertEqual(report.violations, [])
        self.assertGreater(report.checked, 50)


if __name__ == "__main__":
    unittest.main(verbosity=2)
