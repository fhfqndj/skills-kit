# Whole-codebase review

Reference for `requesting-code-review`. When the ask is a review of the project,
architecture, or backend, not a diff, the step pipeline in `SKILL.md` does not
fit. Do this instead.

## Whole-codebase review (user says «проведём ревью»)

1. **Commit before reviewing.** Reports cite `file:line`; uncommitted edits move them. Also split
   mechanical work (comment trimming, renames) from review into separate commits, otherwise the
   reviewer reads a half-edited tree.
2. **Split by angle, not by folder**, one subagent per angle, all dispatched in one batch:
   backend senior (layer boundaries, transactions, auth/permissions, schema, queue, error handling,
   tests), architecture boundaries (where layers blur, where a cheap seam pays off), frontend
   (layers, data fetching, state, a11y, types, dead code). Same repo, overlapping files — that is
   fine, reviewers only read.
3. **Fence the scope in the user's own words.** If they said "splitting into microservices is the
   future; we are not planning it", write exactly that plus "do not propose brokers, k8s, or a
   migration plan" — otherwise the architecture report turns into a roadmap nobody asked for.
4. **Demand actionable findings, not impressions.** Format per finding: `[severity]
   [area] file:line — problem. Why it hurts. Concrete fix (1–3 sentences, no "think about it" or
   "refactor").`
   Cap the count (10–15) so the list is a plan, not a dump.
5. **Require two closing blocks:** "what is already done well" and "what must NOT be touched now" —
   they stop a rewrite where a fix would do, and they expose a reviewer that did not really read the
   code.
6. **Reviewers must not edit.** Tell them read-only: reading/searching via the native tools and
   running `pytest`/`ruff`/`tsc` is fine, edits and commits are not. Claims like "dead code" are
   valid only with a search showing zero uses.
7. **Synthesise, present, then implement.** Merge duplicates, drop what contradicts the user's
   stated direction, show the user the ranked list before touching code — implementation is a
   separate stage they approve.
