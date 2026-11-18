---
name: github-pr-workflow
description: "Use when running the GitHub PR lifecycle: branch to merge."
version: 1.2.0
author: fhfqndj
license: MIT
platforms: [linux, macos, windows]
metadata:
  group: git
  tags: [GitHub, Pull-Requests, CI/CD, Git, Automation, Merge]
  related_skills: [github-auth, github-code-review]
---

# GitHub Pull Request Workflow

Complete guide for managing the PR lifecycle. Each section shows the `gh` way first; the `git` + `curl` fallback for every step lives in `references/curl-recipes.md`.

## When to Use

- Opening or shepherding a PR: branch, commits, PR body, review request.
- Watching CI on a PR and fixing failures until it is green.
- Merging (squash / merge / rebase), enabling auto-merge, deleting the branch.
- Not for judging the code (`github-code-review`) or repo settings (`github-repo-management`).

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

Branch naming conventions:
- `feature/description` — new features
- `fix/description` — bug fixes
- `refactor/description` — code restructuring
- `docs/description` — documentation
- `ci/description` — CI/CD changes

Branch names — per the `git-naming` skill (L1): allowed actions, description rules and branch lifetime live there; they are not duplicated here, the list above is only an example.

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

Options: `--draft`, `--reviewer user1,user2`, `--label "enhancement"`, `--base develop`

The `POST /repos/$OWNER/$REPO/pulls` body (head/base, draft flag) — `references/curl-recipes.md`.

## 4. Monitoring CI Status

### Check CI Status

**With gh:**

```bash
# One-shot check
gh pr checks

# Watch until all checks finish (polls every 10s)
gh pr checks --watch
```

The combined-status / check-runs calls and a polling loop for machines without `gh` — `references/curl-recipes.md`.

## 5. Auto-Fixing CI Failures

When CI fails, diagnose and fix. This loop works with either auth method.

### Step 1: Get Failure Details

Common failure patterns and how to read them from logs — `references/ci-troubleshooting.md`.

**With gh:**

```bash
# List recent workflow runs on this branch
gh run list --branch $(git branch --show-current) --limit 5

# View failed logs
gh run view <RUN_ID> --log-failed
```

The `curl` route (list runs, download the log zip into `$WORKDIR`) — `references/curl-recipes.md`.

### Step 2: Fix and Push

After identifying the issue, edit the files in place to fix it:

```bash
git add <fixed_files>
git commit -m "fix: resolve CI failure in <check_name>"
git push
```

### Step 3: Verify

Re-check CI status using the commands from Section 4 above.

### Auto-Fix Loop Pattern

When asked to auto-fix CI, follow this loop:

1. Check CI status → identify failures
2. Read failure logs → understand the error
3. Read the failing code and edit it in place → fix the code
4. `git add . && git commit -m "fix: ..." && git push`
5. Wait for CI → re-check status
6. Repeat if still failing (up to 3 attempts, then ask the user)

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

## 7. Complete Workflow Example

```bash
# 1. Start from a clean base branch
git checkout "$BASE" && git pull origin "$BASE"

# 2. Branch
git checkout -b fix/login-redirect-bug

# 3. (make the code changes)

# 4. Commit
git add src/auth/login.py tests/test_login.py
git commit -m "fix: correct redirect URL after login

Preserves the ?next= parameter instead of always redirecting to /dashboard."

# 5. Push
git push -u origin HEAD

# 6. Create PR (picks gh or curl based on what's available)
# ... (see Section 3)

# 7. Monitor CI (see Section 4)

# 8. Merge when green (see Section 6)
```

## Files

- `references/ci-troubleshooting.md` — common CI failure patterns and how to diagnose them from logs.
- `references/curl-recipes.md` — `curl`/GraphQL equivalents for PR create, CI status and polling, logs, merge, auto-merge, plus the PR command table.
