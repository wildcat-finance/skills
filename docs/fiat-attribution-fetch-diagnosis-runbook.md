# Runbook: tell an unfetched merge commit from a broken attribution at integrate

Derived from `.hexaemeron/study.md`, receipted at the start of this run. Three
steps: the spec lands, the fix lands with its guards and the digest cascade it
invalidates, and the last step records the decision, takes the ledger row and
runs the demo path.

Every step ends green. The exit commands are the whole gate.

The Elenchus runner contract is the same for all three steps, because every fix
in this run is Python under the repository's root runner:

- Test command: `python3 tests/run_tests.py --elenchus-report {report}`
- Report format: `unittest-json-v1`
- Expected report schema: `elenchus.unittest.v1`
- Report file: `.elenchus/fiat-898-step-<N>.json`, fresh per step

The report path must not already exist. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`, not evidence that a repair is
guarded.

This run takes the literal path and carries no `version-relations` block. Its
one generation row is instead re-read against live `origin/main` immediately
before the integration merge, in step 3's exit, because `main` moves several
times an hour here and another run landing a Fiat row would make a number
chosen now wrong.

## Step 1: Commit the study and the runbook

**Goal.** Put the receipted spec in the repository so the two steps that follow
can be reviewed against a document a reader can open.

**Entry.** The run branch `fiat/898-tell-an-unfetched-merge-commit-from-a-broken`
at `840d8dd3`, the tip of `origin/main` when the run was cut.

**Exit.** `docs/fiat-attribution-fetch-diagnosis-study.md` and
`docs/fiat-attribution-fetch-diagnosis-runbook.md` exist and are byte-identical
to the receipted artefacts in `.hexaemeron/`, and the committed boundary
describes the tree that now holds them. Proved by
`cmp -s .hexaemeron/study.md docs/fiat-attribution-fetch-diagnosis-study.md`,
`cmp -s .hexaemeron/runbook.md docs/fiat-attribution-fetch-diagnosis-runbook.md`,
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-attribution-fetch-diagnosis-study.md docs/fiat-attribution-fetch-diagnosis-runbook.md`,
`python3 scripts/run_checks.py --base fiat/898-tell-an-unfetched-merge-commit-from-a-broken`,
`python3 scripts/portable_promise_machine.py check`,
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
and `git diff --check`, each exiting 0.

**Files.** `docs/fiat-attribution-fetch-diagnosis-study.md`,
`docs/fiat-attribution-fetch-diagnosis-runbook.md`, `.horos/boundary.json`.

**Tests.** No new test. The existing suites must stay green, and
`tests/test_boundary_currency.py::test_the_committed_boundary_matches_a_fresh_scan`
is the one that notices an unrefreshed boundary. Runner contract as declared
above, report file `.elenchus/fiat-898-step-1.json`.

**Disciplines.** phylax: none, the step adds two documents and opens no
boundary. ephoros: none, nothing here runs unattended. metron: none, no
performance claim. elenchus: none, no failure in hand at entry. hypomnema: this
step is Hypomnema's own output, the spec landing where a reader finds it.

## Step 2: Separate an absent merge object from a broken attribution

**Goal.** Make `done integrate` say which of the two conditions it hit, and name
the fetch when the merge object is simply not local.

**Entry.** The step 1 branch at its exit state, with the spec committed and all
suites green.

**Exit.** `merged_attribution` resolves the merge commit as a commit object
before walking any identity, and refuses with a message that names the absent
object and the `git fetch` that resolves it, without naming any recorded
identity. `commit_is_ancestor`'s unexpected-status refusal names both the
candidate and the descendant. A genuine attribution break still refuses, with
wording distinguishable from the absent-object case. Every repository digest
binding the edit invalidates is refreshed in this same change. Proved by
`python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_hexctl_attribution_fetch.py'`,
`python3 scripts/run_checks.py --base fiat/898-tell-an-unfetched-merge-commit-from-a-broken`,
`python3 scripts/portable_promise_machine.py sync`,
`python3 scripts/portable_promise_machine.py check`,
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
and `git diff --check`, each exiting 0.

**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_hexctl_attribution_fetch.py`,
`.agents/skills/promise-machine/runtime/` regenerated and never hand-edited,
`.horos/boundary.json`, and only those repository digest bindings the edit
actually invalidates.

**Tests.** Four new cases over a temporary repository so no outer index is
touched: a merge object absent from the clone produces a refusal naming the
object and the fetch; that refusal names no recorded identity; a healthy run
whose identities are all real ancestors resolves and proceeds; and a genuine
attribution break still refuses with different wording. Preserve a red result
against the entry controller for the first two before the fix lands. Expected
count: four added. Runner contract as declared above, report file
`.elenchus/fiat-898-step-2.json`.

**Disciplines.** phylax: this step adds one git read of an operator-supplied
SHA and carries the existing bounded wrapper, fixed argv and no shell. ephoros:
the refusal is the signal, and naming the object and the remedy is the whole
point of the step. metron: none, no performance claim. elenchus: the defect is a
failure in hand, reproduced twice, so the fix arrives with cases that fail
without it. hypomnema: that a diagnostic may name a remedy, and that the
controller refuses rather than fetches, are both expensive to reverse and are
recorded in step 3.

## Step 3: Record the decision, take the ledger row and run the demo path

**Goal.** Write down the two decisions, record the generation row this run owes,
and show the problem statement answered end to end.

**Entry.** The step 2 branch at its exit state, with the fix landed and all
suites green.

**Exit.** One decision record under `docs/decisions/` carries both decisions:
that a controller diagnostic may name a remedy, and that the controller refuses
rather than fetching. `plugins/hexaemeron/skills/fiat/EVOLUTION.md` carries
exactly one new row on the generation axis, retaining frontier revision
`state-shape-validation` and its digest
`e413d6041edb34b3807a54019489605814a591f60547755f8f66f01830f643aa` and leaving
the held Next Fiat job byte-identical, with the header and the row naming the
same version. The demo path runs and the two refusals are shown to differ.
Proved by
`python3 -m unittest plugins.hexaemeron.tests.test_hexctl_attribution_fetch`,
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <record> plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report <record>`,
`python3 -m unittest tests.test_decision_records`,
`python3 -m unittest tests.test_evolution_contract`,
`python3 scripts/run_checks.py --base fiat/898-tell-an-unfetched-merge-commit-from-a-broken`,
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
and `git diff --check`, each exiting 0. Immediately before the integration
merge, re-read `docs/decisions/` and
`plugins/hexaemeron/skills/fiat/EVOLUTION.md` on live `origin/main`; if another
run has taken the record number or landed a Fiat row, move both to the smallest
free slot, amending filename, heading and version together.

**Files.** `docs/decisions/ADR-NNN-name-a-remedy-in-a-controller-diagnostic.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md` only if its frontmatter version is
bound to the ledger, the regenerated portable runtime, `.horos/boundary.json`.

**Tests.** No new product test. `tests/test_decision_records.py` gates the
record's number and heading against live `origin/main`, and
`tests/test_evolution_contract.py` gates the ledger row's axis arithmetic,
digest and header agreement. Runner contract as declared above, report file
`.elenchus/fiat-898-step-3.json`.

**Disciplines.** phylax: none, the step adds documents and a ledger row and
opens no boundary. ephoros: none, nothing here runs unattended. metron: none,
the demo is a correctness demonstration and claims no timing. elenchus: none
expected, and any failure the demo surfaces is worked to its cause before the
step closes. hypomnema: this step is Hypomnema's output, the decision record and
the ledger row.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Exit: `docs/fiat-attribution-fetch-diagnosis-study.md` and `docs/fiat-attribution-fetch-diagnosis-runbook.md` exist and are byte-identical to the receipted artefacts in `.hexaemeron/`, and the committed boundary describes the tree that now holds them. Proved by `cmp -s .hexaemeron/study.md docs/fiat-attribution-fetch-diagnosis-study.md`, `cmp -s .hexaemeron/runbook.md docs/fiat-attribution-fetch-diagnosis-runbook.md`, `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/fiat-attribution-fetch-diagnosis-study.md docs/fiat-attribution-fetch-diagnosis-runbook.md`, `python3 scripts/portable_promise_machine.py check`, `python3 plugins/horos/skills/horos/scripts/horos.py check .`, and `git diff --check`, each exiting 0, and by `python3 scripts/run_checks.py --base fiat/898-tell-an-unfetched-merge-commit-from-a-broken` reporting no failure beyond the one recorded in the `local_suite_baseline` receipt. That baseline is the `deterministic-rebuild` failure in `tests/test_child_or_golden_retriever_primer.py`, reproduced on a pristine `origin/main` worktree at `840d8dd3` carrying no run changes, and filed as wildcat-finance/skills#973. Any second failure, or that failure naming a different artefact, fails the step.
**Why.** The baseline exit required `scripts/run_checks.py` to exit 0. It cannot on this host, and for a reason no step of this run causes: the primer's deterministic rebuild does not reproduce the committed PNG and PDF bytes on macOS, while CI reports `invariants=success` for the same commit. The builder interpreter is found, and its Python, Pillow and ReportLab versions are byte-identical to the ones the primer study records, so neither a missing toolchain nor version skew explains it. Requiring a clean exit would make every step of this run unfinishable for a defect it did not introduce, and waiving the check entirely would give up the only local signal there is. Comparing against a recorded, reproduced baseline keeps the gate real while naming exactly what it does not cover.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
