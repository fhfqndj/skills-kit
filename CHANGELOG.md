# Изменения

Формат — по мотивам Keep a Changelog; версия в `plugin.json`, тег — `v<версия>`.

## 1.0.0 — 2026-11-19

Первый публичный релиз.

### Состав

- 27 навыков: `core` — 15, `git` — 8, `code` — 4; плоская раскладка
  `skills/<навык>/SKILL.md`, группа — в `metadata.group` и в `INDEX.md`.
- Пять ролей в `subagents/`, routing-кейсы на все 27 навыков, `CHANGELOG.md`
  и `CONTRIBUTING.md`.

### Установка и проверка

- `scripts/install.sh`: цели `claude`, `opencode`, `codex`, `gemini`, `cursor`,
  `copilot`, `kiro`, произвольный каталог; `--pack` по группам, `--verify`
  проверяет только установленное.
- `make check` — целостность репозитория и язык; `make test` — валидатор,
  установщик, упаковка, поиск и routing-эвалы.
- `scripts/check.py`: контракт frontmatter (`author`, `license`, `platforms`,
  `metadata.group`, `metadata.tags`), ссылки с анкорами, `related_skills`
  только из frontmatter, гигиена по всему репозиторию, обязательные манифесты.
- `scripts/test_packaging.py`: 27 навыков в непосредственных детях `skills/`,
  манифесты указывают на плоский каталог.
- `SKILL.md` ≤250 строк; длинные разборы — в `references/` навыка.

### Релиз

- Версия во всех пяти манифестах; тег `v<версия>`; workflow собирает
  `dist/skills-kit-<версия>.zip`, проверяет совпадение тега и версии и
  публикует ассет.
- `python3 scripts/pack.py --release` — плоская поставка и zip.

### Лицензии

- MIT (см. `LICENSE`); copyright-строки источников адаптированных методов —
  в `README.md`.
