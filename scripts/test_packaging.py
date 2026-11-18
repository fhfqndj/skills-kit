#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
INDEX = REPO / "INDEX.md"
EXPECTED_SKILLS = 27

MANIFESTS = (
    "plugin.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
)

FLAT_INDEX_ROW = re.compile(r"\]\(skills/[a-z0-9-]+/SKILL\.md\)")
NESTED_INDEX_ROW = re.compile(r"\]\(skills/[a-z0-9-]+/[a-z0-9-]+/SKILL\.md\)")


def skill_files() -> list[Path]:
    return sorted(SKILLS.glob("*/SKILL.md"))


class PackagingTests(unittest.TestCase):
    def test_skills_are_direct_children(self) -> None:
        found = skill_files()
        self.assertEqual(
            len(found),
            EXPECTED_SKILLS,
            f"в skills/ {len(found)} навыков, ожидалось {EXPECTED_SKILLS}",
        )
        names = [path.parent.name for path in found]
        self.assertEqual(len(set(names)), len(names), "дубли имён навыков")
        for name in names:
            self.assertTrue(
                (SKILLS / name / "SKILL.md").is_file(),
                f"skills/{name}/SKILL.md не найден",
            )

    def test_no_nested_skill_md(self) -> None:
        nested = [
            path.relative_to(SKILLS).as_posix()
            for path in sorted(SKILLS.rglob("SKILL.md"))
            if len(path.relative_to(SKILLS).parts) > 2
        ]
        self.assertEqual(
            nested,
            [],
            "навык должен лежать плоско (skills/<навык>/SKILL.md), "
            f"а найден вложенный: {', '.join(nested)}",
        )

    def test_index_rows_are_flat(self) -> None:
        text = INDEX.read_text(encoding="utf-8")
        flat = FLAT_INDEX_ROW.findall(text)
        self.assertEqual(
            len(flat),
            len(skill_files()),
            "число строк INDEX.md с плоским путём не равно числу навыков",
        )
        self.assertNotRegex(
            text,
            NESTED_INDEX_ROW,
            "в INDEX.md остались ссылки на skills/<группа>/<навык>/",
        )

    def test_manifest_skills_point_at_flat_root(self) -> None:
        checked = 0
        for rel in MANIFESTS:
            path = REPO / rel
            if not path.is_file():
                continue
            data = json.loads(path.read_text(encoding="utf-8"))
            raw = data.get("skills")
            if raw is None:
                continue
            targets = raw if isinstance(raw, list) else [raw]
            for item in targets:
                self.assertIsInstance(item, str, f"{rel}: skills должен быть строкой")
                root = REPO / item.removeprefix("./").rstrip("/")
                self.assertTrue(root.is_dir(), f"{rel}: каталога {item!r} нет")
                children = [entry for entry in root.iterdir() if entry.is_dir()]
                self.assertTrue(
                    children, f"{rel}: в {item!r} нет каталогов навыков"
                )
                for child in children:
                    self.assertTrue(
                        (child / "SKILL.md").is_file(),
                        f"{rel}: в {item!r} ребёнок {child.name}/ без SKILL.md — "
                        "навык должен лежать плоско",
                    )
                checked += 1
        self.assertGreaterEqual(
            checked, 1, "ни один манифест не объявляет поле skills"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
