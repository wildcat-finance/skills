# Decision: Refuse receipted commits carried into a lower step branch

## Status

Accepted, 2026-09-18, for the skills#1480 study. Step 1 publishes it in the canonical numberless draft home. It has no ADR number.

## Context

In the integrate phase, a later step's receipted commits can be merged into a lower step branch that has not merged yet. At `f0fa0c6632bd5fbef7f35e731646c32741ef282a`, `refuse_rewritten_stack` in `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` admits any moved waiting tip whose receipted head is still an ancestor. `done_merge_step` passes `expected_head_sha=None`, so a moved tip is repaired through `verify_local_range(pr_base, remote_head)` and the carried commits are receipted as the lower step's work. `docs/fiat-carried-step-commits/admission-at-starting-ref.txt` records that controller answering `admitted` for a three-step stack whose step 3 branch was merged into the waiting step 2 branch.

Issue 923 admits an honest extension on a status-0 ancestry answer and issue 1021 receipts an early merge as `early_merge` with `reachable_from`. Both stand. The abandoned branch `fiat/555-refuse-misdirected-step-merges` priced per-commit ancestry at 249,500 pairs on a 500-step fixture and added GitHub reads at `next`.

## Decision

1. Admissibility is by receipt ownership, not by direction or by pull-request state. For each unmerged step whose observed tip differs from its recorded head, the gained range refuses when it holds a commit another step's push receipt owns: the union of every other step's `verified_commits`, else its `head_commit`. A step whose push receipt records `early_merge` is excluded from that set. A cherry-picked copy under a new SHA is out of scope; ownership is by exact SHA.
2. Evidence is split by phase. At `next`, one bounded native `git rev-list --max-count=501 <recorded>..<tip>` runs per moved tip, through `_native_relation_git` with the 30 s timeout and 2 MiB output cap, and there is no GitHub read. At `done merge-step`, the exact repaired range `pr_base..remote_head` that `verify_local_range` already enumerates is intersected with the same set before any mutation. A `rev-list` that fails, times out, exceeds the cap or lists more than 500 commits refuses as unknown.
3. No new receipt field or ledger event. A refusal leaves `state.json` and `ledger.jsonl` byte-identical, legacy runs need no migration, and `verify` replays nothing new. `status` reports a carry as one line and does not refuse.

The reference procedures and their measured results are `docs/fiat-carried-step-commits/design-evidence.json` and the 32 reports under `docs/fiat-carried-step-commits/reports/`; the selection rule is `unique-frontier`.

## Alternatives

- **`owned-commit-ancestry`:** one `merge-base --is-ancestor` per commit owned by every higher step against each lower tip. It passes every gate. It costs 7 added native processes on the healthy three-step fixture against 1, and the process count grows with the commit count.
- **`pull-request-merge-state`:** read each unmerged step's pull request from GitHub at `next` and refuse a merge into a base other than the run branch. It catches only a carry made through the recorded pull request, reads clear on a plain pushed merge or a fabricated tip, and adds one GitHub read per unmerged step per directive. It fails `refuses-whole-carry`, `refuses-partial-carry`, `no-new-github-reads` and `unknown-refuses-as-unknown`.
- **`merge-time-only`:** leave `next` unchanged and intersect the repaired range at `done merge-step` only. Zero added reads at `next`, but the carry stays admitted until the receipt, which comes after the merge the directive asked for has landed. It fails `refuses-whole-carry`, `refuses-partial-carry` and `unknown-refuses-as-unknown`.

## Consequences

`next` withholds the `merge-step` directive and `done merge-step` refuses before mutation when any unmerged tip's gained range, or the repaired receipt range, holds a commit another step's receipt owns. The refusal names the step, branch, recorded head, observed tip, the first carried commit and its owning step, and claims no cause. A healthy stack costs one added native process per `next`, the current-step tip read; a moved tip costs one `rev-list` of at most 501 lines.

Not covered: a cherry-picked copy of another step's commit, a wrong pull-request base before `done merge-step`, repair of a stack already carried, and `refuse_rewritten_stack`'s status-0 admission for commits nobody owns. `docs/decisions/ADR-021-land-a-rewritten-stack-from-the-original-commits.md` is not edited and still owns the genuine-rewrite landing. Number assignment belongs to integration against the actual base; the standing home until then is `docs/decisions/drafts/refuse-receipted-commits-carried-into-a-lower-step-branch.md`.
