#!/usr/bin/env python3
"""Дрейф между репозиторием и локальной библиотекой навыков.

Навык с тем же именем в двух местах — два источника правды: правка в
репозитории не доезжает до сессий, а правка в библиотеке теряется при
установке. Скрипт сравнивает каталоги по именам и содержимому.

    python3 ./scripts/check_drift.py [--library PATH] [--repo PATH] [-v]

Код возврата: 0 — расхождений нет, 1 — есть, 2 — библиотека не найдена.
"""

from __future__ import annotations

import argparse
import difflib
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_LIBRARY = Path.home() / ".dsh" / "skills"


@dataclass
class Report:
    same: list[str] = field(default_factory=list)
    drifted: list[tuple[str, int]] = field(default_factory=list)
    only_repo: list[str] = field(default_factory=list)
    only_library: list[str] = field(default_factory=list)


def skill_names(root: Path) -> dict[str, Path]:
    return {
        skill_md.parent.name: skill_md.parent
        for skill_md in sorted(root.glob("*/SKILL.md"))
    }


def changed_lines(left: Path, right: Path) -> int:
    a = left.read_text(errors="ignore").splitlines()
    b = right.read_text(errors="ignore").splitlines()
    diff = difflib.unified_diff(a, b, lineterm="", n=0)
    return sum(1 for line in diff if line[:1] in "+-" and line[:3] not in ("+++", "---"))


def compare(repo: Path, library: Path) -> Report:
    report = Report()
    repo_skills = skill_names(repo / "skills")
    lib_skills = skill_names(library)
    for name, path in repo_skills.items():
        other = lib_skills.get(name)
        if other is None:
            report.only_repo.append(name)
            continue
        lines = changed_lines(path / "SKILL.md", other / "SKILL.md")
        if lines == 0 and not extra_files(path, other):
            report.same.append(name)
        else:
            report.drifted.append((name, lines))
    report.only_library = sorted(set(lib_skills) - set(repo_skills))
    report.drifted.sort(key=lambda item: -item[1])
    return report


def extra_files(left: Path, right: Path) -> bool:
    """Файлы навыка кроме SKILL.md, которых нет по другую сторону."""
    def files(root: Path) -> set[str]:
        return {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and path.name != "SKILL.md"
        }

    return files(left) != files(right)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--library", type=Path, default=DEFAULT_LIBRARY)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    repo = args.repo.resolve()
    library = args.library.expanduser().resolve()
    if not library.is_dir():
        print(f"библиотека {library} не найдена — сверять не с чем", file=sys.stderr)
        return 2

    report = compare(repo, library)
    print(f"репозиторий: {repo}")
    print(f"библиотека:  {library}")
    print(f"совпадает: {len(report.same)}, разъехалось: {len(report.drifted)}, "
          f"только в репозитории: {len(report.only_repo)}, "
          f"только в библиотеке: {len(report.only_library)}")
    for name, lines in report.drifted:
        print(f"  разъехалось  {name:34} {lines} строк")
    for name in report.only_repo:
        print(f"  только здесь {name}")
    if args.verbose:
        for name in report.only_library:
            print(f"  только в библ {name}")
    elif report.only_library:
        print("  (навыки только из библиотеки — с -v)")

    if report.drifted or report.only_repo:
        print("дрейф: правки в репозитории не доезжают до сессий, "
              "а локальная копия живёт своей жизнью")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
