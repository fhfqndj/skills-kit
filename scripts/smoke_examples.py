#!/usr/bin/env python3
"""Смоук-прогон переносимых команд из навыков.

    python3 scripts/smoke_examples.py

`check_examples.py` проверяет текст, а этот скрипт запускает несколько реальных сниппетов
из библиотеки и сверяет коды возврата. Инструмента нет в системе — строка `skipped`, а не
тишина и не падение. Код возврата 1 — сниппет повёл себя не так, как обещает навык.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Case:
    name: str
    command: list[str]
    expected: int
    tool: str | None = None


CASES = (
    Case("perl-alarm", ["perl", "-e", "alarm 1; exec @ARGV", "sleep", "5"], 142, "perl"),
    Case("perl-pi", ["sh", "-c", "printf 'a\\n' > f && perl -pi -e 's/a/b/' f && grep -q '^b$' f"], 0, "perl"),
    Case(
        "python3-json",
        ["sh", "-c", "printf '{\"a\": 1}' | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"a\"])'"],
        0,
        "python3",
    ),
    Case("shell-guard", ["sh", "-c", "[ x = y ] || { echo no; exit 1; }"], 1),
    Case("filter-repo-help", ["git", "filter-repo", "--help"], 0, "git-filter-repo"),
)


def tool_available(case: Case) -> bool:
    return shutil.which(case.tool) is not None if case.tool else True


def normalize(returncode: int) -> int:
    """shell-код возврата: убитый сигналом процесс даёт 128+N, а subprocess — -N."""
    return 128 - returncode if returncode < 0 else returncode


def execute(cases: tuple[Case, ...] | list[Case], workdir: Path) -> list[str]:
    report: list[str] = []
    for case in cases:
        if not tool_available(case):
            report.append(f"skipped {case.name} ({case.tool} not installed)")
            continue
        result = subprocess.run(case.command, cwd=workdir, capture_output=True, text=True)
        actual = normalize(result.returncode)
        if actual != case.expected:
            detail = (result.stderr or result.stdout).strip().splitlines()[:2]
            report.append(
                f"FAIL {case.name}: exit {actual}, expected {case.expected}"
                + (f" — {' / '.join(detail)}" if detail else "")
            )
        else:
            report.append(f"ok {case.name}")
    return report


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        report = execute(CASES, Path(tmp))
    for line in report:
        print(line)
    failed = [line for line in report if line.startswith("FAIL")]
    skipped = [line for line in report if line.startswith("skipped")]
    print(f"смоук: {len(report)}, провалов: {len(failed)}, пропусков: {len(skipped)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
