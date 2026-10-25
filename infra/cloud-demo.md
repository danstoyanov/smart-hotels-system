# SIN-68 cloud demo plan

The user approved this restricted cloud demo on 25 October 2026. The hotel
and reservations are fictional demos. This file records the approved scope
and the steps actually completed; it is not a production handover.

## Proposed configuration

| Area | Setting |
| --- | --- |
| Project | `smart-hotels-system` with billing account `0177EF-BD94EC-8A99B3` |
| Region | `europe-central2` for Cloud Run, Cloud SQL and Artifact Registry |
| Model | Vertex AI `gemini-3.8-flash` at `global` |
| Image | One container from `Dockerfile`, tagged by the exact Git commit |
| Cloud Run | `smart-hotel-demo`, 1 vCPU, 1 GiB RAM, port 8080, request-based CPU, min 0 and max 1 instance, concurrency 4, timeout 120 seconds |
| Access | Cloud Run IAP with only named approved Google users; no `allUsers` or `allAuthenticatedUsers` grant |
| Cloud SQL | PostgreSQL 16, `smart-hotel-demo-db`, single zone, `db-g1-small`, 10 GiB SSD, automatic storage growth capped at 20 GiB, no authorized client networks |
| DB connection | Cloud Run's encrypted Cloud SQL Unix socket; a dedicated demo database and user; `DATABASE_URL` in Secret Manager |
| Service identity | Dedicated account with `roles/cloudsql.client` and `roles/aiplatform.user`; `roles/secretmanager.secretAccessor` on the database secret only |
| App variables | `CLOUD_DEMO=true`, `ASSISTANT_MODE=vertex`, approved project/model/location, `HOTEL_NAME=Royal Crest Manor`, `HOTEL_LANGUAGE=en`, `HOTEL_TIMEZONE=Europe/Kyiv`, exact HTTPS `APP_ORIGIN`, `COOKIE_SECURE=true` |
| Health | HTTP startup probe on `/api/health`; the endpoint checks the database and migration state with no model call |
| Logs | Cloud Run request logs and safe application diagnostics in Cloud Logging; no guest text, credentials or SDK debug logs |
| Budget | Single-project $50 monthly USD alert budget; gross actual-spend email thresholds at 50%, 80% and 100% to `stoyanov.dann@gmail.com` |
| Acceptance calls | At most five real Gemini requests during the deployed acceptance check; no automatic model retry |

The Cloud Run instance maximum is a capacity setting, not a hard billing limit.
Google Cloud can briefly exceed it during maintenance or a traffic surge. The
app limits API POST bodies to 16 KiB, chat messages to 2,000 characters,
model calls to eight per turn, output to 2,048 tokens and a chat turn to
90 seconds. These limits apply per request, not across the billing account.

## Expected paid resources

- Cloud SQL compute runs while its instance exists, even without visitors.
  Storage, backup storage if enabled, and data transfer can add charges.
- Cloud Run CPU, memory and requests; image build and Artifact Registry storage;
  Vertex AI input and output tokens.
- Secret Manager versions and reads, Cloud Logging above free limits, and
  network transfer where charged.

For scale only, the published `db-g1-small` starting rate of $0.035/hour is
about $25.55 for 730 hours; 10 GiB SSD at $0.17/GiB-month is about $1.70.
That is about $27.25 before backups, Cloud Run, model use, images, logs,
transfer, tax or a regional price difference. It is not a quote for this
account. This shared-core database tier has no Cloud SQL SLA and is for a
demo, not production traffic.

An alert budget sends notices. It does **not** automatically stop all usage or
charges at its threshold. Check the approved region and billing account in the
[Cloud SQL](https://cloud.google.com/sql/pricing),
[Cloud Run](https://cloud.google.com/run/pricing) and
[Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/pricing)
price pages before creating resources.

If the project is linked to an active Google Cloud Free Trial, eligible usage
uses its remaining credit; a budget amount is not a required spend. A paid
billing account can charge for usage after credit expires or for products not
covered by the credit. Check the account type, balance and expiry in Billing
before deployment. See the [Google Cloud Free Trial terms](https://cloud.google.com/free/docs/free-cloud-features).

## Planned deployment order

1. Record new approval, project, region, users, budget and model-call cap.
   Check billing, IAM, model availability and any IAP OAuth setup needed.
2. Create and verify the project budget and email channel before the app is
   exposed. Enable only the APIs needed for this demo.
3. Create the image repository, SQL instance and database, dedicated user,
   service identity and secret. Keep the password outside Git, command logs
   and PR text. Grant the runtime identity only the permissions above.
4. Build and push the exact commit image. Use one-off Cloud Run jobs to run
   `python -m backend.app.db` and then `python -m backend.app.inventory`.
   Check both executions. The hotel inventory import is a separate step.
5. Deploy with IAP and no open invoker grant. Add only approved users to the
   IAP policy. Set the exact HTTPS origin, secure cookie, database socket,
   probe and limits.
6. Verify the real URL with an approved account: answer with a real model,
   full-stay search, room details, read-only review, explicit **demo
   reservation** confirmation and owned lookup. Check another guest cannot
   read it. Check errors, health, logs, access policy and deployed limits.
7. Record the URL, image digest, exact settings, real checks and limitations
   without secrets. T12 owns backup, rollback and final handover.

## Deployment record

The approved project is active and has billing enabled. The current billing
account is open. The remaining trial credit and its expiry are not available
through the CLI checks, so they are unverified. The Google Cloud documentation
lists `gemini-3.8-flash` as GA on the `global` endpoint. No paid model call has
yet been made for SIN-68.

On 25 October 2026, the required APIs were enabled. Budget
`4944a252-e24c-4285-81f7-f8cfbfc85e93` was created for project
`613644187384`, $50 USD per month, excluding credits when measuring spend,
with current-spend thresholds 50%, 80% and 100%. It uses Monitoring email
channel `15735388054728012527` for `stoyanov.dann@gmail.com`. The older
service-specific $2 Hotel AI budget was inspected and left unchanged. Alert
delivery has not been triggered or proven by an email yet.

## Platform references

- [Cloud Run IAP](https://cloud.google.com/run/docs/securing/identity-aware-proxy-cloud-run)
- [Cloud Run health checks](https://cloud.google.com/run/docs/configuring/healthchecks)
- [Cloud Run to Cloud SQL](https://cloud.google.com/sql/docs/postgres/connect-run)
- [Budget alerts](https://cloud.google.com/billing/docs/how-to/budgets)
- [Custom budget email recipients](https://cloud.google.com/billing/docs/how-to/budgets-notification-recipients)
