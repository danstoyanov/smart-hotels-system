# M1 handover — 24 October 2026

## Accepted baseline

M1 is accepted. SIN-58–SIN-62 are Done in Linear. [PR #6](https://github.com/danstoyanov/smart-hotels-system/pull/6)
was merged on 24 October 2026 at 09:46:46 UTC. The accepted main commit is
`d8438fdc08cb26ce1c2314d6311ecb532ac855f2`; its application tree matches the
reviewed T05 head `94dd881a91b0230f4213c26eda1dfc4d129bbd0a`.

Use the current `origin/main` for new approved tasks. The hotel is **Royal Crest
Manor**, with English guest responses and property timezone **Europe/Kyiv**.
`brief.md` records the agreed choices. Do not bring the separate Sanctuary Hotel
playground prototype into this application.

## Delivered scope and layout

| Location | Delivered responsibility |
| --- | --- |
| `frontend/` | Minimal same-origin site, chat, reset, history and source links |
| `backend/app/main.py`, `chat.py` | FastAPI routes and bounded chat/SSE lifecycle |
| `backend/app/sessions.py`, `db.py` | Owned PostgreSQL sessions, completed history and migration runner |
| `backend/migrations/` | Foundation, guest sessions and saved answer sources |
| `backend/app/hotel.py`, `tools.py` | Validated versioned hotel reads and controlled assistant tools |
| `backend/app/agent.py`, `assistant_prompt.txt` | Per-invocation ADK adapter and Gemini instructions |
| `hotel/` | Two rooms, three amenities, six policies and fourteen room-night fixtures |
| `evals/assistant-smoke.json` | Four representative question/review cases |
| `scripts/`, `compose.yaml`, `uv.lock` | PowerShell helpers, local PostgreSQL and locked dependencies |
| `docs/`, `.github/workflows/` | Development evidence and existing CI configuration |

PLAN.md section 2 contains retained reference architecture. Its proposed filenames,
schema and full feature set are not the current implementation. Sections 1 and
3–5 define delivery scope; the table above describes the accepted M1 layout.

## Acceptance evidence

- T01: [PR #1](https://github.com/danstoyanov/smart-hotels-system/pull/1), `brief.md` and `AGENTS.md`.
- T02: [PR #2](https://github.com/danstoyanov/smart-hotels-system/pull/2) and [foundation verification](verification.md).
- T03: [PR #3](https://github.com/danstoyanov/smart-hotels-system/pull/3) and [hotel-data verification](sin-60-verification.md).
- T04: [PR #4](https://github.com/danstoyanov/smart-hotels-system/pull/4), [cleanup PR #5](https://github.com/danstoyanov/smart-hotels-system/pull/5) and [session verification](sin-61-verification.md).
- T05: [PR #6](https://github.com/danstoyanov/smart-hotels-system/pull/6), [foreground acceptance](sin-62-foreground-browser.md) and [browser evidence](sin-62-live-browser.json).

The final recorded real-browser flow returned a grounded breakfast answer, saved
the answer and versioned source in PostgreSQL, opened the source and restored the
same conversation after refresh. It used one user POST and one model call. The
recorded browser journey took 10.516 seconds; the adapter took 7.887 seconds.

These are earlier development results, not new runs. The final review and this
handover update used static file/diff/link checks and merge/status reads only.
No tests, server, Gemini requests or deployment were run for this update.

Earlier verification and timeout reports remain a dated audit trail. Their old
pending/failed statements describe those attempts; this handover and their closure
notes give the current milestone status. The transport/foreground results do not
prove a universal timeout cause or guarantee future provider reliability.

## Limits carried into M2

- Availability fixtures exist, but no full-stay search or booking write exists.
  Prices and currency are unset. The assistant must not invent them or claim actions.
- `ASSISTANT_MODE=stub` remains the safe default. Vertex mode needs private,
  explicitly approved settings and ADC. No credentials belong in Git.
- Session access lasts 24 hours. Reset changes the conversation; it does not delete
  records. Retention, stronger recovery and public deployment controls remain later work.
- Answers are rendered as plain text. Source links identify records actually read;
  they do not prove that every generated claim is correct.
- Provider work is bounded by call, token and timeout limits, with no automatic
  provider retry. These are not an account-wide monetary spending stop.
- Hotel revision immutability across restarts relies on archived files and Git review.

## Next task

[SIN-63 — T06](https://linear.app/singularity-lab/issue/SIN-63/t06-build-full-stay-availability-search)
is next, after the user approves execution. Implement read-only full-stay search
using the existing room IDs, property timezone and explicit inventory fixtures.
Missing nights must remain unknown. T07 adds the fuller guest website; T08 adds
explicit demo reservations. This handover does not start those tasks.
