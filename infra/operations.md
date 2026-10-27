# First cloud demo operations — SIN-69

This runbook covers one fictional hotel. Reservations are demos, not real
bookings. Use the approved Google account. Run commands from the repository root
in PowerShell. The live address is
`https://smart-hotel-demo-PROJECT_NUMBER.europe-central2.run.app`, where
`PROJECT_NUMBER` is the Google Cloud project number.
IAP allows only the approved user. Keep credentials, guest cookies and database
URLs out of commands, logs and Git.

The YAML files in `infra/` use placeholders instead of private identifiers:
`PROJECT_NUMBER` in the Cloud Run files and `NOTIFICATION_CHANNEL_ID` in the
alert files. The update steps below fill in the project number before applying
the files. Take the channel ID from Cloud Monitoring (Alerting → notification
channels) before you create an alert policy from a file.

## Current settings

| Area | Value |
| --- | --- |
| Project and region | `smart-hotels-system`, `europe-central2` |
| Cloud Run service | `smart-hotel-demo`, IAP, one maximum instance, concurrency 4, 120-second request timeout |
| Cloud SQL | PostgreSQL 16 `smart-hotel-demo-db`, `db-g1-small`, 10 GiB SSD, single zone |
| Model | Vertex AI `gemini-3.8-flash` at `global`, `ASSISTANT_MODE=vertex` |
| App | `Royal Crest Manor`, English, `Europe/Kyiv`, secure cookie, exact HTTPS `APP_ORIGIN` |
| Secret | `DATABASE_URL` from Secret Manager `smart-hotel-database-url` version 1 |
| Budget | $50 project alert at 50%, 80% and 100%; separate $2 Vertex AI spend cap |
| Recovery state | Automatic Cloud SQL backups are disabled; no restore drill has passed |
| Operational alerts | Cloud Run 5xx and Cloud SQL down policies use the owner's confirmed email channel |

The $50 alerts do not stop spending. The service maximum and five model calls
per cloud chat turn are request bounds, not account-wide cost caps. Cloud SQL
compute can cost money without visitors. The Free Trial balance and alert email
delivery have not been verified. See [the deployment record](cloud-demo.md).

The applied alert definitions are [`alert-run-errors.yaml`](alert-run-errors.yaml)
and [`alert-sql-down.yaml`](alert-sql-down.yaml). The Cloud Run policy opens
when at least one 5xx response is counted in five minutes. The Cloud SQL
policy opens when its `up` metric stays below one for three minutes. They use
the owner's email notification channel, now explicitly approved for
operations as well as the earlier budget. Policy and channel IDs are
kept in the owner's private notes, not in Git. Metric reporting and policy state
were checked, but no incident or email delivery was tested. There is no
backup-failure alert while backups are disabled.

## Start and inspect

The service and database are managed by Google Cloud. There is no local daemon
to start for the deployed site. Check the resource and health states before
changing anything:

```powershell
$project = "smart-hotels-system"
$region = "europe-central2"
$service = "smart-hotel-demo"
gcloud sql instances describe smart-hotel-demo-db --project=$project --format="json(name,state,settings.backupConfiguration)"
gcloud run services describe $service --project=$project --region=$region --format="json(status.latestReadyRevisionName,status.traffic,status.url)"
gcloud run revisions list --service=$service --project=$project --region=$region
```

Open the live address with the approved Google account, then visit
`/api/health` in the same signed-in browser. HTTP 200 with
`{"status":"ok","database":"ok"}` means the database and migration check
passed. It does not test Vertex AI. An unsigned request should redirect to
Google sign-in. Check Cloud Run request and application logs for the same
period; do not enable prompt or SDK debug logging.

## Update the application

1. Review and merge the approved code first. Start from the exact main commit.
   Run `uv sync --locked` and the relevant local checks. For database changes,
   review new migration files and their compatibility with the old app. Applied
   migration files are immutable.
2. Check the latest backup and take an on-demand backup before a schema or
   demo-data change. Wait for `SUCCESSFUL`. Do not deploy if recovery is not
   ready. Confirm expected cloud charges and any new model calls first.
3. Build one image tagged with the commit, then record its digest. Edit the
   image digest in all three reviewed files:
   [`cloud-run-service.yaml`](cloud-run-service.yaml),
   [`migrate-job.yaml`](migrate-job.yaml), and
   [`import-job.yaml`](import-job.yaml). Never use a moving `latest` tag.
4. Apply and execute the migration job. Check its execution status and log.
   Apply and execute the import job separately only when `hotel/` data changed.
   A successful job definition update is not proof that its task ran.
5. Deploy the reviewed service file. Check the ready revision and traffic,
   health, logs and the guest journey. Save the commit, digest, revision and
   checks in the release record.

```powershell
$commit = git rev-parse HEAD
$image = "europe-central2-docker.pkg.dev/smart-hotels-system/smart-hotel-demo/hotel:$commit"
gcloud builds submit --project=$project --tag=$image .
gcloud artifacts docker images describe $image --project=$project --format="value(image_summary.digest)"
# After putting the returned digest in the three reviewed YAML files,
# fill in the project number in ignored copies under .local/infra:
$projectNumber = gcloud projects describe $project --format="value(projectNumber)"
New-Item -ItemType Directory -Force .local/infra | Out-Null
foreach ($name in "migrate-job", "import-job", "cloud-run-service") {
    $text = (Get-Content "infra/$name.yaml" -Raw).Replace("PROJECT_NUMBER", $projectNumber)
    [IO.File]::WriteAllText("$PWD/.local/infra/$name.yaml", $text)
}
gcloud run jobs replace .local/infra/migrate-job.yaml --project=$project --region=$region
gcloud run jobs execute smart-hotel-demo-migrate --project=$project --region=$region --wait
# Run the import pair only when reviewed hotel data changed:
gcloud run jobs replace .local/infra/import-job.yaml --project=$project --region=$region
gcloud run jobs execute smart-hotel-demo-import --project=$project --region=$region --wait
gcloud run services replace .local/infra/cloud-run-service.yaml --project=$project --region=$region
```

The migration command is `python -m backend.app.db`. It uses a transaction,
advisory lock and file checksum ledger. A failed batch rolls back; fix the new
file, then rerun. The importer command is `python -m backend.app.inventory`.
It loads a validated, versioned `hotel/` revision in a separate transaction.
Follow [the hotel data guide](../hotel/README.md) before editing source data.
The import is repeatable, but a changed fact under the same source version is
rejected. Existing confirmed demo reservations keep their booked nights.

Model changes need a separate approved model, location and paid-call limit.
Edit `ASSISTANT_MODE`, `GOOGLE_CLOUD_LOCATION` or `GEMINI_MODEL` in the reviewed
service YAML, deploy a new revision, and check health and one approved live
answer. `stub` makes no Gemini calls but cannot prove the real assistant.

## Backups and safe restore

Standard Cloud SQL automatic backups are the planned basic recovery source.
The user selected seven daily copies, but did not approve enabling backups
yet. **Automatic backups are still disabled and no backup is available.**
Seven retained backups would normally cover about seven days, not an exact age
guarantee. On-demand backups have a separate lifecycle and should be deleted
after they are no longer needed. After approval, list backup IDs and states
with:

```powershell
gcloud sql backups list --instance=smart-hotel-demo-db --project=$project
gcloud sql backups create --instance=smart-hotel-demo-db --project=$project
```

For a recovery drill, create a **new**, clearly named Cloud SQL PostgreSQL 16
instance in the approved region. Verify its name differs from
`smart-hotel-demo-db`, then restore a successful source backup **to that new
instance only**. A restore overwrites its target and interrupts that target.
Do not point the live service, its jobs or secret at the drill instance. Check
the restored schema and demo data without using real guest credentials. Remove
the temporary instance after recording the result. The exact tested commands
and result belong in [the M3 handover](../docs/m3-handover.md).

Backups protect database state. They do not roll back code or reverse an
incompatible migration. The single-zone database has no high-availability
SLA, and standard backups in the same project do not cover project loss.

## Application rollback

Read the current traffic and revision list first. Confirm that the previous
revision is Ready, its image is still available, its IAP settings are intact,
and its code can use the **current** database schema and hotel revision. A
read-only revision check does not move traffic and does not prove that the old
code can run against every future schema.

For a non-disruptive probe, add a temporary tag to the previous revision,
confirm its traffic is 0%, open its tagged `/api/health` URL with the approved
account, then remove the tag and confirm the current revision still has 100%.
The tag URL has a different Origin, so this probe is limited to read-only
health. It does not prove the whole guest path or an actual traffic switch.

```powershell
gcloud run services update-traffic $service --project=$project --region=$region --update-tags=rollback-check=PREVIOUS_READY_REVISION
gcloud run services describe $service --project=$project --region=$region --format="json(status.traffic)"
# Open the returned rollback-check URL plus /api/health in the signed-in browser.
gcloud run services update-traffic $service --project=$project --region=$region --remove-tags=rollback-check
gcloud run services describe $service --project=$project --region=$region --format="json(status.traffic)"
```

If a new deployment fails, get approval before changing live traffic. Route
100% to the named last known good revision, verify health and the guest path,
then record the outcome. Do not restore a database as part of code rollback.

```powershell
gcloud run services update-traffic $service --project=$project --region=$region --to-revisions PREVIOUS_READY_REVISION=100
```

This routing change is immediate and Cloud Run does not rerun deployment health
checks first. Keep the old revision and image digest until the new release is
accepted. See [Cloud Run rollback guidance](https://cloud.google.com/run/docs/rollouts-rollbacks-traffic-migration).

## Common failures

| Symptom | First check and safe action |
| --- | --- |
| IAP redirects or denies an approved user | Check the signed-in Google account, IAP Web App User binding and OAuth client. Do not make the service public. |
| `/api/health` returns 503 | Check Cloud SQL `RUNNABLE`, Cloud Run startup logs, the socket attachment, secret reference and migration job. Do not print the secret value. |
| Chat fails while health passes | Check Vertex model/location, runtime IAM, the separate Vertex spend cap and safe error logs. Health does not call Gemini. |
| Search returns `unknown_inventory` | Check fixture horizon and import execution. Missing nights are not available nights. Publish a new reviewed demo revision when dates expire. |
| Migration or import job fails | Read execution status and safe logs; correct the file or source version, then rerun that job. Do not use the live database for tests. |
| Booking lookup returns 401 or 404 | Check the original guest session and its 24-hour expiry. A reference alone never grants access; the demo has no account recovery. |
| Budget or alert email absent | Inspect budget/channel and monitoring policy state. A configured threshold does not prove an email was delivered. |

For local development, follow [README.md](../README.md) and use the separate
disposable PostgreSQL database through `scripts/test.ps1`.
