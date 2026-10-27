# Smart Hotels System

[![Checks](https://github.com/danstoyanov/smart-hotels-system/actions/workflows/checks.yml/badge.svg)](https://github.com/danstoyanov/smart-hotels-system/actions/workflows/checks.yml)

A website and AI concierge for one hotel. Guests can read about the hotel, ask
questions in a chat, search for free rooms for a whole stay and confirm a demo
reservation.

> **Demo only.** Royal Crest Manor is a fictional hotel. All rooms, policies and
> dates in `hotel/` are invented sample data. Reservations are clearly labelled
> demo reservations: there are no prices, no payments and no real hotel booking.

![Review page of the demo hotel website](docs/screenshots/sin-67-review-1440.png)

## Contents

- [Features](#features)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Try the demo](#try-the-demo)
- [Run the checks](#run-the-checks)
- [Configuration](#configuration)
- [Optional: use real Gemini through Vertex AI](#optional-use-real-gemini-through-vertex-ai)
- [Project layout](#project-layout)
- [Troubleshooting](#troubleshooting)
- [Project status and limits](#project-status-and-limits)
- [More documentation](#more-documentation)

## Features

- **Hotel website** with room cards, room detail pages and a review page. It works
  on desktop and mobile.
- **AI concierge chat** that answers only from the hotel information in `hotel/`.
  It shows the sources it read and says so when it does not know something.
  Each browser keeps its own private conversation for 24 hours.
- **Full-stay availability search.** A room is offered only when every night of
  the stay is known to be open.
- **Explicit demo reservations.** Search never holds a room. A reservation is saved
  only after the guest presses **Confirm demo reservation**. A repeated request
  does not create a second reservation.
- **Safe local default.** The chat uses a local stub, so you need no cloud account
  and make no paid model calls.

## Tech stack

| Part | Technology |
| --- | --- |
| Frontend | Static HTML, CSS and browser JavaScript (no build step, no npm packages) |
| Backend | Python 3.13, FastAPI, Uvicorn |
| Database | PostgreSQL 17 (local Docker container) |
| AI assistant | Google ADK with Gemini on Vertex AI (optional; stub by default) |
| Tooling | uv for Python and dependencies, Ruff, pytest, Node.js test runner |

The website and the API are served by the same FastAPI app from one origin.

## Quick start

### Prerequisites

- [Git](https://git-scm.com/)
- [uv](https://docs.astral.sh/uv/) 0.13.4 or newer. uv installs Python 3.13 for you.
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine
  with Compose v2), running Linux containers.
- [Node.js](https://nodejs.org/) 22, only for the JavaScript checks.
- Windows: PowerShell 7 or Windows PowerShell 5.1. macOS/Linux: any POSIX shell.

### 1. Get the code and install dependencies

```bash
git clone https://github.com/danstoyanov/smart-hotels-system.git
cd smart-hotels-system
uv python install 3.13
uv sync --locked
```

### 2. Create your local settings

Copy the example file. It contains only public local demo values. If you already
have a `.env`, do not overwrite it.

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

```bash
# macOS / Linux
cp .env.example .env
```

### 3. Start the database

```bash
docker compose up -d --wait db
```

This starts PostgreSQL on `127.0.0.1:5432`. Its data stays in a Docker volume
between restarts.

### 4. Start the app

**Windows PowerShell:**

```powershell
.\scripts\start.ps1
```

If your PowerShell policy blocks scripts, run it once with
`powershell -ExecutionPolicy Bypass -File .\scripts\start.ps1`.

**macOS / Linux** (the same steps as `start.ps1`):

```bash
uv run --locked python -m backend.app.db          # apply database migrations
uv run --locked python -m backend.app.inventory   # load demo rooms and nights
uv run --locked uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --loop backend.app.runtime:new_loop --reload
```

### 5. Open the site

Open <http://127.0.0.1:8000>. Use exactly `127.0.0.1`, not `localhost`: the chat
accepts requests only from the origin in `APP_ORIGIN`.

Check that the API and database are ready:

```bash
curl http://127.0.0.1:8000/api/health
```

The answer should be `{"status":"ok","database":"ok"}`. Stop the server with
Ctrl+C. Stop the database with `docker compose stop db`.

## Try the demo

1. **Ask the concierge.** Open the chat and ask, for example, "What time is
   breakfast?". In the default stub mode you get a fixed demo reply. With
   [Vertex mode](#optional-use-real-gemini-through-vertex-ai) the real assistant
   answers from the hotel information and links its sources.
2. **Search for a stay.** Choose arrival and departure dates and the number of
   guests. The demo inventory covers only the nights of **1–7 November 2026**.
   On a new database you should see:
   - 2 guests, 1–3 November: Garden Room and Manor Suite are available.
   - The Garden Room is closed on 5 November.
   - 5 guests: no room fits the party.
   - Dates after 7 November: inventory is unknown, so nothing is offered.
3. **Review and confirm.** Open a room, go to the review page and press
   **Confirm demo reservation**. You get a demo reference such as `DEM-…`.
   Refresh the page: the reservation is still visible to you, but not to another
   browser. Your demo reservations stay in the local database and keep those
   nights booked for later searches.

> **Note about dates.** Check-in must be today or later in the hotel timezone
> (Europe/Kyiv). After 7 November 2026 the sample nights are in the past, and
> every search returns no rooms. To test later dates, publish a new demo data
> revision as described in [hotel/README.md](hotel/README.md).

## Run the checks

**Windows PowerShell:**

```powershell
.\scripts\check.ps1   # lint, format, JavaScript and unit tests; database tests are skipped
.\scripts\test.ps1    # the same checks plus real PostgreSQL tests in a disposable container
```

**macOS / Linux** (the same steps as the scripts and CI):

```bash
uv run --locked ruff check .
uv run --locked ruff format --check .
node --check frontend/assets/site.js
node --check frontend/assets/chat.js
node --test frontend/tests/sse.test.mjs
uv run --locked python -m backend.app.hotel   # validate the demo hotel data
uv run --locked pytest
```

To include the PostgreSQL tests on macOS/Linux, start the disposable test database,
run pytest against it, then remove it:

```bash
docker compose --profile test up -d --wait test-db
TEST_DATABASE_URL=postgresql://smart_hotels:local_test_only@127.0.0.1:55433/smart_hotels_test uv run --locked pytest
docker compose --profile test rm -s -f test-db
```

The test database is separate (port 55433, memory storage) and is removed after
the run. Never point tests at a database with useful data. GitHub Actions runs the
same checks with PostgreSQL on every push and pull request.

### Optional browser checks

`frontend/tests/*.browser.cjs` are Playwright scripts that drive local Chrome. They
are not part of the scripts above. The full guest journey check needs the app
running in stub mode against the **test** database (not your app database):

```bash
npm install --prefix .local playwright
docker compose --profile test up -d --wait test-db
export DATABASE_URL=postgresql://smart_hotels:local_test_only@127.0.0.1:55433/smart_hotels_test
uv run --locked python -m backend.app.db
uv run --locked python -m backend.app.inventory
ASSISTANT_MODE=stub uv run --locked uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --loop backend.app.runtime:new_loop --no-access-log
# in a second terminal:
NODE_PATH=.local/node_modules node frontend/tests/journey.browser.cjs
```

These scripts use fixed November 2026 dates, so they only pass while those dates
are in the future. They also overwrite screenshots in `docs/screenshots/`.

## Configuration

Settings are read from `.env` in the repository root. Environment variables
override `.env`. `.env` is ignored by Git; never commit real credentials.

| Setting | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | local Docker database | PostgreSQL connection string |
| `HOTEL_NAME` | `Royal Crest Manor` | Hotel name shown on the site |
| `HOTEL_LANGUAGE` | `en` | Reply language for the assistant. The page text stays English. |
| `HOTEL_TIMEZONE` | `Europe/Kyiv` | IANA timezone for hotel dates (not the server timezone) |
| `APP_ORIGIN` | `http://127.0.0.1:8000` | Exact origin allowed to write sessions, chat and bookings |
| `COOKIE_SECURE` | `false` | Set `true` when the site runs over HTTPS |
| `ASSISTANT_MODE` | `stub` | `stub` (no model calls) or `vertex` (real Gemini) |
| `GOOGLE_CLOUD_PROJECT` | empty | Your Google Cloud project, for Vertex mode |
| `GOOGLE_CLOUD_LOCATION` | empty | Vertex AI location, for Vertex mode |
| `GEMINI_MODEL` | `gemini-3.8-flash` | Gemini model, for Vertex mode |
| `CLOUD_DEMO` | `false` | Only for the cloud deployment; needs Vertex, HTTPS and secure cookies |

Restart the server after you change a setting.

## Optional: use real Gemini through Vertex AI

Vertex mode makes **paid** calls to Google Cloud in **your own** project. You need
a Google Cloud project with the Vertex AI API enabled, access to the Gemini model,
and a spending limit you are comfortable with.

1. Sign in with Application Default Credentials. No API key is needed, and no
   credentials are stored in the repository:

   ```bash
   gcloud auth application-default login
   ```

2. Set these values in your private `.env`:

   ```text
   ASSISTANT_MODE=vertex
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_CLOUD_LOCATION=your-location
   GEMINI_MODEL=gemini-3.8-flash
   ```

3. Restart the server.

Each reply is bounded: at most eight model calls, 2,048 output tokens and a
90-second deadline, with no automatic retry. These limits bound one reply; they
are not a spending cap for your account. See
[technical notes](docs/technical-notes.md#hotel-ai-assistant-sin-62) for details.

## Project layout

```text
frontend/            website pages, CSS, browser JavaScript and browser tests
backend/app/         FastAPI app, chat, sessions, AI agent, hotel data, inventory, bookings
backend/migrations/  ordered SQL migrations (never edit an applied file)
backend/tests/       Python unit and PostgreSQL integration tests
hotel/               fictional demo hotel data and inventory (see hotel/README.md)
evals/               representative questions for live assistant checks
scripts/             PowerShell helpers: start, check, test
infra/               Google Cloud deployment files and operations runbook
design/              visual design references
docs/                technical notes, handovers and verification records
compose.yaml         local PostgreSQL and the disposable test database
Dockerfile           one container image for the cloud deployment
```

## Troubleshooting

- **Docker cannot connect.** Start Docker Desktop and wait until the engine is
  ready. After installing Docker, open a new terminal.
- **A port is already in use (5432 or 8000).** Stop the other service, or change the
  host port in `compose.yaml` and the matching URL in `.env`.
- **`/api/health` returns 503.** Check `docker compose ps` and `.env`, then run the
  migrations again (`uv run --locked python -m backend.app.db`).
- **Search returns HTTP 503.** The demo inventory is not loaded. Run
  `uv run --locked python -m backend.app.inventory`.
- **The chat says "Open the chat from the hotel website."** Open the site at the
  exact `APP_ORIGIN` address, `http://127.0.0.1:8000` by default.
- **Search finds no rooms.** Use dates from 1–7 November 2026 that are not in the
  past. Earlier demo reservations in your local database also keep their nights
  booked. See [Try the demo](#try-the-demo) and *Reset local data* below.
- **Dependency installation fails.** Check network access, then repeat
  `uv sync --locked`.
- **Reset local data.** `docker compose down -v` removes the database container and
  its volume. This deletes all local sessions and demo reservations.

## Project status and limits

All three planned stages are delivered:

- **M1 — Local hotel assistant:** website with a Gemini-backed chat that answers from
  hotel information. See the [M1 handover](docs/m1-handover.md).
- **M2 — Reservation journey:** search → room details → review → confirmation.
- **M3 — First cloud version:** a restricted demo on Google Cloud Run, Cloud SQL and
  Vertex AI. Access is limited to approved users. See the
  [M3 handover](docs/m3-handover.md).

Known limits:

- Fictional content only. No prices, currency, payments or real booking system.
- One hotel. The guest pages are in English.
- Guest sessions are browser cookies that last 24 hours. There are no guest accounts.
- Source links show which records the assistant read. They do not prove that every
  sentence of an answer is correct.
- The demo inventory covers only 1–7 November 2026.

[PLAN.md](PLAN.md) describes the goal and task order. [brief.md](brief.md) records
the confirmed demo choices.

## More documentation

| Document | What it covers |
| --- | --- |
| [docs/technical-notes.md](docs/technical-notes.md) | API routes, sessions, chat streaming, assistant limits, availability rules and reservation safety |
| [hotel/README.md](hotel/README.md) | Demo data format, validation and publishing a new data revision |
| [infra/operations.md](infra/operations.md) | Cloud deployment, updates and common failures |
| [infra/cloud-demo.md](infra/cloud-demo.md) | Approved cloud configuration and acceptance record |
| [docs/m1-handover.md](docs/m1-handover.md), [docs/m3-handover.md](docs/m3-handover.md) | Milestone handovers with evidence and limits |
| `docs/sin-*-verification.md` | Check records for each task |
| [AGENTS.md](AGENTS.md) | Workflow rules for coding agents in this repository |

## License

No license has been chosen for this repository yet. Ask the owner before you
reuse the code outside this project.
