# Task workflow

The step-by-step checklist for one Linear issue. Lasting rules are in
[AGENTS.md](../AGENTS.md). Rules that apply to only one task go in its Linear issue.

## Start

- [ ] The user approved execution of this issue.
- [ ] Every `Blocked by` issue is Done and its PR is merged.
- [ ] Get the real Linear ID. Rename the chat to 🔴 <ID>.
- [ ] Set the issue to **In Progress**.
- [ ] Fetch remote refs. Create a new worktree from the latest `origin/main`
      with branch `codex/<linear-id>-<short-description>`.

## During the work

- [ ] Before each action, give the user a few short bullet points in Bulgarian.
- [ ] Ask open questions when they become relevant. Reuse confirmed answers and
      continue independent work while you wait.
- [ ] Stay inside the issue scope. Report larger changes to the user instead of
      making them.
- [ ] Keep evidence (screenshots, JSON reports) in the PR or the Linear issue, not
      in `docs/`. Browser tests write screenshots to `.local/screenshots/`.

## Finish

- [ ] Run the checks that fit the change (see AGENTS.md). Record what you
      actually ran and what you did not run.
- [ ] Open a PR in `danstoyanov/smart-hotels-system`. The
      [PR template](../.github/pull_request_template.md) lists the sections.
      Add desktop and mobile screenshots for visual changes.
- [ ] Attach the PR to the Linear issue. Set the issue to **In Review**.
- [ ] Post a **Result / Check / Next** report in short bullets on the issue.
      Check scope, dependencies and completion evidence against PLAN.md. Leave
      the issue In Progress or In Review while a required result is missing.
- [ ] After the user merges and accepts: set **Done**, rename the chat to 🟢 <ID>
      and update local `main`.

## Linear issue template

Use this for new issues. Create it once in Linear (Settings → Templates).

```markdown
## Goal

<One or two sentences: the result for the guest, the hotel or the project.>

## Implementation

* <Main changes, in order.>
* <Open questions to ask the user when they become relevant.>

## Acceptance

* <Observable results that prove the goal.>
* <Checks that must pass. Mark Done only after the user merges the PR.>

## Notes for this task

* Follow AGENTS.md and docs/workflow.md.
* <Only rules that apply to this task: coding model, budget for paid calls,
  files not to touch, and so on.>
```

## Milestone review

At each milestone handover, spend about ten minutes on AGENTS.md and this file:

- Remove rules that did not protect against a real problem.
- Add a rule only after a real problem, not "just in case".
- Move rules that only applied to one task back into that task's issue.
