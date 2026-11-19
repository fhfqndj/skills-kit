#!/usr/bin/env python3
"""Переносимость команд в примерах навыков.

Проверяет ```bash/sh/shell/console```-блоки в `skills/**/*.md` на команды,
которые не выполняются на заявленных платформах, и плейсхолдеры секретов.
Команда, которую нельзя запустить, — это ложное обещание навыка.

    python3 ./scripts/check_examples.py [--repo PATH]

Код возврата 1 — есть нарушения, 0 — чисто.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SHELL_LANGS = {"bash", "sh", "shell", "console", "zsh"}
FENCE = re.compile(r"^(?:>\s*)*```(\S*)")

# (шаблон, объяснение) — проверяются только строки внутри shell-блоков
SHELL_RULES = (
    (re.compile(r"(?:^|[|;]|&&|\$\()\s*(?:\$\s*)?(?:sudo\s+|env\s+|command\s+|xargs\s+|uv\s+run\s+)?python\b(?!3)"), "python: на macOS и Ubuntu 22.04 бинарника нет — python3"),
    (re.compile(r"(?:^|[|;]|&&)\s*(?:sudo\s+)?timeout\s+\d+"), "timeout: нет в стоковой macOS — perl -e 'alarm N; exec @ARGV'"),
    (re.compile(r"sed\s+-i\s*''"), "sed -i '': BSD-синтаксис, на Linux ломается — perl -pi"),
    (re.compile(r"^\s*(?:\$\s*)?(?:sudo\s+)?assert\s"), "assert: не команда оболочки — [ … ] || { …; exit 1; }"),
)

# (шаблон, объяснение) — только внутри shell-блоков: в прозе это предупреждения, а не команды
GLOBAL_RULES = (
    (re.compile(r"\btoken\s+\*\*\*"), "плейсхолдер *** вместо переменной: пример молча пишет пустой токен"),
    (re.compile(r"\bfilter-branch\b"), "filter-branch: Git рекомендует filter-repo"),
)


@dataclass
class Report:
    violations: list[str] = field(default_factory=list)
    checked: int = 0


def shell_lines(text: str):
    """(номер строки, содержимое) внутри shell-блоков."""
    in_block = False
    for number, line in enumerate(text.splitlines(), start=1):
        match = FENCE.match(line.strip())
        if match:
            lang = match.group(1).lower()
            in_block = (not in_block) and lang in SHELL_LANGS
            continue
        if not in_block:
            continue
        content = re.sub(r"^(?:>\s*)+", "", line)
        if content.lstrip().startswith("#"):
            continue
        yield number, content


def check_file(path: Path, repo: Path) -> list[str]:
    text = path.read_text(errors="ignore")
    rel = path.relative_to(repo).as_posix()
    found: list[str] = []
    for number, line in shell_lines(text):
        for pattern, reason in SHELL_RULES:
            if pattern.search(line):
                found.append(f"{rel}:{number}: {reason}")
    for number, line in shell_lines(text):
        for pattern, reason in GLOBAL_RULES:
            if pattern.search(line):
                found.append(f"{rel}:{number}: {reason}")
    return found


def run(repo: Path = REPO) -> Report:
    report = Report()
    for path in sorted((repo / "skills").rglob("*.md")):
        report.checked += 1
        report.violations.extend(check_file(path, repo))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repo", type=Path, default=REPO)
    args = parser.parse_args(argv)
    report = run(args.repo.resolve())
    for violation in report.violations:
        print(f"ошибка: {violation}")
    print(f"нарушений: {len(report.violations)}, файлов проверено: {report.checked}")
    return 1 if report.violations else 0


if __name__ == "__main__":
    sys.exit(main())
