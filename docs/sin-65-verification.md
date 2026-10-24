# SIN-65 verification — demo reservations

## Result

- A guest can search, open room details, review a stay and choose **Confirm demo reservation**. Search, details and review are read-only. The Ask chat has no booking tool.
- A booking transaction checks the property dates, party size, room capacity, every fixture night and existing bookings. PostgreSQL also rejects overlapping room stays.
- A request UUID returns the same booking for a repeat with the same owner and selection. A changed selection or another owner gets 409. The browser keeps the UUID through refresh and can recover a committed booking after a lost response.
- Reference and request lookup require the owning guest session. A reference alone is not access.
- Availability includes booked nights. Reimport of the same fixture and publication of a new version with the same room IDs do not reopen booked nights.
- The active hotel revision is v2. It describes the new demo action; v1 remains available for old citations. No price, payment or real hotel integration was added.

## Checks

- `uv sync --locked`: passed.
- `scripts/check.ps1`: passed before the database run.
- `scripts/test.ps1`: passed with its disposable PostgreSQL container; 64 Python tests and 3 JavaScript SSE tests passed. The container was removed by the script.
- `node frontend/tests/booking.browser.cjs`: passed in Chrome at 375 and 1440 px with controlled API replies. It covered search → room details → review → confirmation, refresh, lost response recovery, Ask launcher visibility and horizontal overflow. The controlled browser test did not write to PostgreSQL.
- Screenshots: [mobile review](screenshots/sin-65-review-375.png), [mobile confirmation](screenshots/sin-65-confirmed-375.png), [desktop review](screenshots/sin-65-review-1440.png), [desktop confirmation](screenshots/sin-65-confirmed-1440.png).
- `git diff --check`: passed. No Gemini call or cloud change was made.

## Focused failure handling

- The first database run found that the new test shared room IDs with the older availability test and that the migration test expected four files. I gave the new test separate room IDs and updated the migration expectation. Only the affected database tests were repeated.
- The next run found a test-only cookie left in `TestClient` before the no-cookie lookup. I cleared that cookie and repeated only the booking test.
- Playwright was missing from the worktree. I installed it under ignored `.local/` and ran the browser test once. The final full checks ran after the hotel revision was updated.

## Limitations

- Demo sessions last 24 hours and have no account recovery. The guest needs the same live session to see a booking.
- The supplied fixture nights cover only 1–7 November 2026. Later dates need a reviewed new fixture version.
- The browser check uses controlled API replies. The PostgreSQL tests prove the write and isolation rules separately. No paid model call was needed.
