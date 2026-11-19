---
name: plan
description: "Use when writing a markdown plan; do not build."
version: 2.3.1
author: fhfqndj
license: MIT
platforms: [linux, macos, windows]
metadata:
  group: core
  tags: [planning, plan-mode, implementation, workflow, design, documentation]
  related_skills: [test-driven-development, requesting-code-review, verification-before-completion, subagent-driven-development, brainstorming]
---

# Plan Mode

Use this skill when the user wants a plan instead of execution.

## When to Use

- The user asks for a plan, a `/plan` run, or "plan first, don't build yet".
- A task needs a written, reviewable order of work before anyone edits code.
- If the goal is not agreed yet, run `brainstorming` first: a plan built on a guessed goal gets rewritten whole.

## Core behavior

For this turn, you are planning only.

- Do not implement code.
- Do not edit project files except the plan markdown file.
- Do not run mutating shell commands, commit, push, or perform external actions.
- You may inspect the repo or other context with read-only commands/tools when needed.
- Your deliverable is a markdown plan saved inside the active workspace, by default under the plan directory `plans/` (the plan directory and its path are set by the host).

## Output requirements

Write a markdown plan that is concrete and actionable.

Include, when relevant:
- Goal
- Current context / assumptions
- Proposed approach
- Step-by-step plan
- Files likely to change
- Tests / validation
- Risks, tradeoffs, and open questions

If the task is code-related, include exact file paths, likely test targets, and verification steps.

## Save location

Save the plan (write the file) under:
- `plans/YYYY-MM-DD_HHMMSS-<slug>.md`

Treat that as relative to the active working directory / workspace root: a relative path keeps the plan with the workspace on local, remote and container backends alike.

**The active directory is not always the project being planned.** If the session runs from a different repo or vault than the one the plan is about (for example the vault is open, while the target is a project in another directory), `plans/` under the CWD drops the plan into the wrong repository. Save by absolute path inside the target project — `<repo>/plans/YYYY-MM-DD_HHMMSS-<slug>.md` — and state that path in the reply. `plans/` is usually untracked: either add it to `.gitignore` or leave the plan out of the index, and say which you did.

If the runtime provides a specific target path, use that exact path. The exact plan directory is set by the host itself.
If not, create a sensible timestamped filename yourself under `plans/`.

## Existing plans: never start from a clean sheet

Before writing a new plan, check for unchecked items in the plans that already exist: `grep -rn '^- \[ \]' plans/*.md`.

- The new work extends an open plan → update it in place, or carry its unchecked items into the new plan with a link to the old file.
- It is unrelated work → carry the open items into the new plan as an explicit tail ("inherited from `<plan>`: N open items") or ask the user where they should go. Do not silently start clean: the open items may be mid-build in another session.
- Never delete, overwrite, or rename another plan's file to make room.

## Interaction style

- If the request is clear enough, write the plan directly.
- If no explicit instruction accompanies `/plan`, infer the task from the current conversation context.
- If it is genuinely underspecified, ask a brief clarifying question instead of guessing.
- After saving the plan, reply briefly with what you planned and the saved path.

### The user is thinking out loud — do not execute, do not write a plan file

Openings like "что будем делать?", "сегодня план такой…", "приступать не надо, просто думаю" mean conversational mode, not plan mode either: only reading and reconnaissance, and the reply is analysis — order of work, risks, and the decisions that stay with the user. Starting the work or creating `plans/*.md` is allowed on an explicit request only.

Before answering, rebuild the state from facts, never from memory alone: tail of `workspace/RUNS.md`, `git status --short --branch` for every active repo, the most recent session from past-session history (read its last messages), and `grep '^- \[ \]'` over `plans/*.md` for unchecked items. Only then propose what to do next.

Lay the options out as a numbered list in the message, not through a blocking question form: on an open "what shall we do" question the form sits waiting for up to an hour and leaves the turn unfinished, while text asks the same and does not block.

---

# Writing the Plan Well

The rest of this skill is the craft of authoring a *good* implementation plan — the content that goes inside the markdown file above.

## Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume the implementer is a skilled developer but knows almost nothing about the toolset or problem domain. Assume they don't know good test design very well.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## When a Full Implementation Plan Helps

**Always use before:** implementing multi-step features, breaking down complex requirements, delegating to subagents via subagent-driven-development.

**Don't skip when:** the feature seems simple (assumptions cause bugs), you plan to implement it yourself (future you needs guidance), or you're working alone (documentation matters).

## Bite-Sized Task Granularity

**Each task = 2-5 minutes of focused work.** Every step is one action: "write the failing test", "run it to make sure it fails", "implement the minimal code", "run the tests and make sure they pass", "commit". Too-big and right-size examples — `references/plan-template.md`.

## Task Size and Slicing

Size every task before writing it: XS–XL by number of files. L is split, and XL is split before it enters the plan — an implementer does best on S and M. A feature that spans UI and API is sliced vertically: one end-to-end path at a time, not "all backend, then all API, then all UI".

The sizing table, the four split triggers and the bad/good slicing example — `references/slicing.md`.

## Plan Document Structure

Every plan starts with the required header — Goal, Spec, Architecture, Tech Stack, Global
Constraints — then a task registry (`- [ ] Task N: …`), and every task follows one shape: objective,
Interfaces (Consumes / Produces), 2–3 checkable acceptance criteria, files (create/modify/test, exact
paths), then five steps: failing test → run it (expected FAIL) → minimal implementation → run it
(expected PASS) → commit. Copy-paste templates — `references/plan-template.md`.

The registry is the executor's queue: `subagent-driven-development` reads `- [ ]` lines from this
file and flips them after acceptance. A plan without a registry gets one added before execution —
not rebuilt from `###` headings, which do not say what is done.

When a criterion has more than one condition, write it as a Given/When/Then scenario — the format is in `brainstorming/references/spec-template.md` §7.

## Writing Process

### Step 1: Understand Requirements

Read the feature requirements, design documents or user description, acceptance criteria and constraints. **Re-verify any earlier audit, note, or TODO list the plan is based on.** Audits decay: by planning time items may be fixed, half-fixed, or misdescribed. Open each referenced `file:line` and classify every inherited item as `closed`, `partial` (state what exists and what is missing), or `still true`. A stale claim does not just waste a task — it hides the real gap ("no checkpoints" often means the resume data exists but nothing commits it). The plan quotes current `file:line`, never the audit's.

### Step 2: Explore the Codebase

Read-only: find files by mask (for example `src/**/*.py`) to map the project structure; find code by content — the pattern of a similar feature; find tests by mask (`tests/**/*.py`) to see what already exists; read the key files in full before deciding anything.

### Step 3: Design Approach

Decide the architecture pattern, file organization, dependencies needed, and testing strategy.

### Step 4: Write Tasks

Order: setup/infrastructure → core functionality (TDD for each) → edge cases → integration → cleanup/documentation. For a feature that spans UI and API, replace this layer-first order with vertical slices — one working end-to-end path per task; see `references/slicing.md`.

### Step 5: Insert Checkpoints

Insert a checkpoint after every 2–3 tasks, so a broken phase does not leak into the next one. A checkpoint is a checklist, not a paragraph: tests pass with a command and 0 failed, build succeeds with exit 0, the end-to-end scenario works, and the human has looked at the result (shape — `references/plan-template.md`).

The last line is not decoration: a checkpoint nobody looks at is a line in a file. Run the checks yourself and quote fresh output — an implementer's report is not evidence (see `verification-before-completion`).

### Step 6: Add Complete Details

For each task, include **exact file paths** (not "the config file" but `src/config/settings.py`), **complete code examples** (not "add validation" but the actual code), **exact commands** with expected output, and **verification steps** that prove the task works.

### Step 7: Review the Plan

Check:
- [ ] Tasks are sequential and logical
- [ ] Each task is bite-sized (2-5 min)
- [ ] Each task carries 2–3 checkable acceptance criteria; a task is closed only when they pass together with the project's standing bar (the `definition-of-done` reference inside `verification-before-completion`)
- [ ] Every task has an `Interfaces` line: what it consumes and what it produces for the next task
- [ ] The task registry exists (`- [ ] Task N: …`) and matches the `### Task N` sections
- [ ] File paths are exact
- [ ] Code examples are complete (copy-pasteable)
- [ ] Commands are exact with expected output
- [ ] No missing context
- [ ] DRY, YAGNI, TDD principles applied

### Step 8: Pre-mortem the Plan

Assume the plan failed. The question is not "will this work?" but "it is three weeks from now and this failed — why?" Write 3–5 failure narratives, each with a trigger, number or threshold, and the chain to how it would be noticed; rank by likelihood × impact into the plan's `## Risks and Mitigations`; run the inversion "what would guarantee this fails?".

**Gate:** a plan is not handed off until 2–3 named failures, their early signs and the check that catches them are written down. Full method — `references/pre-mortem.md`.

## Principles

### Order by Cost of Failure

Sequence work by what breaks when it breaks, not by ease or file layout: money spent twice or work lost mid-run first, data quality second, infrastructure third, cosmetic debt last. Group items that share one mechanism into one wave (checkpoints + cancellation + lease are the same machinery), so they are built and tested together.

### DRY (Don't Repeat Yourself)

Copy-paste validation in 3 places is a bug: extract a validation function and use it everywhere.

### YAGNI (You Aren't Gonna Need It)

Implement only what's needed now and add no "flexibility" for future requirements. Bad/good example — `references/plan-template.md`.

### TDD (Test-Driven Development)

Every task that produces code includes the full cycle: write failing test → run to verify failure → write minimal code → run to verify pass. See the `test-driven-development` skill.

### Frequent Commits

Commit after every task:
```bash
git add [files]
git commit -m "type: description"
```

## Common Mistakes

Vague tasks, incomplete code, missing verification and missing file paths all produce a plan nobody can execute; bad/good pairs for all four — `references/plan-template.md`. The rule behind them: a task names the exact path, carries copy-pasteable code, and ends with the command and the expected output.

## Execution Handoff

After saving the plan, offer the execution approach:

**"Plan complete and saved. Ready to execute using subagent-driven-development — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"**

When executing, use the `subagent-driven-development` skill:
- A fresh subagent per task, each with full context
- Spec compliance review after each task
- Code quality review after spec passes
- Proceed only when both reviews approve
- Each task ends with the `verification-before-completion` gate: fresh command output, not the child's report

## Files

- `references/slicing.md` — task sizing XS–XL, the four split triggers, vertical slices for features that span UI and API, and task ordering.
- `references/plan-template.md` — header, task and checkpoint templates; granularity, common-mistake and YAGNI examples.
- `references/pre-mortem.md` — the full pre-mortem method for Step 8.

## Remember

```
Bite-sized tasks (2-5 min each)
Exact file paths
Complete code (copy-pasteable)
Exact commands with expected output
Verification steps
DRY, YAGNI, TDD
Frequent commits
```

**A good plan makes implementation obvious.**
