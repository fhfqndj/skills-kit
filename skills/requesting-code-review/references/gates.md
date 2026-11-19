# Baseline test and lint commands

Reference for `requesting-code-review` Step 3. Detect the project language and run the appropriate
tools.

## Test frameworks (auto-detect by project files)

Every command goes through `log`: it keeps the exit code (a piped `| tail` would return 0 and hide
the failure) and prints the last lines of output.

```bash
log() {
  desc="$1"; shift
  out="$(mktemp)"
  "$@" >"$out" 2>&1
  rc=$?
  echo "== $desc → exit $rc"
  tail -5 "$out"
  rm -f "$out"
  return $rc
}

# Python (pytest)
log pytest python3 -m pytest --tb=no -q

# Node (npm test)
log npm npm test -- --passWithNoTests

# Rust
log cargo cargo test

# Go
log go go test ./...
```

## Linting and type checking (run only if installed)

`log` is defined in the block above — run that block first in the same shell. `run_if` prints the
skip instead of staying silent, as the rule below requires.

```bash
run_if() {
  tool="$1"; shift
  command -v "$tool" >/dev/null || { echo "lint: skipped ($tool not installed)"; return 0; }
  log "$@"
}

run_if ruff ruff check .
run_if mypy mypy . --ignore-missing-imports
run_if npx npx eslint .
run_if npx npx tsc --noEmit
run_if cargo cargo clippy -- -D warnings
run_if go go vet ./...
```

## When a tool is missing

A skipped gate is an event, not silence: the report carries `regression: skipped (no framework)` or
`lint: skipped (not installed)`. A silent skip turns a green report into a false one.

## Baseline comparison

Capture the failure count BEFORE your changes as **baseline_failures** (stash changes, run, pop).
Only NEW failures introduced by your changes block the commit. If baseline was clean and your
changes introduce failures, that's a regression. If baseline already had failures, only count NEW
ones.
