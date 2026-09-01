# Runbook: let a step survive a pull request merged before integrate

Derived from `.hexaemeron/study.md`. The selected design is the one the record
below locks; no step reopens that choice.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 98626b1ca0eef51bf90b4b1c23e81244e4c62a694ae589b94b338661451475df
candidate | push-adopts-merge
```

```version-relations
fiat | plugins/hexaemeron/skills/fiat/EVOLUTION.md | next-generation-after-integration-base
```

The declared relation keeps Fiat's ledger row one generation after whatever the
integration base turns out to be, rather than after the ledger in this tree.
The study records why: the base advanced 62 commits during this run's own
preflight and took the generation this run first planned to write, and the 972
record names the same drift biting a row it had already composed.

## Step 1: Land the specification and the decision record

**Goal.** Commit the study, the runbook and the decision record so the run's
specification and its one expensive decision are in the repository before any
controller code changes.
**Entry.** The run branch at the commit it was cut from, with the working tree
clean.
**Exit.** `docs/fiat-early-step-merge-study.md`,
`docs/fiat-early-step-merge-runbook.md` and
`docs/decisions/ADR-068-adopt-an-early-step-merge.md` exist and are committed;
`python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study
docs/fiat-early-step-merge-study.md` exits 0;
`python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py
docs/fiat-early-step-merge-runbook.md` exits 0;
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` reports
clean on all three; and the suite is green.
**Files.** `docs/fiat-early-step-merge-study.md`,
`docs/fiat-early-step-merge-runbook.md`,
`docs/decisions/ADR-068-adopt-an-early-step-merge.md`.
**Tests.** No new tests. The existing suite must stay green, so the runner
contract still applies. Command:
`python3 plugins/hexaemeron/tests/run_tests.py {report}`. Report format
`elenchus.unittest.v1`. Report file
`.hexaemeron/test-reports/step-1.json`.
**Disciplines.** phylax: none, the step adds only documents and opens no
boundary. ephoros: none, nothing here runs unattended. metron: none, no
performance claim. elenchus: none, no failure in hand. hypomnema: the decision
record is this step's whole point, because which transition owns the adopted
merge fixes a receipt shape that is append-only once a run has written it.

## Step 2: Adopt an early merge at push

**Goal.** Let `done push` accept a step pull request already merged into its
recorded base, when the recorded head still equals the pull request head and the
merge commit is reachable from that base, and record the adoption explicitly.
**Entry.** Step 1's exit state.
**Exit.** A push receipt for an early-merged step carries an explicit
`early_merge` block naming the merge commit and the ref it was reachable from;
a pull request head unequal to the receipted head still refuses; a merge commit
not reachable from the recorded base refuses; an unanswered graph query refuses
as unknown; every refusal leaves state and ledger bytes unchanged. Proven by
`python3 plugins/hexaemeron/tests/test_early_step_merge.py --elenchus-report
.hexaemeron/test-reports/step-2.json` exiting 0 with zero failures and zero
errors, and by the full suite staying green.
**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_early_step_merge.py`.
**Tests.** A new focused module, `test_early_step_merge.py`, following issue
923's module: real Git objects for the reachability cases and the delivery
harness for the receipt cases. Expected count 10 to 14 tests. It implements
`run_elenchus_report` so the focused command below works. Command:
`python3 plugins/hexaemeron/tests/test_early_step_merge.py --elenchus-report
{report}`. Report format `elenchus.unittest.v1`. Report file
`.hexaemeron/test-reports/step-2.json`.
**Disciplines.** phylax: this step widens the class of GitHub-reported state a
gate admits, so the two hard gates are its controls, and it adds one bounded
subprocess boundary for the native graph query. ephoros: the refusal must say
which of the two checks failed, because that is how an early merge is told from
a rewritten branch afterwards. metron: none, the step adds at most one bounded
graph query and no network read. elenchus: the new refusals are the fail-closed
posture, and every fix in a round owes a guard test. hypomnema: the
`early_merge` receipt shape is append-only once written, and ADR-068 from step
1 is where it is recorded.

## Step 3: Satisfy merge-step from the recorded adoption

**Goal.** Let `done merge-step` for a step with a recorded adopted merge be
satisfied from that record instead of asking GitHub to merge again, while every
other gate it applies today still applies.
**Entry.** Step 2's exit state.
**Exit.** `done merge-step` for an adopted step succeeds without a second
merge and records which mechanism satisfied it; it still refuses when the
recorded adoption is incomplete or unverified; it still refuses out of step
order; `hexctl verify` replays a run carrying an adopted merge and still
refuses a malformed one; a run initialised before this change keeps its old
receipt shape and has no early-merge evidence inferred. Proven by
`python3 plugins/hexaemeron/tests/test_early_step_merge.py --elenchus-report
.hexaemeron/test-reports/step-3.json` exiting 0 with zero failures and zero
errors, and by the full suite staying green.
**Files.** `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_early_step_merge.py`.
**Tests.** The step 2 module is extended with the merge-step, verify-replay and
legacy-run cases. Expected count 16 to 22 tests in the module after this step.
Command: `python3 plugins/hexaemeron/tests/test_early_step_merge.py
--elenchus-report {report}`. Report format `elenchus.unittest.v1`. Report
file `.hexaemeron/test-reports/step-3.json`.
**Disciplines.** phylax: one recorded fact now stands in for an action, so the
control is that the record must be complete and GitHub-verified before it is
accepted. ephoros: the step emits why a merge did not happen, so the integrate
phase's silence about that step is explained rather than merely absent. metron:
none, no performance claim. elenchus: verify replay is the fail-closed check
that a malformed receipt cannot pass. hypomnema: recorded in the same ADR-068,
because separating the two halves would leave each readable without its reason.

## Step 4: Authorise the transition and record the generation

**Goal.** State the adopted-merge transition in the documents that describe Fiat
to somebody else, reconcile the mutable marketplace prose the versioning
contract requires a frontier run to cold-read, and add the one ledger row this
run owes.
**Entry.** Step 3's exit state.
**Exit.** `SKILL.md`'s push and integrate phase notes and its receipt table
name the adopted-merge transition and its flag; `references/push-discipline.md`
carries the procedure; `plugins/hexaemeron/skills/fiat/EVOLUTION.md` carries
exactly one new generation row whose axis arithmetic, recomputed frontier digest
and header agree, retaining the prior frontier revision and digest byte for byte
and leaving the held next job unchanged; the cold read of mutable first-party
marketplace prose is reconciled or its absence of changes stated; every changed
document is clean under the imprimatur lint; and the suite is green. Proven by
`python3 plugins/hexaemeron/tests/run_tests.py {report}` exiting 0 and by
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` reporting
clean on each changed document.
**Files.** `plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/skills/fiat/references/push-discipline.md`,
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`, and whatever the cold read of
mutable marketplace prose names.
**Tests.** No new behaviour, so no new module. The evolution-contract test must
still pass over the new row, so the suite is the check. Command:
`python3 plugins/hexaemeron/tests/run_tests.py {report}`. Report format
`elenchus.unittest.v1`. Report file
`.hexaemeron/test-reports/step-4.json`.
**Disciplines.** phylax: none, the step changes documents and a ledger, opening
no boundary. ephoros: none, nothing here runs unattended. metron: none, no
performance claim. elenchus: none, no failure in hand. hypomnema: this step is
where the transition stops being undocumented, which is the whole complaint
issue 1021 makes about the mechanism that already half existed.

## Step 5: Demonstrate against a disposable repository

**Goal.** Drive the whole sequence issue 1021 asks for against a disposable
repository: open a step pull request, merge it, then receipt the push and reach
integrate, with no ref rewritten.
**Entry.** Step 4's exit state.
**Exit.** An end-to-end case drives open, merge, push receipt and integrate
against a disposable repository through the delivery harness, asserts that no
ref was rewritten, and asserts that the adopted merge satisfied merge-step;
`.hexaemeron/reports/push-adopts-merge-disposable-repo-regression.json` exists
as one closed `protasis-design-report/v1` object recording exit 0, which
resolves the record's pending conformance cell; and
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py
.hexaemeron/design-evidence.json --transition integration` exits 0. Proven by
`python3 plugins/hexaemeron/tests/test_early_step_merge.py --elenchus-report
.hexaemeron/test-reports/step-5.json` exiting 0 with zero failures and zero
errors, and by the full suite staying green.
**Files.** `plugins/hexaemeron/tests/test_early_step_merge.py`,
`.hexaemeron/reports/push-adopts-merge-disposable-repo-regression.json`.
**Tests.** The module gains the end-to-end disposable-repository case. Expected
count 18 to 25 tests in the module after this step. Command:
`python3 plugins/hexaemeron/tests/test_early_step_merge.py --elenchus-report
{report}`. Report format `elenchus.unittest.v1`. Report file
`.hexaemeron/test-reports/step-5.json`.
**Disciplines.** phylax: the harness writes into a disposable repository only,
and the report path stays inside the worktree because the suite's reporter
refuses anything else. ephoros: none, the regression runs in CI and a failure is
its own signal. metron: none, no performance claim. elenchus: this step is the
guard test for the whole delivery, so it must fail without steps 2 and 3.
hypomnema: none, the decision is already recorded in ADR-068.
