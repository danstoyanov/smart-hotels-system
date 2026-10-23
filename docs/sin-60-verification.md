# SIN-60 verification

Checked on Windows on 23 October 2026 with Python 3.13.2 and the locked dependencies.

- `uv sync --locked`: passed; no dependency changes.
- `uv run --locked python -m backend.app.hotel`: passed for the complete catalogue.
- `scripts/check.ps1`: lint, formatting, JavaScript syntax and 32 tests passed.
- Two existing PostgreSQL tests were skipped locally. Docker is not installed in
  this environment; the PR CI supplies a disposable PostgreSQL service.
- 27 focused hotel tests cover complete rooms/amenities/policies, explicit unknowns,
  missing IDs, malformed read inputs, JSON/schema errors, dates, duplicate IDs,
  invalid references, path escape rejection, safe reload failure/retry, unchanged
  revision protection, old-version reads after restart, API status codes and hotel
  identity mismatch. No database or model is needed for these hotel reads.
- `git diff --check`: passed.

The existing Starlette/httpx test-client deprecation warning remains. No frontend
visual changes were made, so no new screenshots are needed. This task does not add
availability search, reservations, cloud resources, model calls or integrations.

Policy examples were consulted from the pinned reference at the user's request.
The data and code here were written locally. All hotel facts are fictional demo
content. Prices, currency and service fees remain unknown. Hotel versions are
local files, not database imports. Reload keeps a last good snapshot within a
process; after restart, archived-file immutability relies on the documented editing
rule and Git review. Every server process must restart after a file update.
