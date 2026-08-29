# Runbook: bound integration revalidation separately

Study: `.hexaemeron/study.md`. Issue:
[skills#774](https://github.com/wildcat-finance/skills/issues/774).
Base: `main` at `00786ccd`, which the run branch already matches. `main` has
since advanced to `8c4073ed`, so the run owes an integration sync whose
surface is measured at integrate rather than assumed here.

Two steps. Step 1 changes the controller's behaviour and the prose that
describes it. Step 2 records the generation and propagates the version. They
are separate because the first is reviewable as a behaviour change on its own,
and because the second touches sixteen files that carry no logic and would
bury it.

## Version and decision-record identifiers

Neither is pinned here. Both are the next free value above the integration
base at the moment the run integrates.

At the time of writing, `main` holds `fiat-v5.35.1` with 40 history rows,
hexaemeron package `1.6.10`, and `ADR-048` as its highest decision record, so
the expected values are `fiat-v5.36.1`, `1.6.11` and `ADR-049`. Re-read
`plugins/hexaemeron/skills/fiat/EVOLUTION.md`, both plugin manifests and
`docs/decisions/` on the integration base before writing step 2, and take the
next free value then. If any expected value is already taken, use the next free
one and say so in the step's commit message; do not amend this runbook for a
number, and do not reuse a number that any ledger records as a former identity.

## Step 1: Scope the integration bound and pin the four that keep 500

**Goal.** Give integration revalidation its own 4,096-path ceiling at the two
sites that read integration surfaces, leaving every other user of
`GIT_PATHS_MAX` refusing at 500.

**Entry.** The run branch at `00786ccd`, matching `main`, with the baseline
recorded in the study's section 3 and no other change in the tree.

**Exit.** All of the following hold. `INTEGRATION_PATHS_MAX = 4096` exists in
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` beside `GIT_PATHS_MAX`,
which is still `500`. It is read at `git_diff_paths` and at `_manifest_paths`,
and nowhere else. `exact_commit_range`, `scribe_files` and
`_checkpoint_ref_names` still read `GIT_PATHS_MAX`. The two integration
diagnostics name 4096 and the other three name 500, so a refusal says which
limit fired. An artefact naming 4,096 integration paths is accepted and one
naming 4,097 is refused before any state or ledger byte changes. An artefact
over `SOURCE_BYTES_MAX` is still refused whatever its path count. The two
sentences in `plugins/hexaemeron/skills/fiat/SKILL.md` that describe the
version-1 route and the outside-path limit name the new ceiling. The
regenerated portable runtime matches its canonical source. Proven by:

```bash
python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_hexctl_integration_path_bounds.py' -t plugins/hexaemeron/tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

**Files.** Create `plugins/hexaemeron/tests/test_hexctl_integration_path_bounds.py`.
Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and only the two
limit-naming sentences in `plugins/hexaemeron/skills/fiat/SKILL.md`.
Regenerate, never hand-edit, `.agents/skills/promise-machine/runtime/`
including its `MANIFEST.json`, using `python3
scripts/portable_promise_machine.py sync`. Permit `.horos/boundary.json`,
`.horos/candidates.json` and `.horos/census.json` only when the deterministic
scan changes them, and regenerate them after every other file in this step is
final. Do not touch any version, ledger, manifest or marketplace file; those
belong to step 2. Do not touch
`docs/fiat-sync-run-generator-aggregates-study.md`, its runbook, its proof or
`ADR-044`: they record what was true when the aggregate transition shipped, and
repointing them would make them claim an agreement nobody measured. Any other
file requires a receipted runbook amendment first.

**Tests.** Create `plugins/hexaemeron/tests/test_hexctl_integration_path_bounds.py`,
recovering the shape merged at `cb502e55` and extending it, since that version
predates `fiat-integration-revalidation/v2` and covers only three of the seven
acceptance conditions. It must cover, one case each: the module holds
`GIT_PATHS_MAX == 500` and `INTEGRATION_PATHS_MAX == 4096`; a v1 sync artefact
of 907 individually covered paths receipts, which refused before this change; a
v2 sync artefact whose outside-path array exceeds 500 receipts, which is the
route #556 actually needs; 4,097 paths refuse at both `git_diff_paths` and
`_manifest_paths` with a diagnostic naming 4096; a commit range over 500
commits still refuses with the commit-range diagnostic; `scribe_files` still
refuses over 500 paths; `_checkpoint_ref_names` still refuses over 500 refs; an
existing valid sync fixture under 500 paths receipts byte-identically to
before; and an artefact over `SOURCE_BYTES_MAX` refuses regardless of path
count. Expect nine or more new cases, and expect the Hexaemeron total to rise
by that number against the baseline. Every one must fail with the change
reverted.

**Disciplines.** phylax: the two widened sites sit at the Git subprocess
boundary and the untrusted-artefact boundary; confirm `GIT_OUTPUT_MAX`,
`GIT_TIMEOUT`, `SOURCE_BYTES_MAX`, the path grammar and the `allowed` set are
all unchanged, so the count is the only thing that moved. ephoros: the only
signal this step owes is a diagnostic that distinguishes which of the two
ceilings refused, which the exit pins. metron: no speed claim is made and no
measurement is owed; the bounds that remain are termination guards, not budgets.
elenchus: the guard convention is a case that fails with the change reverted,
named for the property rather than the defect; the runner contract for any
repair round is test command `python3 plugins/hexaemeron/tests/run_tests.py
--elenchus-report {report}`, report format `unittest-json-v1`, expected schema
`elenchus.unittest.v1`, report file `.elenchus/fiat-774-step-1.json`, and the
path must be fresh, with a missing, stale, empty, malformed or
infrastructure-failed report classified `inconclusive` rather than guarded.
hypomnema: no standing record is created here; the decision belongs to step 2's
ADR, and this step's `SKILL.md` sentences describe behaviour rather than
justify it.

## Step 2: Record the generation and propagate the version

**Goal.** Record one Fiat generation row for the change, propagate the plugin
and skill versions everywhere they are stated, and give the decision a standing
record.

**Entry.** Step 1's signed, audited, prose-checked branch tip, with
`INTEGRATION_PATHS_MAX` in place and both suites green against the study's
baseline. Re-read the live Fiat ledger, both plugin manifests, both
marketplaces and `docs/decisions/` on the integration base before the first
edit, and resolve the three identifiers as the section above requires.

**Exit.** All of the following hold. Fiat's ledger gains exactly one history
row on the `generation` axis, retaining frontier revision
`state-shape-validation` and its digest byte for byte, citing issue #774, its
study, this runbook and the new ADR, and stating that the held issue 363 job is
untouched; the header's current version matches that row. Fiat's `SKILL.md`
frontmatter version, both hexaemeron plugin manifests, both marketplace
listings and the propagation test all name the new plugin version. The new ADR
records why the bound was split rather than raised, naming #679's prior art,
#680's unrelated revert, #710's scope refusal, the five call sites and why
three keep 500. `docs/a-child-or-a-golden-retriever-study.md` names the new
plugin version, which also clears the pre-existing failure recorded in the
study's section 3. The regenerated portable runtime matches its canonical
source and `.horos/boundary.json` describes the final tree. Proven by:

```bash
python3 -m unittest tests.test_evolution_contract tests.test_version_propagation
python3 -m unittest discover -s tests
python3 plugins/hexaemeron/tests/run_tests.py
python3 scripts/portable_promise_machine.py check
python3 scripts/promise_machine.py check
python3 scripts/promise_machine.py coverage --check
python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md plugins/hexaemeron/skills/fiat/EVOLUTION.md docs/decisions/ADR-049-bound-integration-revalidation-separately.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report docs/decisions/ADR-049-bound-integration-revalidation-separately.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/horos/skills/horos/scripts/horos.py check .
git diff --check
```

The ADR filename in those two commands follows the number resolved at entry; if
it is not 049, use the resolved name in both.

**Files.** Create the resolved `docs/decisions/ADR-0NN-bound-integration-revalidation-separately.md`.
Change `plugins/hexaemeron/skills/fiat/EVOLUTION.md`,
`plugins/hexaemeron/skills/fiat/SKILL.md` frontmatter only,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, `tests/test_evolution_contract.py`,
`tests/test_version_propagation.py`, `tests/promise_machine_coverage.json`,
`scripts/build_child_or_golden_retriever_primer.py`,
`tests/test_child_or_golden_retriever_primer.py`, and only the current-version
sentence in `docs/a-child-or-a-golden-retriever-study.md`. Regenerate, never
hand-edit, `.agents/skills/promise-machine/runtime/` including its
`MANIFEST.json`. Regenerate `.horos/boundary.json`, `.horos/candidates.json`
and `.horos/census.json` last, after every other file in this step is final.
Leave step 1's controller and test files alone. Any other file requires a
receipted runbook amendment first.

**Tests.** No new behaviour is added, so no new behavioural case is written.
Update `tests/test_evolution_contract.py` so the latest-row assertions name the
new Fiat row, its axis, its retained revision and digest, its issue and study
evidence, and so the predecessor assertions shift by one. Update
`tests/test_version_propagation.py` to the new hexaemeron package version, and
`scripts/build_child_or_golden_retriever_primer.py` with
`tests/test_child_or_golden_retriever_primer.py` to the same value. Expect no
change in the Hexaemeron total against step 1's exit, and expect the root total
to stay at its baseline with the primer error cleared.

**Disciplines.** phylax: no boundary opens; every file here is prose, a version
string or a generated copy. ephoros: no signal is added, because nothing new
runs unattended. metron: none; nothing here is done for speed. elenchus: the
same runner contract as step 1, with report file
`.elenchus/fiat-774-step-2.json`; the propagation tests are the red baseline
that must fail before the version moves and pass after. hypomnema: the ADR is
the standing record for the split, the ledger row records the change and its
frontier position, the controller holds the executable value once, and the
generated copies own no independent decision.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Tests: Create `plugins/hexaemeron/tests/test_hexctl_integration_path_bounds.py`, recovering the shape merged at `cb502e55` and extending it, since that version predates `fiat-integration-revalidation/v2` and covers only three of the seven acceptance conditions. It must cover, one case each: the module holds `GIT_PATHS_MAX == 500` and `INTEGRATION_PATHS_MAX == 4096`; `git_diff_paths` accepts 4,096 paths and refuses 4,097 with a diagnostic naming 4096; `_manifest_paths` accepts 4,096 and refuses 4,097 with that same number; a v1 sync artefact of 907 individually covered paths receipts, which refused before this change; a v2 sync artefact whose outside-path array exceeds 500 receipts, which is the route #556 actually needs; a commit range over 500 commits still refuses with the commit-range diagnostic; `scribe_files` still refuses over 500 paths; `_checkpoint_ref_names` still refuses over 500 refs; an existing valid sync surface under 500 paths receipts unchanged; and an artefact over `SOURCE_BYTES_MAX` refuses regardless of path count. Expect ten cases, and expect the Hexaemeron total to rise by ten against the baseline. Five of them are guards and must fail with the change reverted: the two ceiling cases, the module-constant case, the v1 907-path case and the v2 outside-surface case. The other five are pins and must pass both before and after, because their whole purpose is that those surfaces did not move: the three sites that keep 500, the small v1 surface and the byte ceiling. The v2 case builds its own repository rather than reusing the issue 710 fixture, whose sync commit `f0a84ca3` is unreachable in a fresh clone.

**Why.** The original clause required every new case to fail with the change reverted. Five of the cases exist to prove that a bound did not move, so they pass in both directions by construction, and the clause could only have been met by deleting the evidence that three sites still refuse at 500. Measured on this branch: five fail with the bound reverted and five pass either way.

**Steps touched.** Step 1

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Files: Create `plugins/hexaemeron/tests/test_hexctl_integration_path_bounds.py`. Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and only the two limit-naming sentences in `plugins/hexaemeron/skills/fiat/SKILL.md`. Update the runtime binding source digest in `tests/promise_machine_coverage.json` to the new controller digest, because that file records a digest over `hexctl.py` and the Promise Machine check this step's exit requires cannot pass while it names the old one. Regenerate, never hand-edit, `.agents/skills/promise-machine/runtime/` including its `MANIFEST.json`, using `python3 scripts/portable_promise_machine.py sync`. Permit `.horos/boundary.json`, `.horos/candidates.json` and `.horos/census.json` only when the deterministic scan changes them, and regenerate them after every other file in this step is final. Do not touch any version, ledger, plugin manifest or marketplace file; those belong to step 2. Do not touch `docs/fiat-sync-run-generator-aggregates-study.md`, its runbook, its proof or `ADR-044`: they record what was true when the aggregate transition shipped, and repointing them would make them claim an agreement nobody measured. Any other file requires a receipted runbook amendment first.

**Why.** The step's exit requires `python3 scripts/promise_machine.py check` and `coverage --check` to pass, and both refuse with seven PM071 drift findings once `hexctl.py` changes, because `tests/promise_machine_coverage.json` records a digest over that file. The original Files field assigned it to step 2, which makes step 1's exit unreachable. The file carries no version string, so step 2 has no other reason to touch it, and PR #679 moved the same digest in the same commit as the controller change.

**Steps touched.** Step 1

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Files: Create the resolved `docs/decisions/ADR-0NN-bound-integration-revalidation-separately.md`. Change `plugins/hexaemeron/skills/fiat/EVOLUTION.md`, `plugins/hexaemeron/skills/fiat/SKILL.md` frontmatter only, `plugins/hexaemeron/.claude-plugin/plugin.json`, `plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `tests/test_evolution_contract.py`, `tests/test_version_propagation.py`, `scripts/build_child_or_golden_retriever_primer.py`, `tests/test_child_or_golden_retriever_primer.py`, and only the current-version sentence in `docs/a-child-or-a-golden-retriever-study.md`. Leave `tests/promise_machine_coverage.json` alone: step 1 already moved its runtime binding digest, and nothing in this step changes a result surface it records. Regenerate, never hand-edit, `.agents/skills/promise-machine/runtime/` including its `MANIFEST.json`. Regenerate `.horos/boundary.json`, `.horos/candidates.json` and `.horos/census.json` last, after every other file in this step is final. Leave step 1's controller and test files alone. Any other file requires a receipted runbook amendment first.

**Why.** `tests/promise_machine_coverage.json` records a digest over `hexctl.py`, which step 1 changes and step 2 does not. The preceding amendment moved it into step 1 so that step's exit is reachable; leaving it in both lists would invite a second edit with nothing to record. The file carries no version string, so the version propagation this step performs does not reach it.

**Steps touched.** Step 2

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Files: Create `plugins/hexaemeron/tests/test_hexctl_integration_path_bounds.py`. Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and only the two limit-naming sentences in `plugins/hexaemeron/skills/fiat/SKILL.md`. Move every checked-in digest that binds the controller or a file this step edits, and no other: the runtime binding digest in `tests/promise_machine_coverage.json`, `INTEGRATED_CONTROLLER_SHA256` in `plugins/hexaemeron/tests/test_issue_429_recovery.py`, and the reviewed-divergence digest for the coverage manifest in `scripts/verify_issue_622_inoculation.py` together with the matching `current_sha256` in `tests/fixtures/issue-622-inoculation-v1.json`, which the verifier requires to agree. Re-point acceptance 1 in `plugins/hexaemeron/tests/test_hexctl_generator_aggregates.py`, which asserts that version 1 refuses the 1,095-path incident on its count: that refusal was the entry controller's and this change supersedes it, so the case now records the historical refusal, asserts the count no longer stops the artefact, and leaves the aggregate acceptances alone. Regenerate, never hand-edit, `.agents/skills/promise-machine/runtime/` including its `MANIFEST.json`, using `python3 scripts/portable_promise_machine.py sync`. Permit `.horos/boundary.json`, `.horos/candidates.json` and `.horos/census.json` only when the deterministic scan changes them, and regenerate them after every other file in this step is final. Do not touch any version, ledger, plugin manifest or marketplace file; those belong to step 2. Do not touch `docs/fiat-sync-run-generator-aggregates-study.md`, its runbook, its proof or `ADR-044`: they record what was true when the aggregate transition shipped, and repointing them would make them claim an agreement nobody measured. Any other file requires a receipted runbook amendment first.

**Why.** Running the step's own exit commands surfaced three bindings the study's five-call-site analysis did not reach. Two are digests over `hexctl.py` held outside the controller, in the issue 429 recovery pin and the issue 622 inoculation record, and the third is issue 710's acceptance 1, which asserts the exact refusal this change removes. None of the three can stay as it is once the bound moves, and none belongs to step 2, which touches no result surface any of them records. The 622 pair has to move together because the verifier refuses when its compiled expectation and the record's own `current_sha256` disagree.

**Steps touched.** Step 1

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Files: Create `plugins/hexaemeron/tests/test_hexctl_integration_path_bounds.py`. Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and only the two limit-naming sentences in `plugins/hexaemeron/skills/fiat/SKILL.md`. Move every checked-in digest that binds the controller or a file this step edits, and no other: the runtime binding digest in `tests/promise_machine_coverage.json`, `INTEGRATED_CONTROLLER_SHA256` in `plugins/hexaemeron/tests/test_issue_429_recovery.py`, and the reviewed-divergence digest for the coverage manifest in `scripts/verify_issue_622_inoculation.py` together with the matching `current_sha256` in `tests/fixtures/issue-622-inoculation-v1.json`, which the verifier requires to agree. Re-point acceptance 1 in `plugins/hexaemeron/tests/test_hexctl_generator_aggregates.py`, which asserts that version 1 refuses the 1,095-path incident on its count: that refusal was the entry controller's and this change supersedes it, so the case now records the historical refusal, asserts the count no longer stops the artefact, and leaves the aggregate acceptances alone. Add the new module to `FIXTURE_COMMIT_MATRIX` in `plugins/hexaemeron/tests/test_disposable_git_signing.py`, because it builds disposable Git history and issue 622's guard covers every module that does. Permit the configured audit record at `audit/rounds/` and its generated `.synopsis.md` companion, in Warden rounds only. Regenerate, never hand-edit, `.agents/skills/promise-machine/runtime/` including its `MANIFEST.json`, using `python3 scripts/portable_promise_machine.py sync`. Permit `.horos/boundary.json`, `.horos/candidates.json` and `.horos/census.json` only when the deterministic scan changes them, and regenerate them after every other file in this step is final. Do not touch any version, ledger, plugin manifest or marketplace file; those belong to step 2. Do not touch `docs/fiat-sync-run-generator-aggregates-study.md`, its runbook, its proof or `ADR-044`: they record what was true when the aggregate transition shipped, and repointing them would make them claim an agreement nobody measured. Any other file requires a receipted runbook amendment first.

**Why.** Audit round 1 found that the new module builds disposable Git history and is not in issue 622's inherited-signing guard, which names every other module that does. It passes that guard today, run by hand under an injected `commit.gpgsign=true` and a hostile signer that was never invoked, but nothing keeps it passing. The Files field also had no clause for the audit record and its synopsis, which every Warden round has to write.

**Steps touched.** Step 1

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Files: Create `plugins/hexaemeron/tests/test_hexctl_integration_path_bounds.py`, and, in the prose phase, the repository copies of this run's receipted artefacts at `docs/fiat-integration-path-bound-study.md` and `docs/fiat-integration-path-bound-runbook.md`, byte-identical to `.hexaemeron/study.md` and `.hexaemeron/runbook.md`, so the ledger row and the ADR can cite them by path. Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` and only the two limit-naming sentences in `plugins/hexaemeron/skills/fiat/SKILL.md`. Move every checked-in digest that binds the controller or a file this step edits, and no other: the runtime binding digest in `tests/promise_machine_coverage.json`, `INTEGRATED_CONTROLLER_SHA256` in `plugins/hexaemeron/tests/test_issue_429_recovery.py`, and the reviewed-divergence digests for the coverage manifest and the signing guard in `scripts/verify_issue_622_inoculation.py` together with the matching `current_sha256` values in `tests/fixtures/issue-622-inoculation-v1.json`, which the verifier requires to agree. Re-point acceptance 1 in `plugins/hexaemeron/tests/test_hexctl_generator_aggregates.py`, which asserts that version 1 refuses the 1,095-path incident on its count: that refusal was the entry controller's and this change supersedes it, so the case now records the historical refusal, asserts the count no longer stops the artefact, and leaves the aggregate acceptances alone. Add the new module to `FIXTURE_COMMIT_MATRIX` in `plugins/hexaemeron/tests/test_disposable_git_signing.py`, because it builds disposable Git history and issue 622's guard covers every module that does. Permit the configured audit record at `audit/rounds/` and its generated `.synopsis.md` companion, in Warden rounds only. Regenerate, never hand-edit, `.agents/skills/promise-machine/runtime/` including its `MANIFEST.json`, using `python3 scripts/portable_promise_machine.py sync`. Permit `.horos/boundary.json`, `.horos/candidates.json` and `.horos/census.json` only when the deterministic scan changes them, and regenerate them after every other file in this step is final. Do not touch any version, ledger, plugin manifest or marketplace file; those belong to step 2. Do not touch `docs/fiat-sync-run-generator-aggregates-study.md`, its runbook, its proof or `ADR-044`: they record what was true when the aggregate transition shipped, and repointing them would make them claim an agreement nobody measured. Any other file requires a receipted runbook amendment first.

**Why.** Fiat commits the repository copies of the study and runbook in step 1 after the prose pass, and the Files field never named them, so the step could not ship them without a refusal. Step 2's exit requires the ledger row to cite the study and this runbook, which needs them at a repository path. The clause also now names the signing-guard digest, which round 1's repair moved alongside the coverage manifest under the existing every-binding rule.

**Steps touched.** Step 1

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds.
