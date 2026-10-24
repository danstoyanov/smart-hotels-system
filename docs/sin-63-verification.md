# SIN-63 verification

## Failed checks and next changes

- Initial fetch: `.git/FETCH_HEAD: Permission denied`. Hypothesis: sandbox blocks Git metadata writes. Change: run the same fetch with approved extended access. Result: passed.
- Worktree setup: Git did not recognize the work tree and uv cache writes were denied. Hypothesis: the new managed worktree is outside the current sandbox roots. Change: use approved extended access in that exact worktree. Result: branch creation and `uv sync --locked` passed.
- New test lint: UTC alias, lambda style and long SQL lines failed. Hypothesis: test formatting only. Change: use UTC, a named helper and split SQL strings. Repeat only new test lint and format.

## Scope

Read-only full-stay search for one fictional demo hotel. No booking writes, website changes, paid calls or cloud changes.

- First full run: 61 passed, two failed. Inventory SQL cases passed before the offline ADK model failed while deep-copying a request (`cannot pickle _asyncio.Task`). Hypothesis: the copied tool holds the real pool. Change: record only tool/contents strings in this test model; repeat inventory tests only.
- The same run also failed the existing Vertex route test: its adapter stub does not accept the new availability keyword. Hypothesis: stale test signature. Next change, after the inventory result: update only that stub signature and verify the injected service.

- Focused inventory repeat: the ADK tool ran, but the assertion could not see room IDs because SDK string output abbreviates dictionaries. Change only test capture to JSON message contents, then repeat inventory checks. No application change.

- Inventory tests after JSON capture fix: 2 passed. Next: update only the existing route test adapters to accept availability and assert its service type; repeat that route test.

- Existing Vertex route test after signature fix: 1 passed. No application behavior change was needed.

## Acceptance evidence

- The first `scripts/test.ps1` run completed lint, format, JavaScript syntax, three
  SSE module tests and hotel validation. Python: 61 passed and two failed.
- Both failures were localized to test adapters, corrected one factor at a time,
  and verified with the affected tests on fresh disposable PostgreSQL containers.
- Inventory checks cover full stays, overlap with a closed night, adjacent dates,
  missing nights, capacity (including exact capacity), invalid dates/counts,
  API/tool equality, direct SQL safeguards and unchanged inventory after searches.
- A real ADK runner with a scripted local model calls the real database tool and
  receives the available room facts. No provider client or paid request is used.
- The existing Vertex route test checks the new service argument and retains
  history/source persistence and isolation checks.

## Limits

No live Gemini test was run: paid calls were not authorized. No visual changes
were made, so desktop/mobile screenshots do not apply. Fixed demo dates stay in
November 2026. Test-only copies move the same open/closed pattern into the future.
Reservations, room pages and booking navigation remain T07/T08 work.

## Final result

- Result: SQL, API and agent share full-stay/capacity rules. The active fixture
  import is atomic, repeatable and rejects changed data under the same version.
- Check: final focused inventory run: 2 passed, including revision rejection.
  Final affected route run: 1 passed. These close the two failures from the first
  full run; the whole suite was not rerun after those test-only corrections.
  Lint/format checks on changed tests and `git diff --check` passed.
  The disposable `test-db` container was removed after every run and its final
  Compose status was empty. The application database was not used for tests.
- Next: human review of SIN-63 and its PR. No merge or next issue is authorized.

The SDK emitted existing Starlette HTTP client and aiohttp deprecation warnings.
They did not fail the checks. No dependency versions or Gemini runtime settings
were changed. PLAN sections 1 and 3–5 were checked: this delivers T06 only; M2
still needs T07/T08 and acceptance. SIN-62 is Done and its PR #6 merge is an
ancestor of the worktree base `cc4c237af8f09ac2617fe5e7b12fa24d35e92702`.
