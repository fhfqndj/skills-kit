# Review workflows: setup, pre-push, end-to-end PR

Reference for sections 4 and 5 of `SKILL.md`: the full step-by-step recipes. The
rules — what to check and how to report — stay in `SKILL.md`.

## Setup (for PR interactions)

Every PR-level command needs `$GITHUB_TOKEN`, `$OWNER`, `$REPO` and `$BASE`. On a
host without the `gh-env.sh` helper (`github-auth` skill, `scripts/`), run this
block once per shell:

```bash
if command -v gh &>/dev/null && gh auth status &>/dev/null; then
  AUTH="gh"
else
  AUTH="git"
  # If GITHUB_TOKEN is unset, read it from the git credential store.
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

## 4. Pre-Push Review Workflow

When the user asks you to "review the code" or "check before pushing":

1. `git diff $BASE...HEAD --stat` — see scope of changes
2. `git diff $BASE...HEAD` — read the full diff
3. For each changed file, read it in full if you need more context
4. Apply the checklist from `SKILL.md`
5. Present findings in the structured format (Critical / Warnings / Suggestions / Looks Good)
6. If critical issues found, offer to fix them before the user pushes

## 5. PR Review Workflow (End-to-End)

When the user asks you to "review PR #N", "look at this PR", or gives you a PR URL, follow this recipe:

### Step 1: Set up environment

```bash
# Source gh-env.sh from the github-auth skill's scripts/ directory
# (the path to your skills directory is host-specific — see your host's docs).
source <skills-dir>/github-auth/scripts/gh-env.sh
# Or run the inline setup block from the top of this file
```

### Step 2: Gather PR context

Get the PR metadata, description, and list of changed files to understand scope before diving into code: `gh pr view 123`, `gh pr diff 123 --name-only`, `gh pr checks 123` (REST equivalents — `curl-recipes.md`).

### Step 3: Check out the PR locally

Use the `git fetch origin pull/$PR_NUMBER/head:pr-$PR_NUMBER && git checkout pr-$PR_NUMBER` from Section 2 of `SKILL.md`. It gives you full access to the working tree — you can read files, search the tree and run tests.

### Step 4: Read the diff and understand changes

```bash
git diff $BASE...HEAD               # full diff against the base branch
git diff $BASE...HEAD -- path/to/file.py   # file-by-file, for large PRs
```

For each changed file, read it in full to see context around the changes — diffs alone can miss issues visible only with surrounding code.

### Step 5: Run automated checks locally (if applicable)

```bash
# Run tests if there's a test suite
python -m pytest 2>&1 | tail -20
# or: npm test, cargo test, go test ./..., etc.

# Run linter if configured
ruff check . 2>&1 | head -30
# or: eslint, clippy, etc.
```

### Step 6: Apply the review checklist (Section 3)

Go through each category: Correctness, Security, Code Quality, Testing, Performance, Documentation — full items in `review-checklist.md`.

### Step 7: Post the review to GitHub

Collect your findings and submit them as a formal review with inline comments.

**With gh:**
```bash
# If no issues — approve
gh pr review $PR_NUMBER --approve --body "Reviewed by the agent. Code looks clean — good test coverage, no security concerns."

# If issues found — request changes with inline comments
gh pr review $PR_NUMBER --request-changes --body "Found a few issues — see inline comments."
```

**With curl — atomic review with multiple inline comments:** `curl-recipes.md`.

### Step 8: Also post a summary comment

In addition to inline comments, leave a top-level summary so the PR author gets the full picture at a glance. Use the review output format from `review-output-template.md`; the ready `gh pr comment` command with the verdict block is there too.

### Step 9: Clean up

```bash
git checkout "$BASE"
git branch -D pr-$PR_NUMBER
```

### Decision: Approve vs Request Changes vs Comment

- **Approve** — no critical or warning-level issues, only minor suggestions or all clear
- **Request Changes** — any critical or warning-level issue that should be fixed before merge
- **Comment** — observations and suggestions, but nothing blocking (use when you're unsure or the PR is a draft)
