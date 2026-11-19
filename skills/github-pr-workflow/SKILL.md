---
name: github-pr-workflow
description: "Use when working a GitHub repo: issues, PR, CI."
version: 1.3.0
author: fhfqndj
license: MIT
platforms: [linux, macos, windows]
metadata:
  group: git
  tags: [GitHub, Pull-Requests, Issues, Releases, CI/CD, Git, Automation, Merge]
  related_skills: [github-auth, github-code-review]
---

# GitHub Pull Request Workflow

Complete guide for managing the PR lifecycle. Each section shows the `gh` way first; the `git` + `curl` fallback for every step lives in `references/curl-recipes.md`.

## When to Use

- Opening or shepherding a PR: branch, commits, PR body, review request.
- Watching CI on a PR and fixing failures until it is green.
- Merging (squash / merge / rebase), enabling auto-merge, deleting the branch.
- Issues, releases, topics, branch protection and Actions secrets — the commands are in the references below.
- Not for judging the code (`github-code-review`) or for getting access (`github-auth`).

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository with a GitHub remote

### Quick Auth Detection

```bash
# Determine which method to use throughout this workflow
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  # Ensure we have a token for API calls: read it from the git credential store.
  # Where your host keeps its own token (env file, secret store) — see your host's docs.
  if [ -z "$GITHUB_TOKEN" ]; then
    GITHUB_TOKEN=$(printf 'protocol=https\nhost=github.com\n' | GIT_TERMINAL_PROMPT=0 git credential fill 2>/dev/null | sed -n 's/^password=//p')
  fi
fi
echo "Using: $AUTH"
```

### Extracting Owner/Repo from the Git Remote

Many `curl` commands need `owner/repo`. Extract it from the git remote:

```bash
# Works for both HTTPS and SSH remote URLs
REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)
echo "Owner: $OWNER, Repo: $REPO"

# Base branch: read the remote's default instead of hardcoding "main"
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
BASE=${BASE:-main}   # origin/HEAD may be unset; fall back to the remote's default
echo "Base: $BASE"
```

---

## 1. Branch Creation

This part is pure `git` — identical either way:

```bash
# Make sure you're up to date
git fetch origin
git checkout "$BASE" && git pull origin "$BASE"

# Create and switch to a new branch
git checkout -b feature/add-user-authentication
```

Branch names follow the project's naming skill (`git-naming`): allowed actions, description rules and branch lifetime live there, not here. If the project has no such convention, `feature/` and `fix/` are the safe minimum.

## 2. Making Commits

Make the changes in the files, then commit:

```bash
# Stage specific files
git add src/auth.py src/models/user.py tests/test_auth.py

# Subject format — see the git-naming skill
git commit -m "feat: add user authentication"
```

Commit messages follow the `git-naming` skill: `[action]: [comment]`, subject of
5–6 words, lowercase, no trailing period. Do not introduce a competing message
format here — allowed actions, comment rules and branch names live in
`git-naming` and are not duplicated.

## 3. Pushing and Creating a PR

### Push the Branch (same either way)

```bash
git push -u origin HEAD
```

**`remote rejected … (Internal Server Error)` on `git-receive-pack` is a GitHub-side failure, not a token problem.**
Retry the push 2–3 times with a pause of a few seconds (`git push origin <branch> -v` shows whether the pack
got through); changing the token and rerunning `gh auth status` on the first failure wastes time. If the branch
made it after the retry (the output shows `* [new branch]`) but `gh pr create` still fails with `Head sha can't
be blank` or `No commits between …`, a manually created PR/Draft may have claimed the branch: check
`git ls-remote --heads origin <branch>` and only then create the PR.

### Create the PR

**With gh:**

```bash
gh pr create \
  --title "feat: add JWT-based user authentication" \
  --body "## Summary
- Adds login and register API endpoints
- JWT token generation and validation

## Test Plan
- [ ] Unit tests pass

Closes #42"
```

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`.
Body skeletons — `templates/pr-body-feature.md`, `templates/pr-body-bugfix.md`.

The `POST /repos/$OWNER/$REPO/pulls` body (head/base, draft flag) — `references/curl-recipes.md`.

## 4. Monitoring CI Status

`gh pr checks` — one-shot; `gh pr checks --watch` — until all checks finish. The combined-status and check-runs calls plus a polling loop for machines without `gh` — `references/curl-recipes.md`.

## 5. Auto-Fixing CI Failures

Loop: list runs on the branch (`gh run list --branch $(git branch --show-current)`), read the failure (`gh run view <RUN_ID> --log-failed`), fix in place, commit, push, re-check. Failure patterns per stack and the decision tree — `references/ci-troubleshooting.md`. Three attempts and still red — ask the user instead of pushing a fourth guess.

## 6. Merging

**With gh:**

```bash
# Squash merge + delete branch (cleanest for feature branches)
gh pr merge --squash --delete-branch

# Enable auto-merge (merges when all checks pass)
gh pr merge --auto --squash --delete-branch
```

The REST merge call, branch cleanup and the GraphQL auto-merge mutation — `references/curl-recipes.md`.

Merge methods: `"merge"` (merge commit), `"squash"`, `"rebase"`

## Issues, releases, repository settings

Issues: `gh issue create --title … --body-file templates/bug-report.md --label …`; list, filter, triage, bulk edits and every `curl` fallback — `references/issues-api.md`. Feature requests — `templates/feature-request.md`.

Releases, topics, branch protection, Actions secrets and workflows, gists — `references/github-api-cheatsheet.md`. Cloning, forking and repository settings through the API — `references/git-curl-basics.md`, `references/git-curl-advanced.md`. Repos across an organization — `references/org-grouping.md`.

## Files

- `references/ci-troubleshooting.md` — CI failure patterns by stack and the auto-fix decision tree.
- `references/curl-recipes.md` — `curl`/GraphQL equivalents for PR create, CI status, logs, merge, auto-merge.
- `references/issues-api.md` — issues and comments: list, search, create, triage, bulk edits.
- `references/github-api-cheatsheet.md` — releases, topics, branch protection, Actions secrets and workflows.
- `references/git-curl-basics.md`, `references/git-curl-advanced.md` — clone, fork, settings, org operations.
- `references/org-grouping.md` — repositories grouped across an organization.
- `templates/` — PR bodies, bug report, feature request.
