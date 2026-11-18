# Safe fallbacks and instrumentation

Reference for `systematic-debugging`. A fallback buys time; it is never the fix.

When the fix cannot land immediately, degrade safely instead of crashing:

- **Safe default + warning** — return the documented default and log a warning naming the missing input; a missing config value must not take the whole feature down.
- **Graceful degradation** — catch the failure at the boundary and render an explicit error or empty state, so the user sees "unavailable" instead of a blank page.
- A fallback is a stopgap, not a fix: it does not close the bug and needs its own note or ticket.

Logging is instrumentation, not code: add it only while it earns its keep, and remove it when done. Keep permanently: error boundaries with reporting, API error logs with request context, performance metrics on key user flows. Remove: temporary debug lines (tag them with a unique prefix so cleanup is one search) and anything containing secrets, tokens or PII — those go always, not sometimes.
