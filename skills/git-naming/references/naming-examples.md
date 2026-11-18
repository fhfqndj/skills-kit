# Примеры сообщений коммитов и имён веток

Справочник к `SKILL.md`: готовые примеры по каждому действию и разбор соответствия префиксов.

## Примеры коммитов

```text
feat: add user authentication

fix: progress bar

ci: update github workflow

refactor: simplify api client

build: update dependencies

chore: remove unused config

docs: update installation guide

test: add login tests

style: format components
```

## Комментарий: лучше и хуже

Лучше:

```text
fix: progress bar
```

чем:

```text
fix: fix the progress bar issue
```

Лучше:

```text
feat: add user authentication
```

чем:

```text
feat: implement a completely new authentication system
```

## Примеры веток

```text
feature/new-ui

feature/user-auth

fix/progress-bar

refactor/api-client

release/v2

docs/installation

test/login-flow
```

## Важное различие

Префиксы коммитов и веток не совпадают.

Коммит:

```text
feat: add user authentication
```

Ветка:

```text
feature/user-auth
```

Коммит:

```text
fix: progress bar
```

Ветка:

```text
fix/progress-bar
```

Коммит:

```text
refactor: simplify api client
```

Ветка:

```text
refactor/api-client
```
