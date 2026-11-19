# API GitHub без gh

Подробности к разделу «API GitHub без gh» из `SKILL.md`. Когда `gh` недоступен, полный API GitHub доступен через `curl` с personal access token — так сделаны запасные пути в остальных навыках про GitHub.

## Токен для вызовов API

```bash
# Option 1: Export as env var (preferred — keeps it out of commands)
export GITHUB_TOKEN="<token>"

# Then use in curl calls:
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

## Достать токен из кредов git

Если креды git уже настроены (любым credential helper — от `gh`, `cache` или `store`), токен можно вытащить:

```bash
# Read from the git credential store
printf 'protocol=https\nhost=github.com\n' | GIT_TERMINAL_PROMPT=0 git credential fill | sed -n 's/^password=//p'
```

Если токен лежит в окружении или файле хоста (а не в git-кредедах), способ его взять — по инструкции своего хоста.

## Помощник: определить способ доступа

Этот блок ставится в начало любого рабочего процесса с GitHub:

```bash
# Try gh first, fall back to git + curl
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  echo "AUTH_METHOD=gh"
elif [ -n "$GITHUB_TOKEN" ]; then
  echo "AUTH_METHOD=curl"
elif GITHUB_TOKEN=$(printf 'protocol=https\nhost=github.com\n' | GIT_TERMINAL_PROMPT=0 git credential fill 2>/dev/null | sed -n 's/^password=//p') && [ -n "$GITHUB_TOKEN" ]; then
  export GITHUB_TOKEN
  echo "AUTH_METHOD=curl"
else
  echo "AUTH_METHOD=none"
  echo "Need to set up authentication first"
fi
```

Тот же выбор в виде готового скрипта — `scripts/gh-env.sh` (`GH_AUTH_METHOD`, `GITHUB_TOKEN`, `GH_OWNER`, `GH_REPO`); блок выше нужен там, где скрипт недоступен.
