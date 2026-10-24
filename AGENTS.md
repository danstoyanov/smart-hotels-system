# Project instructions

## Start and scope

- Read the current Linear issue, PLAN.md sections 1 and 3–5, this file, brief.md and docs/m1-handover.md. Read DESIGN.md if present.
- PLAN.md section 2 is architecture guidance, not a feature checklist. Keep the plan focused on future work.
- REFERENCE.md is a pointer only. Consult the example project only when the user asks.
- Build one demo hotel with local `hotel/` data, FastAPI, PostgreSQL, ADK and Gemini. Use clear Python and browser JavaScript.
- Follow the confirmed choices in brief.md. Label fictional content and demo reservations. Exclude payments, real hotel integrations and multiple hotels. Cloud resources and paid calls need explicit authorization.

## Setup and checks

- Run `uv sync --locked` from the root. See README.md for PostgreSQL and PowerShell startup.
- Use `scripts/check.ps1` for local checks and `scripts/test.ps1` for the separate disposable PostgreSQL database. Never use the application database for tests.
- Do not invent setup commands or claim unrun checks passed. Never commit credentials or real guest data.
- Add focused safeguards and checks with each feature. For documentation changes, check the diff, links and agreement with the plan and confirmed choices; no application tests are needed.

## Task and review workflow

- Use English B1–B2 in documentation, reports and PRs. Give short bullet updates before actions and while working.
- Get the real Linear ID. Name the chat 🔴 <ID> at start and 🟢 <ID> only after acceptance and PR merge.
- Start after execution approval and after blocking issues are Done with their PRs merged. Fetch origin, then create a managed Codex worktree from the latest origin/main and a branch named codex/<linear-id>-<short-description>.
- Work on one issue in its worktree. Reuse confirmed answers; ask relevant open questions and continue independent work while waiting. Missing approval is not approval.
- For SIN-58, use gpt-6.1-sol with low reasoning effort. This coding model is separate from the hotel's Gemini runtime model. Ask before substituting if unavailable.
- Use local checks and human review. Do not start other agents. Open a PR in danstoyanov/smart-hotels-system with the issue ID/link, changes, actual checks and limitations. Include desktop/mobile screenshots for visual changes. Attach the PR to Linear and the Codex chat.
- Set Linear In Progress at start and In Review when the PR is ready. The user reviews and merges. Set Done only after merge and acceptance; do not merge or begin the next issue yourself.
- Report Result / Check / Next in short bullets. Check scope, dependencies and completion evidence against PLAN.md. Leave the issue In Progress or In Review while required results are missing.
