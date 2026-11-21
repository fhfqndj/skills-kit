# Каталог навыков

Что открывать под задачу. На старте — не всё, а пять: `plan` (если задача
больше одного шага), `git-naming` (первый коммит и каждая ветка),
`local-work-hygiene` (где живут прогоны и пробы), `test-driven-development`
(если пишется логика), `verification-before-completion` (перед «готово»).
Остальное — по триггеру из таблиц.

`L1` — авторская методология, `L2` — проверенная общая практика с
зафиксированными командами и граблями. Подробности, если они не влезли в
`SKILL.md`, лежат внутри каталога навыка (`references/`, `scripts/`, `templates/`).

## Ядро — `core`

Правила самой работы: как планировать, делегировать, держать контекст, где жить
пробам и как обслуживать библиотеку навыков. Открывается первым.

| Навык | Ур. | Когда открывать | Файлов |
|---|---|---|---|
| [`brainstorming`](skills/brainstorming/SKILL.md) | L1 | цель ещё не ясна: выяснить, что строить, и согласовать дизайн | 2 |
| [`agent-context`](skills/agent-context/SKILL.md) | L1 | агенту не хватает контекста: длинная сессия, передача работы | 2 |
| [`delegating-to-subagents`](skills/delegating-to-subagents/SKILL.md) | L1 | задача делится на параллельные куски: бриф, приёмка, границы | 5 |
| [`local-work-hygiene`](skills/local-work-hygiene/SKILL.md) | L1 | прогоны, клоны и пробы: где им жить и что не трогать | 3 |
| [`merge-reconciler`](skills/merge-reconciler/SKILL.md) | L1 | несколько агентов правили одну ветку и конфликтуют | 1 |
| [`plan`](skills/plan/SKILL.md) | L1 | задача больше одного шага: сначала план, потом код | 4 |
| [`quality-bar`](skills/quality-bar/SKILL.md) | L1 | планка качества проекта не записана: ратчет и защита от ослабления | 4 |
| [`project-context`](skills/project-context/SKILL.md) | L1 | проект ведёт контекст в `local/`: паспорт, план, журнал, грабли | 1 |
| [`customer-spec-review`](skills/customer-spec-review/SKILL.md) | L1 | пришло ТЗ заказчика: разобрать до кода, найти дырки, оценить | 1 |
| [`skill-library-maintenance`](skills/skill-library-maintenance/SKILL.md) | L1 | навык создаётся, правится или курируется: формат, дедуп, язык | 3 |
| [`skill-sourcing`](skills/skill-sourcing/SKILL.md) | L1 | нужен готовый навык, промпт или автоматизация: поиск до своей работы | 2 |
| [`mcp-search`](skills/mcp-search/SKILL.md) | L1 | нужен готовый MCP-сервер или подключение | 2 |
| [`subagent-driven-development`](skills/subagent-driven-development/SKILL.md) | L1 | утверждённый план исполняется задача за задачей через субагентов | 1 |
| [`using-skills-kit`](skills/using-skills-kit/SKILL.md) | L1 | начало любой задачи: сначала проверить каталог навыков | 3 |
| [`verification-before-completion`](skills/verification-before-completion/SKILL.md) | L1 | перед «готово / исправлено / проходит»: свежее доказательство | 2 |

## Git и GitHub — `git`

Имена, ветки, PR, ревью, доступ агента к репозиторию.

| Навык | Ур. | Когда открывать | Файлов |
|---|---|---|---|
| [`git-naming`](skills/git-naming/SKILL.md) | L1 | первый коммит и каждая ветка: тип, область, формат | 4 |
| [`git-worktrees`](skills/git-worktrees/SKILL.md) | L2 | вторая копия репозитория под ветку: параллельные агенты | 1 |
| [`github-agent-access`](skills/github-agent-access/SKILL.md) | L2 | агенту нужен доступ к GitHub: scoped-токен, границы | 2 |
| [`github-auth`](skills/github-auth/SKILL.md) | L2 | доступ к GitHub не настроен: токен, SSH, gh login | 7 |
| [`github-code-review`](skills/github-code-review/SKILL.md) | L2 | ревью чужого PR: диффы, inline-комментарии | 5 |
| [`github-pr-workflow`](skills/github-pr-workflow/SKILL.md) | L2 | работа через PR, issues и релизы: ветка → PR → CI → merge | 12 |

## Код и качество — `code`

Как писать, чинить и проверять код до того, как его увидит человек.

| Навык | Ур. | Когда открывать | Файлов |
|---|---|---|---|
| [`codebase-reconnaissance`](skills/codebase-reconnaissance/SKILL.md) | L2 | код чужой или незнакомый: read-only разбор до правок | 3 |
| [`requesting-code-review`](skills/requesting-code-review/SKILL.md) | L2 | перед коммитом или PR: security-скан, гейты, автофикс | 6 |
| [`systematic-debugging`](skills/systematic-debugging/SKILL.md) | L2 | баг непонятен: воспроизвести → изолировать → причина → фикс | 5 |
| [`test-driven-development`](skills/test-driven-development/SKILL.md) | L2 | пишется логика: тест раньше кода | 4 |

Всего навыков: **25** — L1: **16**, L2: **9**.

## Порядок первого дня

1. `local-work-hygiene` — где живёт проект, где пробы, что не трогать.
2. `git-naming` — имя ветки и первого коммита.
3. `plan` — план и согласование до кода.
4. `codebase-reconnaissance` — если код чужой.
5. `test-driven-development` — первая логика.
6. `requesting-code-review` — перед первым PR.
7. `github-pr-workflow` — PR, CI, merge.

## Связанное

- [README](README.md) — принципы отбора, архитектура, установка.
- [subagents](subagents/README.md) — роли для делегирования.
