# Доступ с сервера выката: deploy-ключ и GHCR

Подробности к «Методу 3» из `SKILL.md`.

Два разных доступа, их не путать: **deploy-ключ** даёт серверу `git` (read-only), **PAT** даёт тянуть
приватные образы из GHCR. Ни один не должен лежать в репозитории или в истории чата.

## git на сервере — deploy-ключ

```bash
# на сервере
ssh-keygen -t ed25519 -N "" -f ~/.ssh/gh_deploy
cat ~/.ssh/gh_deploy.pub

# на машине агента: добавить ключ в репозиторий, только на чтение
gh api -X POST /repos/<owner>/<repo>/keys -f title=deploy-key \
  -f key="$(cat key.pub)" -F read_only=true

# на сервере: без этого файла `git fetch` в CI-шаге падает,
# хотя разовое клонирование с GIT_SSH_COMMAND работало.
# Не перезаписывать ~/.ssh/config — в нём алиасы и ключи других хостов.
mkdir -p ~/.ssh/config.d
printf 'Host github.com\n  IdentityFile ~/.ssh/gh_deploy\n  StrictHostKeyChecking accept-new\n' \
  > ~/.ssh/config.d/gh_deploy
chmod 600 ~/.ssh/config.d/gh_deploy
touch ~/.ssh/config
grep -q '^Include ~/.ssh/config.d/\*' ~/.ssh/config || {
  printf 'Include ~/.ssh/config.d/*\n' | cat - ~/.ssh/config > ~/.ssh/config.tmp
  mv ~/.ssh/config.tmp ~/.ssh/config
}
chmod 600 ~/.ssh/config
```

## Приватные образы — GHCR

Нужен **classic PAT с единственным scope `read:packages`** (fine-grained для пакетов не подходит).
`-u` — это логин **владельца токена**, а не название организации.

```bash
echo "$GHCR_PULL_TOKEN" | docker login ghcr.io -u "$GHCR_PULL_USER" --password-stdin
# ... деплой ...
docker logout ghcr.io        # не оставлять креды на машине
```

В CI токен хранится секретом репозитория (`gh secret set GHCR_PULL_TOKEN < файл`), а сервер получает его только на время
выката; значение не печатать в чат.

**Проверка, что образ именно скачан, а не собран локально:**

```bash
docker images --digests | grep "$TAG"     # RepoDigest sha256:… заполнен → скачан; пусто → собран
```

Права на пуши в GHCR выдаёт `permissions: packages: write` в workflow; `GITHUB_TOKEN` для этого
достаточно, отдельный PAT нужен только читающей стороне.
