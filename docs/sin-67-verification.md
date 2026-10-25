# SIN-67 verification — core guest journey

## Result

- The connected local stub journey passed on desktop (1440 px) and mobile (375 px): question, full-stay search, room details, review, explicit confirmation, owned lookup and refresh. Desktop confirmation used keyboard focus and Enter.
- The browser used the real FastAPI routes and a separate disposable PostgreSQL `smart_hotels_test` database. The answer was a stub reply. No new Gemini request was made.
- No consequential T10 application defect was found. This task adds a repeatable connected browser check and records the evidence. It does not change guest behavior.

## Existing checks and gap closed

- Existing Python tests cover hotel unknown facts, full-stay inventory, booking recheck and replay, session ownership, provider failure and timeout cleanup. JavaScript SSE tests cover stream parsing. Earlier browser tests cover website and booking behavior with controlled API replies.
- Those checks did not give one current browser run through the full journey with a real local API and PostgreSQL. `frontend/tests/journey.browser.cjs` covers that gap. It needs a running local stub server and the disposable test database; it is not part of `scripts/check.ps1`.

## Commands and outcomes

- `uv sync --locked`: passed.
- `powershell -ExecutionPolicy Bypass -File scripts/test.ps1`: passed; 68 Python and 3 JavaScript tests. The script removed its test container.
- For the browser run, `docker compose --profile test up -d --wait test-db`, then `DATABASE_URL=postgresql://smart_hotels:local_test_only@127.0.0.1:55433/smart_hotels_test` with `uv run --locked python -m backend.app.db` and `uv run --locked python -m backend.app.inventory`: passed. The disposable container was recreated before the final run.
- With the same `DATABASE_URL` and `ASSISTANT_MODE=stub`, `uv run --locked uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --loop backend.app.runtime:new_loop --no-access-log`: started. `NODE_PATH=.local/node_modules node frontend/tests/journey.browser.cjs`: passed on 1440 and 375 px. Playwright was installed only in ignored `.local/` with `npm install --prefix .local playwright`.
- The browser confirmed that an unknown price policy returns `unknown`, five guests have no matching room, dates outside 1–7 November 2026 have unknown inventory, and review does not make a reservation. A lost booking response was simulated after the server committed. Refresh recovered the owned booking, and replay of the same request returned HTTP 200 with the same reference. The existing PostgreSQL booking test also asserts one row for a repeated request ID.
- Existing focused tests `test_provider_failure_empty_output_and_call_limit`, `test_stub_failure_does_not_save_or_block`, and `test_timeout_allows_new_turn_without_leaking_guest_text` passed in the full test run. These use failure simulation; they are not fresh provider incidents.

## Browser evidence

- [Desktop review](screenshots/sin-67-review-1440.png) and [desktop confirmation](screenshots/sin-67-confirmed-1440.png).
- [Mobile review](screenshots/sin-67-review-375.png) and [mobile confirmation](screenshots/sin-67-confirmed-375.png).

## Limits and next step

- The new browser run proves local stub behavior only. The earlier accepted M1 [foreground Gemini result](sin-62-foreground-browser.md) covered a grounded answer and saved source after refresh. It was a past run, not a new SIN-67 model result. A new paid Gemini check needs fresh approval and a call limit before execution.
- The fixture ends on 7 November 2026. The site is a fictional demo with no price, payment or real booking integration. T11 still needs approved-user access, cloud configuration and spending controls; this task creates no cloud resources.
