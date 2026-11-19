#!/usr/bin/env python3
"""Гейт версии навыка: изменённый SKILL.md обязан поднять version.

    python3 scripts/check_versions.py [--base origin/master] [--repo PATH]

Сравнивает `version` в рабочем дереве с версией в базе для каждого изменённого
`skills/<навык>/SKILL.md`. Новый навык без базы — ок, удалённый — пропуск.
Код возврата 1 — есть навык с правкой без роста версии.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VERSION = re.compile(r"^version:\s*(\d+)\.(\d+)\.(\d+)\s*$", re.M)


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
    )


def git_out(repo: Path, *args: str) -> str:
    return git(repo, *args).stdout


def skill_version(text: str) -> tuple[int, int, int] | None:
    match = VERSION.search(text)
    return tuple(int(x) for x in match.groups()) if match else None


def changed_skills(repo: Path, merge_base: str) -> list[str]:
    committed = git_out(repo, "diff", "--name-only", f"{merge_base}...HEAD", "--", "skills")
    working = git_out(repo, "status", "--porcelain", "--", "skills")
    paths = set(committed.splitlines())
    for line in working.splitlines():
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ")[1]
        paths.add(path)
    return sorted(path for path in paths if path.endswith("/SKILL.md"))


def resolve_merge_base(repo: Path, base: str) -> str:
    if git(repo, "rev-parse", "--verify", base).returncode != 0:
        raise SystemExit(f"ошибка: база {base} не найдена — гейт без базы ничего не проверяет")
    result = git(repo, "merge-base", base, "HEAD")
    return result.stdout.strip() or base


def check(repo: Path, base: str) -> list[str]:
    problems: list[str] = []
    for path in changed_skills(repo, resolve_merge_base(repo, base)):
        target = repo / path
        if not target.exists():
            continue  # навык удалён — версию не с чем сравнивать
        current = skill_version(target.read_text(errors="ignore"))
        previous_text = git_out(repo, "show", f"{resolve_merge_base(repo, base)}:{path}")
        previous = skill_version(previous_text)
        name = Path(path).parent.name
        if previous is None:
            if current is None:
                problems.append(f"{name}: нет version в SKILL.md")
            continue
        if current is None:
            problems.append(f"{name}: version пропала из SKILL.md")
        elif current <= previous:
            problems.append(
                f"{name}: SKILL.md изменён, а version {'.'.join(map(str, current))} "
                f"не выросла (было {'.'.join(map(str, previous))})"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="origin/master")
    parser.add_argument("--repo", type=Path, default=REPO)
    args = parser.parse_args(argv)
    problems = check(args.repo.resolve(), args.base)
    for problem in problems:
        print(f"ошибка: {problem}")
    merge_base = resolve_merge_base(args.repo.resolve(), args.base)
    print(
        f"база: {merge_base[:8]}, изменённых навыков: "
        f"{len(changed_skills(args.repo.resolve(), merge_base))}, нарушений: {len(problems)}"
    )
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
