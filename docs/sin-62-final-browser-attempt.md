# SIN-62 final browser acceptance attempt — 24 October 2026

## Outcome: failed; stopped

The user explicitly approved one paid browser-submitted question, up to eight
internal model calls, and no automatic retries. The existing application ran in
Vertex mode against the existing local `sin62_assistant_demo` PostgreSQL database.
The existing Chrome/Playwright live test submitted:

`Is breakfast included and when is it served?`

No mock, fixture response or request interception was used.

## Exact failure evidence

- Browser error: `Reply interrupted. Reload history, then try again.`
- Browser stack: `frontend/tests/assistant-live.browser.cjs:29:13`.
- Adapter classification: `MODEL_TIMEOUT`.
- Exception: `TimeoutError`; recorded chain: `TimeoutError`, `CancelledError`.
- Phase: `model`; one model call attempted.
- Elapsed adapter time: **64.519 seconds**.
- No provider HTTP status or usage was returned. All reported token fields and
  billed cost remain unknown, not zero.

The server access log records the chat POST count in
[the JSON evidence](sin-62-final-browser-failure.json). The browser error and full
safe invocation diagnostics are preserved there. See the
[failure screenshot](screenshots/sin-62-final-browser-failure.png).

## Configuration preserved

Transport remains aiohttp. Model gemini-3.8-flash, smart-hotels-system/global,
Vertex API v1, temperature 0.2, HTTP timeout 60000 ms, LOW thinking, 2048 output
tokens, maximum eight model calls, one provider attempt, and existing application
deadlines are unchanged. No Google Cloud settings were changed.

## Stop condition respected

No second question, retry, investigation, further test, commit or push followed
the failure. The temporary acceptance server on port 8074 was stopped; the other
local application and database processes were preserved. The live test did not
reach answer/source and refresh verification, so those acceptance checks remain
unpassed. No conclusion is drawn about the timeout's cause.

T05 is not ready for final acceptance or merge. PR #6 remains unchanged remotely.
Further work requires the user's decision.
## Focused smoke/browser comparison — 24 October 2026

No paid request or application-code change was made for this comparison.

| Item | Successful aiohttp smoke | Failed real browser |
| --- | --- | --- |
| Actual async transport | aiohttp | aiohttp, confirmed by traceback in `aiohttp.client` |
| Model input SHA-256 | `6bc9fde28ccff50cebd5e8f044ca9e78cd54a1377bcc9a3ca12abc8deb29e94f` | Identical |
| Configured endpoint / API | Vertex global, project smart-hotels-system, v1 | Identical explicit client configuration |
| Generation configuration | Gemini 3.8 Flash, temperature 0.2, LOW thinking, 2048 output tokens, one attempt | Identical |
| Time limits | HTTP 60 s; runner 85 s | HTTP 60 s; runner 85 s; API 90 s; session lease 120 s |
| Model-call cap / attempted | 2 / 1 | 8 / 1 |
| Runtime | Same Python 3.13.2 environment and pinned SDKs; Windows selector loop | Same environment; Uvicorn custom loop factory resolves the same `new_loop` |
| Launch | Foreground CLI in an active execution session | Detached Start-Process child, API port 8074, INFO logging, existing demo PostgreSQL database |
| Result | 7.149 s; 872 reported tokens | 64.519 s; no response status or usage |

The input hash covers model, contents (including history) and generation config,
but excludes HTTP options. It is not a live wire-body or resolved-IP capture.
Identical input hashes establish that the prepared prompt, hotel evidence, tools
and guest input match. Endpoint, API version and HTTP timeout are equal in the
shared client constructor and process startup parameters. No actual aiohttp
request URL/resolved IP/proxy/credential fingerprint was saved for both historical
calls, so complete network-environment equality cannot be claimed.

The extra model-call allowance cannot explain this failure: only the first call
was attempted. APP_ORIGIN and DATABASE_URL differ from the direct smoke context,
but neither changes the provider request. The failure stack is waiting at
`await resp.start(conn)` for HTTP response headers, not in database saving or
browser rendering. No proven configuration/code cause was found.

### Deadline alignment

The intended order is 60 < 85 < 90 < 120 seconds. The 60-second HTTP limit is per
request; 85 seconds bounds the whole runner, not eight times 60 seconds. The
session lease starts at admission and outlasts the API deadline. The observed
failure occurs well before the 85/90/120-second limits, so those limits did not
cause this attempt's failure.

There is a narrow edge near the outer deadline: the five seconds from 85 to 90
can be consumed by the adapter's shielded five-second cleanup, with no guaranteed
reserve for setup/history/database commit. The runner's 85-second scope starts
after setup; shielded cleanup can also outlive outer cancellation. GuestStream
has its own bounded five-second cleanup. This timing design is not a strict
90-second wall-clock guarantee. It does not explain the observed HTTP timeout
at 64.519 seconds, and no deadline was changed without evidence of that edge.

### Proposed next experiment — not executed

After a new explicit approval, run the same existing API server in the foreground
inside an active execution session, instead of a detached Start-Process child.
Keep aiohttp, endpoint/API, all Gemini settings, question and deadlines unchanged.
Use the existing browser test for one breakfast question, at most eight model
calls and no automatic retries. Record the same input hash, actual SDK transport
and endpoint, safe network-environment fingerprints (no tokens/credentials),
model-call timing and result. Keep the launching session alive until the browser
finishes. This tests the concrete process/network-lifetime difference and can
complete the remaining acceptance path if it succeeds; a single success still
would not prove a universal timeout cause.

No arbitrary transport, temperature, thinking, timeout or cloud change was made.
Stop here pending the user's decision.


## Later foreground result

The user subsequently approved a single foreground-browser attempt. It passed
without Gemini configuration changes; see [sin-62-foreground-browser.md](sin-62-foreground-browser.md).
This document preserves the earlier detached failure and is not the current acceptance status.
