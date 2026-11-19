# Публикация в новый репозиторий

Два случая. «Тот же проект, прежнюю историю не показывать» — шаги 1–5 ниже; краткая версия и правила выбора текста первого коммита — в `SKILL.md`, раздел «Публикация в новый репозиторий с чистой историей». «Копия дерева под новым именем» — разделы 0–7; путь `--orphan` остаётся для случая, когда репозиторий — то же дерево, здесь дерево копируется.

## Шаги 1–5: то же дерево, чистая история

Когда проект уезжает в новый (корпоративный) репозиторий и прежнюю историю показывать не надо:

1. Сначала прогнать тесты и линтеры: откатываться на старые коммиты в новом репозитории будет нечем.
2. Внутренние документы и секреты убрать из индекса, оставив на диске: `git rm --cached deploy/deploy.md`, `.env`, `.env.prod`, затем добавить их в `.gitignore`. Проверка: `git ls-files | grep -iE 'deploy\.md|(^|/)\.env'` — пусто.
3. Сохранить историю локальной веткой: `git branch archive/history master`; на GitHub её не пушить.
4. Один коммит без родителей: `git checkout --orphan clean`, `git add -A`, `git commit -m "initial commit"`, `git branch -M clean master`.
5. Пуш и default branch: `git push -u origin master`, затем `gh api -X PATCH repos/<owner>/<repo> -f default_branch=master`.

## 0. Решения до команд

Все вопросы человеку — одним списком сразу:

- имя репозитория (кандидаты формулировать за владельца, с рекомендацией);
- приватный/публичный;
- история: один `initial commit` или перенос прежних коммитов;
- путь локальной копии (рядом с остальными проектами владельца — обычно `<projects>/<имя>`);
- судьба старого репозитория: оставить / архивировать / удалить.

По одному вопросу в сессии — это лишние круги.

## 1. Осмотр источника

```bash
grep -rn "<старое-имя>" --include="*.ts" --include="*.tsx" --include="*.json" \
  --include="*.md" --include="*.yml" . --exclude-dir=node_modules --exclude-dir=dist --exclude=package-lock.json
git ls-files | wc -l
git ls-files | grep -iE 'deploy\.md|(^|/)\.env|dist/'
```

README, `package.json`, `docker-compose.yml` — главные места самоупоминаний.

## 2. Копия и переименование

```bash
SRC=<старое-дерево>; DST=<projects>/<новое-имя>
mkdir -p "$DST"
rsync -a --exclude '.git' --exclude 'node_modules' --exclude 'dist' "$SRC/" "$DST/"
cd "$DST"
perl -pi -e 's/<старое-имя>/<новое-имя>/g' package.json docker-compose.yml README.md
printf '\n# Local env\n.env\n.env.*\n!.env.example\n' >> .gitignore
```

После `git clone` в новом репозитории остался бы старый remote и вся прежняя история. Самоупоминания ищутся по всему проекту (`grep -rn "<старое-имя>"`), а эта замена правит `package.json`, `docker-compose.yml` (`image`, `container_name`) и README: иначе имя пакета, образ и контейнер остаются старыми при новом имени репозитория.

## 3. Проверки до коммита

```bash
npm ci
npm run lint
npm run typecheck
npm run build
```

Проверки идут до коммита: откатываться в новом репозитории нечем. Каждый вывод смотреть целиком: `tail` скрывает первую ошибку в списке, а exit-код после пайпа показывает код `tail`, не `npm`.

## 4. Локальный репозиторий

```bash
git init -b master -q
# идентичность — до первого коммита; активный аккаунт gh auth status
# должен совпадать с владельцем репозитория
git config --local user.name "<аккаунт-владельца>"
git config --local user.email "<email коммитов>"
git add -A
git diff --cached --name-only | grep -iE 'node_modules|dist/|(^|/)\.env$' || echo "suspicious: none"
git commit -m "initial commit"     # ровно текст владельца
git log --oneline
git status --short --branch
```

## 5. Удалённый репозиторий

```bash
gh repo create <имя> --private \
  --description "<описание проекта>" \
  --source . --remote origin --push

gh api -X PATCH repos/<owner>/<repo> -f default_branch=master --jq '.default_branch'

# topics задаются одним вызовом и заменяют весь список
gh api --method PUT repos/<owner>/<repo>/topics \
  -f "names[]=react" -f "names[]=vite" -f "names[]=typescript" --jq '.names'
```

`gh repo edit --add-topic` делает то же самое, но длинный список флагов иногда отклоняется до запуска как «долгоживущий процесс» — API-форма идемпотентна и проходит одной командой.

## 6. Проверка результата по API

Результат проверять по API, а не по выводу `gh repo create`: `default_branch`, число блобов в `git/trees?recursive=1`, число коммитов, visibility, совпадение `git rev-parse HEAD origin/master`.

```bash
gh repo view <owner>/<repo> --json name,owner,visibility,defaultBranchRef,description,url \
  --jq '{name,owner:.owner.login,visibility,default:.defaultBranchRef.name,url}'
gh api "repos/<owner>/<repo>/git/trees/master?recursive=1" --jq '[.tree[]|select(.type=="blob")]|length'
gh api repos/<owner>/<repo>/commits --jq 'length'
git rev-parse HEAD origin/master   # хеши должны совпасть
```

Число блобов сверить с `git ls-files | wc -l` в локальной папке.

## 7. Документация

- Переименовать файл заметки проекта под новое имя, поправить `[[ссылку]]` в индексной заметке раздела, обновить путь запуска, remote, идентичность коммитов.
- Старый репозиторий оставить в заметке отдельной строкой: он остаётся историей разработки.
- Исторические блоки «что проверено» не переписывать — они датированы и описывают прежнее состояние.

## Правила после публикации

- Локальную папку называть по имени репозитория, даже если в обсуждении звучало другое имя-кандидат.
- Старый репозиторий по умолчанию не трогать: архивирование и удаление — только по решению владельца (удаление требует scope `delete_repo` и обычно делается через UI).
- Заметку проекта в базе знаний обновлять в том же проходе (см. раздел 7).
- Красный `npm run lint` из-за генерённых компонентов (например `react-refresh/only-export-components` в shadcn-файлах) публикацию не блокирует, но и молчать о нём нельзя: сказать владельцу и предложить правку отдельным коммитом, а не рефакторить сгенерированные файлы по ходу публикации.
