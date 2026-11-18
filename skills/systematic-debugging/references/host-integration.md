# Host integration

Reference for `systematic-debugging`. Tool names, delegation mechanics and path
conventions are host-specific; the capabilities below are what the process
needs.

## Investigation capabilities

During Phase 1 you need four capabilities from your host:

- **Search files** — find error strings, trace function calls, locate patterns.
- **Read files** — read source with line numbers for precise analysis.
- **Run commands** — run tests, check git history, reproduce bugs.
- **Web research** — look up error messages and library docs.

## With a subagent

For complex multi-component debugging, dispatch investigation subagents. Give each one:

- the full error text, the failing file path and the exact test command;
- the brief: follow systematic-debugging — read the error carefully, reproduce it, trace the data flow to the root cause, report findings, do NOT fix yet;
- read-only access to the repo and permission to run commands.

## With test-driven-development

When fixing bugs:
1. Write a test that reproduces the bug (RED)
2. Debug systematically to find root cause
3. Fix the root cause (GREEN)
4. The test proves the fix and prevents regression
