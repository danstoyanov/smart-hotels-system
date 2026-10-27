# Smart Hotels System — development plan

## 1. Product goal

Build a working system for one hotel: a website, an AI assistant answering from hotel information, availability search and an explicit reservation flow. Run it on Google Cloud with Gemini through Vertex AI.

The first version uses demo hotel data and clearly labels demo reservations. The reference project is a source of useful ideas, not a specification to copy or audit. Consult it only to resolve a concrete implementation question. Commit comparisons, feature parity and upstream requirement mappings are not delivery requirements.

## 2. Architecture

This section describes the system as it is built now. It is guidance for new work, not a feature checklist. Behaviour details are in [technical notes](docs/technical-notes.md); cloud settings are in [infra/cloud-demo.md](infra/cloud-demo.md). The example project in REFERENCE.md is a source of ideas only.

![Architecture: the guest browser calls one FastAPI app; for a chat turn FastAPI starts a new ADK agent that calls Gemini or the stub; the agent's tools read hotel/ files and search PostgreSQL; FastAPI stores sessions, turns and demo bookings in PostgreSQL; a reservation needs explicit confirmation](docs/images/architecture.svg)

- One FastAPI app serves the website, static assets and the API from one origin. Writes require the exact `APP_ORIGIN` and an owned guest session cookie.
- PostgreSQL owns durable state. Hotel facts are read from validated files in `hotel/`; nightly inventory is imported from those files into PostgreSQL.
- The chat streams over fetch/SSE: `turn_started`, optional `text`, committed `result`, then `done`, or a safe `error`. Only completed answers are saved.
- The assistant has no booking tool. Reservations are created only by the review page after explicit confirmation.
- Deployment: one container image (`Dockerfile`) on Cloud Run, Cloud SQL for PostgreSQL and Gemini through Vertex AI, with restricted IAP access.

| Location | Responsibility |
| --- | --- |
| `backend/app/main.py` | App factory, page routes, health, hotel information and availability API |
| `backend/app/chat.py`, `sessions.py` | Origin checks, guest sessions, history, chat turns and SSE lifecycle |
| `backend/app/agent.py`, `assistant_prompt.txt`, `tools.py` | Per-reply ADK adapter, instructions and the three tools: `list_information`, `read_information`, `search_availability` |
| `backend/app/hotel.py` | Validated, versioned hotel data and its read API |
| `backend/app/inventory.py` | Inventory import and full-stay search |
| `backend/app/bookings.py` | Demo reservations: confirmation, idempotency, recheck and owned lookup |
| `backend/app/db.py`, `settings.py`, `runtime.py`, `diagnostics.py` | Connection pool and migrations, configuration, event loop, safe provider diagnostics |
| `backend/migrations/` | Ordered SQL: `guest_sessions`, `turns` (with saved `sources`), `inventory_sources`, `inventory_rooms`, `inventory_nights`, `demo_bookings`, `schema_migrations` and the `search_inventory` function |
| `frontend/` | Static pages, CSS, browser JavaScript and browser tests |
| `hotel/`, `evals/` | Fictional demo data and representative assistant questions |
| `scripts/`, `compose.yaml`, `.github/workflows/` | Local start and checks, local and test PostgreSQL, CI |
| `infra/` | Cloud Run, jobs, alerts and the operations runbook |

| Route | Purpose |
| --- | --- |
| `GET /`, `/rooms/{room_id}`, `/review`, `/assets/*` | Public pages and static files |
| `GET /api/health` | Database and migration readiness; no model call |
| `GET /api/site`, `/api/hotel/catalogue`, `/api/hotel/{section}[/{item_id}]` | Public hotel information |
| `GET /api/availability` | Read-only full-stay search |
| `POST /api/session`, `POST /api/conversation`, `GET /api/history` | Owned guest session, new conversation, completed history |
| `POST /api/chat` | One owned chat turn with SSE |
| `POST /api/bookings` | Explicitly confirmed demo reservation |
| `GET /api/bookings/{reference}`, `/api/bookings/by-request/{request_id}` | Owned reservation lookup |

Limits that bound one reply (call, tool, evidence, token and time limits) are listed in the technical notes. They are not a monetary spending cap.

## 3. Development tasks

Tasks describe results in our application. Their IDs are retained for continuity; older review documents are historical context. T01–T12 are delivered; section 6 records their acceptance and open limits.

| Task | Deliverable | Completion check |
| --- | --- | --- |
| T01 — Starting choices | One hotel, initial language, timezone and demo scope; use placeholders for missing content | Enough information to begin development |
| T02 — Runnable foundation | Frontend, FastAPI, local PostgreSQL, configuration and startup instructions | Website and API run locally |
| T03 — Hotel information | Rooms, amenities and policies in a simple maintained source | The backend can retrieve the relevant hotel information |
| T04 — Conversations | Guest session, chat API and saved history | A guest can continue their own conversation |
| T05 — AI assistant | ADK and Gemini integration using hotel information | Answers representative questions and admits missing information |
| T06 — Availability | Date and guest-count search against stored inventory | Returns suitable options for the entire stay |
| T07 — Guest website | Hotel pages, chat, room cards and reservation navigation | The main journey works on desktop and mobile |
| T08 — Reservations | Review, explicit confirmation and reservation reference | Saves once, rechecks availability and restricts access to the guest |
| T09 — Essential safeguards | Session isolation, safe rendering, request limits, timeouts and clear errors | No cross-guest data access; failures allow a safe retry |
| T10 — Core journey checks | Focused tests of answers, availability and reservation confirmation | Main journey passes; consequential defects are fixed |
| T11 — Google Cloud deployment | Cloud Run, Cloud SQL, Vertex AI, secrets, basic logs and budget alerts | The deployed site completes the main journey with a live model |
| T12 — Launch and handover | Startup/update instructions, rollback and basic database backup setup | The first version is usable and maintainable |

Work order: T01–T02 → T03–T05 → T06–T08 → T11–T12. Add T09 safeguards and T10 checks alongside each feature, before exposing it publicly. Reuse code only when it helps delivery and its license permits it; a full import is not required.

Test our behavior in proportion to its risk. Do not reproduce the reference's full test suite, introduce arbitrary capacity targets or build advanced recovery infrastructure without a concrete need. Use local checks and human review; external coding/review agents are not part of this workflow.

## 4. Delivery stages

| Stage | Visible result | Ready when |
| --- | --- | --- |
| M1 — Local hotel assistant | A website with working model-backed chat | Answers from hotel information and handles unknown questions |
| M2 — Reservation journey | Search → room details → review → confirmation | Availability and reservation saving work correctly |
| M3 — First cloud version | The system runs on Google Cloud | Main journey, guest isolation, error handling and cost limits are checked |

The priority is a working end-to-end version. Improve it from actual use. A demo reservation is not a real hotel booking; real operation requires approved hotel content and an authoritative inventory/booking integration.

## 5. Decisions when needed

- Start with demo data from `hotel/`. Hotel name, language and timezone are configurable and can be changed later.
- Cloud project, region, Gemini model, budget alert and approved-user access (Cloud Run IAP) were confirmed on 25 October 2026. See [infra/cloud-demo.md](infra/cloud-demo.md). Access control alone does not cap cloud spending.
- Open: Cloud SQL backups are disabled. The user chose seven daily copies as the target but has not enabled them. A safe restore check is still needed.
- For the first version, use hotel information and demo inventory from `hotel/` through application tools; no external hotel integration is required.
- Later, if needed: payments, guest accounts, multiple hotels, staff inbox, messaging channels and advanced scaling. These do not block the demo.

## 6. Short progress report

For each completed task, record only:

- Result: what now works.
- Check: what was actually checked and the outcome.
- Next: the next task or a concrete blocker.

Keep this plan focused on future development. Historical audits and detailed work logs do not belong here.

### M1 accepted — 2026-10-24

- Result: T01–T05 (SIN-58–SIN-62) are Done. The local Royal Crest Manor website has versioned hotel data, private PostgreSQL-backed conversations and a Gemini/ADK assistant with saved source references. PR #6 was merged into main at `d8438fdc08cb26ce1c2314d6311ecb532ac855f2`.
- Check: The final review read the plan, code, structure, recorded development evidence and merge state. No tests, server or model calls were run during the review or this documentation update. The earlier foreground acceptance report records a successful real-model answer and source/history recovery after refresh.
- Next: M1 is closed. Read [the M1 handover](docs/m1-handover.md) for its evidence and limits.

### M2 guest journey accepted — 2026-10-24

- Result: SIN-63–SIN-65 (T06–T08) are Done; PRs #8–#10 are merged. The demo journey covers search, room details, review and explicit reservation confirmation.
- Check: [SIN-64 verification](docs/history/sin-64-verification.md) and [SIN-65 verification](docs/history/sin-65-verification.md) record local and desktop/mobile checks. T08 used a separate disposable PostgreSQL database.
- Next: M2 is closed. T09 safeguards and T10 journey checks remain before public access. Cloud setup and launch need separate approval.

### M3 first cloud version — 2026-10-25

- Result: SIN-66–SIN-69 (T09–T12) are Done; PRs #11–#14 are merged. Request limits and safe retry are in place, the connected journey check exists, and a restricted demo runs on Cloud Run, Cloud SQL and Vertex AI with an operations runbook and two alert policies.
- Check: [SIN-66](docs/history/sin-66-verification.md) and [SIN-67](docs/history/sin-67-verification.md) verification, the [T11 record](infra/cloud-demo.md) and the [M3 handover](docs/m3-handover.md) record the actual local and cloud checks, including one approved live chat request and an old-revision health probe.
- Next: the recovery check is open because Cloud SQL backups are disabled (section 5). The cloud demo inventory (revision v2) ends on 7 November 2026.

### Repository readiness — 2026-10-27

- Result: SIN-85 (PR #15) rewrote the README for external local testing and moved behaviour details to [technical notes](docs/technical-notes.md). SIN-86 shortened AGENTS.md, added the [task workflow](docs/workflow.md), a PR template and a documentation link check. SIN-87 replaced personal cloud identifiers with placeholders, moved task records to [docs/history](docs/history/README.md) and published demo data v3 (to 30 June 2027).
- Check: SIN-85 ran the README quick start and `scripts/test.ps1` locally. SIN-86 and SIN-87 results are in their PRs.
- Next: the owner chooses the license and GitHub description. Updating the cloud demo to data v3 needs a separate approval.
