# Feedback loop: triage, construction, tightening

Reference for `systematic-debugging` Phase 1, step 2. The rule — a tight,
red-capable loop before any theory — is in `../SKILL.md`; this file holds the
detail.

## Non-reproducible? Triage by cause

- **Timing** — add timestamps around the suspected area, widen the race window with delays or load, run under concurrency.
- **Environment** — compare runtime versions, OS, env vars and data; reproduce in CI where the environment is clean.
- **State** — look for leaked state between tests or requests: globals, singletons, caches; run the scenario in isolation vs after other operations.
- **Truly random** — add defensive logging at the suspected site, alert on the error signature, document the conditions and revisit when it recurs.

## Ways to construct a loop — try in roughly this order

1. **Failing test** at the seam that reaches the bug: unit, integration, or end-to-end.
2. **HTTP script / curl** against a running dev server.
3. **CLI invocation** with fixture input, diffing stdout/stderr against expected output.
4. **Headless browser script** (Playwright/Puppeteer) asserting on DOM, console, or network.
5. **Replay a captured trace**: HAR, request payload, event log, queue message, or webhook body.
6. **Throwaway harness** that boots the smallest useful slice of the system and calls the failing path.
7. **Property / fuzz loop** when the bug is intermittent wrong output over a broad input space.
8. **Bisection harness** suitable for `git bisect run` when the bug appeared between two known states.
9. **Differential loop** comparing old vs new version, two configs, two providers, or two datasets.
10. **Human-in-the-loop script** only as a last resort: script the human steps and capture their result so the loop stays structured.

## Bisect instead of guessing

When the bug appeared between two known states, use the tight loop as the bisect predicate:

```bash
git bisect start
git bisect bad                  # current commit is broken
git bisect good <known-good-sha>
git bisect run <focused-test>   # the tight loop from step 2
git bisect reset
```

## Tighten the loop once it exists

- Make it faster: cache setup, narrow scope, skip unrelated initialization.
- Make the signal sharper: assert the exact symptom, not generic success.
- Make it more deterministic: pin time, seed randomness, isolate filesystem, freeze network.

For non-deterministic bugs, the immediate goal is a higher reproduction rate, not perfection. Run the trigger 100x, parallelize, add stress, narrow timing windows, or inject sleeps. A 50% flake is debuggable; a 1% flake usually is not.
