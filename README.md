# Smart Hotels System

A local foundation for Royal Crest Manor, a fictional demo hotel. FastAPI serves the
website and API on the same origin. PostgreSQL holds application state. This task
adds no assistant, model calls, hotel inventory or reservations.

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

The health endpoint returns HTTP 200 only when PostgreSQL answers and the initial
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
feature tables belong to later tasks. There is no seed command in T02.

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
