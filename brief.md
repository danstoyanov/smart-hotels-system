# Demo brief — SIN-58

## Confirmed choices

The user confirmed these choices on 23 October 2026. The hotel name is for this fictional demo; it is not a claim about a real business.

| Choice | Value |
| --- | --- |
| Demo hotel | Royal Crest Manor |
| Initial guest language | English |
| Property timezone | Europe/Kyiv (IANA timezone) |
| Properties | One hotel |
| Reservations | Demo only, clearly labelled; no real hotel booking |
| Local content source | `hotel/` for reviewed hotel information and demo inventory |
| Stack | Static browser JavaScript, FastAPI, PostgreSQL, Google ADK and Gemini |

PostgreSQL will hold application state. Application tools will expose the reviewed hotel data to the assistant. Hotel name, language and timezone must be configurable when the application is built. Use the property timezone for hotel dates rather than the server timezone.

## Demo scope

Build the journey in PLAN.md: hotel pages, answers from hotel information, availability search, reservation review and explicit confirmation. The assistant must admit missing information. Search does not create a reservation. A demo reservation must be clearly identified before confirmation and in its result.

Payments, real hotel integrations and multiple hotels are excluded. This task creates no cloud resources and makes no paid model calls. Guest accounts, staff inboxes, messaging channels and advanced scaling are deferred.

## Open decisions

- Room names, amenities, policies, prices and inventory dates are not approved business facts. Keep them as clearly marked fictional demo data.

## Later decisions

- Cloud project, region, Gemini runtime model, budget alert and restricted access were confirmed on 25 October 2026 for T11. See [infra/cloud-demo.md](infra/cloud-demo.md). Each new cloud change or paid call still needs approval.
- Tested dependency versions are in `uv.lock`. Local run commands are in [README.md](README.md).

## Baseline and review (SIN-58 record)

The user approved publishing the current PLAN.md and REFERENCE.md to GitHub main before the SIN-58 worktree was created. The task starts from baseline commit `0a33db6c341b142098577b43f3d960bf3f903a70`.

Review this brief and AGENTS.md in the SIN-58 PR. The user reviews and merges; mark the issue Done only after merge and acceptance.
