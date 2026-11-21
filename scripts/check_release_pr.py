#!/usr/bin/env python3
"""Гейт релиза: коммит тега обязан прийти из PR, влитого в master.

    python3 scripts/check_release_pr.py <pulls.json>

Разбирает ответ GitHub API `commits/<sha>/pulls`. Код 0 — в массиве есть PR
с непустым `merged_at` и `base.ref == "master"`; 1 — массив пуст или влитого
PR в master нет; 2 — файла нет, JSON битый или это не массив. Сеть не
используется: только разбор файла.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = "master"


def merged_into_master(pulls: list[object]) -> dict[str, object] | None:
    for pull in pulls:
        if not isinstance(pull, dict) or pull.get("merged_at") is None:
            continue
        base = pull.get("base")
        if isinstance(base, dict) and base.get("ref") == BASE:
            return pull
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pulls_json", type=Path, help="ответ GitHub API commits/<sha>/pulls")
    args = parser.parse_args(argv)

    try:
        text = args.pulls_json.read_text(encoding="utf-8")
    except OSError:
        print(f"ошибка: нет файла {args.pulls_json}", file=sys.stderr)
        return 2

    try:
        pulls = json.loads(text)
    except json.JSONDecodeError:
        print(f"ошибка: файл {args.pulls_json} — битый JSON", file=sys.stderr)
        return 2

    if not isinstance(pulls, list):
        print(f"ошибка: файл {args.pulls_json} — это не JSON-массив", file=sys.stderr)
        return 2

    if not pulls:
        print("ошибка: GitHub не вернул ни одного PR для коммита — релиз только из влитого PR", file=sys.stderr)
        return 1

    pull = merged_into_master(pulls)
    if pull is None:
        print("ошибка: нет PR, влитого в master — релиз только из влитого PR", file=sys.stderr)
        return 1

    print(f"PR #{pull.get('number', '?')} влит в master")
    return 0


if __name__ == "__main__":
    sys.exit(main())
