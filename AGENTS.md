# Project instructions

Lasting rules for every task. Follow [docs/workflow.md](docs/workflow.md) for the
task steps (Linear, branch, PR, reports). Rules for one task belong in its Linear issue.

## Read first

- The current Linear issue, PLAN.md sections 1 and 3–6, this file, brief.md,
  docs/m3-handover.md, and PRODUCT.md and DESIGN.md (for visual work).
- PLAN.md section 2 describes the current architecture; it is not a feature checklist.
  Keep PLAN.md focused on future work.
- REFERENCE.md is a pointer only. Consult the example project only when the user asks.

## Scope

- One fictional demo hotel with local `hotel/` data, FastAPI, PostgreSQL, Google ADK
  and Gemini. Use clear Python and browser JavaScript.
- Follow the confirmed choices in brief.md. Label fictional content and demo reservations.
- Exclude payments, real hotel integrations and multiple hotels.
- Cloud resources and paid model calls need explicit user approval. Missing approval
  is not approval.

## Safety and checks

- Run `uv sync --locked` from the root. README.md has the startup steps.
- Use `scripts/check.ps1` for local checks and `scripts/test.ps1` for the separate
  disposable PostgreSQL database. Never use the application database for tests.
- Do not invent setup commands. Do not claim that a check passed unless you ran it.
- Never commit credentials or real guest data.
- Add focused safeguards and checks with each feature. For documentation changes,
  check the diff, links (`scripts/check_links.py`) and agreement with the plan.

## Communication and review

- Talk to the user in Bulgarian. Write code, documentation, commits, PRs and Linear
  text in English B1–B2.
- Work on one issue at a time. Do not start other agents.
- The user reviews and merges. Do not merge or begin the next issue yourself.
