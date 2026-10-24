# SIN-61 verification

**Closure — 24 October 2026:** PRs #4 and #5 are merged and SIN-61 is Done.
The sections below describe the T04 implementation and its checks at the time;
T05 later added the real model. Old pending-merge statements are historical.
See [M1 handover](m1-handover.md) for current scope and limits.

## Result

Guest cookies own database-backed conversations. Refresh restores completed turns;
New conversation rotates the conversation ID. Fetch/SSE shows provisional text and
reports completion only after the answer commit. The response adapter is a local
stub, with no model calls. Origin checks, expiry, duplicate rejection and disconnect
cleanup are part of this change.

## Checks

- `uv sync --locked` completed on Windows with Python 3.13.2.
- Local lint, format, JavaScript syntax, hotel validation and Python checks passed.
  PostgreSQL tests skip locally because Docker is unavailable.
- GitHub CI uses disposable PostgreSQL 17.6. Run 39941736164 passed all 47 tests,
  including real session ownership, reset, expiry, duplicate, concurrent admission,
  interrupted streams, stale-worker fencing, failed saves and restart history tests.
  A final CI run also checks the latest-20 history bound and readiness migration.
- Node SSE tests passed for split frames, split UTF-8, invalid JSON and truncation.
- `frontend/tests/chat.browser.cjs` passed in installed Chrome through the bundled
  Playwright runtime at 1440px and 390px. It checks send, safe text, reload, reset,
  Stop, enabled controls, page errors and horizontal overflow. It uses controlled
  API fixtures, not a local database. Start the app and run it with Playwright
  available in NODE_PATH; CHAT_TEST_ORIGIN defaults to http://127.0.0.1:8061.
- Desktop/mobile screenshots show those UI fixtures, not a live database/model.
  Both were inspected: labels, focusable controls, wrapping and spacing fit.
- The UI detector reports the inherited Arial font and cream background. This
  scoped change keeps the existing page's typography and palette. No design-system
  files were changed. The issue prohibits other agents, so checks stayed local.

## Limits and next step

Local HTTP uses a non-Secure cookie; HTTPS must use COOKIE_SECURE=true and an exact
APP_ORIGIN. Sessions last 24 hours. People sharing a browser share its credential.
Reset changes the visible conversation, not database retention. One session can
have one active turn; a failed cleanup can remain busy until its two-minute lease
expires. There is no replay/status endpoint or model integration in this task.
The user reviews and merges the PR, then accepts the criteria before SIN-61 is Done.

## Self-review after merge

- Checked SIN-61 and PLAN sections 1 and 3–5 against guest ownership, completed
  history after refresh, conversation reset and interrupted requests. Ownership
  comes only from the session cookie; reset rotates only that session's conversation.
- Read REFERENCE.md and consulted only the pinned example's session/history and
  streaming code. Its stream-reader cleanup highlighted an open-response defect:
  our parser released its lock without cancelling on parse/handler failures.
- Fixed that cleanup and added a regression that failed before the fix and passed
  after it. No endpoints or advanced recovery features were added.
- Three focused SSE tests passed. Desktop/mobile browser checks passed, including
  Stop, failed reply followed by a successful message, refresh and reset. These use
  API fixtures. The local session suite passed its cookie check and skipped eleven
  PostgreSQL checks because Docker is unavailable; follow-up CI runs the real DB tests.
- Remaining limits are unchanged: a local response stub, fixed 24-hour sessions,
  reset without data deletion, and up to two minutes busy after process/cleanup
  failure. The follow-up PR needs user review and merge.
