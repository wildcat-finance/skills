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
The study records why: the base advanced 106 commits across this run's two preflights and took the
generation this run first planned to write, and the 972
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

### Amendment -- 2026-09-01

**What changed.** Complete replacement Exit: `docs/fiat-early-step-merge-study.md`, `docs/fiat-early-step-merge-runbook.md` and `docs/decisions/ADR-068-adopt-an-early-step-merge.md` exist and are committed; `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/fiat-early-step-merge-study.md` exits 0; `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/fiat-early-step-merge-runbook.md` exits 0; `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py` reports clean on all three; the repository-wide suite `python3 -m unittest discover -t . -s tests` exits 0; and `python3 plugins/hexaemeron/tests/run_tests.py <fresh-report-path>` reports zero errors and no failure other than the one this base already carries, `test_check_runner.CheckMapContractTests.test_every_tracked_path_has_exactly_one_owner`, whose count must not rise.
Complete replacement Tests: No new tests. Both suites must stay as green as the base leaves them, so the runner contract still applies. The repository-wide suite is `python3 -m unittest discover -t . -s tests`, which must exit 0. The plugin command is `python3 plugins/hexaemeron/tests/run_tests.py {report}`, whose report path must not already exist because the reporter refuses to overwrite one. Report format `elenchus.unittest.v1`. Report file `.hexaemeron/test-reports/step-1.json`.
**Why.** Two corrections. The Exit said "the suite is green" without naming which suite, and the repository-wide suite is the one hosted CI gates on, so a step could earn a green receipt from the plugin suite and three lints while the branch was red; issue 1067 records that happening. And the plugin suite is not green at this run's base: `test_every_tracked_path_has_exactly_one_owner` fails because commit `6b91ad96` added a tracked `VENUES.json` without registering it in `tests/check-map-v1.json`. It reproduces at an unmodified base with no commits of this run applied, so an Exit demanding a wholly green plugin suite could never be met by any step here and would have to be either falsely receipted or repaired outside this run's scope.
**Steps touched.** Step 1's Exit and Tests fields only.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-01

**What changed.** Complete replacement Exit: A push receipt for an early-merged step carries an explicit `early_merge` block naming the merge commit and the ref it was reachable from; a pull request head unequal to the receipted head still refuses; a merge commit not reachable from the recorded base refuses; an unanswered graph query refuses as unknown; every refusal leaves state and ledger bytes unchanged. Proven by `python3 plugins/hexaemeron/tests/test_early_step_merge.py --elenchus-report .hexaemeron/test-reports/step-2.json` exiting 0 with zero failures and zero errors; by the repository-wide suite `python3 -m unittest discover -t . -s tests` exiting 0; and by `python3 plugins/hexaemeron/tests/run_tests.py <fresh-report-path>` reporting zero errors and no failure other than the one this base already carries, `test_check_runner.CheckMapContractTests.test_every_tracked_path_has_exactly_one_owner`, whose count must not rise.
Complete replacement Tests: A new focused module, `test_early_step_merge.py`, following issue 923's module: real Git objects for the reachability cases and the delivery harness for the receipt cases. Expected count 10 to 14 tests. It implements `run_elenchus_report` so the focused command below works. The focused command is `python3 plugins/hexaemeron/tests/test_early_step_merge.py --elenchus-report {report}`, and its report path must stay inside the worktree and must not already exist, because the suite's reporter refuses a target it would overwrite. The repository-wide suite is `python3 -m unittest discover -t . -s tests`, which must exit 0. The plugin suite is `python3 plugins/hexaemeron/tests/run_tests.py <fresh-report-path>`. Report format `elenchus.unittest.v1`. Report file `.hexaemeron/test-reports/step-2.json`.
**Why.** The same two corrections step 1 took. The Exit said "the full suite staying green" without naming which suite, and the repository-wide suite is the one hosted CI gates on, so a step could earn a green receipt from the plugin suite and three lints while the branch was red; issue 1067 records that happening. And the plugin suite is not green at this base: `test_every_tracked_path_has_exactly_one_owner` fails because commit `6b91ad96` added a tracked `VENUES.json` without registering it in `tests/check-map-v1.json`, which reproduces with none of this run's commits applied, so an Exit demanding a wholly green plugin suite could not be met honestly here.
**Steps touched.** Step 2's Exit and Tests fields only.
**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-01

**What changed.** Complete replacement Files: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_early_step_merge.py`, and the artefacts whose digests are bound to the controller and must be re-pinned with it: `tests/promise_machine_coverage.json`, holding nine fiat runtime bindings plus the run-observation controller pin and the reviewed field map for `fiat-receipted-delivery`, `plugins/hexaemeron/tests/test_issue_429_recovery.py`, holding `INTEGRATED_CONTROLLER_SHA256`, and the generated reading boundary `.horos/boundary.json`. The step also carries corrections to `docs/decisions/ADR-068-adopt-an-early-step-merge.md` and `docs/fiat-early-step-merge-study.md`, which restate the mechanism the withdrawn claim described wrongly.
**Why.** Editing the controller invalidates digest-bound artefacts far from the edit, and the repository-wide suite fails on them in places that look unrelated: five root tests went red on a stale `hexctl.py` digest recorded in the coverage inventory. Re-pinning them is not a separate deliverable but the same change, and the coverage command refuses a bare re-pin, requiring the field map to be reviewed with the digest. The two document corrections travel here because their subject is the claim step two disproved and because step one's branch is already pushed with an open pull request, so an additive correction on this branch keeps every receipted head an ancestor.
**Steps touched.** Step 2's Files field only.
**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-01

**What changed.** Complete replacement Exit: `done merge-step` for an adopted step succeeds without a second merge and records which mechanism satisfied it; it still refuses when the recorded adoption is incomplete or unverified; it still refuses out of step order; `hexctl verify` replays a run carrying an adopted merge and still refuses a malformed one; a run initialised before this change keeps its old receipt shape and has no early-merge evidence inferred. Proven by `python3 plugins/hexaemeron/tests/test_early_step_merge.py --elenchus-report .hexaemeron/test-reports/step-3.json` exiting 0 with zero failures and zero errors; by the repository-wide suite `python3 -m unittest discover -t . -s tests` exiting 0; and by `python3 plugins/hexaemeron/tests/run_tests.py <fresh-report-path>` reporting zero errors and no failure other than the one this base already carries, `test_check_runner.CheckMapContractTests.test_every_tracked_path_has_exactly_one_owner`, whose count must not rise.
Complete replacement Files: `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_early_step_merge.py`, and the artefacts whose digests are bound to the controller and must be re-pinned with it: `tests/promise_machine_coverage.json`, `plugins/hexaemeron/tests/test_issue_429_recovery.py` and the generated reading boundary `.horos/boundary.json`.
Complete replacement Tests: The step 2 module is extended with the merge-step, verify-replay and legacy-run cases. Expected count 16 to 22 tests in the module after this step. The focused command is `python3 plugins/hexaemeron/tests/test_early_step_merge.py --elenchus-report {report}`, and its report path must stay inside the worktree and must not already exist, because the suite's reporter refuses a target it would overwrite. The repository-wide suite is `python3 -m unittest discover -t . -s tests`, which must exit 0. The plugin suite is `python3 plugins/hexaemeron/tests/run_tests.py <fresh-report-path>`. Report format `elenchus.unittest.v1`. Report file `.hexaemeron/test-reports/step-3.json`.
**Why.** The same three corrections the earlier steps took, for the same reasons. The Exit named no suite, and the repository-wide one is what hosted CI gates on, which issue 1067 records as the gap behind a green receipt on a red branch. The plugin suite is not green at this base on an unowned tracked `VENUES.json`, so an Exit demanding a wholly green one could not be met honestly. And editing the controller invalidates digest-bound artefacts far from the edit, which the previous step proved by turning five root tests red on a stale digest; re-pinning them is the same change rather than a separate deliverable.
**Steps touched.** Step 3's Exit, Files and Tests fields only.
**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-01

**What changed.** Complete replacement Tests: The step 2 module is extended with the merge-step, verify-replay and legacy-run cases, and with a guard for an adoption the run branch does not carry. Expected count 16 to 24 tests in the module after this step. The focused command is `python3 plugins/hexaemeron/tests/test_early_step_merge.py --elenchus-report {report}`, and its report path must stay inside the worktree and must not already exist, because the suite's reporter refuses a target it would overwrite. The repository-wide suite is `python3 -m unittest discover -t . -s tests`, which must exit 0. The plugin suite is `python3 plugins/hexaemeron/tests/run_tests.py <fresh-report-path>`. Report format `elenchus.unittest.v1`. Report file `.hexaemeron/test-reports/step-3.json`.
**Why.** Round 1 of this step's audit found that satisfying a step from its adoption record is only sound when the run branch actually carries that step's work. An early merge lands in the base the pull request targeted, which above the bottom of the stack is the step below rather than the run branch, so whether the run branch carries the work depends on which of the two merges happened first. The fix adds a reachability gate and the guard test that fails without it, which takes the module one test past the range this field first stated.
**Steps touched.** Step 3's Tests field only.
**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-01

**What changed.** Complete replacement Exit: `SKILL.md`'s push and integrate phase notes and its receipt table name the adopted-merge transition; `references/push-discipline.md` carries the procedure and the case the refusal names; `plugins/hexaemeron/skills/fiat/EVOLUTION.md` carries exactly one new generation row whose axis arithmetic, recomputed frontier digest and header agree, retaining the prior frontier revision and digest byte for byte and leaving the held next job unchanged; the skill's frontmatter version matches that ledger; `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` admits the new version; the evolution-contract test's pinned ledger head matches; the cold read of mutable first-party marketplace prose is reconciled or its absence of changes stated; every changed document is clean under the imprimatur lint; the repository-wide suite `python3 -m unittest discover -t . -s tests` exits 0; and `python3 plugins/hexaemeron/tests/run_tests.py <fresh-report-path>` reports zero errors and no failure other than the one this base already carries, `test_check_runner.CheckMapContractTests.test_every_tracked_path_has_exactly_one_owner`, whose count must not rise.
Complete replacement Files: `plugins/hexaemeron/skills/fiat/SKILL.md`, `plugins/hexaemeron/skills/fiat/references/push-discipline.md`, `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` for the compatible-version set, `tests/test_evolution_contract.py` for the pinned ledger head, the artefacts whose digests are bound to the controller, `tests/promise_machine_coverage.json` and `plugins/hexaemeron/tests/test_issue_429_recovery.py`, the generated reading boundary `.horos/boundary.json`, and whatever the cold read of mutable marketplace prose names.
Complete replacement Tests: No new behaviour, so no new module. The evolution-contract test must pass over the new row, and the checkpoint restore tests over the new compatible version, so both suites are the check. The repository-wide suite is `python3 -m unittest discover -t . -s tests`, which must exit 0. The plugin suite is `python3 plugins/hexaemeron/tests/run_tests.py {report}`, whose report path must not already exist. Report format `elenchus.unittest.v1`. Report file `.hexaemeron/test-reports/step-4.json`.
**Why.** The Exit and Files fields named neither the skill frontmatter version, the checkpoint compatible-version set nor the evolution-contract pin, and all three move with a ledger row: the frontmatter must match the ledger by contract, the restore tests refuse a version the set does not admit, and the contract test pins the head by value. The Exit also named no suite and did not account for the failure this base already carries, the same two corrections the earlier steps took.
**Steps touched.** Step 4's Exit, Files and Tests fields only.
**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-01

**What changed.** Complete replacement Exit: `SKILL.md`'s push and integrate phase notes name the adopted-merge transition, and its receipt table is deliberately left unchanged; `references/push-discipline.md` carries the procedure and the case the refusal names; `plugins/hexaemeron/skills/fiat/EVOLUTION.md` carries exactly one new generation row whose axis arithmetic, recomputed frontier digest and header agree, retaining the prior frontier revision and digest byte for byte and leaving the held next job unchanged; the skill's frontmatter version matches that ledger; `CHECKPOINT_COMPATIBLE_CONTROLLER_VERSIONS` admits the new version; the evolution-contract test's pinned ledger head and newest-row assertions match; every digest-bound derivative of the controller and of `SKILL.md` is re-pinned, so `python3 scripts/agent_instruction.py check --manifest tests/fixtures/agent-instruction-v1/manifest.json`, `python3 scripts/promise_machine.py coverage --check`, `python3 scripts/portable_promise_machine.py check` and `python3 plugins/horos/skills/horos/scripts/horos.py check .` all exit 0; the cold read of mutable first-party marketplace prose is reconciled or its absence of changes stated; every changed document is clean under the imprimatur lint; the repository-wide suite `python3 -m unittest discover -t . -s tests` exits 0; and `python3 plugins/hexaemeron/tests/run_tests.py <fresh-report-path>` reports zero errors and no failure other than the one this base already carries, `test_check_runner.CheckMapContractTests.test_every_tracked_path_has_exactly_one_owner`, whose count must not rise.
Complete replacement Files: `plugins/hexaemeron/skills/fiat/SKILL.md`, `plugins/hexaemeron/skills/fiat/references/push-discipline.md`, `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `tests/test_evolution_contract.py`, `plugins/hexaemeron/README.md` as the one document the cold read found stale, and the digest-bound derivatives: `tests/promise_machine_coverage.json`, `plugins/hexaemeron/tests/test_issue_429_recovery.py`, the `tests/fixtures/agent-instruction-v1/` corpus, meaning its manifest and the `fiat-study-runbook-phase` model, compact encoding and source spans together with the shared measurement and parity evidence records, and the generated reading boundary `.horos/boundary.json`.
**Why.** Two corrections, both forced by evidence rather than chosen. The receipt table sits inside the byte range the agent-instruction corpus measures, and editing it grew that range from 4,328 to 4,493 bytes, which changes a recorded token count. Token counts can only be re-measured through a tokenizer adapter, and this environment has none: `measure` refuses with `WAI-E-ADAPTER.UNAVAILABLE`. Reverting those two rows to their original bytes keeps the measured region byte-identical, so every span digest, offset and token count stays true, and the phase notes plus `push-discipline.md`, which sit outside the measured range, carry the whole transition instead. The Files field also did not name the corpus, and editing `SKILL.md` at all invalidates it: the corpus digest covers the manifest's fixture block, which holds the source digest, so eight root tests failed on it until every derived binding was re-pinned.
**Steps touched.** Step 4's Exit and Files fields only.
**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.
