# Baseline test and lint commands

Reference for `requesting-code-review` Step 3. Detect the project language and
run the appropriate tools.

## Test frameworks (auto-detect by project files)

```bash
# Python (pytest)
python -m pytest --tb=no -q 2>&1 | tail -5

# Node (npm test)
npm test -- --passWithNoTests 2>&1 | tail -5

# Rust
cargo test 2>&1 | tail -5

# Go
go test ./... 2>&1 | tail -5
```

## Linting and type checking (run only if installed)

```bash
# Python
which ruff && ruff check . 2>&1 | tail -10
which mypy && mypy . --ignore-missing-imports 2>&1 | tail -10

# Node
which npx && npx eslint . 2>&1 | tail -10
which npx && npx tsc --noEmit 2>&1 | tail -10

# Rust
cargo clippy -- -D warnings 2>&1 | tail -10

# Go
which go && go vet ./... 2>&1 | tail -10
```

## Baseline comparison

Capture the failure count BEFORE your changes as **baseline_failures** (stash
changes, run, pop). Only NEW failures introduced by your changes block the
commit. If baseline was clean and your changes introduce failures, that's a
regression. If baseline already had failures, only count NEW ones.
