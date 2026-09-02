# Local proof: stale-base exclusion

Status: repository bootstrap, 2 September 2026.

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
remote. A candidate executable, tracked attributes, repository filter, and
hook remain inert while the base-owned policy accepts the exact assignment
tree. Separate cases refuse a moved head and malformed assignment trailers.

## Enforcement qualification

The study's 30 August 2026 readback recorded ruleset `21830871` with
enforcement `evaluate`. This step does not change that ruleset. The
`adr-assignments` context is not required, and Actions integration `15368` has
not been verified for this context by a live canary. Production race freedom
is not claimed.

A later separately authorised operation must observe the status on its exact
head, require integration `15368`, retain strict up-to-date checks, keep the
bypass set empty, and activate the ruleset. The local status model refuses a
missing context or any other integration identifier; it supplies test evidence
only and does not perform that external operation.
