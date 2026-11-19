# Plan document template and examples

Reference for `plan`: the exact shapes a plan document uses, and the bad/good
examples behind the rules in `SKILL.md`.

## Plan Document Structure

### Header (Required)

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For the implementing agent:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** [One sentence describing what this builds]

**Spec:** `<path>/SPEC.md` — or `none: the restate agreed in chat is the spec`

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

**Repository:** `<path>` — work on branch `<branch>`

**Global Constraints:** [the project's standing bar — coverage, lint, permissions, size limits;
link `CONSTRAINTS.md` when the project has one. A constraint with no command is not a constraint.]

**Non-goals:** [cut option — the rung that beat it, one per line; `—` when nothing was cut]

---
```

### Task registry

Directly after the header — the only list the executor reads as a to-do queue. One line per task,
same numbering as the sections below:

```markdown
## Tasks

- [ ] Task 1: [name]
- [ ] Task 2: [name]
- [ ] Task 3: [name]
```

A task without a registry line does not exist for the executor. Keep the registry and the
`### Task N` sections in sync; status lives only in this list.

### Task Structure

Each task follows this format:

````markdown
### Task N: [Descriptive Name]

**Objective:** What this task accomplishes (one sentence)

**Interfaces:** Consumes: [signatures, files, data this task relies on] · Produces: [what the next
task may rely on]. Without this line the executor of task 3 does not see task 1's contract.

**Acceptance criteria** (2–3 checkable items, not more):
- [ ] [Specific, testable condition]
- [ ] [Specific, testable condition]

When a criterion has more than one condition, write it as a Given/When/Then scenario — the format is in `brainstorming/references/spec-template.md` §7.

**Acceptance command:** the one command that must pass for this task (`make test`, `pytest tests/… -q`)

**Files:**
- Create: `exact/path/to/new_file.py`
- Modify: `exact/path/to/existing.py:45-67` (line numbers if known)
- Test: `tests/path/to/test_file.py`

**Step 1: Write failing test**

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify failure**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: FAIL — "function not defined"

**Step 3: Write minimal implementation**

```python
def function(input):
    return expected
```

**Step 4: Run test to verify pass**

Run: `pytest tests/path/test.py::test_specific_behavior -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
````

## Bite-Sized Task Granularity

**Too big:**
```markdown
### Task 1: Build authentication system
[50 lines of code across 5 files]
```

**Right size:**
```markdown
### Task 1: Create User model with email field
[10 lines, 1 file]

### Task 2: Add password hash field to User
[8 lines, 1 file]

### Task 3: Create password hashing utility
[15 lines, 1 file]
```

## Checkpoint shape

A checkpoint is a checklist, not a paragraph:

```markdown
## Checkpoint: after Tasks 1–3
- [ ] Tests pass: `pytest -q` → 0 failed
- [ ] Build succeeds: `npm run build` → exit 0
- [ ] The end-to-end scenario works: `<exact command or URL>`
- [ ] The human has looked at the result
```

## Common Mistakes

### Vague Tasks

**Bad:** "Add authentication"
**Good:** "Create User model with email and password_hash fields"

### Incomplete Code

**Bad:** "Step 1: Add validation function"
**Good:** "Step 1: Add validation function" followed by the complete function code

### Missing Verification

**Bad:** "Step 3: Test it works"
**Good:** "Step 3: Run `pytest tests/test_auth.py -v`, expected: 3 passed"

### Missing File Paths

**Bad:** "Create the model file"
**Good:** "Create: `src/models/user.py`"

## Minimal solution ladder

Run this once in Step 3, before choosing patterns and dependencies. Take the first rung that fully
works; a rung that only partly works is not a rung.

| # | Rung | Question |
|---|---|---|
| 1 | Does it need to exist? | Which part of the request would we drop, and who notices? |
| 2 | Already in this codebase | Is there a helper, component, service or pattern doing this? Use it the way neighbours do. |
| 3 | Standard library or platform feature | Does the language or the platform already do it? A house component beats a native widget only when it exists. |
| 4 | An installed dependency | Does a dependency we already ship do it? Never add a dependency for a few lines. |
| 5 | One line | Can it be one line a reader understands at a glance? |
| 6 | The minimum that works | Only now write code — the smallest version that covers the task. |

Lazy about the solution, not about the change: read the code the change touches, and never cut
validation, error handling, security, accessibility or a test for non-trivial logic.

Example — «экспорт CSV»: not a new package with its own writer (rung 4 beaten by rung 3), not a
`pyexcel` dependency for ten columns; `csv` from the standard library over the existing
`iter_users()` — six lines, one test.

Every cut option goes to `Non-goals` in the header with the rung that beat it.

## YAGNI example

```python
# Bad — YAGNI violation
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.preferences = {}  # Not needed yet!
        self.metadata = {}     # Not needed yet!

# Good — YAGNI
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```
