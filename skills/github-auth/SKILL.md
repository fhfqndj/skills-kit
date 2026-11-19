---
name: github-auth
description: "Открывать, когда настраивается доступ к GitHub."
version: 1.2.2
author: fhfqndj
license: MIT
platforms: [linux, macos, windows]
metadata:
  group: git
  tags: [GitHub, Authentication, Git, gh-cli, SSH, Setup]
  related_skills: [github-pr-workflow, github-code-review, github-agent-access]
---

# Настройка доступа к GitHub

Навык про то, как выдать агенту доступ к репозиториям GitHub, PR, issues и CI. Два пути:

- **`git` (есть всегда)** — HTTPS-токен (personal access token) или SSH-ключ;
- **`gh` CLI (если установлен)** — более широкий доступ к API GitHub и проще с авторизацией.

## Когда открывать

Открывать, когда агенту нужен доступ к GitHub: первый вход на машине, выпуск и хранение токена, SSH-ключ, починка 401/403/404, доступ сервера выката к репозиторию и GHCR.

Не открывать, когда доступ уже настроен, а задача — issues, PR, ревью или настройки репозитория: это `github-pr-workflow`, `github-code-review`.

## С чего начать: проверка

Когда просят работать с GitHub, сначала прогнать:

```bash
# Check what's available
git --version
gh --version 2>/dev/null || echo "gh not installed"

# Check if already authenticated
gh auth status 2>/dev/null || echo "gh not authenticated"
git config --global credential.helper 2>/dev/null || echo "no git credential helper"
```

**Дерево решений:**

1. `gh auth status` показывает авторизацию → всё готово, дальше использовать `gh`.
2. `gh` установлен, но не авторизован → метод «gh auth» ниже.
3. `gh` не установлен → метод «только git» ниже (sudo не нужен).

---

## Метод 1: только git (без gh и без sudo)

Работает на любой машине, где есть `git`. Права root не нужны.

### Вариант A: HTTPS с personal access token (рекомендуется)

Самый переносимый способ: работает везде, настройка SSH не нужна.

**Шаг 1. Создать personal access token.** Пользователь открывает **https://github.com/settings/tokens**: «Generate new token (classic)», имя вида «agent-<имя-машины>», scopes:

- `repo` — полный доступ к репозиторию: чтение, запись, push, PR;
- `workflow` — запуск и управление GitHub Actions;
- `read:org` — если работа идёт с репозиториями организации;
- срок жизни (90 дней — разумное умолчание); скопировать: второй раз токен не показывается.

**Шаг 2. Настроить хранение токена.** Если `gh` всё же установлен, сначала пусть helper настроит он — `gh auth setup-git` (предпочтительный способ): токен лежит в его защищённом хранилище, а git получает helper, который отдаёт креды; ни `.git/config`, ни `~/.git-credentials` токена не содержат.

```bash
gh auth setup-git

# Test operation that triggers auth — with a helper in place this should not prompt
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

**Если `gh` нет — helper `cache`** (креды живут в памяти, на диск не попадают):

```bash
# Cache in memory for 8 hours (28800 seconds) instead of saving to disk
git config --global credential.helper 'cache --timeout=28800'

# Username: <their-github-username>
# Password: <paste the personal access token, NOT their GitHub password>
git ls-remote https://github.com/<their-username>/<any-repo>.git
```

**Fallback только по прямой просьбе: `store`.**

```bash
# "store" writes the token to ~/.git-credentials in PLAINTEXT.
# Offer it only when the owner explicitly asks for a persistent credential,
# keep the token scoped and expiring, and run `chmod 600 ~/.git-credentials`
# after the first auth. Never present this as the default.
git config --global credential.helper 'store'
```

**Не вставлять токен в URL remote.** `https://<username>:<token>@github.com/...` оставляет токен в `.git/config`, в выводе `git remote -v` и в логах; для постоянного доступа нужен credential helper (`gh auth setup-git` или `cache`).

**Шаг 3. Настроить идентичность git.** Идентичность — в репозитории, а не в глобальном конфиге владельца: глобальные значения принадлежат ему, агент их не переписывает.

```bash
git config --local user.name "Their Name"
git config --local user.email "their-email@example.com"
```

**Шаг 4. Проверить:**

```bash
# Test push access (this should work without any prompts now)
git ls-remote https://github.com/<their-username>/<any-repo>.git

# Verify identity
git config --local user.name
git config --local user.email
```

### Вариант B: доступ по SSH-ключу

Годится, когда пользователь предпочитает SSH или ключи уже заведены.

```bash
ls -la ~/.ssh/id_*.pub 2>/dev/null || echo "No SSH keys found"

# Generate an ed25519 key (modern, secure, fast)
ssh-keygen -t ed25519 -C "their-email@example.com" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub        # paste at https://github.com/settings/keys → "New SSH key"

ssh -T git@github.com
# Expected: "Hi <username>! You've successfully authenticated..."

# Rewrite HTTPS GitHub URLs to SSH automatically
git config --global url."git@github.com:".insteadOf "https://github.com/"
```

Публичный ключ добавляется на **https://github.com/settings/keys**: «New SSH key», вставить содержимое публичного ключа, заголовок вроде «agent-<имя-машины>». Идентичность — так же локально: `git config --local user.name` / `user.email`.

---

## Метод 2: авторизация через gh CLI

Если `gh` установлен, он закрывает и API, и креды git одним шагом.

### Интерактивный вход через браузер (десктоп)

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser
```

**Грабля:** когда `gh auth login` идёт через pty в фоновой сессии (особенно на Windows), ответы подавать отдельными вводами: Enter — отдельным вводом, а не `\n` в одной строке. В Windows-PTY (ConPTY/pywinpty) `\n` терминатором строки не считается, вопрос «Press Enter to open the browser» молча не завершается и вход виснет. Браузер из фоновой сессии может не открыться на десктопе — тогда device flow ниже. Механика — `references/gh-login.md`.

### Ручной OAuth device flow (TTY не нужен — проверено)

Запасной путь, когда интерактивный вход невозможен (сессия ведётся агентом, браузера нет, headless). Используется публичный client id gh; пользователь вводит код на github.com/login/device. Документированный минимум для `gh auth login --with-token` — scopes `repo,read:org,gist`; `,workflow` добавлять только если надо пушить файлы workflow.

Полный цикл (запрос device code, polling с `slow_down`/`expired_token`, переносимый таймаут вокруг `--with-token`) — `references/gh-login.md`.

### Вход по токену (headless и SSH-серверы)

```bash
echo "<THEIR_TOKEN>" | gh auth login --with-token

# Set up git credentials through gh
gh auth setup-git
```

Если `--with-token` зависает и здесь (headless без keyring — известные зависания), оборачивать в переносимый таймаут (`perl -e 'alarm 20; exec @ARGV' gh …`) и использовать запасной путь через `hosts.yml` из `references/gh-login.md`.

### Проверка

```bash
gh auth status
```

---

## Метод 3: доступ с сервера выката (клон + приватный реестр)

Два разных доступа, их не путать: **deploy-ключ** даёт серверу `git` (read-only), **PAT** даёт тянуть приватные образы из GHCR. Ни один не должен лежать в репозитории или в истории чата.

- **deploy-ключ:** `ssh-keygen -t ed25519 -N "" -f ~/.ssh/gh_deploy` на сервере; публичную часть добавить в репозиторий только на чтение — `gh api -X POST /repos/<owner>/<repo>/keys -f title=deploy-key -f key="$(cat key.pub)" -F read_only=true`. На сервере ключ подключается файлом `~/.ssh/config.d/gh_deploy` с `Include` в `~/.ssh/config`, а не перезаписью конфига: в нём алиасы и ключи других хостов.
- **GHCR:** classic PAT с единственным scope `read:packages` (fine-grained не подходит), `-u` — логин владельца токена; после деплоя `docker logout ghcr.io`. В CI токен — секрет репозитория (`gh secret set GHCR_PULL_TOKEN < файл`).

Полные команды, проверка «образ скачан, а не собран», и права `packages: write` — `references/server-deploy.md`.

---

## API GitHub без gh

Когда `gh` недоступен, полный API GitHub доступен через `curl` с personal access token — так сделаны запасные пути в остальных навыках про GitHub: `export GITHUB_TOKEN="<token>"`, дальше `curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user`.

Как достать токен из кредов git и как определить способ доступа блоком-помощником (gh / curl / none) — `references/api-without-gh.md`; готовый скрипт — `scripts/gh-env.sh`.

---

## Если не работает

| Проблема | Что делать |
|---------|----------|
| `git push` спрашивает пароль | GitHub отключил вход по паролю. В поле пароля — personal access token либо переход на SSH |
| `remote: Permission to X denied` | У токена нет scope `repo` — перевыпустить с нужными scopes |
| `fatal: Authentication failed` | Сохранённые креды устарели — `git credential reject`, затем авторизоваться заново |
| `ssh: connect to host github.com port 22: Connection refused` | SSH через порт HTTPS: `Host github.com` с `Port 443` и `Hostname ssh.github.com` в `~/.ssh/config` |
| `gh` → `HTTP 404` или GraphQL `Could not resolve to a Repository` на существующий приватный репозиторий | `gh` ходит в API от **активного** аккаунта, а у него нет доступа к организации/владельцу. Одна команда: `GH_TOKEN=$(gh auth token --user <account>) gh …`; вся сессия: `gh auth switch --user <owner>` |
| Push или клон приватного репозитория другого аккаунта отвечает 404 | Локальный helper репозитория прибить к токену владельца (команда в `references/troubleshooting.md`) |

Полная таблица с командами и разбором 404/GraphQL, креды-хелперов и нескольких аккаунтов — `references/troubleshooting.md`.

## Файлы

- `references/gh-login.md` — вход через `gh`: браузер, device flow, вход по токену, обход зависания `--with-token` без keyring.
- `references/server-deploy.md` — deploy-ключ и GHCR для сервера выката, проверка происхождения образа.
- `references/api-without-gh.md` — токен для `curl`, токен из credential store, блок определения способа доступа.
- `references/troubleshooting.md` — полная таблица симптомов, причин и команд починки доступа.
