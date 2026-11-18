# Pre-mortem

Reference for `plan` Step 8. The gate itself — a plan is not handed off until
2–3 named failures, their early signs and the check that catches them are
written down — is in `SKILL.md`.

## Step 8: Pre-mortem the Plan

Assume the plan failed. The question is not "will this work?" but "it is three weeks from now and this failed — why?" (pre-mortem).

- **3–5 failure narratives.** Each names a specific trigger, a number or threshold where one exists, and the chain: trigger → first-order effect → second-order effect → how it would be noticed. "It didn't scale" is not a narrative; "the nightly import hits the 30-minute worker limit at ~40k rows, retries stack up, and the queue backs up for hours" is.
- **Rank by likelihood × impact**, keep the top ones in the plan's `## Risks and Mitigations` section (add it to the document if missing), each with an early warning sign and the first check that would catch it.
- **Run the inversion:** "what would guarantee this fails?" — no tests on the data path, one person owning a weekend deploy, a dependency with no lockfile. If any of those conditions already exists, it is a finding, not a hypothetical.
- **Gate:** the plan is not handed off until 2–3 named failures, their early signs and the check that catches them are written down. A plan with no failure modes was not stress-tested.
