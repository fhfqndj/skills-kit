# Если доступ к GitHub не работает

Полная таблица к разделу «Если не работает» из `SKILL.md`: симптом, причина и команда-починка.

| Проблема | Что делать |
|---------|----------|
| `git push` спрашивает пароль | GitHub отключил вход по паролю. В поле пароля — personal access token либо переход на SSH |
| `remote: Permission to X denied` | У токена нет scope `repo` — перевыпустить с нужными scopes |
| `fatal: Authentication failed` | Сохранённые креды устарели — `git credential reject`, затем авторизоваться заново |
| `ssh: connect to host github.com port 22: Connection refused` | Попробовать SSH через порт HTTPS: добавить в `~/.ssh/config` `Host github.com` с `Port 443` и `Hostname ssh.github.com` |
| Креды не сохраняются | Проверить `git config --global credential.helper` — там должен быть helper от `gh`, `cache` или (осознанный fallback) `store` |
| Несколько аккаунтов GitHub | SSH с разными ключами по алиасам хоста в `~/.ssh/config` либо `git config --local credential.helper` на уровне репозитория |
| `gh` отдаёт `HTTP 404: Not Found` на существующий приватный репозиторий организации | `gh` ходит в API от **активного** аккаунта, а у него может не быть доступа к организации, тогда как git пушит токеном другого аккаунта из helper. Ограничить одну команду: `GH_TOKEN=$(gh auth token --user <account>) gh run list` (тот же префикс для `view`/`watch`/`download`). Токен не печатать; какой аккаунт использует git — смотреть через `printf 'protocol=https\nhost=github.com\n\n' \| GIT_TERMINAL_PROMPT=0 git credential fill` |
| `gh repo view owner/repo` говорит GraphQL `Could not resolve to a Repository`, хотя репозиторий есть (приватный, принадлежит другому залогиненному аккаунту) | Та же причина: активный аккаунт его не видит. Когда следующие команды относятся к тому владельцу, переключить всю сессию: `gh auth switch --user <owner>`; для одной команды — префикс `GH_TOKEN=...` |
| Push или клон приватного репозитория другого аккаунта отвечает 404, хотя токен активного аккаунта рабочий | Прибить локальный helper репозитория к токену владельца: `git config --local credential.helper '!f() { test "$1" = get && printf "username=x-access-token\npassword=%s\n" "$(gh auth token --user <owner>)"; }; f'` — глобальный helper gh следует за активным аккаунтом и молча переключается под тобой |
| `gh: command not found`, sudo нет | Использовать метод 1 (только git) — установка не нужна |
