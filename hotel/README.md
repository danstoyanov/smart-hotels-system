# Demo hotel information

All content in this folder is fictional demo data for Royal Crest Manor. It is not
information about a real business. Initial language: English (`en`). Property dates
and times use `Europe/Kyiv`. Do not add credentials, private contact details or guest data.

`catalogue.json` lists complete JSON revisions and selects one active revision.
`revisions/royal-crest-demo.v2.json` is active. It keeps the two rooms, three amenities,
six policies and fourteen explicit inventory nights from v1, and describes the new
demo reservation step. V1 remains available for older citations. The Garden Room is closed
on 5 November. A missing night is unknown, never assumed open. These are fixtures;
the full-stay search imports them into PostgreSQL. Reading or searching never
holds rooms or creates reservations. Only explicit confirmation on the review page
can create a demo reservation.

## Edit, validate and reload

1. Copy the active file to a new file, for example `revisions/royal-crest-demo.v3.json`.
2. Increase its `version` to `3`. Edit room facts, amenities, full policy bodies or
   individual inventory nights. Keep `demo: true`. Keep old files unchanged.
3. Add the new source ID, version and file to `catalogue.json.sources`. Keep older
   entries so their citations remain readable. Set `active_version` to `3`.
4. Run `uv run --locked python -m backend.app.hotel`. Exit code 0 means the complete
   catalogue passed validation; exit code 1 means invalid or missing data. The
   command reports schema field errors without changing the running application.
5. Run migrations and `uv run --locked python -m backend.app.inventory` to import
   the active room/inventory revision into PostgreSQL. Restart the local server. With `scripts/start.ps1`, stop with
   Ctrl+C and run it again. Uvicorn's normal Python reload does not watch JSON files.
   For application code that needs an in-process reload, call
   `app.state.hotel.reload()` from trusted local code. It validates all files before
   replacing the snapshot. A failed reload raises `HotelDataError` and keeps the
   last good snapshot. A repeat reload is safe. No public reload endpoint exists.

Prepare and validate the files before restarting. An invalid first load returns
`unavailable` (HTTP 503) for hotel reads; the website still opens. Keep a working
copy in Git so a restart with bad files can be fixed by restoring the last version.
Each running process owns its own snapshot; restart every process after an update.

Published ID/version pairs must not change or disappear. In-process reload enforces
this against the loaded snapshot. Across restarts, keeping archived files unchanged
is an editing rule enforced by code review and Git, not a separate database ledger.
All listed old revisions are validated and readable after restart. To roll back,
select an earlier listed version as active and reload; do not delete later versions.

The active source name, language and timezone must match `HOTEL_NAME`,
`HOTEL_LANGUAGE` and `HOTEL_TIMEZONE`. If these change, add a matching source version
and update the application settings together. The API refuses mismatched facts.

## Reading from backend tools

The running app exposes `app.state.hotel`, a `HotelStore`. Use `get_rooms(room_id)`,
`get_amenities(amenity_id)` or `get_policy(policy_id)`. Omit the optional room/amenity
ID to read the complete list. `read("inventory")` returns all explicit nights.
These reads need no database or model. `HotelStore` can also be loaded directly:

```python
from backend.app.hotel import HotelStore

store = HotelStore()
store.reload()
result = store.get_policy("arrival")
```

A result includes the complete requested records, hotel identity and
`source: {source_id, version, demo}`. Preserve that source in any later answer or
citation. `read("policies", "arrival", source_id="royal-crest-demo", version=1)`
retrieves the exact archived revision instead of the active one. Do not truncate a
policy to the catalogue or infer missing details from a different policy.

Read-only HTTP routes:

- `GET /api/hotel/catalogue`: active source and listed revisions.
- `GET /api/hotel/rooms` and `/api/hotel/rooms/manor-suite`.
- `GET /api/hotel/amenities` and `/api/hotel/amenities/wifi`.
- `GET /api/hotel/policies` and `/api/hotel/policies/arrival`.
- `GET /api/hotel/inventory`: fixture nights, not a booking availability result.

Add `?source_id=royal-crest-demo&version=1` to pin any information read to a revision.
Supply both parameters together. Filesystem paths are never accepted by these routes.

`ok` returns facts. `unknown` returns a published explanation of an unset policy
(for example `prices`), with its source. A policy list keeps each policy's own
`known`/`unknown` status. Missing IDs/revisions return `not_found` (HTTP 404);
invalid read inputs return `invalid_input` (HTTP 422); unloaded data returns
`unavailable` (HTTP 503). Framework request validation also uses HTTP 422. Callers
must respect these states and must not fill gaps with invented facts.

## Policy examples

At the user's request, the policy topics and a few sample values were informed by
`hotel/policies/` in the reference repository named in `REFERENCE.md`, at its pinned
commit. The text and fixture format here were written for this project. The demo
uses check-in 15:00, checkout 11:00, staff confirmation for special arrangements,
capacity including children/infants and example flexible/non-refundable terms.
Currency, room prices and service fees are deliberately unset. The reference's
Bali location, timezone, service prices and implemented booking claims do not apply.


For availability, use `/api/availability` or the agent's `search_availability` tool,
not the raw inventory read. Both use the same PostgreSQL full-stay query. Missing
nights stay unknown; a closed night rules a room out. Room capacity includes every
person. See [the availability contract](../README.md#full-stay-availability-sin-63).
The database import also rejects changed room/inventory data under a loaded
source ID/version, across restarts. Old imported versions remain available for
rollback by selecting their unchanged catalogue revision. The hotel data API has no
write route. The separate reservation API requires an owned guest session and
explicit confirmation.
