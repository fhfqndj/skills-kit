---
name: github-issues
description: "Use when you create, assign or triage a GitHub issue."
version: 1.2.0
author: fhfqndj
license: MIT
platforms: [linux, macos, windows]
metadata:
  group: git
  tags: [GitHub, Issues, Project-Management, Bug-Tracking, Triage]
  related_skills: [github-auth, github-pr-workflow]
---

# GitHub Issues Management

Create, search, triage, and manage GitHub issues. Each section shows `gh` first; the raw `curl` calls live in `references/curl-api.md`.

## When to Use

Open this skill when you create, edit, label, assign, comment on, close, or reopen a GitHub issue, link an issue to a PR, triage an incoming queue, or need a bug-report / feature-request body.

Skip it for pull requests (`github-pr-workflow`), repositories, topics, and releases (`github-repo-management`), and authentication itself (`github-auth`). Batch edits and every `curl` fallback are in `references/curl-api.md`.

## Prerequisites

- Authenticated with GitHub (see `github-auth` skill)
- Inside a git repo with a GitHub remote, or specify the repo explicitly

### Setup

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  # If GITHUB_TOKEN is unset, read it from the git credential store.
  # Where your host keeps its own token (env file, secret store) — see your host's docs.
  if [ -z "$GITHUB_TOKEN" ]; then
    GITHUB_TOKEN=$(printf 'protocol=https\nhost=github.com\n' | GIT_TERMINAL_PROMPT=0 git credential fill 2>/dev/null | sed -n 's/^password=//p')
  fi
fi

REMOTE_URL=$(git remote get-url origin)
OWNER_REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||')
OWNER=$(echo "$OWNER_REPO" | cut -d/ -f1)
REPO=$(echo "$OWNER_REPO" | cut -d/ -f2)

# Base branch: read the remote's default instead of hardcoding "main"
BASE=$(git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null | sed 's|^origin/||')
BASE=${BASE:-main}   # origin/HEAD may be unset; fall back to the remote's default
```

---

## 1. Viewing Issues

```bash
gh issue list
gh issue list --state open --label "bug"
gh issue list --assignee @me
gh issue list --search "authentication error" --state all
gh issue view 42
```

Without `gh` — `references/curl-api.md` §1: list, filter by label, view one issue, and search.

## 2. Creating Issues

```bash
gh issue create \
  --title "Login redirect ignores ?next= parameter" \
  --body "## Description
After logging in, users always land on /dashboard.

## Steps to Reproduce
1. Navigate to /settings while logged out
2. Get redirected to /login?next=/settings
3. Log in
4. Actual: redirected to /dashboard (should go to /settings)

## Expected Behavior
Respect the ?next= query parameter." \
  --label "bug,backend" \
  --assignee "username"
```

The `curl` payload is in `references/curl-api.md` §2.

### Bug Report Template

```
## Bug Description
<What's happening>

## Steps to Reproduce
1. <step>
2. <step>

## Expected Behavior
<What should happen>

## Actual Behavior
<What actually happens>

## Environment
- OS: <os>
- Version: <version>
```

The fuller version, with error output and additional context, is `templates/bug-report.md` — pass it with `gh issue create --body-file templates/bug-report.md`.

### Feature Request Template

```
## Feature Description
<What you want>

## Motivation
<Why this would be useful>

## Proposed Solution
<How it could work>

## Alternatives Considered
<Other approaches>
```

`templates/feature-request.md` adds a scope/effort estimate and additional context.

## 3. Managing Issues

### Add/Remove Labels

```bash
gh issue edit 42 --add-label "priority:high,bug"
gh issue edit 42 --remove-label "needs-triage"
```

Listing the repo's labels, and the `curl` calls for adding and removing — `references/curl-api.md` §3.

### Assignment

```bash
gh issue edit 42 --add-assignee username
gh issue edit 42 --add-assignee @me
```

### Commenting

```bash
gh issue comment 42 --body "Investigated — root cause is in auth middleware. Working on a fix."
```

### Closing and Reopening

```bash
gh issue close 42
gh issue close 42 --reason "not planned"
gh issue reopen 42
```

### Linking Issues to PRs

Issues are automatically closed when a PR merges with the right keywords in the body:

```
Closes #42
Fixes #42
Resolves #42
```

To create a branch from an issue:

```bash
gh issue develop 42 --checkout
```

The manual `git` equivalent is in `references/curl-api.md` §3.

## 4. Issue Triage Workflow

When asked to triage issues:

1. **List untriaged issues:**

```bash
gh issue list --label "needs-triage" --state open
```

2. **Read and categorize** each issue (view details, understand the bug/feature)
3. **Apply labels and priority** (see Managing Issues above)
4. **Assign** if the owner is clear
5. **Comment with triage notes** if needed

The `curl` list for step 1 is in `references/curl-api.md` §4.

## 5. Bulk Operations

For batch operations, combine API calls with shell scripting:

```bash
# Close all issues with a specific label
gh issue list --label "wontfix" --json number --jq '.[].number' | \
  xargs -I {} gh issue close {} --reason "not planned"
```

The `curl` + `while read` version is in `references/curl-api.md` §5.

## Quick Reference Table

| Action | gh | curl endpoint |
|--------|-----|--------------|
| List issues | `gh issue list` | `GET /repos/{o}/{r}/issues` |
| View issue | `gh issue view N` | `GET /repos/{o}/{r}/issues/N` |
| Create issue | `gh issue create ...` | `POST /repos/{o}/{r}/issues` |
| Add labels | `gh issue edit N --add-label ...` | `POST /repos/{o}/{r}/issues/N/labels` |
| Assign | `gh issue edit N --add-assignee ...` | `POST /repos/{o}/{r}/issues/N/assignees` |
| Comment | `gh issue comment N --body ...` | `POST /repos/{o}/{r}/issues/N/comments` |
| Close | `gh issue close N` | `PATCH /repos/{o}/{r}/issues/N` |
| Search | `gh issue list --search "..."` | `GET /search/issues?q=...` |

## Files

- `references/curl-api.md` — the full `curl` fallback for every section: listing, creating, labels, assignment, comments, close/reopen, triage, batch close, and the endpoint table.
- `templates/bug-report.md` — bug report body with environment and error-output sections.
- `templates/feature-request.md` — feature request body with motivation, alternatives, and scope estimate.
