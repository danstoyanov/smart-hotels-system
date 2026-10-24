# SIN-62 controlled transport comparison — 24 October 2026

## Result

Changed the existing T05 adapter to use aiohttp by default. HTTPX remains an
explicit comparison option. The required `google-genai[aiohttp]==2.33.0`
dependency locks aiohttp 3.14.5; ADK 2.13.0 and GenAI 2.33.0 are unchanged.
This is a supported local runtime mitigation, not proof that HTTPX is defective
or that every future timeout is fixed. No architecture replacement was made.

## Authorization and fixed inputs

The user explicitly approved at most two paid agent executions, one per transport,
with at most two model calls each (four total maximum), and no automatic retries.
Exactly two executions ran, with one model call attempted in each. No additional
paid browser, smoke, retry or grading call was made.

Both used the existing adapter and the same hotel snapshot, empty history,
property date, question, prompt, tools, Gemini 3.8 Flash, project
`smart-hotels-system`, location `global`, Vertex API `v1`, LOW thinking,
temperature 0.2, output-token limit 2048, HTTP timeout 60000 ms and invocation
limit 85 seconds. Provider attempts remain one. Only the HTTP transport changed.
Settings applied only to that command's process; persistent stub configuration,
Google Cloud resources, IAM, billing settings and account configuration are unchanged.

The question was: `Is breakfast included and when is it served?`
The first-model-request SHA-256 values match in the live report. Offline checks
also compared the actual serialized JSON payloads and verified the same endpoint,
API version, 60-second timeout configuration and absence of retries.
HTTPX uses its per-operation timeout semantics; aiohttp uses its total-request
semantics for the same SDK timeout value. The outer application limit is equal.

## Recorded results

| Transport | Outcome | Total elapsed seconds | Model calls | Phase | Reported usage |
| --- | --- | ---: | ---: | --- | --- |
| HTTPX | ReadTimeout before response headers | 67.573 | 1 | model | Unknown |
| aiohttp | Completed, answer reviewed against hotel record | 7.149 | 1 | completed | 825 input + 47 output = 872 total tokens |

Total elapsed includes client setup, authentication and cleanup. The HTTPX request
started at 5.998 s and failed at 66.268 s, consistent with its 60-second read wait.
No provider HTTP status or usage was returned for that call; billed usage/cost
remain unknown. Missing thinking usage is unknown, not a reported zero.
The aiohttp answer correctly states included breakfast, 07:00–10:00, dietary
arrangements requiring staff confirmation, the demo limitation and the Breakfast
version-1 source.

Full timings, phases, call counts, usage and input hashes are in
[the JSON evidence](sin-62-transport-ab.json). Model callbacks measure both paths;
HTTP request/header hooks are specific to the HTTPX comparison path. The lack
of an aiohttp header-hook event is not evidence of absent headers.

## Changes and offline checks

- Kept the existing adapter, controlled tools, session/persistence architecture
  and all model/endpoint/generation settings.
- Added a two-run comparison mode to the existing smoke runner, with explicit
  paid opt-in, a fixed breakfast question, a frozen property date and two-call cap.
- Corrected the method assertion to `method.lower() == "post"`.
- Distinguish model-originated aiohttp TimeoutError from the outer application
  deadline; preserve HTTPX ReadTimeout classification and unknown usage/cost.
- The 12 focused adapter/diagnostic tests passed, including serialized-request
  parity, both mocked SDK transport boundaries, no retry, opt-in and run limits.
  No new test service, database cluster or test framework was created.

To prepare dependencies: `uv sync --locked`.
Only after a separate explicit paid approval, the comparison command is:

```powershell
uv run --locked python -m backend.smoke --compare-transports --case breakfast --approved-paid-calls --output docs/sin-62-transport-ab.json
```

Do not rerun that command under this task's consumed two-execution approval.
It needs Vertex runtime settings for its process. No `.env` or gcloud change is
required to preserve the normal stub setup.

## Remaining T05 acceptance checks

Only the successful real-model website journey remains unverified on the current
T05 runtime: send a question, receive and save its answer/sources, open a versioned
source, then refresh and recover the saved conversation. The existing real-browser
check previously failed on the provider request; its fixture checks are not a live
pass. It needs a separately approved live agent execution, beyond this task's
consumed two-run allowance. The existing browser script is available; no new test
infrastructure is needed.

Existing live evidence already covers arrival, breakfast, unknown prices and
refusal to claim booking/availability success. Focused offline checks cover the
adapter/tools and failure contracts. Do not repeat those checks merely to claim
broader certainty. No soak test or general proof of reliability is a T05 criterion.
T05/M1 cannot yet be marked accepted; PR #6 remains unmerged and no new PR was made.


## Later acceptance update

The separately approved foreground real-browser test passed with one user request
and one model call, including answer/source persistence and refresh. See
[the foreground report](sin-62-foreground-browser.md). The earlier remaining-check
section is historical; no requested T05 technical check remains unverified.
User acceptance and merge are still pending.
