---
name: github-repo-management
description: "Use when managing repos: clone, create, fork, releases."
version: 1.2.0
author: fhfqndj
license: MIT
platforms: [linux, macos, windows]
metadata:
  group: git
  tags: [GitHub, Repositories, Git, Releases, Secrets, Configuration]
  related_skills: [github-auth, github-pr-workflow, github-issues]
---

# GitHub Repository Management

Create, clone, fork, configure, and manage GitHub repositories. Each section shows `gh` first; the full `git` + `curl` fallback lives in `references/git-curl-basics.md` (clone, create, fork, info, settings) and `references/git-curl-advanced.md` (protection, secrets, releases, Actions, gists).

## When to Use

- Creating, cloning, forking, or syncing a repository.
- Setting topics, description, default branch, branch protection, or Actions secrets.
- Cutting a release, inspecting or re-running workflows, creating a gist.
- Grouping repos across an organization with topics or custom properties.
- Not for the branch/PR lifecycle (`github-pr-workflow`) or review (`github-code-review`).

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)

### Setup

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  if [ -z "$GITHUB_TOKEN" ]; then
    # Read the token from the git credential store; where your host keeps its own token — see your host's docs.
    GITHUB_TOKEN=$(printf 'protocol=https\nhost=github.com\n' | GIT_TERMINAL_PROMPT=0 git credential fill 2>/dev/null | sed -n 's/^password=//p')
  fi
fi

# Get your GitHub username (needed for several operations)
if [ "$AUTH" = "gh" ]; then
  GH_USER=$(gh api user --jq '.login')
else
  GH_USER=$(curl -s -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user | python -c "import sys,json; print(json.load(sys.stdin)['login'])")
fi
```

If you're inside a repo already:

```bash
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)

# Base branch: read the remote's default instead of hardcoding "main"
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
BASE=${BASE:-main}   # origin/HEAD may be unset; fall back to the remote's default
```

---

## 1. Cloning Repositories

```bash
git clone https://github.com/owner/repo-name.git              # HTTPS, credential helper
git clone --depth 1 https://github.com/owner/repo-name.git    # shallow, faster on large repos
gh repo clone owner/repo-name -- --depth 1                    # gh shorthand
```

Target directory, `--branch`, SSH remotes and the plain `git clone` variants — `references/git-curl-basics.md`.

## 2. Creating Repositories

**With gh:**

```bash
# Create a public repo and clone it
gh repo create my-new-project --public --clone

# Private, with description and license
gh repo create my-new-project --private --description "A useful tool" --license MIT --clone

# Under an organization
gh repo create my-org/my-new-project --public --clone

# From existing local directory
cd /path/to/existing/project
gh repo create my-project --source . --public --push
```

After `gh repo create ... --source . --push` the repository still carries the default branch `main`, which nothing has pushed: the repo URL opens looking empty even though `master` is there. Fix it immediately — `gh api -X PATCH repos/<owner>/<repo> -f default_branch=master` — and set topics in a single call, remembering that topics **replace** the whole list: `gh api --method PUT repos/<owner>/<repo>/topics -f "names[]=react" -f "names[]=vite"`.

**Do not chain creation with configuration in one command.** A line like `git commit … && gh repo create … --source . --push && gh api -X PATCH …` is refused wholesale by the long-lived-process guard in the agent's command runner, so none of it runs. Split it: commit, then `gh repo create … --push` as its own call (if that one is still refused, run it in the background per your host's instructions and check `git status --short --branch` afterwards), then settings through `gh api`. `gh repo edit` trips the same guard — use the API for description, topics and default branch.

**Verify what actually landed.** Four numbers after the push: `gh api repos/O/R --jq '.default_branch'` equals your branch; the blob count `gh api "repos/O/R/git/trees/master?recursive=1" --jq '[.tree[]|select(.type=="blob")]|length'` equals `git ls-files | wc -l`; `gh api repos/O/R/commits --jq 'length'` equals the number of commits you meant to publish (1 for a clean start); `git rev-parse HEAD origin/master` prints the same SHA twice.

### From a Template

**With gh:**

```bash
gh repo create my-new-app --template owner/template-repo --public --clone
```

The `POST /repos/{template_owner}/{template_repo}/generate` equivalent — `references/git-curl-basics.md`.

## 3. Forking Repositories

**With gh:**

```bash
gh repo fork owner/repo-name --clone
```

The `POST /repos/{owner}/{repo}/forks` + `git clone` + `upstream` recipe — `references/git-curl-basics.md`.

### Fork vs private mirror

A fork of a public repo **cannot** be made private: `gh api -X PATCH repos/<owner>/<repo> -f private=true` answers `422 Validation Failed … Public forks can't be made private`. When the copy must be private (source-available licence, client work, internal fork), create a separate private repo and push into it, keeping the upstream link by hand — commands (create, remotes, push, verify) in `references/git-curl-basics.md`.

- **A shallow clone cannot be pushed into an empty repo.** The push dies with `remote: fatal: did not receive expected object <sha>` and `remote unpack failed: index-pack failed` — a `--depth 1` pack is incomplete by construction. Fetch full history first (`git fetch --unshallow upstream`) and fetch it from a remote that actually has it — upstream or the public fork, never the new empty private repo — then push; the local `.git` grows to the real size of the project.
- **Read the default branch instead of assuming:** vendors differ (`master` for n8n, `main` for Activepieces), and `git push origin master` then fails with `src refspec master does not match any`.
- **Verify what landed:** `private=true`, `fork=false` and a non-zero `size` on the API are the proof; a size of `0KB` means the push has not finished or was rejected.
- **Private visibility does not relax the licence.** A private copy of a source-available project is still internal-use only, and if the licence is not permissive, delete the public fork afterwards — a public copy is distribution, a private one is internal use.

### Keeping a Fork in Sync

**With gh:**

```bash
gh repo sync $GH_USER/repo-name
```

The pure-`git` fetch/merge/push recipe with the remote's default branch — `references/git-curl-basics.md`.

## 4. Repository Information

```bash
gh repo view owner/repo-name
gh repo list --limit 20
gh search repos "machine learning" --language python --sort stars
```

The `curl` calls and JSON parsing for details, repo lists and search — `references/git-curl-basics.md`; endpoint map — `references/github-api-cheatsheet.md`.

## 5. Repository Settings

**With gh:**

```bash
gh repo edit --description "Updated description" --visibility public
gh repo edit --enable-wiki=false --enable-issues=true
gh repo edit --default-branch main
gh repo edit --add-topic "machine-learning,python"
gh repo edit --enable-auto-merge
```

The `PATCH /repos/{owner}/{repo}` body and the topics `PUT` — `references/git-curl-basics.md`.

## 6. Branch Protection

Branch to protect is the remote's default `$BASE` from the setup block, not a hardcoded `main`. The `GET`/`PUT .../branches/$BASE/protection` calls and the protection body (required status checks, review count, `enforce_admins`) — `references/git-curl-advanced.md`.

## 7. Secrets Management (GitHub Actions)

**With gh:**

```bash
gh secret set API_KEY --body "your-secret-value"
gh secret set SSH_KEY < ~/.ssh/id_rsa
gh secret list
gh secret delete API_KEY
```

Secrets via curl need libsodium encryption with the repo's public key; the full PyNaCl recipe, `PUT` and list calls — `references/git-curl-advanced.md`. Note: for secrets, `gh secret set` is dramatically simpler. If setting secrets is needed and `gh` isn't available, recommend installing it for just that operation.

## 8. Releases

**With gh:**

```bash
gh release create v1.0.0 --title "v1.0.0" --generate-notes
gh release create v2.0.0-rc1 --draft --prerelease --generate-notes
gh release create v1.0.0 ./dist/binary --title "v1.0.0" --notes "Release notes"
gh release list
gh release download v1.0.0 --dir ./downloads
```

The `POST`/`GET /repos/{owner}/{repo}/releases` calls and asset upload — `references/git-curl-advanced.md`.

## 9. GitHub Actions Workflows

**With gh:**

```bash
gh workflow list
gh run list --limit 10
gh run view <RUN_ID>
gh run view <RUN_ID> --log-failed
gh run rerun <RUN_ID>
gh run rerun <RUN_ID> --failed
gh workflow run ci.yml --ref main
gh workflow run deploy.yml -f environment=staging
```

The `curl` list/logs/rerun/dispatch recipes (including downloading logs to `$WORKDIR`) — `references/git-curl-advanced.md`.

## 10. Gists

**With gh:**

```bash
gh gist create script.py --public --desc "Useful script"
gh gist list
```

The `POST`/`GET /gists` calls — `references/git-curl-advanced.md`.

## 11. Grouping Repositories Across an Organization

GitHub has no folders. Topics tag a repo and make it globally searchable; custom properties are org-level metadata that drive the `prop` filter on the org Repositories page and can target rulesets. Neither touches the repo path. Commands for both, the scope/404 and Free-plan gotchas, and the verification calls — `references/org-grouping.md`.

## Creating repos in someone else's organization

- Creating a repository in a user's org and pushing the first commit is the owner's action, not a routine step: do it only when the request names the repo in the same turn. A "yes" picked from a choice list is not durable permission — the owner may have meant to do it themselves and ask to roll back.
- Know your undo before pushing: `gh repo delete` needs the `delete_repo` scope and otherwise answers `HTTP 403 ... needs the "delete_repo" scope`. `gh auth refresh -h github.com -s delete_repo` is interactive (browser approval), so it cannot be done silently mid-task; without it, deletion is UI-only for the owner — say that plainly instead of promising a rollback you cannot perform.
- Org policy can forbid deploy keys: `gh repo deploy-key add` answers `422 Deploy keys are disabled for this repository`. Read-only is the default (there is no `--allow-read-only` flag; only `-w/--allow-write`). If keys are blocked, plan delivery another way (fine-grained PAT scoped to Contents: read, or CI rsync instead of `git clone` on the server).

## Files

- `references/git-curl-basics.md` — `git` + `curl` for clone, create, fork (incl. private mirror and sync), repo info and settings.
- `references/git-curl-advanced.md` — `git` + `curl` for branch protection, Actions secrets encryption, releases, workflow logs/rerun/dispatch, gists, and the quick reference table.
- `references/org-grouping.md` — topics vs custom properties: commands, verification, scopes and 404 pitfalls.
- `references/github-api-cheatsheet.md` — REST endpoints by area, pagination, rate limits, curl patterns.
