# Decision: Dispatch the skills-runtime rebuild from the source repository

## Status

Accepted, 2026-09-17, for the #1053 study. Publication in the canonical numberless draft home `docs/decisions/drafts/dispatch-the-skills-runtime-rebuild-from-the-source.md` is due in Step 1 of the run; the number is assigned at integration under ADR-077. Amends ADR-066, which stays accepted: its hourly-schedule statement and its accepted hour of lag no longer describe how the package is rebuilt.

## Context

ADR-066 moved the generated package to `wildcat-finance/skills-runtime` and had that repository rebuild it on an hourly `schedule`, with up to an hour of lag accepted as the cost of the split. The schedule never fired. At 2026-09-17T21:09Z the destination had zero `schedule` runs and three `workflow_dispatch` runs since its creation on 2026-08-30, roughly 430 missed firings, while sibling repositories in the same organisation ran thousands of scheduled runs in the same period. The organisation Actions policy is therefore not the cause, and the repository-level policy allows all actions. What remains is GitHub-side: the `schedule` trigger of this workflow was never registered, and nothing in the destination can prove otherwise until it fires. The published package sat at a source commit 17 days old while the generator and the payload moved.

The generated `README.md`, `docs/skills-runtime-publication.md`, `INSTALL.md` and the root `README.md` all told readers the package was rebuilt hourly.

## Decision

A workflow in `wildcat-finance/skills`, `.github/workflows/dispatch-skills-runtime-rebuild.yml`, runs on every push to `main` and on manual dispatch and starts the destination's existing `workflow_dispatch` job through `POST /repos/wildcat-finance/skills-runtime/actions/workflows/sync.yml/dispatches`. It authenticates with `RUNTIME_DISPATCH_TOKEN`, a fine-grained token an operator creates by hand with Actions read and write on `wildcat-finance/skills-runtime` only. The workflow declares `permissions: {}`, checks nothing out, and refuses with an explicit error when the secret is absent.

The destination job is not changed. It keeps its own `GITHUB_TOKEN`, `contents: write`, drift guard, verification before commit, and `schedule` entry. The schedule is no longer relied on; the source push is the trigger, and manual dispatch is the recovery path when the token is absent or revoked.

The generated `README.md` and the three documents describe the trigger as it is: rebuilt when the source `main` moves, with the source commit recorded in the package.

## Alternatives

- **Re-register the schedule** by changing the cron expression in both copies of `sync.yml`. Needs a workflow-scope push to the destination, cannot be verified until the next firing, keeps the hour of lag, and rests on an unproven cause. Removed by the schedule-independence gate.
- **Poll faster in the destination** with a second cron entry. Depends on the same `schedule` event that never fired. Removed by the same gate.
- **Push from the source on merge**, ADR-066's rejected option B. Needs a contents-write credential across the repository boundary and gives up the destination's self-contained token story. Removed by the permissions gate.

## Consequences

One secret exists in `wildcat-finance/skills` that can start, and only start, a job in `wildcat-finance/skills-runtime`. Its expiry and revocation are operator events; the dispatch workflow fails red on the next push to `main` when it is gone, and the last published package stays where it is. The published package now moves within about one minute of a source merge rather than within an hour, and currency is checkable as before from the source commit the package records.

ADR-066's `schedule` remains in the destination workflow because removing it needs a workflow-scope push that this run does not make. Issue #1052's drift-guard repair stays its own coordinated change to that file.
