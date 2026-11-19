# Safe fallbacks and instrumentation

Reference for `systematic-debugging`. A fallback buys time; it is never the fix.

When the fix cannot land immediately, degrade safely instead of crashing:

- **Safe default + warning** — return the documented default and log a warning naming the missing input; a missing config value must not take the whole feature down.
- **Graceful degradation** — catch the failure at the boundary and render an explicit error or empty state, so the user sees "unavailable" instead of a blank page.
- A fallback is a stopgap, not a fix: it does not close the bug and needs its own note or ticket.

Logging is instrumentation, not code: add it only while it earns its keep, and remove it when done. Keep permanently: error boundaries with reporting, API error logs with request context, performance metrics on key user flows. Remove: temporary debug lines (tag them with a unique prefix so cleanup is one search) and anything containing secrets, tokens or PII — those go always, not sometimes.

## External cause

Not every bug has a root cause you can fix: the cause may be a third-party service, a platform
timer, data you do not own, or a race in someone else's binary. The Iron Law is not a promise that
the cause is reachable — it is a promise that you do not patch symptoms without one.

This exit opens only when Phase 1 shows **both**: the trigger is external **and** the local handling
is correct. An external trigger routinely exposes a local defect — a missing `try`, an unchecked
response, a retry storm. Proof before using it: the code receives correct inputs and does what the
contract says (call path, logs, a test that pins its behaviour). Without that proof you are back in
Phase 2 with a local suspect.

Once the local side is clean, do three things:

1. **Document what you measured:** which input, environment, version or timing reproduces it, and
   what you ruled out.
2. **Contain instead of patch — test-first.** A guard, a bounded retry or a fallback changes
   behaviour, so it starts with a failing test on the refusal path (TDD), and the note says this is
   containment, not a fix.
3. **Hand it over:** an issue with the measurement, a version pin, a monitoring signal that fires
   when it recurs. Say plainly in the report that the root cause is outside the codebase.

**Do not** loop back to Phase 1 forever, and do not present containment as a fix. A documented
external cause — with the local side proven clean and a regression test on the containment — is a
finished investigation; an unexplained patch is not.

