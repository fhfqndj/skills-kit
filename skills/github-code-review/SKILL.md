---
name: github-code-review
description: "Use when you review PR code: diffs, inline comments."
version: 1.2.0
author: fhfqndj
license: MIT
platforms: [linux, macos, windows]
metadata:
  group: git
  tags: [GitHub, Code-Review, Pull-Requests, Git, Quality]
  related_skills: [github-auth, github-pr-workflow]
---

# GitHub Code Review

Perform code reviews on local changes before pushing, or review open PRs on GitHub. Most of this skill uses plain `git` — the `gh`/`curl` split only matters for PR-level interactions.

## When to Use

- Reviewing a local diff before a commit or push.
- Reviewing an open PR: read the diff, check out the branch, run tests.
- Leaving inline comments, approving, or requesting changes on a PR.
- Not for creating the PR itself (`github-pr-workflow`) or repo setup (`github-repo-management`).

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repository

### Setup (for PR interactions)

```bash
# Auth + owner/repo: the github-auth helper detects gh, the token and the remote
source <skills-dir>/github-auth/scripts/gh-env.sh   # GH_AUTH_METHOD, GITHUB_TOKEN, GH_OWNER, GH_REPO
AUTH=$GH_AUTH_METHOD; OWNER=$GH_OWNER; REPO=$GH_REPO

# Base branch: read the remote's default instead of hardcoding "main"
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
BASE=${BASE:-main}   # origin/HEAD may be unset; fall back to main
```

No helper script on this host? The inline detection block (gh vs git, token from the credential store, owner/repo, base branch) — `references/review-workflows.md`.

---

## 1. Reviewing Local Changes (Pre-Push)

This is pure `git` — works everywhere, no API needed.

### Get the Diff

```bash
# Staged changes (what would be committed)
git diff --staged

# All changes vs the base branch (what a PR would contain)
git diff $BASE...HEAD

# File names only
git diff $BASE...HEAD --name-only

# Stat summary (insertions/deletions per file)
git diff $BASE...HEAD --stat
```

### Review Strategy

1. **Get the big picture first**, then review file by file — read the changed files in full for context and use the diff to see what changed:

```bash
git diff $BASE...HEAD --stat
git log $BASE..HEAD --oneline
git diff $BASE...HEAD -- src/auth/login.py
```

2. **Check for common issues:**

```bash
# Debug statements, TODOs, console.logs left behind
git diff $BASE...HEAD | grep -n "print(\|console\.log\|TODO\|FIXME\|HACK\|XXX\|debugger"

# Large files accidentally staged
git diff $BASE...HEAD --stat | sort -t'|' -k2 -rn | head -10

# Secrets or credential patterns: file names only, never print values
git diff $BASE...HEAD -i -G'password|secret|api_key|private_key' --name-only

# Merge conflict markers
git diff $BASE...HEAD | grep -n "<<<<<<\|>>>>>>\|======="
```

3. **Present structured feedback** to the user.

### Review Output Format

When reviewing local changes, present findings as **Critical / Warnings / Suggestions / Looks Good**, each finding with `file:line` and a concrete fix. The worked example, severity guide and verdict rules — `references/review-output-template.md`.

---

## 2. Reviewing a Pull Request on GitHub

### View PR Details

**With gh:**

```bash
gh pr view 123
gh pr diff 123
gh pr diff 123 --name-only
```

The REST calls for PR metadata and changed-file stats — `references/curl-recipes.md`.

### Check Out PR Locally for Full Review

This works with plain `git` — no `gh` needed:

```bash
# Fetch the PR branch and check it out
git fetch origin pull/123/head:pr-123
git checkout pr-123

# Now you can read files, search the tree, run tests, etc.

# View diff against the base branch
git diff $BASE...pr-123
```

**With gh (shortcut):**

```bash
gh pr checkout 123
```

### Leave Comments on a PR

**General PR comment — with gh:**

```bash
gh pr comment 123 --body "Overall looks good, a few suggestions below."
```

The `POST .../issues/$PR_NUMBER/comments` equivalent — `references/curl-recipes.md`.

### Leave Inline Review Comments

**Single inline comment — with gh (via API):**

```bash
HEAD_SHA=$(gh pr view 123 --json headRefOid --jq '.headRefOid')

gh api repos/$OWNER/$REPO/pulls/123/comments \
  --method POST \
  -f body="This could be simplified with a list comprehension." \
  -f path="src/auth/login.py" \
  -f commit_id="$HEAD_SHA" \
  -f line=45 \
  -f side="RIGHT"
```

The `curl` version with the same body fields — `references/curl-recipes.md`.

### Submit a Formal Review (Approve / Request Changes)

**With gh:**

```bash
gh pr review 123 --approve --body "LGTM!"
gh pr review 123 --request-changes --body "See inline comments."
gh pr review 123 --comment --body "Some suggestions, nothing blocking."
```

**With curl — multi-comment review submitted atomically:** `references/curl-recipes.md`.

Event values: `"APPROVE"`, `"REQUEST_CHANGES"`, `"COMMENT"`

The `line` field refers to the line number in the *new* version of the file. For deleted lines, use `"side": "LEFT"`.

---

## 3. Review Checklist

When performing a code review (local or PR), systematically check:

- **Correctness** — does it do what it claims; edge cases; graceful error paths.
- **Security** — no hardcoded secrets; input validation; no SQL injection, XSS or path traversal; auth/authz checks.
- **Code Quality** — clear naming; no premature abstraction; DRY; single responsibility.
- **Testing** — new code paths; happy path and error cases; readable tests.
- **Performance** — no N+1 or unnecessary loops; caching where it pays; no blocking calls in async paths.
- **Documentation** — public APIs; "why" comments; README when behavior changed.

The full checklist, item by item — `references/review-checklist.md`.

---

## 4. Pre-Push Review Workflow

When the user asks you to "review the code" or "check before pushing": `--stat` → full diff → read each changed file in full → apply the checklist → present findings by severity → offer to fix critical issues before the push.

Full recipe — `references/review-workflows.md`.

---

## 5. PR Review Workflow (End-to-End)

When the user asks you to "review PR #N", "look at this PR", or gives you a PR URL: setup → PR context (`gh pr view`, `gh pr diff --name-only`, `gh pr checks`) → check out the PR locally → read the diff and each changed file in full → run tests and linter locally → apply the checklist → post the review (approve or request changes, inline comments) → post a summary comment → clean up (checkout the base branch, delete `pr-<N>`).

**Approve** only with no critical or warning-level findings; **request changes** on any of them; **comment** when nothing blocks or the PR is a draft.

Full recipe with every step and command, including cleanup — `references/review-workflows.md`.

## Files

- `references/review-workflows.md` — inline setup block, pre-push recipe, end-to-end PR review in nine steps, approve/request-changes/comment rule.
- `references/curl-recipes.md` — `curl` equivalents: PR details/files, comments, inline comments, atomic reviews.
- `references/review-checklist.md` — the full correctness/security/quality/testing/performance/docs checklist.
- `references/review-output-template.md` — severity guide, verdict rules, PR summary, local example, `gh` summary command.
