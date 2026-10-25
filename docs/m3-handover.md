# M3 cloud demo handover — SIN-69 review draft

This is the first cloud demo of one fictional hotel. It is restricted to one
approved Google user. Reservations are demos, not real bookings. The live site
is <https://smart-hotel-demo-613644187384.europe-central2.run.app>. Use
[the operations runbook](../infra/operations.md) for startup, updates, model
settings, checks and common failures. [The T11 record](../infra/cloud-demo.md)
contains the original deployment settings and acceptance evidence.

## Current state and decisions

On 25 October 2026, the live Cloud SQL instance was `RUNNABLE`. Its standard
automatic backups were **disabled**; `gcloud sql backups list` returned no
backups. The user chose seven daily copies as the future retention target but
declined to enable them now and declined a temporary restore instance. No
restore was attempted or passed. Do not use the live database as a restore or
test target. The release cannot meet the recovery acceptance check until this
is resolved.

The user confirmed `stoyanov.dann@gmail.com` for operational notifications.
After separate approval, two Cloud Monitoring policies were created. Cloud Run
5xx policy `11854293725787736831` and Cloud SQL down policy
`11854293725787735888` are enabled and point to email channel
`15735388054728012527`. The user explicitly approved reusing its address for
operations. The existing $50 project budget uses that email too, but is a
separate budget alert. No incident or email delivery was triggered. There is
no backup-failure alert while backups are disabled. The older $2 Vertex AI
spend cap remains separate. Neither is a complete cap on Cloud SQL or Cloud
Run charges. Trial credit balance and expiry remain unverified.

## Checks made for this handover

| Check | Actual result | Limit |
| --- | --- | --- |
| Base and setup | PR #13 was merged into `origin/main` at `44d791dc`; a separate `codex/sin-69-cloud-handover` worktree was created; `uv sync --locked` passed. | No application tests were run for the documentation change. |
| Database and backups | Cloud SQL `smart-hotel-demo-db` was `RUNNABLE`; automatic backups were off and the backup list was empty. | No restore check. |
| Application rollback probe | Cloud Run revision `smart-hotel-demo-00003-zwv` was Ready and had 100% traffic. Previous revision `smart-hotel-demo-00002-mcx` was Ready, and its image digest `sha256:1bd45a0b04c6902bd3380880a2800be4879a9338ab65c2db1610e2253310f7a2` still existed. A temporary tag sent 0% normal traffic to the old revision; its signed-in `/api/health` returned `{"status":"ok","database":"ok"}`. The tag was removed, and the current revision again showed 100% as the only traffic target. | Live traffic was not switched. This proves an old-app health probe against the current database, not the full guest path or compatibility with future migrations. |
| Health | A signed-in browser GET to `/api/health` returned `{"status":"ok","database":"ok"}`. | The health route does not call Gemini. |
| Guest path | A browser search for 4–6 November 2026, two guests found Manor Suite for the full stay. The review page made no reservation. With user approval, one chat question about breakfast returned the 07:00–10:00 fact with `Breakfast · demo source v2`. Explicit confirmation created fictional reservation `DEM-7F044E578142`; it remained visible after refresh. The chat answer also remained after refresh. | One chat POST was made; the exact internal provider call count was not logged. This was not a new cross-session isolation test. The demo reservation now occupies those sample nights. |
| Logs | A read of Cloud Run error-level logs since 21:19 UTC on 25 October returned no entries. | Absence of these log entries is not a full reliability or alert-delivery test. |
| Operational alerts | Both policies were read back as enabled with the confirmed email channel. Cloud SQL `database/up` reported `1` for `smart-hotels-system:smart-hotel-demo-db`; Cloud Run `request_count` reported the `smart-hotel-demo` service label. | No incident or email delivery was tested. The 5xx filter had no error series to trigger. |

The user approved the single new chat request with a maximum of five internal
model calls, and separately approved the demo reservation. No other paid model
request was made for this handover.

The key cloud commands actually run for this review were:

```powershell
gcloud sql instances describe smart-hotel-demo-db --project=smart-hotels-system --format="json(settings.backupConfiguration,settings.availabilityType,settings.dataDiskSizeGb)"
gcloud sql backups list --instance=smart-hotel-demo-db --project=smart-hotels-system
gcloud run revisions list --service=smart-hotel-demo --project=smart-hotels-system --region=europe-central2
gcloud run revisions describe smart-hotel-demo-00002-mcx --project=smart-hotels-system --region=europe-central2
gcloud artifacts docker images describe europe-central2-docker.pkg.dev/smart-hotels-system/smart-hotel-demo/hotel@sha256:1bd45a0b04c6902bd3380880a2800be4879a9338ab65c2db1610e2253310f7a2 --project=smart-hotels-system
gcloud run services update-traffic smart-hotel-demo --project=smart-hotels-system --region=europe-central2 --update-tags=rollback-check=smart-hotel-demo-00002-mcx
# The tagged /api/health URL returned {"status":"ok","database":"ok"} in a signed-in browser.
gcloud run services update-traffic smart-hotel-demo --project=smart-hotels-system --region=europe-central2 --remove-tags=rollback-check
gcloud monitoring policies create --policy-from-file=infra/alert-run-errors.yaml --project=smart-hotels-system
gcloud monitoring policies create --policy-from-file=infra/alert-sql-down.yaml --project=smart-hotels-system
gcloud monitoring policies list --project=smart-hotels-system
```

The two policy creation commands returned the IDs above. The Monitoring API
read-only checks then found the Cloud SQL `up=1` series and Cloud Run request
series with the expected service label. No `gcloud sql instances patch`,
backup create, restore, or live traffic switch command was run.

## M3 checklist

| Task | Accepted PR | Handover result |
| --- | --- | --- |
| [SIN-58 — choices](https://linear.app/singularity-lab/issue/SIN-58/t01-confirm-demo-scope-and-project-choices) | [#1](https://github.com/danstoyanov/smart-hotels-system/pull/1) | One hotel, English, Europe/Kyiv, demo only |
| [SIN-59 — local base](https://linear.app/singularity-lab/issue/SIN-59/t02-build-the-runnable-local-foundation) | [#2](https://github.com/danstoyanov/smart-hotels-system/pull/2) | Local FastAPI, PostgreSQL and checks |
| [SIN-60 — hotel data](https://linear.app/singularity-lab/issue/SIN-60/t03-add-demo-hotel-information) | [#3](https://github.com/danstoyanov/smart-hotels-system/pull/3) | Versioned fictional `hotel/` content |
| [SIN-61 — conversations](https://linear.app/singularity-lab/issue/SIN-61/t04-build-guest-sessions-and-chat-history) | [#4](https://github.com/danstoyanov/smart-hotels-system/pull/4), [#5](https://github.com/danstoyanov/smart-hotels-system/pull/5) | Owned session and saved history |
| [SIN-62 — assistant](https://linear.app/singularity-lab/issue/SIN-62/t05-connect-the-hotel-ai-assistant) | [#6](https://github.com/danstoyanov/smart-hotels-system/pull/6) | ADK and Gemini with hotel evidence |
| [SIN-63 — availability](https://linear.app/singularity-lab/issue/SIN-63/t06-build-full-stay-availability-search) | [#8](https://github.com/danstoyanov/smart-hotels-system/pull/8) | Full-stay demo search |
| [SIN-64 — guest site](https://linear.app/singularity-lab/issue/SIN-64/t07-build-the-guest-website-and-room-pages) | [#9](https://github.com/danstoyanov/smart-hotels-system/pull/9) | Desktop/mobile pages and read-only review |
| [SIN-65 — reservations](https://linear.app/singularity-lab/issue/SIN-65/t08-add-explicit-demo-reservations) | [#10](https://github.com/danstoyanov/smart-hotels-system/pull/10) | Explicit demo confirmation and owned lookup |
| [SIN-66 — safeguards](https://linear.app/singularity-lab/issue/SIN-66/t09-complete-essential-safeguards) | [#11](https://github.com/danstoyanov/smart-hotels-system/pull/11) | Guest isolation, limits and safe errors |
| [SIN-67 — journey checks](https://linear.app/singularity-lab/issue/SIN-67/t10-check-the-main-guest-journey) | [#12](https://github.com/danstoyanov/smart-hotels-system/pull/12) | Focused journey checks |
| [SIN-68 — cloud demo](https://linear.app/singularity-lab/issue/SIN-68/t11-deploy-the-demo-to-google-cloud) | [#13](https://github.com/danstoyanov/smart-hotels-system/pull/13) | Restricted Cloud Run, Cloud SQL and Vertex demo |
| [SIN-69 — operations](https://linear.app/singularity-lab/issue/SIN-69/t12-prepare-launch-and-handover) | [#14, in review](https://github.com/danstoyanov/smart-hotels-system/pull/14) | Runbook, new guest check, 0%-traffic old-revision probe and operational policies; backups, restore and full traffic rollback remain open |

All listed PRs through #13 were confirmed merged in GitHub. SIN-69 remains In
Progress until the missing recovery work is approved, carried out safely and
reviewed. It must not be marked Done before the user accepts and merges its PR.

## Limits and future scope

- Only the approved account can enter through IAP. There are no guest accounts,
  staff inboxes or account recovery. Sessions expire after 24 hours.
- The inventory horizon is 1–7 November 2026. It does not roll forward.
  A new reviewed demo source revision and import are needed for later dates.
- Content, rooms, inventory and reservations are fictional. No prices,
  payments or real hotel integration exist. The chatbot can make mistakes.
- Cloud SQL is a single-zone, shared-core demo database without an SLA.
  Backups are disabled, so database recovery is not demonstrated.
- Future real operation needs approved hotel facts, authoritative inventory
  and booking integration, a recovery policy and tests, and appropriate access,
  retention, monitoring and capacity decisions. Multiple hotels, payments,
  messaging channels and advanced scaling are outside this demo.

## Result / Check / Next

- **Result:** A reviewable operations guide and M3 checklist exist for the first
  restricted cloud demo.
- **Check:** New browser health, chat, search, review, confirmation and refresh
  checks passed as described above. The old revision passed a 0%-traffic
  health probe, and two operational policies and matching metrics were
  verified. No backup, restore or full traffic rollback passed; alert email
  delivery is unverified.
- **Next:** If approved later, enable basic backups and perform an isolated
  restore drill. Review the limited application rollback probe, then review the PR
  and accept the handover. Keep SIN-69 open until then.
