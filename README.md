# Smart Hotels System

A local foundation for Royal Crest Manor, a fictional demo hotel. FastAPI serves the
website and API on the same origin. PostgreSQL holds application state. Local
`hotel/` files provide validated demo rooms, amenities, policies and inventory fixtures. The chat uses a local response stub. There are no model calls or reservation operations yet.

## Requirements

- Python 3.13 (uv can install it), uv 0.13.4 and Node.js 22 for the JavaScript check.
- Docker Desktop running with Linux containers and Docker Compose v2 or newer.
- PowerShell 7 or Windows PowerShell 5.1.

## First setup (PowerShell)

Run commands from the repository root. Do not overwrite an existing `.env`.

```powershell
uv python install 3.13
uv sync --locked
Copy-Item .env.example .env
docker compose up -d --wait db
.\scripts\start.ps1
```

Open http://127.0.0.1:8000. The website, `/assets/*`, `/api/site` and `/api/health`
share that origin. The server binds to loopback only. Stop it with Ctrl+C.
If your PowerShell policy blocks scripts, use a one-process override:
`powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1`.

`start.ps1` runs migrations before starting the server. To run each step directly:

```powershell
uv run --locked python -m backend.app.db
uv run --locked uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --loop backend.app.runtime:new_loop --reload
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

The health endpoint returns HTTP 200 only when PostgreSQL answers and the guest-session
migration exists. It returns a safe HTTP 503 response on failure; it never calls a
model. It has a five-second deadline. Database connection details stay private.
The page can still load while PostgreSQL is unavailable.

## Configuration

`.env` is ignored by Git. `.env.example` has public local demo credentials only;
never use them for a deployed database. Environment variables override `.env`.

| Setting | Default / purpose |
| --- | --- |
| `DATABASE_URL` | Local PostgreSQL connection; keep private outside this demo |
| `HOTEL_NAME` | Royal Crest Manor |
| `HOTEL_LANGUAGE` | `en` (initial interface copy is English) |
| `HOTEL_TIMEZONE` | `Europe/Kyiv`, a validated IANA timezone |

Changing language metadata does not translate the English page. No Google Cloud
credentials or Gemini settings are needed yet. Later tasks add the model adapter.

## Migrations

Add numbered SQL files to `backend/migrations/`; never edit an applied file.
The migration command uses one transaction, a database advisory lock, and a checksum
ledger. A repeat run makes no changes. A failed run rolls back the whole batch;
fix the new file and run again. The initial migration creates only the ledger;
feature tables belong to later tasks. Hotel information is read from local files
and does not need a database seed. See [hotel/README.md](hotel/README.md) for editing,
validation, reload commands and the `/api/hotel/*` read API.

## Hotel information

Run `uv run --locked python -m backend.app.hotel` to validate the complete demo
catalogue. FastAPI loads a validated snapshot at startup. Reads include a source ID,
version and demo label. Missing facts are explicit; no model fills in the gaps.
See [hotel/README.md](hotel/README.md) for the data format and safe version updates.

## Checks and disposable database

```powershell
.\scripts\check.ps1   # lint, format, JavaScript syntax and unit tests
.\scripts\test.ps1    # same checks plus real PostgreSQL integration tests
```

`test.ps1` starts a separate `test-db` container on loopback port 55433. Its database
is `smart_hotels_test`, with memory-backed storage. The script removes this test
container in `finally`, including after failure. It does not stop or reset `db`.
Do not run two copies of this script at once.

Container names are `smart-hotels-system-db-1` for the app database and
`smart-hotels-system-test-db-1` for tests. The website/API runs on the host.
The application database uses port 5432 and a named volume, so normal restarts keep its data.

Without `TEST_DATABASE_URL`, `check.ps1` reports the PostgreSQL tests as skipped.
CI always supplies a separate PostgreSQL service and requires those tests.
To use an existing disposable local database instead of Docker:

```powershell
$env:TEST_DATABASE_URL = "postgresql://USER:PASSWORD@127.0.0.1:5432/smart_hotels_test"
.\scripts\check.ps1
Remove-Item Env:TEST_DATABASE_URL
```

Use a dedicated empty database whose name ends in `_test`. Tests apply migrations
and exercise rollback; never point tests at a database with useful data.
Python versions and dependencies are recorded in `.python-version` and `uv.lock`.
The frontend uses browser JavaScript without packages, so it has no npm lockfile.

## Stop and troubleshoot

- `docker compose stop db` stops the local database and keeps its data.
- `docker compose down` removes containers but keeps the application volume.
- If a port is occupied, stop the other service or change the Compose host port
  and the matching URL in `.env` (or the test script).
- If Docker cannot connect, start Docker Desktop and wait until its engine is ready.
  After installing Docker, open a new terminal so it picks up the updated PATH.
- If health returns 503, check `docker compose ps`, `.env`, and rerun migrations.
- If dependency installation fails, check network access, then repeat `uv sync --locked`.

See `brief.md` for approved demo choices and `PLAN.md` for the next tasks.

## Guest conversations (SIN-61)

Open the site at `APP_ORIGIN` (default `http://127.0.0.1:8000`). A different host,
including `localhost` instead of `127.0.0.1`, requires a matching setting. All
session/chat writes require this exact Origin. For HTTPS, set `COOKIE_SECURE=true`.
The local HTTP default is false. Cookies are host-only, HttpOnly and SameSite=Strict.
The database stores SHA-256 hashes of random 256-bit tokens, not the cookie values.

- `POST /api/session` creates or reuses a session. Its fixed lifetime is 24 hours;
  reuse does not extend it. An expired or invalid cookie starts a fresh session.
- `GET /api/history` returns the current conversation's latest 20 completed turns,
  oldest first. The cookie is the only ownership credential. No guest IDs are accepted.
- `POST /api/conversation` starts a new conversation. Earlier history stays in the
  database but is no longer returned. Reset is rejected while a reply is active.
- `POST /api/chat` takes `{turn_id, message}` with a client-generated UUID and
  1–2000 nonblank characters. It streams `turn_started`, `text`, committed `result`,
  then `done` using fetch/SSE. Partial text is provisional. The browser uses plain
  text rendering, so guest input cannot become HTML.

Missing/expired cookies return 401 for history, reset and chat. Use Reload chat to
start a new session; old history is not recovered. Duplicate UUIDs return a generic
409 for every guest, including after reset. Reload history before retrying with a
new UUID. This task does not add replay or a turn-status endpoint.

Stop reply aborts fetch. Only complete answers enter history. Refresh reads saved
history; it does not resume a running reply. If the database commit succeeded but
the network lost the result, Reload chat restores the saved answer. A failed reply
emits a safe `error` without `done`. A storage outage returns 503 before streaming,
or a safe SSE error if streaming already started.

Only one turn runs per session. Admission and completion use short transactions;
model work holds no database connection. Replies have a 90-second deadline and a
16,000-character output limit. Disconnect cleanup has a shielded five-second limit.
If the process dies or cleanup cannot reach PostgreSQL, the two-minute busy lease
expires; the next chat/reset marks the old turn interrupted. A stale worker cannot
save over a later turn. Expiry during a reply also prevents saving the answer.

Sessions are browser credentials, not guest accounts. People sharing a browser
share its session. New conversation clears the visible conversation; it is not a
data-deletion feature. Data retention and deployment controls belong to later tasks.
