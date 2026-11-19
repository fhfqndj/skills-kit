#!/usr/bin/env python3
"""Заметки релиза из CHANGELOG.

    python3 scripts/release_notes.py --version 1.3.0 [--changelog CHANGELOG.md]

Печатает содержимое секции `## <версия>` до следующего заголовка `## `. Код возврата 2 —
секции нет: релиз без заметок хуже, чем релиз, который не вышел.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def extract(text: str, version: str) -> str | None:
    header = re.compile(rf"^##\s+{re.escape(version)}(\s|$)", re.M)
    match = header.search(text)
    if match is None:
        return None
    start = match.start()
    rest = text[match.end():]
    next_header = re.search(r"^##\s+", rest, re.M)
    end = match.end() + next_header.start() if next_header else len(text)
    return text[start:end].strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", required=True, help="версия без префикса v, например 1.3.0")
    parser.add_argument("--changelog", type=Path, default=REPO / "CHANGELOG.md")
    args = parser.parse_args(argv)

    text = args.changelog.read_text(encoding="utf-8")
    section = extract(text, args.version)
    if section is None:
        print(f"ошибка: в {args.changelog} нет секции «## {args.version}»", file=sys.stderr)
        return 2
    print(section)
    return 0


if __name__ == "__main__":
    sys.exit(main())
