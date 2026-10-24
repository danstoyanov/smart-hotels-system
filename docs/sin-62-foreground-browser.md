# SIN-62 foreground browser acceptance — 24 October 2026

## Result: requested acceptance flow passed

The existing FastAPI application ran in the foreground in an active execution
session, using the existing local demo PostgreSQL database. The existing real
Chrome/Playwright test submitted one breakfast question through the actual API.
No mock/fixture response or request interception was used.

The user separately approved exactly one paid user request, up to eight internal
model calls, no automatic retries and no changes to Gemini settings. The browser
and server each recorded exactly one chat POST. The adapter attempted one model
call, with one provider attempt.

## Answer and persistence checks

Question: `Is breakfast included and when is it served?`

Answer: Breakfast is included at Royal Crest Manor, daily 07:00–10:00. Special
dietary arrangements need staff confirmation and cannot be arranged through this
demo. The answer was compared with the reviewed local hotel record.

- Correct answer and the `Breakfast` demo source v1 were visible in the page.
- The source route returned HTTP 200 and the expected source version.
- The completed answer and source references were stored by the real API/database.
- After page refresh, the history API returned the same turn and sources, and the
  page displayed the same answer and source URLs.
- Existing desktop/mobile checks found no horizontal overflow or page errors;
  screenshots were inspected. The existing reset check also passed without a
  second model question.

Evidence: [browser result and safe diagnostics](sin-62-live-browser.json),
[desktop](screenshots/sin-62-final-live-desktop.png),
[mobile](screenshots/sin-62-final-live-mobile.png),
[safe startup environment](sin-62-foreground-environment.json).

## Timing and usage

- Complete browser journey: **10.516 seconds**.
- Adapter invocation: **7.887 seconds**, completed without failure.
- One model call: **6.459 seconds**.
- Reported usage: **825 input + 44 output = 869 total tokens**.
- Reported usage is complete for the call. No thinking count was returned; no
  dollar cost was calculated. Missing cost is unknown, not zero.
- Model input SHA-256: `6bc9fde28ccff50cebd5e8f044ca9e78cd54a1377bcc9a3ca12abc8deb29e94f`,
  matching the earlier smoke and detached-browser inputs.

## Configuration unchanged

Gemini 3.8 Flash; aiohttp 3.14.5; Vertex project smart-hotels-system, global/v1;
temperature 0.2; LOW thinking; 2048 output tokens; HTTP timeout 60 seconds;
runner/API/lease limits 85/90/120 seconds; maximum eight model calls; provider
attempts one. No Google Cloud settings, deployment, IAM or billing changes.
The test used only process-local runtime settings; no credentials were committed.

The foreground attempt passed after the earlier detached attempt timed out.
This does not by itself prove that process detachment caused the timeout or
that future provider timeouts are eliminated. No more experiments, tests or
features were added after this pass.

## Handover

All requested T05 technical acceptance checks now have evidence: representative
real-model answers, unknown-fact/booking honesty, focused offline adapter/tool
checks and the real website persistence/refresh journey. Earlier offline and
live checks are recorded in the existing verification and transport reports;
they were not rerun for this final attempt.

The changes are prepared for commit on the existing T05 branch for PR #6.
Final acceptance and merge belong to the user. No new PR or merge was made;
do not mark SIN-62 Done before acceptance and merge.
