# SIN-64 verification — 24 October 2026

## Result

T07 adapts the user-supplied design for the existing one-hotel app. It adds
responsive home and room pages, a full-stay search form, and a selection review.
The review makes no booking write and shows no confirmation action. The existing
chat session, history and SSE code remains in place. Hotel facts come from
`hotel/` through the backend. The page does not show sample prices, awards,
reviews, locations or services from the design reference.

The chat now opens from a fixed Ask button on every page. It keeps one shared
conversation window and uses the same session, history and chat API. The window
can be opened and closed with the keyboard, and Escape returns focus to the button.
The navigation logo uses a larger gold fleur-de-lis and a larger hotel name.
The Ask button keeps its star.

## Check

- Confirmed SIN-63 is Done in Linear and PR #8 is merged before starting.
- `uv sync --locked` passed in the managed SIN-64 worktree.
- `scripts/check.ps1` passed: lint, format, JavaScript syntax, hotel validation,
  three SSE tests and 48 Python tests; 15 database tests were skipped without
  a test URL.
- `scripts/test.ps1` passed against its separate disposable PostgreSQL
  container: 63 Python tests, the static checks above and three SSE tests.
  The script removed the test container.
- `frontend/tests/guest.browser.cjs` passed in Chrome at 375, 768 and 1440 px.
  It checked no horizontal overflow, two room cards, three amenities, six
  policies, local image loading, chat readiness, room detail links, keyboard
  focus, availability results, review with no confirmation control, empty and
  unavailable states, and console output. The intentional HTTP 503 fixture
  produced one expected browser resource error; no other console errors appeared.
- Screenshots: [mobile 375 px](screenshots/sin-64-375.png),
  [desktop 1440 px](screenshots/sin-64-1440.png), and
  [selection review](screenshots/sin-64-review.png).
- Follow-up chat change: `uv sync --locked` and `scripts/check.ps1` passed
  (48 Python tests, 15 database tests skipped, three SSE tests). The guest
  browser check passed at 375, 768 and 1440 px, including the fixed button,
  keyboard open/close, focus and overflow. The chat browser check passed on
  desktop and mobile with controlled API replies for send, history, reset,
  stop and error recovery. The assistant browser check passed for safe text,
  source links, history and reset in the window. [Open chat at 375 px](screenshots/sin-64-chat-375.png)
  and [open chat at 1440 px](screenshots/sin-64-chat-1440.png) show the result.
- The logo follow-up passed the guest browser check at 375, 768 and 1440 px.
  A separate 789 px visual check confirmed the larger brand fits the navigation.
  The 375 px view keeps the brand and availability button on one row, with no
  horizontal overflow.

## Limits and next step

The browser check uses controlled API replies for UI state and does not use
the application database for tests. The backend search was covered by the
separate PostgreSQL suite. Screenshots use stub chat mode. No paid Gemini
requests or cloud resources were used. T08 will add explicit demo reservation
confirmation after this PR is accepted and merged.
