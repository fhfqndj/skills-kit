#!/usr/bin/env python3
"""Проверка целостности skills-kit. Запуск: ./scripts/check.py [-v] [--repo PATH]

Проверяет: YAML-frontmatter навыков (allowed-keys, полный контракт полей,
semver, kebab-case, дубли ключей), дубли имён и near-дубли description, мусор и
пустые каталоги внутри skills/, имена вспомогательных файлов, линт ролей
subagents/, битые внутренние ссылки (включая ссылки с анкором/query),
абсолютные пути и секреты во всех текстовых файлах репозитория, полноту
INDEX.md, parity INDEX↔диск↔subagents, счётчик «Файлов» в INDEX,
двусторонность related_skills, покрытие навыков routing-кейсами, parity
манифестов установки. Код выхода 1 при ошибках.

Правила — чистые функции ниже; CLI только собирает файлы и печатает отчёт.
Пороги и baseline редакционного долга — константами здесь, а не в навыках:
автор навыка не должен сам себе выдавать исключение.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

TEXT_EXT = {".md", ".py", ".sh", ".txt", ".json", ".yaml", ".yml"}
TEXT_NAMES = frozenset({"Makefile", ".gitattributes", ".editorconfig"})
HYGIENE_SKIP_DIRS = frozenset({".git", "dist", "__pycache__", "local"})

JUNK_NAMES = {".DS_Store", "Thumbs.db"}
JUNK_DIRS = {"__pycache__", ".pytest_cache", "node_modules"}
JUNK_SUFFIXES = {".pyc", ".pyo", ".pyd"}

ABS_PATH = re.compile(
    r"(?<![\w~])/(?:Users|home)/[^\s]+"
    r"|(?<![\w~])/(?:root|opt)(?:/[^\s]*)?"
    r"|(?<![A-Za-z0-9_])[A-Za-z]:\\[^\s]+"
)
SECRETS = [
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]

ALLOWED_FRONTMATTER_KEYS = frozenset(
    {"name", "description", "version", "author", "license", "platforms", "metadata"}
)
REQUIRED_FRONTMATTER_KEYS = (
    "name",
    "description",
    "version",
    "author",
    "license",
    "platforms",
    "metadata",
)
EXPECTED_AUTHOR = "fhfqndj"
EXPECTED_LICENSE = "MIT"
KEBAB_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GROUP_LINE = re.compile(r"^  group:[ \t]*(\S+)[ \t]*$", re.M)
SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
MAX_DESCRIPTION = 60

AUX_MD_NAME = re.compile(r"^[a-z0-9][a-z0-9.-]*\.md$")
AUX_MD_ALLOW = frozenset({"EXAMPLES.md"})

TRIGGER_TOKENS = frozenset(
    {
        "открывать",
        "открывается",
        "открыть",
        "когда",
        "применять",
        "применяется",
        "use",
        "when",
        "using",
        "использовать",
        "используй",
    }
)
STOPWORDS = frozenset(
    {
        "и", "в", "во", "на", "для", "по", "с", "со", "что", "как", "не", "а",
        "из", "при", "это", "или", "о", "об", "от", "до", "у", "к", "же", "ли",
        "то", "нужно", "нужен", "надо", "его", "её", "их", "который", "которая",
        "которые", "если", "чем", "над", "под", "без", "через", "между", "также",
        "уже", "есть",
        "the", "a", "an", "of", "for", "to", "and", "or", "in", "on", "with",
        "use", "using", "this", "that", "it", "is", "are", "be", "by", "as",
        "at", "from", "into", "your", "you",
    }
)
DESCRIPTION_ERROR_JACCARD = 0.85
DESCRIPTION_WARN_JACCARD = 0.60

TRIGGER_PREFIX = re.compile(
    r"^(открывать|открывается|использовать|используй|применять|применяется|use when|use|перед|если|когда)\b",
    re.I,
)
WHEN_SECTION = re.compile(
    r"^#{1,4}\s+(?:когда открывать|when to use|когда применять)\b", re.I | re.M
)
SKILL_LINE_BUDGET = 250

TRIGGER_BASELINE: frozenset[str] = frozenset()
WHEN_SECTION_BASELINE: frozenset[str] = frozenset()
LINE_BUDGET_BASELINE: frozenset[str] = frozenset()
REFERENCE_ORPHAN_BASELINE: frozenset[str] = frozenset()

GROUPS = frozenset({"core", "git", "code"})

INDEX_SUMMARY = re.compile(
    r"Всего навыков:\s*\*\*(\d+)\*\*\s*[—–-]\s*L1:\s*\*\*(\d+)\*\*\s*,\s*L2:\s*\*\*(\d+)\*\*"
)
INDEX_ROW = re.compile(
    r"^\|\s*\[`([^`]+)`\]\(skills/([a-z0-9-]+)/SKILL\.md\)\s*\|\s*(L[12])\s*\|",
    re.M,
)
INDEX_ROW_FILES = re.compile(
    r"^\|\s*\[`([^`]+)`\]\(skills/([a-z0-9-]+)/SKILL\.md\)\s*\|"
    r"\s*L[12]\s*\|[^|\n]*\|\s*(\d+)\s*\|\s*$",
    re.M,
)
ROLE_TABLE_ROW = re.compile(
    r"^\|\s*\[`([a-z0-9-]+)\.md`\]\(([a-z0-9-]+)\.md\)", re.M
)
LINK_TARGET = re.compile(r"\]\(([^)\n]+)\)")
LINK_EXTERNAL = ("http", "mailto", "MEDIA")
RELATED_LINE = re.compile(r"^([ \t]*)related_skills:[ \t]*(.*)$")

ROLE_REQUIRED_SECTIONS = (
    ("Что делает", re.compile(r"\bчто делает\b")),
    ("Что дать в `context`", re.compile(r"\bчто дать в context\b")),
    ("Формат ответа", re.compile(r"\bформат ответа\b")),
    ("Чего не делает", re.compile(r"\bчего не делает\b")),
)

ROOT_MANIFEST = "plugin.json"
OTHER_MANIFESTS = (
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".agents/plugins/marketplace.json",
)
MARKETPLACE_MANIFESTS = frozenset(
    {".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"}
)


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    skills: int = 0
    baseline: Counter[str] = field(default_factory=Counter)
    baseline_items: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    details: list[str] = field(default_factory=list)


def split_frontmatter(text: str) -> tuple[list[str] | None, str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i], "\n".join(lines[i + 1 :])
    return None, text


def _unquote(value: str) -> tuple[str, str | None]:
    if not value:
        return "", None
    quote = value[0]
    if quote in "\"'":
        if len(value) < 2 or not value.endswith(quote):
            return value, "незакрытая кавычка"
        return value[1:-1], None
    if ": " in value:
        return value, "двоеточие с пробелом в значении без кавычек"
    return value, None


def parse_frontmatter(
    text: str,
    allowed_keys: frozenset[str] | None = None,
    strict_values: bool = True,
) -> tuple[dict[str, str], list[str]]:
    lines, _ = split_frontmatter(text)
    if lines is None:
        return {}, ["нет YAML-frontmatter"]
    meta: dict[str, str] = {}
    errors: list[str] = []
    for raw in lines:
        if "\t" in raw:
            errors.append("таб в YAML-frontmatter (нужны пробелы)")
            continue
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw.startswith((" ", "-")):
            continue
        if ":" not in raw:
            errors.append(f"строка YAML без key: value — {raw.strip()!r}")
            continue
        key, value = raw.split(":", 1)
        key, value = key.strip(), value.strip()
        if not key:
            errors.append("пустой ключ в YAML-frontmatter")
            continue
        if key in meta:
            errors.append(f"дубль ключа {key} в YAML-frontmatter")
            continue
        if allowed_keys is not None and key not in allowed_keys:
            errors.append(f"недопустимый ключ frontmatter: {key}")
        if strict_values:
            cleaned, quote_error = _unquote(value)
            if quote_error:
                errors.append(f"{key}: {quote_error}")
        elif len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            cleaned = value[1:-1]
        else:
            cleaned = value
        meta[key] = cleaned
    return meta, errors


def skill_group(text: str) -> str:
    lines, _ = split_frontmatter(text)
    if lines is None:
        return ""
    match = GROUP_LINE.search("\n".join(lines))
    return match.group(1).strip("\"'") if match else ""


def parse_inline_list(value: str) -> list[str] | None:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return None
    inner = value[1:-1].strip()
    if not inner:
        return []
    items = [item.strip().strip("\"'") for item in inner.split(",")]
    return [item for item in items if item]


def metadata_value(text: str, key: str) -> str | None:
    lines, _ = split_frontmatter(text)
    if lines is None:
        return None
    pattern = re.compile(rf"^[ \t]+{re.escape(key)}:[ \t]*(.*)$")
    for line in lines:
        match = pattern.match(line)
        if match:
            return match.group(1).strip()
    return None


def related_skills_from_frontmatter(text: str) -> tuple[list[str], list[str]]:
    lines, _ = split_frontmatter(text)
    if lines is None:
        return [], []
    for index, raw in enumerate(lines):
        match = RELATED_LINE.match(raw)
        if not match:
            continue
        indent = len(match.group(1))
        value = match.group(2).strip()
        if value:
            items = parse_inline_list(value)
            if items is None:
                return [], [
                    "related_skills должен быть inline-списком [...] "
                    "или блочным списком"
                ]
            return items, []
        items: list[str] = []
        for following in lines[index + 1 :]:
            if not following.strip():
                continue
            item = re.match(r"^([ \t]*)-[ \t]*(.*)$", following)
            if not item or len(item.group(1)) <= indent:
                break
            name = item.group(2).strip().strip("\"'")
            if name:
                items.append(name)
        return items, []
    return [], []


def check_skill_frontmatter(
    rel: str, dirname: str, text: str
) -> tuple[dict[str, str], list[str]]:
    meta, raw_errors = parse_frontmatter(text, ALLOWED_FRONTMATTER_KEYS)
    errors = [f"{rel}: {error}" for error in raw_errors]
    if not meta:
        return meta, errors
    for key in REQUIRED_FRONTMATTER_KEYS:
        if key == "metadata":
            if key not in meta:
                errors.append(f"{rel}: пустое обязательное поле {key}")
        elif not meta.get(key):
            errors.append(f"{rel}: пустое обязательное поле {key}")
    author = meta.get("author", "")
    if author and author != EXPECTED_AUTHOR:
        errors.append(f"{rel}: author={author}, а нужен {EXPECTED_AUTHOR}")
    license_name = meta.get("license", "")
    if license_name and license_name != EXPECTED_LICENSE:
        errors.append(
            f"{rel}: license={license_name}, а нужен {EXPECTED_LICENSE}"
        )
    platforms_value = meta.get("platforms", "")
    if platforms_value:
        platforms = parse_inline_list(platforms_value)
        if platforms is None:
            errors.append(
                f"{rel}: platforms должен быть непустым inline-списком "
                f"[linux, macos, windows]"
            )
        elif not platforms:
            errors.append(
                f"{rel}: platforms пуст — нужен хотя бы один в inline-списке"
            )
    group = skill_group(text)
    if not group:
        errors.append(
            f"{rel}: нет metadata.group (нужна группа: core, git или code)"
        )
    elif group not in GROUPS:
        errors.append(
            f"{rel}: metadata.group={group} не входит в группы core, git, code"
        )
    tags_value = metadata_value(text, "tags")
    if tags_value is None:
        errors.append(
            f"{rel}: нет metadata.tags (нужен непустой inline-список)"
        )
    else:
        tags = parse_inline_list(tags_value)
        if tags is None:
            errors.append(
                f"{rel}: metadata.tags должен быть inline-списком [...]"
            )
        elif not tags:
            errors.append(
                f"{rel}: metadata.tags пуст — нужен хотя бы один тег"
            )
    name = meta.get("name", "")
    if name:
        if not KEBAB_NAME.match(name):
            errors.append(f"{rel}: name={name} не kebab-case")
        if name != dirname:
            errors.append(f"{rel}: name={name} не совпадает с каталогом {dirname}")
    version = meta.get("version", "")
    if version and not SEMVER.match(version):
        errors.append(f"{rel}: version={version} не semver (нужно x.y.z)")
    description = meta.get("description", "")
    if description and len(description) > MAX_DESCRIPTION:
        errors.append(
            f"{rel}: description длиннее {MAX_DESCRIPTION} символов "
            f"({len(description)}) — он уходит в системный промпт"
        )
    return meta, errors


def description_tokens(description: str) -> set[str]:
    text = description.strip().strip("\"'").lower().replace("ё", "е")
    tokens = re.findall(r"[a-zа-я0-9]+", text)
    return {
        token
        for token in tokens
        if token not in TRIGGER_TOKENS
        and token not in STOPWORDS
        and len(token) >= 3
    }


def jaccard(left: set[str], right: set[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 0.0


def description_collisions(
    descriptions: dict[str, str],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    tokens = {name: description_tokens(desc) for name, desc in descriptions.items()}
    for left, right in combinations(sorted(tokens), 2):
        score = jaccard(tokens[left], tokens[right])
        if score >= DESCRIPTION_ERROR_JACCARD:
            errors.append(
                f"{left} и {right}: description почти дублируются "
                f"(Jaccard {score:.2f}) — развести триггеры"
            )
        elif score >= DESCRIPTION_WARN_JACCARD:
            warnings.append(
                f"{left} и {right}: description похожи (Jaccard {score:.2f})"
            )
    return errors, warnings


def trigger_warning(rel: str, description: str) -> str | None:
    if TRIGGER_PREFIX.match(description.strip().strip("\"'")):
        return None
    first = description.strip().strip("\"'").split()
    return (
        f"{rel}: description не начинается с триггера "
        f"(«{first[0] if first else ''}») — агент не поймёт, когда открывать"
    )


def repo_text_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(
            name for name in dirnames if name not in HYGIENE_SKIP_DIRS
        )
        base = Path(dirpath)
        for name in sorted(filenames):
            path = base / name
            parts = path.relative_to(root).parts
            if (
                path.suffix in TEXT_EXT
                or name in TEXT_NAMES
                or ".githooks" in parts
            ):
                yield path


def strip_code(text: str) -> str:
    return re.sub(r"`[^`]*`", "", re.sub(r"```.*?```", "", text, flags=re.S))


def hygiene_errors(rel: str, text: str) -> list[str]:
    errors: list[str] = []
    for match in ABS_PATH.finditer(strip_code(text)):
        errors.append(f"{rel}: абсолютный путь {match.group(0)}")
    for pattern in SECRETS:
        if pattern.search(text):
            errors.append(f"{rel}: похоже на секрет ({pattern.pattern[:24]}…)")
    return errors


def link_target_path(target: str) -> str:
    target = target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1].strip()
    if not target:
        return ""
    if target.startswith(LINK_EXTERNAL):
        return ""
    path = re.split(r"[#?]", target, maxsplit=1)[0]
    return path.strip()


def broken_link_errors(rel: str, path: Path, text: str) -> list[str]:
    errors: list[str] = []
    prose = strip_code(text)
    for target in LINK_TARGET.findall(prose):
        local = link_target_path(target)
        if not local:
            continue
        if not (path.parent / local).resolve().exists():
            errors.append(f"{rel}: битая ссылка {local}")
    return errors


def junk_errors(repo: Path, skills: Path) -> list[str]:
    errors: list[str] = []
    for dirpath, dirnames, filenames in os.walk(skills):
        root = Path(dirpath)
        for name in sorted(dirnames):
            if name in JUNK_DIRS:
                path = root / name
                errors.append(f"{path.relative_to(repo)}: мусорный каталог {name}/")
        dirnames[:] = [name for name in dirnames if name not in JUNK_DIRS]
        for name in sorted(filenames):
            path = root / name
            if name in JUNK_NAMES or path.suffix in JUNK_SUFFIXES:
                errors.append(f"{path.relative_to(repo)}: мусорный файл")
    return errors


def empty_dir_errors(repo: Path, skills: Path) -> list[str]:
    errors: list[str] = []
    for dirpath, dirnames, filenames in os.walk(skills):
        path = Path(dirpath)
        if path == skills or path.name in JUNK_DIRS:
            continue
        if not dirnames and not filenames:
            errors.append(f"{path.relative_to(repo)}: пустой каталог")
    return errors


def aux_name_errors(repo: Path, skills: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(skills.rglob("*.md")):
        if path.name in ("SKILL.md", *AUX_MD_ALLOW):
            continue
        if not AUX_MD_NAME.match(path.name):
            errors.append(
                f"{path.relative_to(repo)}: имя вспомогательного файла "
                f"{path.name} — строчные латинские, цифры, точки, дефисы"
            )
    return errors


def role_headings(text: str) -> list[str]:
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    headings = re.findall(r"^##\s+(.+?)\s*$", prose, re.M)
    return [re.sub(r"[`*_]+", "", heading).strip().lower() for heading in headings]


def check_role(rel: str, stem: str, text: str) -> list[str]:
    meta, raw_errors = parse_frontmatter(text, strict_values=False)
    errors = [f"{rel}: {error}" for error in raw_errors]
    if meta:
        name = meta.get("name", "")
        if not name:
            errors.append(f"{rel}: пустое поле name")
        elif name != stem:
            errors.append(f"{rel}: name={name} не совпадает с файлом {stem}.md")
    headings = role_headings(text)
    for label, pattern in ROLE_REQUIRED_SECTIONS:
        if not any(pattern.search(heading) for heading in headings):
            errors.append(f"{rel}: нет раздела «{label}»")
    if not any(heading.startswith("composition") for heading in headings):
        errors.append(f"{rel}: нет раздела «Composition»")
    elif not headings[-1].startswith("composition"):
        errors.append(f"{rel}: «Composition» должен быть последним разделом")
    return errors


def parity_errors(
    skill_names: set[str],
    index_text: str,
    role_readme: str,
    role_names: set[str],
) -> list[str]:
    errors: list[str] = []
    summary = INDEX_SUMMARY.search(index_text)
    if not summary:
        errors.append("INDEX.md: нет итоговой строки «Всего навыков: N — L1: M, L2: K»")
    else:
        total, l1, l2 = (int(value) for value in summary.groups())
        if total != len(skill_names):
            errors.append(f"INDEX.md: всего {total}, а навыков на диске {len(skill_names)}")
        if l1 + l2 != total:
            errors.append(f"INDEX.md: L1 {l1} + L2 {l2} ≠ всего {total}")
        rows = INDEX_ROW.findall(index_text)
        actual_l1 = sum(1 for _, _, level in rows if level == "L1")
        actual_l2 = sum(1 for _, _, level in rows if level == "L2")
        if (actual_l1, actual_l2) != (l1, l2):
            errors.append(
                f"INDEX.md: в строке L1 {l1}/L2 {l2}, а в таблице "
                f"L1 {actual_l1}/L2 {actual_l2}"
            )

    table_roles = {
        name for name, target in ROLE_TABLE_ROW.findall(role_readme) if name == target
    }
    for name in sorted(role_names - table_roles):
        errors.append(f"subagents/README.md: роль {name}.md не описана в таблице")
    for name in sorted(table_roles - role_names):
        errors.append(f"subagents/README.md: строка про {name}.md, а файла нет")
    return errors


def plural(count: int, one: str, few: str, many: str) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return one
    if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14:
        return few
    return many


def skill_file_count(skill_dir: Path) -> int:
    total = 0
    for path in skill_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.name in JUNK_NAMES or path.suffix in JUNK_SUFFIXES:
            continue
        if any(part in JUNK_DIRS for part in path.parts):
            continue
        total += 1
    return total


def file_count_errors(index_text: str, skill_dirs: dict[str, Path]) -> list[str]:
    errors: list[str] = []
    counts = {
        match.group(1): int(match.group(3))
        for match in INDEX_ROW_FILES.finditer(index_text)
    }
    listed = {name for name, _, _ in INDEX_ROW.findall(index_text)}
    for name in sorted(listed - set(counts)):
        if name in skill_dirs:
            errors.append(
                f"INDEX.md: {name}: в колонке «Файлов» не число — "
                f"фактически {skill_file_count(skill_dirs[name])}"
            )
    for name, declared in sorted(counts.items()):
        if name not in skill_dirs:
            continue
        actual = skill_file_count(skill_dirs[name])
        if actual != declared:
            errors.append(
                f"INDEX.md: {name}: в колонке «Файлов» {declared}, "
                f"фактически {actual}"
            )
    return errors


def one_way_related_pairs(
    related: dict[str, set[str]],
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for name, refs in related.items():
        for ref in refs:
            if ref == name or ref not in related:
                continue
            if name not in related[ref]:
                pairs.append((name, ref))
    return sorted(pairs)


def routing_coverage(repo: Path, skill_names: set[str], report: Report) -> None:
    cases_dir = repo / "evals" / "routing"
    covered = (
        {path.stem for path in cases_dir.glob("*.json") if path.is_file()}
        if cases_dir.is_dir()
        else set()
    )
    missing = sorted(skill_names - covered)
    if not missing:
        return
    report.notes.append(
        f"routing-кейсов нет: {len(missing)} (из {len(skill_names)})"
    )
    report.baseline_items.extend(
        f"routing-кейс отсутствует: {name}" for name in missing
    )


def load_manifest(path: Path) -> tuple[dict | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        return None, f"не читается: {error}"
    except json.JSONDecodeError as error:
        return None, f"битый JSON: {error.msg} (строка {error.lineno})"
    if not isinstance(data, dict):
        return None, "на верхнем уровне ожидается JSON-объект"
    return data, None


def manifest_version(data: dict, rel: str) -> str | None:
    if rel in MARKETPLACE_MANIFESTS:
        plugins = data.get("plugins")
        if isinstance(plugins, list) and plugins and isinstance(plugins[0], dict):
            version = plugins[0].get("version")
            return version if isinstance(version, str) else None
        return None
    version = data.get("version")
    return version if isinstance(version, str) else None


def manifest_skill_targets(data: dict) -> list[str]:
    skills = data.get("skills")
    if isinstance(skills, str):
        return [skills]
    if isinstance(skills, list):
        return [item for item in skills if isinstance(item, str)]
    return []


def manifest_plugin_roots(data: dict, rel: str) -> list[str]:
    targets: list[str] = []
    source = data.get("source")
    if isinstance(source, dict) and isinstance(source.get("path"), str):
        targets.append(source["path"])
    if rel in MARKETPLACE_MANIFESTS:
        plugins = data.get("plugins")
        if isinstance(plugins, list) and plugins and isinstance(plugins[0], dict):
            plugin_source = plugins[0].get("source")
            if isinstance(plugin_source, dict) and isinstance(
                plugin_source.get("path"), str
            ):
                targets.append(plugin_source["path"])
    return targets


def resolve_manifest_path(repo: Path, raw: str) -> tuple[Path | None, str | None]:
    if Path(raw).is_absolute():
        return None, f"путь {raw!r} — абсолютный, нужен относительный"
    normalized = raw.strip().removeprefix("./").rstrip("/") or "."
    return repo / normalized, None


def manifest_path_errors(repo: Path, rel: str, data: dict) -> list[str]:
    errors: list[str] = []
    for raw in manifest_skill_targets(data):
        target, problem = resolve_manifest_path(repo, raw)
        if problem or target is None:
            errors.append(f"{rel}: {problem}")
            continue
        if not target.is_dir():
            errors.append(f"{rel}: путь к навыкам {raw!r} не существует")
        elif not any(target.glob("*/SKILL.md")):
            errors.append(f"{rel}: в каталоге навыков {raw!r} нет ни одного SKILL.md")
    for raw in manifest_plugin_roots(data, rel):
        target, problem = resolve_manifest_path(repo, raw)
        if problem or target is None:
            errors.append(f"{rel}: {problem}")
            continue
        if not target.is_dir():
            errors.append(f"{rel}: путь плагина {raw!r} не существует")
        elif not (target / "plugin.json").is_file() and not (target / "skills").is_dir():
            errors.append(
                f"{rel}: в каталоге плагина {raw!r} нет ни plugin.json, ни skills/"
            )
    return errors


def missing_manifest_errors(repo: Path) -> list[str]:
    return [
        f"{rel}: нет манифеста (при корневом {ROOT_MANIFEST} обязателен)"
        for rel in OTHER_MANIFESTS
        if not (repo / rel).is_file()
    ]


def manifest_errors(repo: Path) -> list[str]:
    root_path = repo / ROOT_MANIFEST
    if not root_path.is_file():
        return []
    errors = missing_manifest_errors(repo)
    root, load_error = load_manifest(root_path)
    if root is None:
        return [f"{ROOT_MANIFEST}: {load_error}", *errors]
    name = root.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append(f"{ROOT_MANIFEST}: пустое поле name")
    root_version = manifest_version(root, ROOT_MANIFEST)
    if not root_version:
        errors.append(f"{ROOT_MANIFEST}: пустое поле version")
    elif not SEMVER.match(root_version):
        errors.append(f"{ROOT_MANIFEST}: version={root_version} не semver (нужно x.y.z)")
    errors.extend(manifest_path_errors(repo, ROOT_MANIFEST, root))
    if not root_version:
        return errors
    for rel in OTHER_MANIFESTS:
        path = repo / rel
        if not path.is_file():
            continue
        data, sibling_error = load_manifest(path)
        if data is None:
            errors.append(f"{rel}: {sibling_error}")
            continue
        version = manifest_version(data, rel)
        if not version:
            errors.append(f"{rel}: нет версии (version или plugins[0].version)")
        elif version != root_version:
            errors.append(
                f"{rel}: version={version}, а в {ROOT_MANIFEST} {root_version}"
            )
        errors.extend(manifest_path_errors(repo, rel, data))
    return errors


def budget_warnings(
    rel: str, name: str, text: str, report: Report
) -> None:
    lines = len(text.splitlines())
    if lines <= SKILL_LINE_BUDGET:
        return
    if name in LINE_BUDGET_BASELINE:
        report.baseline["SKILL.md >250 строк"] += 1
        report.baseline_items.append(f"SKILL.md >300: {name} ({lines} строк)")
        return
    report.warnings.append(
        f"{rel}: SKILL.md {lines} строк (> {SKILL_LINE_BUDGET}) — разрезать в references/"
    )


def reference_orphans(
    repo: Path, skill_dir: Path, text: str, report: Report
) -> None:
    references = skill_dir / "references"
    if not references.is_dir():
        return
    for path in sorted(references.rglob("*.md")):
        rel_in_skill = path.relative_to(skill_dir).as_posix()
        parents = {
            parent.relative_to(skill_dir).as_posix() + "/"
            for parent in path.parents
            if parent != skill_dir
            and parent != references
            and references in parent.parents
        }
        reachable = path.name in text or rel_in_skill in text
        reachable = reachable or any(parent in text for parent in parents)
        if reachable:
            continue
        rel = path.relative_to(repo).as_posix()
        if rel.removeprefix("skills/") in REFERENCE_ORPHAN_BASELINE:
            report.baseline["недостижимых references"] += 1
            report.baseline_items.append(f"orphan reference: {rel}")
            continue
        report.warnings.append(f"{rel}: {rel_in_skill} недостижим из SKILL.md")


def run(repo: Path = REPO) -> Report:
    report = Report()
    skills = repo / "skills"
    if not skills.is_dir():
        report.errors.append("нет каталога skills/")
        return report
    readme = repo / "README.md"
    index = repo / "INDEX.md"
    subagents = repo / "subagents"

    skill_dirs: list[tuple[Path, Path]] = []
    skill_names: dict[str, Path] = {}
    for skill_md in sorted(skills.rglob("SKILL.md")):
        rel_md = skill_md.relative_to(skills)
        if len(rel_md.parts) == 2:
            continue
        report.errors.append(
            f"{skill_md.parent.relative_to(repo)}: навык должен лежать плоско: "
            f"skills/<навык>/SKILL.md"
        )
    for skill_md in sorted(skills.glob("*/SKILL.md")):
        skill_dir = skill_md.parent
        rel = skill_dir.relative_to(skills)
        name = skill_dir.name
        if name in skill_names:
            report.errors.append(
                f"дубль имени навыка: {name} ({skill_names[name]} и {skill_dir})"
            )
        skill_names[name] = skill_dir
        skill_dirs.append((rel, skill_md))
    report.skills = len(skill_names)

    descriptions: dict[str, str] = {}
    related_map: dict[str, set[str]] = {}
    for rel, skill_md in skill_dirs:
        name = skill_md.parent.name
        text = skill_md.read_text(errors="ignore")
        meta, errors = check_skill_frontmatter(rel.as_posix(), name, text)
        report.errors.extend(errors)
        if not meta:
            continue
        description = meta.get("description", "")
        if description:
            descriptions[name] = description
        related_map[name] = set()
        related, related_errors = related_skills_from_frontmatter(text)
        for error in related_errors:
            report.errors.append(f"{rel}: {error}")
        for ref in related:
            if not ref:
                continue
            if ref not in skill_names:
                report.errors.append(
                    f"{rel}: related_skills ссылается на {ref}, которого нет"
                )
            elif ref != name:
                related_map[name].add(ref)
        budget_warnings(rel.as_posix(), name, text, report)
        reference_orphans(repo, skill_md.parent, text, report)
        if description:
            if name in TRIGGER_BASELINE:
                report.baseline["description без триггера"] += 1
                report.baseline_items.append(f"description без триггера: {name}")
            else:
                warning = trigger_warning(rel.as_posix(), description)
                if warning:
                    report.warnings.append(warning)
        if not WHEN_SECTION.search(strip_code(text)):
            if name in WHEN_SECTION_BASELINE:
                report.baseline["без раздела «когда»"] += 1
                report.baseline_items.append(f"без раздела «когда»: {name}")
            else:
                report.warnings.append(
                    f"{rel}: нет раздела «Когда открывать»/«When to Use»/"
                    f"«Когда применять»"
                )

    collision_errors, collision_warnings = description_collisions(descriptions)
    report.errors.extend(collision_errors)
    report.warnings.extend(collision_warnings)

    one_way = one_way_related_pairs(related_map)
    if one_way:
        report.notes.append(
            f"related_skills: односторонних ссылок {len(one_way)} "
            f"(норма; список — с -v)"
        )
        report.details.extend(
            f"related_skills: {a} → {b}, обратной ссылки нет" for a, b in one_way
        )

    for path in repo_text_files(repo):
        rel = path.relative_to(repo)
        text = path.read_text(errors="ignore")
        report.errors.extend(hygiene_errors(rel.as_posix(), text))
        if path.suffix == ".md":
            report.errors.extend(broken_link_errors(rel.as_posix(), path, text))

    report.errors.extend(junk_errors(repo, skills))
    report.errors.extend(empty_dir_errors(repo, skills))
    report.errors.extend(aux_name_errors(repo, skills))

    roles: list[Path] = []
    if not subagents.is_dir():
        report.errors.append("нет каталога subagents/")
    else:
        roles = sorted(path for path in subagents.glob("*.md") if path.name != "README.md")
        for path in roles:
            report.errors.extend(
                check_role(
                    path.relative_to(repo).as_posix(),
                    path.stem,
                    path.read_text(errors="ignore"),
                )
            )
    role_readme = subagents / "README.md"
    if not role_readme.is_file():
        report.errors.append("нет subagents/README.md")
    role_names = {path.stem for path in roles}

    if not readme.is_file():
        report.errors.append("нет README.md")
    if not index.is_file():
        report.errors.append("нет INDEX.md")
    else:
        index_text = index.read_text(errors="ignore")
        named = set(
            re.findall(r"\]\(skills/([a-z0-9-]+)/SKILL\.md\)", index_text)
        )
        for name in sorted(set(skill_names) - named):
            report.errors.append(f"INDEX.md: навык {name} не описан в каталоге")
        for name in sorted(named - set(skill_names)):
            report.errors.append(f"INDEX.md: строка про {name}, а навыка нет")
        for target in re.findall(
            r"\]\(((?:skills|docs|subagents)/[^)#]+)\)", index_text
        ):
            if not (repo / target).exists():
                report.errors.append(f"INDEX.md: битая ссылка {target}")
        report.errors.extend(file_count_errors(index_text, skill_names))
        if readme.is_file() and role_readme.is_file():
            report.errors.extend(
                parity_errors(
                    set(skill_names),
                    index_text,
                    role_readme.read_text(errors="ignore"),
                    role_names,
                )
            )
    routing_coverage(repo, set(skill_names), report)
    report.errors.extend(manifest_errors(repo))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--repo",
        type=Path,
        default=REPO,
        help="корень репозитория (по умолчанию — корень этого скрипта)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="показать baseline-нарушения, которые не считаются предупреждениями",
    )
    args = parser.parse_args(argv)
    report = run(args.repo.resolve())

    for warning in report.warnings:
        print(f"предупреждение: {warning}")
    for error in report.errors:
        print(f"ошибка: {error}")
    for note in report.notes:
        print(f"baseline: {note}")
    if report.baseline:
        summary = ", ".join(
            f"{label}: {count}" for label, count in sorted(report.baseline.items())
        )
        print(f"baseline (не входит в предупреждения): {summary}")
    if args.verbose:
        for item in report.baseline_items:
            print(f"  baseline: {item}")
        for item in report.details:
            print(f"  детали: {item}")
    print(
        f"\nнавыков: {report.skills}, ошибок: {len(report.errors)}, "
        f"предупреждений: {len(report.warnings)}"
    )
    if not report.errors:
        print("проверка пройдена")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
