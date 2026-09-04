# Local proof: stale-base exclusion

Status: repository bootstrap, 4 September 2026.

## Scope

This proof covers the local allocator and the base-owned workflow contract.

- The standing choice remains in
  [the unnumbered decision](../decisions/drafts/assign-adr-numbers-at-merge-not-at-authoring.md).
- Hypomnema's governed row remains in
  [`hypomnema/EVOLUTION.md`](../../plugins/hexaemeron/skills/hypomnema/EVOLUTION.md).
- Fiat's composition evidence remains in
  [`fiat/EVOLUTION.md`](../../plugins/hexaemeron/skills/fiat/EVOLUTION.md).

## Reproduction

Run from the repository root:

```bash
python3 -m unittest tests.test_adr_assignment_workflow -v
python3 -m unittest plugins.hexaemeron.tests.test_hypomnema_decision_assignments -v
python3 -m unittest plugins.hexaemeron.tests.test_fiat_decision_assignments -v
python3 -m unittest tests.test_decision_records -v
```

The root fixture begins with ADR-060 at base `B`. Candidate `A` and candidate
`B` each plan `adr/<slug>=ADR-061`. After candidate `A` advances the fixture's
`main` ref, replay of candidate `B` returns `base-moved`. Rebuilding candidate
`B` from that new base plans ADR-062. The mutation fixture removes the two
mutable-base comparisons from a disposable allocator copy and confirms that
the stale report then replays, so the comparison is the causal guard.

The workflow execution fixture serves the candidate through a disposable bare
remote. A candidate executable, tracked attributes, and a remote repository
filter remain inert while the base-owned policy accepts the exact assignment
tree. A second fixture gives the runner account a global `core.hooksPath`
whose `reference-transaction` and `post-index-change` hooks touch a sentinel;
the policy accepts without the sentinel appearing, and a disposable copy of
the step with its `HOME`, `GIT_CONFIG_GLOBAL`, and `core.hooksPath` isolation
removed does fire the hook, so the isolation is the causal guard. The object
ceilings bound the objects reachable from the head but not from the base, so
a base history larger than the ceiling does not refuse the candidate; a
lowered-ceiling copy of the step shows the acceptance and the refusal on
either side of that count. Separate cases refuse a moved head and malformed
assignment trailers.

## Enforcement qualification

A 4 September 2026 read of ruleset `21830871` (Required CI, default branch)
recorded enforcement `evaluate`, required contexts `identity` and `invariants`
under integration `15368`, strict up-to-date checks off, and no bypass actors.
This step does not change that ruleset. The
`adr-assignments` context is not required, and Actions integration `15368` has
not been verified for this context by a live canary. Production race freedom
is not claimed.

A later separately authorised operation must observe the status on its exact
head, require integration `15368`, turn strict up-to-date checks on, keep the
bypass set empty, and activate the ruleset. Strict up-to-date checks are the
merge-time half of stale-base exclusion: no `pull_request_target` event fires
when `main` moves, so a success status posted against an earlier base stays on
the head until the branch is updated, and only the strict policy forces that
update and its re-evaluation before the merge. The local status model refuses
a missing context or any other integration identifier; it supplies test
evidence only and does not perform that external operation.
