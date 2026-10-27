# SIN-66 verification — essential safeguards

## Result

- API POST requests have a 16 KiB body limit, leaving room for a 2,000-character UTF-8 chat message. Oversized requests return HTTP 413 before a route writes data. The limit also applies when Content-Length is absent.
- A simulated reply timeout leaves the turn interrupted. The guest can send a new turn and sees only completed history. The response and application log do not contain the private guest text.
- Existing ownership, safe text rendering, booking replay, context limits and provider timeouts remain in place. No Gemini model setting changed.
- PLAN.md and README.md now show M2 as accepted after SIN-65 and PR #10 were merged.

## Checks

- `uv sync --locked`: passed.
- `scripts/check.ps1`: passed with database tests skipped because no test database was set.
- `scripts/test.ps1`: passed with its separate disposable `smart_hotels_test` PostgreSQL container; 68 Python and 3 JavaScript tests passed. The script removed the container.
- The new focused tests cover oversized chat, booking and session POST bodies, plus a reply timeout, safe error, cleanup, retry and private text in logs.
- No paid model call or cloud change was made.

## Before public access

- The first cloud demo must have restricted access. Choose the approved-user sign-in method in T11, then configure the deployment origin, HTTPS cookie and Cloud Run request timeout for the existing 90-second chat deadline. Access control alone does not cap cloud spending.
- Complete T10 journey checks and T11 deployment work. Set a spending limit and alerts before enabling Vertex in a public deployment.
- Review fictional hotel content and demo inventory dates. The fixture only covers 1–7 November 2026. Reservations remain demo only; no real inventory or payment integration exists.
- Set retention, backup and rollback procedures in T12. Guest sessions expire after 24 hours and have no account recovery.
