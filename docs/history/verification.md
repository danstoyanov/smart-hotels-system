# SIN-59 verification

**Closure — 24 October 2026:** PR #2 is merged and SIN-59 is Done. The checks
below are historical development evidence; none were rerun for this update.
See [M1 handover](../m1-handover.md) for current scope and next work.

Checked on Windows on 23 October 2026 with Python 3.13.2, uv 0.13.4,
Node.js 22.21.0, Docker Desktop 4.96.3 and Docker Compose 5.6.1.

- `uv sync --locked`: passed.
- `docker compose up -d --wait db`: healthy on loopback port 5432.
- Migration CLI: applied `001_foundation.sql`; second run reported up to date.
- `scripts/test.ps1`: seven tests passed; no skips. The test container was removed.
- Ruff lint, Ruff format and Node syntax checks: passed.
- `scripts/start.ps1`: migration check and reload server started successfully.
- Live `/api/health`: HTTP 200, database ok; no model dependency or call.
- Desktop 1440 × 1000 and mobile 390 × 844: page is readable, connection button
  works and content has no horizontal overflow. Screenshots are in `screenshots/`.
- `git diff --check`: passed.

The current Starlette test client emits a deprecation warning for httpx. Tests pass;
this does not affect the application runtime. The page is a demo foundation only.
No hotel data, chat, reservations, model calls or cloud resources were added.

Windows startup uses `backend.app.runtime:new_loop` because Psycopg async
connections require a selector event loop. The migration CLI and tests use the
same loop factory.
