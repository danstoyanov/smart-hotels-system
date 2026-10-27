# SIN-62 timeout comparison — 24 October 2026

**Historical investigation:** This report describes an earlier point in T05.
The later [foreground acceptance](sin-62-foreground-browser.md) passed, the user
merged PR #6 and SIN-62 is Done. Earlier In Progress/unmerged statements below
are historical. See [M1 handover](../m1-handover.md). No investigation was rerun.

## Result

The immediate failure is a provider-request read timeout before response headers.
The deeper cause is not proven. No production code correction is retained from
this task. Existing uncommitted work is preserved. PR #6 is not merged or updated
by a commit from this task; SIN-62 remains In Progress.

## Sources and scope

- PR #6 head: `c110e06eabc96be80264d36baabe53b5fcdf89d2`.
- Existing uncommitted diagnostics and evidence in this PR worktree were present
  before this task. They are not new verification runs by this task.
- Working local prototype: the separate checkout in Documents/ChatGPT, with its
  existing ADK playground. Its earlier successful live answers were reused as
  evidence; no new live question was sent.
- Owain reference: [agent.py](https://github.com/ai-developer-community/hotel-ai-agent/blob/269d6c1f989715aff72080fa90ba02fd3f21fd1f/backend/app/agent.py)
  and [tools.py](https://github.com/ai-developer-community/hotel-ai-agent/blob/269d6c1f989715aff72080fa90ba02fd3f21fd1f/backend/app/tools.py).
- Official SDK guidance: [optional aiohttp client](https://github.com/googleapis/python-genai#faster-async-client-option-aiohttp).
  The installed SDK source was also inspected.

## Differences found before edits

| Area | PR #6 / existing local work | Successful prototype |
| --- | --- | --- |
| Runtime versions | Python 3.13.2, ADK 2.13.0, GenAI 2.33.0, HTTPX 0.28.1 | Same versions |
| Async SDK transport | HTTPX; aiohttp absent | aiohttp 3.14.5 |
| Google endpoint configuration | Vertex, global, explicit API v1 | Google Cloud ADC, global, SDK default v1beta1 |
| Provider attempts | One; automatic retry disabled | Up to three configured attempts |
| Time bounds | HTTP 60 s, invocation 85 s, API 90 s | HTTP 60 s, no matching application deadline |
| Hotel facts | Royal Crest Manor, Europe/Kyiv, controlled versioned records | Sanctuary demo guide, Asia/Makassar |
| Model / thinking | Gemini 3.8 Flash, LOW thinking | Gemini 3.8 Flash, default thinking |
| Tool flow | Catalogue then full record; local pending work also prepares records | One read-only guide tool |

Both SDK clients were inspected with AnonymousCredentials and no network call.
This confirmed the selected transport, rather than inferring it from lockfiles.
The reference also uses catalogue/read tool calls, LOW thinking, SSE, isolated
working state and one provider attempt. These patterns do not by themselves
explain the timeout and do not justify replacing the application architecture.

## What the existing evidence establishes

`docs/sin-62-browser-failure.json` records one attempted model call. Its request
started at 3.235 seconds and failed at 63.360 seconds, without a response-header
event, HTTP status or usage. The failure occurred before a model-selected tool
was called. This is consistent with the configured 60-second HTTP wait, rather
than the outer 85/90-second deadlines. It does not identify whether the delay
was at the provider, proxy or connection layer.

`docs/sin-62-live-evidence.json` also contains earlier successful PR-worktree
breakfast, price and booking-limit answers. Therefore, the HTTPX path is not
proven to fail for every request. Pre-reading records may reduce round trips,
but it does not establish a fix: the browser failure was on the first request
with a record already prepared. Missing usage and cost remain unknown.

## Two bounded correction/check cycles

1. Tried the official `google-genai[aiohttp]==2.33.0` extra, keeping the model,
   endpoint settings, retries, deadlines and architecture unchanged. Added an
   offline SDK-boundary test and a candidate distinction between model timeout
   and outer application timeout. Lock resolution selected aiohttp 3.14.5 without
   changing ADK or GenAI versions. Lint stopped on a 101-character line before
   tests ran.
2. Fixed that line. Lint and formatting passed. Focused checks finished with
   **15 passed, 1 failed**. The new test intercepted the real aiohttp request,
   but its `method == "POST"` assertion failed because the SDK supplied `post`.
   It stopped before the simulated timeout. This is a test-fixture error, not
   evidence that the production timeout correction works or fails.

No third cycle was run. The candidate dependency, lockfile, diagnostics and test
changes were restored byte-for-byte from the pre-task snapshot. Environment sync
was used only to restore the original locked packages. No paid Gemini calls,
Google Cloud changes, new project, database infrastructure or PR merge occurred.
The historical checks in the earlier verification report are not new passes.

## Verifiable blocker and next step

The observed failure location and transport difference are established; a causal
fix is not. Paid calls are not authorized for this continuation. An explicitly
approved, bounded live comparison is needed to test the aiohttp candidate in
the actual PR adapter with the same question and otherwise unchanged settings,
no automatic retries, and captured elapsed time, phase and reported usage. Keep
API-version, thinking and transport changes separate. The successful prototype
alone cannot prove which difference matters, or rule out intermittent service
latency. Keep PR #6 in draft and SIN-62/M1 incomplete.


## Approved follow-up

The later user-approved two-run comparison and the bounded aiohttp runtime
mitigation are recorded in [sin-62-transport-ab.md](sin-62-transport-ab.md) and
[the JSON evidence](sin-62-transport-ab.json). The preceding sections describe
the earlier stopped investigation, not the current follow-up result.
