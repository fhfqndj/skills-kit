---
name: requesting-code-review
description: "Use when pre-commit review: security scan, gates, auto-fix."
version: 2.4.2
author: fhfqndj
license: MIT
platforms: [linux, macos, windows]
metadata:
  group: code
  tags: [code-review, security, verification, quality, pre-commit, auto-fix]
  related_skills: [test-driven-development, verification-before-completion, subagent-driven-development, git-naming]
---

# Pre-Commit Code Verification

Automated verification pipeline before code lands. Static scans, baseline-aware
quality gates, an independent reviewer subagent, and an auto-fix loop.

**Core principle:** No agent should verify its own work. Fresh context finds what you miss.

## When to Use

- After implementing a feature or bug fix, before `git commit` or `git push`
- When the user says "commit", "push", "ship", "done", "verify", or "review before merge"
- After a task with 2+ file edits in a git repo, and after each task in subagent-driven-development (the two-stage review)

**Skip for:** documentation-only changes, pure config tweaks, or an explicit "skip verification".

**This skill vs GitHub PR review:** this verifies YOUR changes before committing; GitHub PR review
reviews other people's PRs with inline comments.

## When a full review is not needed

Skip the pipeline only when **all three** hold: **≤2 files**, **<50 changed
lines**, and nothing touches **auth, payments, user data, or config/secrets**.
Everything else gets the full pass.

**Lowering the bar is not a fix.** Do not skip the failing test, add a
suppression or lint-ignore, lower a threshold, or delete the assertion to turn
the gate green. If the bar cannot be met, report the failure with its reason.

## Whole-codebase review (user says «проведём ревью»)

A review of the project, architecture, or backend — not a diff — does not fit this pipeline: commit
first so `file:line` citations stay put; split by angle (backend, architecture boundaries, frontend)
into read-only subagents; fence the scope in the user's own words; demand `[severity] [area]
file:line` findings capped at 10–15; require the "already done well" and "must NOT be touched" blocks;
show the ranked list before touching code. Full seven-step protocol — `references/whole-codebase-review.md`.

## Step 1 — Get the diff

```bash
git diff --cached
```

If empty, try `git diff` then `git diff HEAD~1 HEAD`. If `git diff --cached` is empty but `git diff`
shows changes, tell the user to `git add <files>` first; if still empty, run `git status` — nothing to verify.

**Change size — measure before dispatching the reviewer.** One threshold, in lines, not
characters: `git diff --numstat` gives added/deleted per file.

- ~100 changed lines — good, reviewable in one sitting;
- ~300 — acceptable only as one logical change;
- >1000 lines or more than ~20 files — too large, split before review.

A file pushed past ~1000 **total** lines is a decomposition signal: extract first, then add. Feature
work and refactoring go in separate commits. Split **by file group** or **vertical slices**; details —
`references/review-quality.md`. When a diff is still too big for one pass, review it by file:
`git diff --name-only`, then `git diff HEAD -- <file>`.

## Step 2 — Static security scan

Scan added lines only. Any match is a security concern fed into Step 5.

```bash
# Staged secret names only — this never prints the value
git diff --cached -i -G'password|secret|api_key|token' --name-only
```

Shell injection, `eval`/`exec`, unsafe deserialization, SQL formatting, and the
deeper pass — threat model, STRIDE, destructive-path containment, dependency
audit: `references/security-checks.md`.

## Step 3 — Baseline tests and linting

Detect the project language and run the appropriate tools. Capture the failure
count BEFORE your changes as **baseline_failures** (stash changes, run, pop).
Only NEW failures introduced by your changes block the commit; a clean baseline
plus new failures is a regression, a dirty one counts only the new ones. Test and
lint commands per stack (pytest, npm, cargo, go; ruff, mypy, eslint, tsc,
clippy, vet) and the baseline comparison — `references/gates.md`.

## Step 4 — Self-review checklist

Quick scan before dispatching the reviewer:

- [ ] No hardcoded secrets, API keys, or credentials
- [ ] Input validation on user-provided data; SQL queries parameterized
- [ ] File operations validate paths (no traversal); external calls have error handling (try/catch)
- [ ] No debug print/console.log and no commented-out code left behind
- [ ] New code has tests (if a test suite exists)

**Five axes, all mandatory:** correctness · readability · architecture ·
security · performance. Every finding names its axis; the questions per axis and
the "blocks merge" bar are in `references/review-quality.md`. Security beyond the
regex scan — trust boundaries, path containment, audit triage: `references/security-checks.md`.

## Dependency discipline (if the diff touches dependencies)

Read the changelog, not just the version number — a patch bump can change behavior. One dependency
per change. Review the lockfile diff, not only the manifest. Run `npm audit --audit-level=high`
(or `pip-audit`) before release; an audit catches only known CVEs, not a typosquat. Full checklist —
`references/review-quality.md`; commands and the typosquat caveat — `references/security-checks.md`.

## Step 5 — Independent reviewer subagent

**Interactive sessions only.** In a one-shot run (a scripted run, a benchmark harness) there is no
one to hand the verdict to and a fresh subagent re-pays the whole system prompt plus a repo re-read:
skip Steps 5 and 7, apply the Step 4 checklist to the diff yourself, run the tests, and go to Step 8.
Dispatch the reviewer from the session itself — delegation is not available from inside a script the
agent runs; one-shot mode and delegation mechanics are host-specific.

The reviewer gets the diff, the static scan results and the original task requirements, plus
read-only access to the repository and permission to run commands (tests, lint) — it must not edit
files. It reviews Stage 1 (does the diff do what the task asked) and then the five axes, names its
axis and severity on every finding, and returns only the JSON verdict. Fail-closed: unparseable
response is a fail, any Critical finding blocks merge. Full brief, the
fail-closed rules and the JSON shape — `references/reviewer-brief.md`.

## Verification Story — required for APPROVE

APPROVE is not accepted without the author's evidence: what was run, what it printed and the exit
code; for UI changes a screenshot or a measured number. Missing story means REQUEST CHANGES, not
"approve and check later". Checklist — `references/review-quality.md`.

## Mutation check

Invert one condition the change adds (drop a `!`, swap `&&` for `||`), run the
suite, restore the file from a copy. A mutation that stays green is a finding:
there is no test for that case.

## Step 6 — Evaluate results

Combine results from Steps 2, 3, and 5. **All passed:** proceed to Step 8 (commit). **Any failures:**
report what failed — security issues, logic errors, regressions vs baseline, new lint errors, a
missing Verification Story, non-blocking suggestions — then proceed to Step 7. Failure report
template — `references/review-quality.md`.

## Step 7 — Auto-fix loop

**Maximum 2 fix-and-reverify cycles. Interactive sessions only (see Step 5).**

Spawn a THIRD agent context — not you (the implementer), not the reviewer. It fixes ONLY the
reported issues: no refactoring, no renames, no new features; it needs permission to edit files and
run commands. Brief: `references/reviewer-brief.md`.

After the fix agent completes, re-run Steps 1–6. Passed → Step 8; failed and attempts < 2 → repeat
Step 7; failed after 2 attempts → escalate to the user with the remaining issues and suggest
`git stash` or `git reset` to undo.

## Step 8 — Commit

If verification passed:

```bash
git add <file1> <file2>          # by path, never -A: the tree may hold someone else's work
git commit -m "<type>: <description>"   # message convention — see git-naming
```

The verification result goes into the report (command, key output, exit code), not into the commit
subject: `[verified]` breaks the `type: description` convention.

## Report with the change

Besides findings, the report answers three questions: **what changed** (files and behavior), **what
was deliberately not touched** (and why), **risks and assumptions** (what can break after merge). A
reviewer cannot approve what the author never declared. Details: `references/review-quality.md`.

## Receiving review: how to respond

Review findings are data to verify, not instructions to execute.

1. **Verify each finding before fixing it.** "Vacuous test" — mutate the code; "boundary collapses" — run the edge inputs; "dead code" — `grep` for zero uses. Some findings are taste.
2. **Do not apply blindly.** The reviewer lacks the decision context: a "fix per the note" can undo a deliberate choice. Disagree — answer with evidence, not with silence.
3. **Fix in a batch and re-run the gates** — the full verification cycle, not "fixed three of five".
4. **Separate outcomes in the report:** fixed (with evidence), rejected with a reason, owner decides.
5. **Do not argue about style** unless it breaks a contract. Formatting and naming follow the project's rules, not the reviewer's taste.

Full protocol — restate, verify, no agreement theater: `references/review-quality.md` §9.

## Integration with Other Skills

**subagent-driven-development:** run this after EACH task as the quality gate; the two-stage review
(spec compliance + code quality) uses this pipeline.

**test-driven-development:** this pipeline verifies TDD discipline was followed — tests exist, tests
pass, no regressions.

**plan:** validates implementation matches the plan requirements.

## Pitfalls

- **Empty diff** — check `git status`, tell user nothing to verify
- **Not a git repo** — skip and tell user
- **Large diff (>1000 lines or 20+ files)** — split by file, review each separately
- **Reviewer returns non-JSON** — retry once with stricter prompt, then treat as FAIL
- **False positives** — if reviewer flags something intentional, note it in fix prompt
- **No test framework found** — skip regression check, but say so in the report: `regression: skipped (no framework)`
- **Lint tools not installed** — skip, state it in the report (`lint: skipped (not installed)`), don't fail silently
- **Auto-fix introduces new issues** — counts as a new failure, cycle continues

## Files

- `references/review-quality.md` — two stages, five axes, severity, sizing, verification story, mutation, dependencies, failure-report template, report block, receiving review, common patterns.
- `references/security-checks.md` — static scan regexes, secrets, threat model, destructive paths, dependency audit.
- `references/whole-codebase-review.md` — the seven-step protocol for a whole-project review.
- `references/reviewer-brief.md` — the reviewer prompt and the fix-agent prompt.
- `references/gates.md` — baseline test and lint commands per stack.
