# Вход через gh: браузер, device flow, токен, обход зависания

Подробности к «Методу 2» из `SKILL.md`. Всё, что ниже, — про `gh auth login`; выбор между `gh` и чистым `git` описан в самом навыке.

## Интерактивный вход через браузер (десктоп)

> **ГРАБЛИ (сессии, где агент ведёт gh на Windows):** когда `gh auth login` идёт через pty в фоновом процессе, ответы подавать отдельными вводами: Enter — отдельным вводом, а не `\n` в одной строке. Enter в Windows-PTY (ConPTY/pywinpty) — это возврат каретки; один `\n` терминатором строки не считается, поэтому вопрос gh «Press Enter to open the browser» (блокирующее чтение строки) молча не завершается и вход виснет. Учесть и то, что браузер из фоновой сессии может не открыться на десктопе пользователя: тогда переходить к device flow ниже.

```bash
gh auth login
# Select: GitHub.com
# Select: HTTPS
# Authenticate via browser
```

## Ручной OAuth device flow (TTY не нужен — проверено)

Запасной путь, когда интерактивный вход невозможен (сессия ведётся агентом, браузера нет, headless). Используется публичный client id gh; пользователь вводит код на github.com/login/device. Документированный минимум для `gh auth login --with-token` — scopes `repo,read:org,gist`; `,workflow` добавлять только если надо пушить файлы workflow.

```bash
# 1. Request a device code (gh's official client_id)
RESP=$(curl -s -X POST -H "Accept: application/json" \
  -d "client_id=178c6fc778ccc68e1d6a&scope=repo,read:org,gist" \
  https://github.com/login/device/code)
DEVICE_CODE=$(echo "$RESP" | sed 's/.*"device_code":"\([^"]*\)".*/\1/')
USER_CODE=$(echo "$RESP" | sed 's/.*"user_code":"\([^"]*\)".*/\1/')
INTERVAL=$(echo "$RESP" | sed 's/.*"interval":\([0-9]*\)".*/\1/'); INTERVAL=${INTERVAL:-5}
echo "Tell the user: go to https://github.com/login/device and enter code: $USER_CODE"

# 2. Poll for the token (respect interval; +5s on slow_down; ~15 min expiry).
#    Run this loop as a background process and show the user the code first.
while true; do
  sleep "$INTERVAL"
  POLL=$(curl -s -X POST -H "Accept: application/json" \
    -d "client_id=178c6fc778ccc68e1d6a&device_code=${DEVICE_CODE}&grant_type=urn:ietf:params:oauth:grant-type:device_code" \
    https://github.com/login/oauth/access_token)
  case "$POLL" in
    *access_token*)
      # Never echo the token; pipe it straight into gh.
      # perl-таймаут стережёт зависание без keyring (см. грабли ниже):
      # при срабатывании (SIGALRM, код 142) писать ~/.config/gh/hosts.yml напрямую.
      echo "$POLL" | sed 's/.*"access_token":"\([^"]*\)".*/\1/' | perl -e 'alarm 20; exec @ARGV' gh auth login --with-token \
        || { echo "WITH_TOKEN_HUNG_OR_FAILED — use the hosts.yml fallback below"; exit 1; }
      gh auth setup-git
      gh auth status
      echo "LOGIN_COMPLETE"; break ;;
    *authorization_pending*) ;;                      # keep polling
    *slow_down*) INTERVAL=$((INTERVAL + 5)) ;;       # back off per GitHub docs
    *expired_token*) echo "CODE_EXPIRED — restart the flow"; exit 1 ;;
    *access_denied*) echo "USER_DENIED"; exit 1 ;;
    *) echo "UNEXPECTED: $POLL"; exit 1 ;;
  esac
done
```

Замечание: при установке через winget на Windows gh лежит в `/c/Program Files/GitHub CLI` — добавить в PATH в той же оболочке: `export PATH="$PATH:/c/Program Files/GitHub CLI"`.

## Грабля: `gh auth login --with-token` виснет без keyring

> **ГРАБЛИ (headless Linux): `gh auth login --with-token` может висеть бесконечно.**
> На машинах без keyring (VPS, контейнеры, нет сессии dbus) хранилище кредов gh
> может ждать секрет-сервис без конца — даже с `--insecure-storage` и без вывода.
> Если команда не вернулась примерно за 20 секунд (оборачивать в переносимый таймаут
> `perl -e 'alarm 20; exec @ARGV' gh …`, чтобы это увидеть), пропускай механизм входа gh и запиши хранилище напрямую:
>
> ```bash
> # $TOKEN = the access token from the device flow above (never echo it)
> mkdir -p ~/.config/gh
> LOGIN=$(curl -s -H "Authorization: token $TOKEN" https://api.github.com/user \
>   | sed 's/.*"login": *"\([^"]*\)".*/\1/')
> printf 'github.com:\n    users:\n        %s:\n            oauth_token: %s\n    git_protocol: https\n    oauth_token: %s\n    user: %s\n' \
>   "$LOGIN" "$TOKEN" "$TOKEN" "$LOGIN" > ~/.config/gh/hosts.yml
> chmod 600 ~/.config/gh/hosts.yml
> gh auth status          # reads hosts.yml directly — verifies without the keyring
> gh auth setup-git       # wires the git credential helper (does not hang)
> ```
>
> `gh auth status` и `setup-git` читают файловое хранилище, keyring не трогают,
> поэтому работают сразу. Проверено на headless x86_64 VPS (gh 2.97.0, август
> 2026) после двух зависаний `--with-token`.

## Вход по токену (headless и SSH-серверы)

```bash
echo "<THEIR_TOKEN>" | gh auth login --with-token

# Set up git credentials through gh
gh auth setup-git
```

Если `--with-token` зависает и здесь, использовать запасной путь через `hosts.yml` из граблей выше.

## Проверка

```bash
gh auth status
```
