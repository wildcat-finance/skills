# Runbook: a commit gate that survives a fresh clone

Derived from `.hexaemeron/study.md` for issue
[#857](https://github.com/wildcat-finance/skills/issues/857). Base ref
`8dc3aca54adeca49387a2bdfc174cf6e72d02a11` on `main`, run branch
`fiat/857-framework-16-the-commit-gate-lives-in-one-cl`.

## Two readings recorded rather than resolved silently

**The decision record ships unnumbered.** The study's section 12 and its
acceptance table both name `docs/decisions/ADR-074-*.md`, which is the correct
arithmetic against a base whose highest record is `ADR-073`. Run #856 is open
on the same base and its runbook claims the same number, and
`tests/test_decision_records.py:108` only sees a collision once the other
number reaches `origin/main`, so the second run to merge would renumber its
record and every reference to it. `docs/decisions/` already carries
`draft-fix-the-issue-status-block-markers.md`, an unnumbered record that drops
the `ADR-` prefix so the filename check skips it, pending issue #888. The user
chose that form for this run. The record therefore ships as
`docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md`
and whoever merges it assigns a number by hand.

That moves the command proving acceptance condition 1.
`tests/test_decision_records.py` globs `ADR-*.md` and never sees a draft, so
Step 1 adds `DecisionRecordTests` to `tests/test_commit_gate.py` to hold the
draft's required sections instead. No existing test's assertions change.

**Steps 3 and 4 swap the study's order.** The study's section 3 build order
puts the visibility assertion in step 3 and the index-mutation regression in
step 4. The design record's one pending criterion,
`index-mutation-regression`, blocks `step:4`, and Fiat runs the design checker
at that transition immediately before opening step 4, so the report proving it
has to exist before step 4 starts. The work that produces a report sits in the
step before its stop point. Step 3 therefore writes the regression, the guard
it needs and its report; step 4 is where the gate becomes the shipped,
documented, suite-bound state. Nothing else about the order changes, and every
step still assumes only the earlier steps' exit states.

## Where the pending gate lands

One conformance gate is pending in the design record.
`index-mutation-regression` blocks `step:4`. Step 3 produces
`.hexaemeron/reports/hooks-path-plus-visibility-index-mutation-regression.json`
as one closed `protasis-design-report/v1` object, whose `command` is the
resolver the record names, `python3 -m unittest
tests.test_commit_gate.HookIndexMutationTests -v`, and whose `exit` is zero.

## The runner contract every step shares

Test command `python3 tests/run_tests.py --elenchus-report {report}`, report
format `elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-<N>.json`.
Warden receives those three inputs and may not substitute a nearby suite.

Every step's exit runs the root suite, `python3 scripts/run_checks.py --full`,
at exit zero, against a committed tree. Three lints passing is not the suite.

Three known false reds, carried from the study's constraints. A `run_checks.py`
failure reported as `WAI-E-ADAPTER.TIMEOUT` is parallel load rather than a
defect; rerun with `--jobs 1`. A Python pin check that comes back one short is
usually a stale sibling under `.claude/worktrees/`. The dead-code check needs a
clean tree, so each step commits before running the suite.

No step edits any file under `audit/`. Those bytes are pinned. No step changes
ruleset `21830871`, changes what an existing test asserts, or gates a push or a
merge.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 6e7a5ca5397d6b84951d79d6f5b1ea3a6cedd724824ba0f28434f82a72b36a44
candidate | hooks-path-plus-visibility
```

## Step 1: Commit the run documents and give the gate an owned home

**Goal.** Put the study, this runbook, the design record and the decision
record in the repository, and declare the paths the gate will occupy, so every
later step writes into a home the check runner already owns.

**Entry.** `fiat/857-framework-16-the-commit-gate-lives-in-one-cl` at
`8dc3aca54adeca49387a2bdfc174cf6e72d02a11`, clean tree.

**Exit.** `docs/commit-gate/study.md` and `docs/commit-gate/runbook.md` are
byte-identical copies of the two `.hexaemeron/` artefacts.
`docs/commit-gate/design-evidence.json` and `docs/commit-gate/reports/` carry
the design record and the reports it cites, with the record-relative `reports/`
layout preserved.
`docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md`
records the chosen home, the trade each rejected option loses, and the
consequence that the green record is a convenience rather than proof.
`.githooks/README.md` names the activation command and the bypass token.
`tests/check-map-v1.json` gains one owner entry binding `.githooks` to the
`root` scope. `.horos/boundary.json` is regenerated. Proved by `python3
scripts/run_checks.py --full` at exit zero on the committed tree.

**Files.** `docs/commit-gate/study.md`, `docs/commit-gate/runbook.md`,
`docs/commit-gate/design-evidence.json`, `docs/commit-gate/reports/*.json`,
`docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md`,
`.githooks/README.md`, `tests/test_commit_gate.py`, `tests/check-map-v1.json`,
`.horos/boundary.json`.

**Tests.** `tests/test_commit_gate.py` is created with `DecisionRecordTests`:
the draft record exists at the exact path; its first heading is a title rather
than an `ADR-NNN` heading; it carries `## Status`, `## Context`, `## Decision`,
`## Alternatives` and `## Consequences`; its alternatives section names each of
`installed-hooks`, `ci-only` and the null option with the trade each loses; its
consequences section states that the green record is a convenience rather than
proof; and `docs/decisions/` contains no file matching `ADR-074-*.md`, so the
run cannot drift back into the collision. Expect six cases. Step audit runner
contract is test command `python3 tests/run_tests.py --elenchus-report
{report}`, report format `elenchus.unittest.v1`, report file
`.elenchus/fiat-857-step-1.json`.

**Disciplines.** phylax: none, this step adds no input path and starts no
process. ephoros: none, nothing here runs unattended. metron: none, no
performance claim. elenchus: none, no failure in hand. hypomnema: the decision
record is the whole point of the step, and where the gate lives is expensive to
reverse once contributors have activated it.

## Step 2: Add the gate and prove it refuses an untested tree

**Goal.** Ship the tracked hook and the greenlight command, so an activated
checkout refuses a commit whose staged tree is not the tree the suite passed
on.

**Entry.** Step 1's exit state.

**Exit.** `.githooks/pre-commit` refuses a commit when no green record exists,
when the record names a tree other than the staged one, and when the record
cannot be read, writing one line to standard error that names which cause
applies. `.githooks/greenlight` runs `python3 -m unittest discover -s tests`
and, on exit zero alone, writes the identity from `git write-tree` into the
green record under `git rev-parse --git-dir`. Both files are tracked
executable. `FIAT_SKIP_PRECOMMIT=1` passes a commit through. Proved by `python3
-m unittest tests.test_commit_gate -v` at exit zero and `python3
scripts/run_checks.py --full` at exit zero on the committed tree.

**Files.** `.githooks/pre-commit`, `.githooks/greenlight`,
`tests/test_commit_gate.py`, `.horos/boundary.json`.

**Tests.** `tests/test_commit_gate.py` gains three classes, each driving a
throwaway fixture repository through the vetted scratch helpers so
`tests/test_scratch_quiescence.py` stays green and the outer tree stays
untouched. `GreenTreeTests`: with a green recorded for tree T, a commit staging
T succeeds; a commit staging any other tree exits non-zero; a commit with no
record at all exits non-zero; an unreadable record exits non-zero; each refusal
names its cause. `BypassTests`: `FIAT_SKIP_PRECOMMIT=1` admits an untested tree
and the literal token appears in the tracked gate. `TrackedGateTests`: both
scripts are tracked with the executable bit; the activation command writes a
relative `core.hooksPath`; the value set in the shared configuration is read
back from a linked worktree and resolves to that worktree's own copy. Expect
twelve cases. Step audit runner contract is test command `python3
tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-2.json`.

**Disciplines.** phylax: the hook runs on every commit in every activated
checkout and inherits git's exported environment, so this step opens the
boundary section 9 names first. ephoros: the refusal line is the signal that
answers "why was my commit refused", so this step owns study question 1.
metron: the gate must add at most 200 milliseconds to a commit whose tree is
already recorded green, measured by the study's command before this step
closes. elenchus: the stale-record refusal lands with the test that fails
without it. hypomnema: none, the decision record already covers the choice.

## Step 3: Guard the hook path against index mutation, and resolve the pending gate

**Goal.** Prove that running the gate under a polluted git environment cannot
touch another repository's index, and produce the report the design record's
pending criterion names.

**Entry.** Step 2's exit state.

**Exit.** `tests.test_commit_gate.HookIndexMutationTests` passes: driving the
gate with `GIT_INDEX_FILE` and `GIT_PREFIX` pointing at an outer repository, and
with `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT` set, leaves that
repository's staged state byte-identical. The gate starts no process other than
fixed-argument `git` invocations against its own repository and reads no
configuration an inherited override could redirect.
`.hexaemeron/reports/hooks-path-plus-visibility-index-mutation-regression.json`
exists as one closed `protasis-design-report/v1` object naming candidate
`hooks-path-plus-visibility`, criterion `index-mutation-regression`, the
resolver command the record declares, and `exit` zero. Proved by `python3 -m
unittest tests.test_commit_gate.HookIndexMutationTests -v` at exit zero,
`python3 tests/run_tests.py` at exit zero for
`tests/test_boundary_currency.py`, and `python3 scripts/run_checks.py --full`
at exit zero on the committed tree.

**Files.** `.githooks/pre-commit`, `.githooks/greenlight`,
`tests/test_commit_gate.py`,
`.hexaemeron/reports/hooks-path-plus-visibility-index-mutation-regression.json`,
`.horos/boundary.json`.

**Tests.** `tests/test_commit_gate.py` gains `HookIndexMutationTests`: the
outer repository's index digest is recorded, the gate is run with
`GIT_INDEX_FILE` and `GIT_PREFIX` aimed at it, and the digest is asserted
unchanged; the same under `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT`
carrying an override the gate would otherwise read; a case asserting the gate
resolves its green record through `git rev-parse --git-dir` so one worktree's
green cannot authorise another worktree's commit. The class lives in
`tests/test_commit_gate.py` rather than `tests/test_boundary_currency.py`,
because acceptance condition 5 refuses a guard that lives only in the file that
once caused the defect, and
`tests/test_boundary_currency.py`'s `GitEnvironmentIsolation` class is left
exactly as it is. Expect five cases. Step audit runner contract is test command
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-3.json`.

**Disciplines.** phylax: this step closes the inherited-environment boundary
with the control section 9 names. ephoros: none, the guard emits nothing.
metron: none, no performance claim beyond step 2's budget. elenchus: the
regression is the guard test for the phantom-deletion class, and it fails
without the control it guards. hypomnema: none, no new expensive choice.

## Step 4: Make the absence of the gate visible, and document it

**Goal.** Fail the root suite in a checkout where the gate is not activated,
with a message naming the one command that fixes it, and write the activation
and the bypass into the place contributors read.

**Entry.** Step 3's exit state, with the design checker green at `step:4`.

**Exit.** `tests.test_commit_gate.ActivationTests` fails in a checkout whose
`core.hooksPath` is unset or points anywhere other than the tracked directory,
and its failure message contains the literal `git config core.hooksPath
.githooks`. `AGENTS.md` gains the activation command and the bypass token in
its checks and lints section, added rather than rewritten. The draft decision
record's consequences section names the visibility assertion and states that
hosted execution cannot see whether a contributor activated the gate locally.
Proved by `python3 -m unittest tests.test_commit_gate -v` at exit zero in an
activated checkout, and `python3 scripts/run_checks.py --full` at exit zero on
the committed tree.

**Files.** `tests/test_commit_gate.py`, `AGENTS.md`,
`docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md`,
`docs/commit-gate/runbook.md`, `.horos/boundary.json`.

**Tests.** `tests/test_commit_gate.py` gains `ActivationTests`: an unset
`core.hooksPath` fails and the message names the activation command; a value
pointing at another directory fails the same way; the tracked directory holds
an executable `pre-commit`; and the assertion reads the checkout's own
configuration rather than a fixture's, so it is the shipped checkout it
reports on. Expect four cases. Step audit runner contract is test command
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-4.json`.

**Disciplines.** phylax: none, this step opens no boundary the gate did not
already open. ephoros: the failure message is the signal that answers "is the
gate on in this checkout", so this step owns study question 2. metron: none, a
test in the root suite carries no per-commit cost. elenchus: the assertion
fails closed in the other direction, so a checkout with no activation fails
the suite rather than passing quietly. hypomnema: `AGENTS.md` is quoted by the
router corpus, so this step adds to its checks section and runs the root suite
before it closes.

## Step 5: Demonstrate the gate on a clone that has never seen it

**Goal.** Run the study's demo path end to end on a fresh clone and record what
it did, so the five acceptance conditions are answered by an observed run
rather than by a claim.

**Entry.** Step 4's exit state.

**Exit.** `docs/commit-gate/demonstration.md` records one run of the demo path
against a clone of the run branch made into a fresh directory: the root suite
refused before activation and the transcript shows the activation command in
its output; the activation command was run once; `.githooks/greenlight`
recorded a green; a commit of that tree succeeded; a file was then edited and
the next commit was refused; and `FIAT_SKIP_PRECOMMIT=1` let that same commit
through. Each of the five acceptance conditions is answered with the exact
command and its exit code, and anything the run could not establish is named.
Proved by `python3 -m unittest tests.test_commit_gate -v` at exit zero and
`python3 scripts/run_checks.py --full` at exit zero on the committed tree.

**Files.** `docs/commit-gate/demonstration.md`, `docs/commit-gate/runbook.md`,
`.horos/boundary.json`.

**Tests.** `tests/test_commit_gate.py` gains `DemonstrationRecordTests`: the
demonstration record exists, names all five acceptance conditions, and records
an exit code for each command it reports. Expect three cases. No existing test
is changed. Step audit runner contract is test command `python3
tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-5.json`.

**Disciplines.** phylax: none, the demonstration runs in a throwaway clone and
adds no path. ephoros: none, the record is read by people rather than emitted
by a running system. metron: the demonstration reports the measured per-commit
overhead against the study's 200 millisecond budget. elenchus: none, no failure
in hand. hypomnema: the demonstration record is where a later reader finds out
what was actually observed, so it names its gaps.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit: `docs/commit-gate/study.md`, `docs/commit-gate/runbook.md`, `docs/commit-gate/design-evidence.json` and `docs/commit-gate/reports/` carry the four `.hexaemeron/` artefacts as they stood when this step was built, with the record-relative `reports/` layout preserved and every cited report resolving from the shipped record. The runbook, the design record and all forty reports are byte-identical to their sources. `docs/commit-gate/study.md` differs from its source on five lines and only in a link target, rewritten from the sibling form to `../../plugins/hexaemeron/skills/<skill>/SKILL.md` for each of the five phase skills, because Hypomnema's H001 refuses a link that resolves to nothing and reaches `docs/` through both the `lint-hypomnema` check and `tests/test_shipped_tree_lints.py`; no other byte differs. A later step refreshes the shipped runbook copy once this runbook stops changing. `docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md` records the chosen home, the trade each rejected option loses, and the consequence that the green record is a convenience rather than proof. `.githooks/README.md` names the activation command and the bypass token. `tests/check-map-v1.json` gains one owner entry binding `.githooks` to the `root` scope. `.horos/boundary.json` is regenerated. Proved by `python3 scripts/run_checks.py --full` at exit zero on the committed tree.

**Why.** The receipted Exit demanded that the shipped study copy be byte-identical to its source and that `python3 scripts/run_checks.py --full` exit zero, and on this repository those two cannot both hold. The study's five phase-skill links use the sibling form that resolves between skills under `plugins/hexaemeron/skills/`, and from `docs/commit-gate/` each one resolves to nothing. Hypomnema's H001 reports all five and exits 1, by two independent routes inside the full run. The source study is controller-pinned and study amendments are append-only, so its link targets cannot be rewritten in place. The shipped copy therefore carries the five rewritten targets and nothing else, and the Exit now says so. The runbook copy's byte-identity claim is also scoped to the artefact as it stood at this step, because this amendment changes the runbook it was copied from.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit: `tests.test_commit_gate.ActivationTests` fails in a checkout whose `core.hooksPath` is unset or points anywhere other than the tracked directory, and its failure message contains the literal `git config core.hooksPath .githooks`. `AGENTS.md` gains the activation command and the bypass token in its checks and lints section, added rather than rewritten. The draft decision record's consequences section names the visibility assertion and states that hosted execution cannot see whether a contributor activated the gate locally. `docs/commit-gate/study.md` and `docs/commit-gate/runbook.md` are refreshed to the bytes receipted at this step's entry, so both shipped copies carry every amendment recorded up to that point; the study copy keeps its five rewritten phase-skill link targets and differs from its source in nothing else. Proved by `python3 -m unittest tests.test_commit_gate -v` at exit zero in an activated checkout, `python3 scripts/run_checks.py --full` at exit zero on the committed tree, and a byte comparison of each refreshed copy against its source reported in the step's commit message. Complete replacement Files: `tests/test_commit_gate.py`, `AGENTS.md`, `docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md`, `docs/commit-gate/study.md`, `docs/commit-gate/runbook.md`, `.horos/boundary.json`.

**Why.** Three step 1 round 1 findings land here. S1-R1-01, medium: the shipped study sends a reader to `.hexaemeron/` five times for artefacts that ship at `docs/commit-gate/`, and the study amendment dated today records the mapping, so the shipped copy has to be refreshed to carry it. S1-R1-04, low: the shipped runbook still asserts byte-identity for the study and does not carry the amendment that corrected it, which the same refresh fixes. S1-R1-03, low, is an erratum this block records rather than repairs, because it sits in this runbook's preamble rather than in a step field: the collision check named at line 14 is at `tests/test_decision_records.py:110`, not `:108`, at the base, at the step 1 commit and in the working tree. The two `scripts/run_checks.py` line numbers the study cites are one off for the same reason and are left as recorded, because that file has moved since. A residual remains: an amendment recorded after step 4 would stale the refreshed copies again, and step 5 already lists the runbook copy among its files.

**Steps touched.** Step 4.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit: `docs/commit-gate/study.md`, `docs/commit-gate/runbook.md`, `docs/commit-gate/design-evidence.json` and `docs/commit-gate/reports/` carry the four `.hexaemeron/` artefacts as they stood when this step was built, with the record-relative `reports/` layout preserved and every cited report resolving from the shipped record. The runbook, the design record and all forty reports are byte-identical to their sources. `docs/commit-gate/study.md` differs from its source on five lines and only in a link target, rewritten from the sibling form to `../../plugins/hexaemeron/skills/<skill>/SKILL.md` for each of the five phase skills, because Hypomnema's H001 refuses a link that resolves to nothing and reaches `docs/` through both the `lint-hypomnema` check and `tests/test_shipped_tree_lints.py`; no other byte differs. A later step refreshes the shipped copies once this runbook stops changing. `docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md` records the chosen home, the trade each rejected option loses, and the consequence that the green record is a convenience rather than proof. `.githooks/README.md` names the activation command and the bypass token. `tests/check-map-v1.json` gains one owner entry binding `.githooks` to the `root` scope. `.horos/boundary.json` is regenerated, and stays regenerated for every commit this step's audit rounds add on top of it. Proved by `python3 scripts/run_checks.py --full` at exit zero on the committed tree.

**Why.** Re-issues the step 1 Exit replacement first recorded earlier today. That amendment stayed in the ledger but stopped reaching the worker packet, because the controller binds a runbook amendment to the study digest current when it was recorded and a later study amendment changes that digest. Round 2 caught the packet handing back the superseded Exit, which the tree does not satisfy and was never meant to; the artefact was never wrong. Recorded as S1-R2-02, medium. The Exit also now requires the reading boundary to stay regenerated across the audit rounds' own commits, which is finding S1-R2-05, high: round 1's record commit added two tracked files without a rescan and turned a green receipt into a red branch.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit: `tests.test_commit_gate.ActivationTests` fails in a checkout whose `core.hooksPath` is unset or points anywhere other than the tracked directory, and its failure message contains the literal `git config core.hooksPath .githooks`. `AGENTS.md` gains the activation command and the bypass token in its checks and lints section, added rather than rewritten. The draft decision record's consequences section names the visibility assertion and states that hosted execution cannot see whether a contributor activated the gate locally. `docs/commit-gate/study.md` and `docs/commit-gate/runbook.md` are refreshed to the bytes receipted at this step's entry, so both shipped copies carry every amendment recorded up to that point; the study copy keeps its five rewritten phase-skill link targets and differs from its source in nothing else. Proved by `python3 -m unittest tests.test_commit_gate -v` at exit zero in an activated checkout and `python3 scripts/run_checks.py --full` at exit zero on the committed tree. The refresh is proved inside that suite rather than in prose, by assertions a fresh clone can run without reading anything outside the repository. Complete replacement Files: `tests/test_commit_gate.py`, `AGENTS.md`, `docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md`, `docs/commit-gate/study.md`, `docs/commit-gate/runbook.md`, `.horos/boundary.json`. Complete replacement Tests: `tests/test_commit_gate.py` gains `ActivationTests`: an unset `core.hooksPath` fails and the message names the activation command; a value pointing at another directory fails the same way; the tracked directory holds an executable `pre-commit`; and the assertion reads the checkout's own configuration rather than a fixture's, so it is the shipped checkout it reports on. Expect four cases. It also gains `ShippedCopyTests`, which prove the refresh from inside the repository: `docs/commit-gate/study.md` carries exactly the number of `### Amendment --` headings this step writes into the test as a literal, `docs/commit-gate/runbook.md` carries exactly its own literal count, and the shipped study's every `.hexaemeron/` reference is accompanied somewhere in the same file by the mapping to `docs/commit-gate/`, so a reader who follows a citation is never left without one. Expect three cases, seven in the file's new work for this step. Step audit runner contract is test command `python3 tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-4.json`.

**Why.** Re-issues the step 4 Exit and Files replacements recorded earlier today, which the study amendment above unbound from the worker packet, and answers audit finding S1-R2-03, low, from step 1 round 2. The previous Exit proved the refresh by a byte comparison reported in the step's own commit message, which is evidence written by the party it certifies and which no command in a clone can repeat, because `.hexaemeron/` is absent there. The replacement moves that proof into the repository suite, where a stranger with only the clone can run it. Files gains `docs/commit-gate/study.md`, which finding S1-R1-04 requires and the original list omitted.

**Steps touched.** Step 4.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit: `tests.test_commit_gate.ActivationTests` fails in a checkout whose `core.hooksPath` is unset or points anywhere other than the tracked directory, and its failure message contains the literal `git config core.hooksPath .githooks`. `AGENTS.md` gains the activation command and the bypass token in its checks and lints section, added rather than rewritten. The draft decision record's consequences section names the visibility assertion, states that hosted execution cannot see whether a contributor activated the gate locally, and carries the first-execution cost the study records beside its steady-state budget. Every artefact under `docs/commit-gate/` is refreshed to the bytes receipted at this step's entry: the study and runbook so they carry every amendment recorded up to that point, and the design record with its reports so the shipped record holds no row the controller has since resolved. The study copy keeps its five rewritten phase-skill link targets and differs from its source in nothing else. Proved by `python3 -m unittest tests.test_commit_gate -v` at exit zero in an activated checkout and `python3 scripts/run_checks.py --full` at exit zero on the committed tree. The refresh is proved inside that suite rather than in prose, by assertions a fresh clone can run without reading anything outside the repository. Complete replacement Files: `tests/test_commit_gate.py`, `AGENTS.md`, `docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md`, `docs/commit-gate/study.md`, `docs/commit-gate/runbook.md`, `docs/commit-gate/design-evidence.json`, `docs/commit-gate/reports/`, `.horos/boundary.json`. Complete replacement Tests: `tests/test_commit_gate.py` gains `ActivationTests`: an unset `core.hooksPath` fails and the message names the activation command; a value pointing at another directory fails the same way; the tracked directory holds an executable `pre-commit`; and the assertion reads the checkout's own configuration rather than a fixture's, so it is the shipped checkout it reports on. Expect four cases. It also gains `ShippedCopyTests`, which prove the refresh from inside the repository: `docs/commit-gate/study.md` carries exactly the number of `### Amendment --` headings this step writes into the test as a literal, `docs/commit-gate/runbook.md` carries exactly its own literal count, every `.hexaemeron/` reference in the shipped study is accompanied somewhere in the same file by the mapping to `docs/commit-gate/`, and every report the shipped design record cites resolves under `docs/commit-gate/reports/` at the digest the record names. Expect four cases, eight in the file's new work for this step. Step audit runner contract is test command `python3 tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-4.json`.

**Why.** Re-issues step 4's Exit, Files and Tests, which the study amendment above unbound from the worker packet by changing the study digest they were recorded against. Two additions ride with the re-issue. The consequences section now carries the first-execution cost, because step 2 round 2 established it and a decision record that states a 200 millisecond budget without it would mislead the reader the record exists for. And the refresh now covers the shipped design record and its reports, closing the lead step 1's audit carried forward: once step 3 resolves `index-mutation-regression`, a shipped record left alone would keep four pending rows the controller no longer has.

**Steps touched.** Step 4.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit: `tests.test_commit_gate.ActivationTests` fails in a checkout whose `core.hooksPath` is unset or points anywhere other than the tracked directory, and its failure message contains the literal `git config core.hooksPath .githooks`. `AGENTS.md` gains the activation command and the bypass token in its checks and lints section, added rather than rewritten. The draft decision record's consequences section names the visibility assertion, states that hosted execution cannot see whether a contributor activated the gate locally, and carries the first-execution cost the study records beside its steady-state budget. Every artefact under `docs/commit-gate/` is refreshed to the bytes receipted at this step's entry: the study and runbook so they carry every amendment recorded up to that point, and the design record with its reports so the shipped record holds no row the controller has since resolved. The study copy keeps its five rewritten phase-skill link targets and differs from its source in nothing else. Proved by `python3 -m unittest tests.test_commit_gate -v` at exit zero in an activated checkout and `python3 scripts/run_checks.py --full` at exit zero on the committed tree. The refresh is proved inside that suite rather than in prose, by assertions a fresh clone can run without reading anything outside the repository. Complete replacement Files: `tests/test_commit_gate.py`, `AGENTS.md`, `docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md`, `docs/commit-gate/study.md`, `docs/commit-gate/runbook.md`, `docs/commit-gate/design-evidence.json`, `docs/commit-gate/reports/`, `.horos/boundary.json`. Complete replacement Tests: `tests/test_commit_gate.py` gains `ActivationTests`: an unset `core.hooksPath` fails and the message names the activation command; a value pointing at another directory fails the same way; the tracked directory holds an executable `pre-commit`; and the assertion reads the checkout's own configuration rather than a fixture's, so it is the shipped checkout it reports on. Expect four cases. It also gains `ShippedCopyTests`, which prove the refresh from inside the repository: `docs/commit-gate/study.md` carries exactly the number of `### Amendment --` headings this step writes into the test as a literal, `docs/commit-gate/runbook.md` carries exactly its own literal count, every `.hexaemeron/` reference in the shipped study is accompanied somewhere in the same file by the mapping to `docs/commit-gate/`, and every report the shipped design record cites resolves under `docs/commit-gate/reports/` at the digest the record names. Expect four cases, eight in the file's new work for this step. Step audit runner contract is test command `python3 tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-4.json`.

**Why.** Re-issues step 4's Exit, Files and Tests unchanged. The study amendment above unbound them from the worker packet by changing the study digest they were recorded against, which is the third time this run has met that ordering rule. The content is identical to the previous issue; only its binding is new.

**Steps touched.** Step 4.

**Still holding.** Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit: `tests.test_commit_gate.HookIndexMutationTests` passes: driving the gate with `GIT_INDEX_FILE` and `GIT_PREFIX` pointing at an outer repository, with `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT` set, with `GIT_CONFIG_GLOBAL` or `GIT_CONFIG_SYSTEM` naming a configuration file, with both selectors absent and `$HOME/.gitconfig` carrying the override, and with `GIT_DIR` naming another repository whose own configuration carries the override, leaves that repository's staged state byte-identical and starts no command the override names. The gate starts no process other than fixed-argument `git` invocations against its own repository and reads no configuration an inherited override could redirect, whether the override arrives in-band, through a file selector or through a repository selector. The hook half drops `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES` and `GIT_NAMESPACE` and keeps `GIT_INDEX_FILE` and `GIT_PREFIX`, so under an inherited `GIT_DIR` it still admits the recorded green tree and refuses any other tree in the repository git runs it from. On the `git rev-parse --git-dir` refusal path the hook's one refusal line carries git's own first standard-error line, stripped of control characters and bounded, so `tests.test_commit_gate.RefusalLineTests` shows the hook started outside any repository refusing on one line that names `not a git repository`. `.hexaemeron/reports/hooks-path-plus-visibility-index-mutation-regression.json` exists as one closed `protasis-design-report/v1` object naming candidate `hooks-path-plus-visibility`, criterion `index-mutation-regression`, the resolver command the record declares, and `exit` zero. Proved by `python3 -m unittest tests.test_commit_gate.HookIndexMutationTests -v` at exit zero, `python3 tests/run_tests.py` at exit zero for `tests/test_boundary_currency.py`, and `python3 scripts/run_checks.py --full` at exit zero on the committed tree. Complete replacement Tests: `tests/test_commit_gate.py` gains `HookIndexMutationTests`: the outer repository's index, working-tree status and refs are recorded, the gate is run with `GIT_INDEX_FILE` and `GIT_PREFIX` aimed at it, and that state is asserted unchanged; the same under `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT` carrying an override the gate would otherwise read; the same down the three configuration-file routes, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` and `$HOME/.gitconfig` with both selectors absent, for each half; the hook half under `GIT_DIR` naming another repository whose own configuration carries the override, asserting the command did not run and that repository's state is unchanged; the hook half under the same inherited `GIT_DIR` admitting the recorded green tree and refusing another tree in the repository it runs from; and a case asserting the gate resolves its green record through `git rev-parse --git-dir` so one worktree's green cannot authorise another worktree's commit. Expect nine cases. `RefusalLineTests` gains one case: the hook started outside any repository refuses on one line that carries `not a git repository`. The class lives in `tests/test_commit_gate.py` rather than `tests/test_boundary_currency.py`, because acceptance condition 5 refuses a guard that lives only in the file that once caused the defect, and `tests/test_boundary_currency.py`'s `GitEnvironmentIsolation` class is left exactly as it is. Step audit runner contract is test command `python3 tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-3.json`.

**Why.** Findings S3-R1-02, medium, S3-R1-03, low, and S3-R1-04, low, from step 3 round 1, and the study amendment dated today that records the decision behind them. The previous Exit named two inherited variables and the previous Tests expected five cases; the tree at 612e0b64 ships seven, two of them driving configuration-file routes the pinned documents named nowhere, and the round measured `GIT_DIR` still open in the hook half. The replacement names every route the regression drives, records the decision that the hook half drops the repository-selecting variables and keeps the index git names, and puts the refusal-line change in scope, because the round declined to make either change under a step whose contract did not ask for it. The runbook preamble's `.hexaemeron/reports/` path is a working path for the run and stays as it is.

**Steps touched.** Step 3.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit: `tests.test_commit_gate.HookIndexMutationTests` passes: driving the gate with `GIT_INDEX_FILE` and `GIT_PREFIX` pointing at an outer repository, with `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT` set, with `GIT_CONFIG_GLOBAL` or `GIT_CONFIG_SYSTEM` naming a configuration file, with both selectors absent and `$HOME/.gitconfig` carrying the override, and with `GIT_DIR` naming another repository whose own configuration carries the override, leaves that repository's staged state byte-identical and starts no command the override names. The gate starts no process other than fixed-argument `git` invocations against its own repository and reads no configuration an inherited override could redirect, whether the override arrives in-band, through a file selector or through a repository selector. The hook half drops `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES` and `GIT_NAMESPACE` and keeps `GIT_INDEX_FILE` and `GIT_PREFIX`, so under an inherited `GIT_DIR` it still admits the recorded green tree and refuses any other tree in the repository git runs it from. The hook half refuses when `git rev-parse --show-prefix` answers a non-empty value, on one line naming that cause, before it locates a record or reads an index: git runs a hook from the root of the working tree, so an empty prefix is the ordinary case, and a non-empty one means discovery climbed out of the work tree the gate was started in and into a repository enclosing it. A work tree with no `.git` of its own nested inside another repository is therefore refused rather than gated by the enclosing repository's green record, and the bypass token admits it. On the `git rev-parse --git-dir` refusal path the hook's one refusal line carries git's own first standard-error line, stripped of control characters and bounded, so `tests.test_commit_gate.RefusalLineTests` shows the hook started outside any repository refusing on one line that names `not a git repository`. `.hexaemeron/reports/hooks-path-plus-visibility-index-mutation-regression.json` exists as one closed `protasis-design-report/v1` object naming candidate `hooks-path-plus-visibility`, criterion `index-mutation-regression`, the resolver command the record declares, and `exit` zero. Proved by `python3 -m unittest tests.test_commit_gate.HookIndexMutationTests -v` at exit zero, `python3 tests/run_tests.py` at exit zero for `tests/test_boundary_currency.py`, and `python3 scripts/run_checks.py --full` at exit zero on the committed tree. Complete replacement Tests: `tests/test_commit_gate.py` gains `HookIndexMutationTests`: the outer repository's index, working-tree status and refs are recorded, the gate is run with `GIT_INDEX_FILE` and `GIT_PREFIX` aimed at it, and that state is asserted unchanged; the same under `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT` carrying an override the gate would otherwise read; the same down the three configuration-file routes, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` and `$HOME/.gitconfig` with both selectors absent, for each half; the hook half under `GIT_DIR` naming another repository whose own configuration carries the override, asserting the command did not run and that repository's state is unchanged; the hook half under the same inherited `GIT_DIR` admitting the recorded green tree and refusing another tree in the repository it runs from; a case driving a `.git`-less work tree nested inside an enclosing repository whose `LAST_GREEN` names the staged tree, asserting the commit is refused, that the refusal names the prefix cause, that the enclosing repository's configured command did not run, and that its staged state is unchanged; and a case asserting the gate resolves its green record through `git rev-parse --git-dir` so one worktree's green cannot authorise another worktree's commit. Expect ten cases. `RefusalLineTests` gains one case: the hook started outside any repository refuses on one line that carries `not a git repository`. The class lives in `tests/test_commit_gate.py` rather than `tests/test_boundary_currency.py`, because acceptance condition 5 refuses a guard that lives only in the file that once caused the defect, and `tests/test_boundary_currency.py`'s `GitEnvironmentIsolation` class is left exactly as it is. Step audit runner contract is test command `python3 tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-3.json`.

**Why.** Finding S3-R2-01, low, from step 3 round 2. The previous Exit closed the repository selectors and recorded the split-work-tree trade as a refusal, and the round measured that the refusal holds only while no repository encloses the work tree. Nested inside repository E, discovery answers E: E's `core.fsmonitor` ran during the gate's own `git write-tree`, which is the process class the Exit already forbids, and with E's `LAST_GREEN` naming the staged tree the commit was admitted, so one checkout's record authorised another's. That is the `worktree-record-crossing` concern the register requires closed, reached by a route the register's own control does not cover, so it is closed here rather than accepted. The round measured the control and declined to ship it, because the Exit fixed the case counts and an unguarded fix is what the Disciplines clause refuses; this amendment is what that judgement was waiting for.

**Steps touched.** Step 3.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit: `tests.test_commit_gate.HookIndexMutationTests` passes: driving the gate with `GIT_INDEX_FILE` and `GIT_PREFIX` pointing at an outer repository, with `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT` set, with `GIT_CONFIG_GLOBAL` or `GIT_CONFIG_SYSTEM` naming a configuration file, with both selectors absent and `$HOME/.gitconfig` carrying the override, and with `GIT_DIR` naming another repository whose own configuration carries the override, leaves that repository's staged state byte-identical and starts no command the override names. The gate starts no process other than fixed-argument `git` invocations against its own repository and reads no configuration an inherited override could redirect, whether the override arrives in-band, through a file selector or through a repository selector. The hook half drops `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES` and `GIT_NAMESPACE` and keeps `GIT_INDEX_FILE` and `GIT_PREFIX`, so under an inherited `GIT_DIR` it still admits the recorded green tree and refuses any other tree in the repository git runs it from. The hook half refuses, on one line naming the cause it measured, in each of two cases, before it locates a record or reads an index. It refuses when `git rev-parse --show-prefix` answers a non-empty value: git runs a hook from the root of the working tree, so an empty prefix is the ordinary case, and a non-empty one means the gate was started somewhere other than the root of the repository discovery answers. It refuses when the index it is about to read does not belong to the repository discovery answers, which the gate decides by comparing the directory holding `GIT_INDEX_FILE`, resolved against the directory the hook runs in when the value is relative, with the directory `git rev-parse --git-dir` answers, resolved the same way. Those two together refuse a work tree with no `.git` of its own driven through `--git-dir` and `--work-tree` at any depth inside another repository, including at that repository's own root, where the prefix is empty and only the index comparison separates them; so no repository's green record can authorise a commit into a repository it does not hold, and the bypass token admits both. An ordinary gated commit is untouched by both controls: a plain commit, a commit from a subdirectory, `commit -a`, `commit --amend`, a commit in a linked worktree and a commit in a subdirectory of one each answer an empty prefix and an index inside the git directory discovery answers. On the `git rev-parse --git-dir` refusal path the hook's one refusal line carries git's own first standard-error line, stripped of control characters and bounded, so `tests.test_commit_gate.RefusalLineTests` shows the hook started outside any repository refusing on one line that names `not a git repository`. `.hexaemeron/reports/hooks-path-plus-visibility-index-mutation-regression.json` exists as one closed `protasis-design-report/v1` object naming candidate `hooks-path-plus-visibility`, criterion `index-mutation-regression`, the resolver command the record declares, and `exit` zero. Proved by `python3 -m unittest tests.test_commit_gate.HookIndexMutationTests -v` at exit zero, `python3 tests/run_tests.py` at exit zero for `tests/test_boundary_currency.py`, and `python3 scripts/run_checks.py --full` at exit zero on the committed tree. Complete replacement Tests: `tests/test_commit_gate.py` gains `HookIndexMutationTests`: the outer repository's index, working-tree status and refs are recorded, the gate is run with `GIT_INDEX_FILE` and `GIT_PREFIX` aimed at it, and that state is asserted unchanged; the same under `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT` carrying an override the gate would otherwise read; the same down the three configuration-file routes, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` and `$HOME/.gitconfig` with both selectors absent, for each half; the hook half under `GIT_DIR` naming another repository whose own configuration carries the override, asserting the command did not run and that repository's state is unchanged; the hook half under the same inherited `GIT_DIR` admitting the recorded green tree and refusing another tree in the repository it runs from; a case driving a `.git`-less work tree in a subdirectory of an enclosing repository whose `LAST_GREEN` names the staged tree, asserting the commit is refused, that the refusal names the prefix cause, that the enclosing repository's configured command did not run, and that its staged state is unchanged; a case driving the same crossing with the second work tree at the enclosing repository's own root, where the prefix is empty, asserting the commit is refused, that the refusal names the index cause, and the same two negative results; a case asserting an ordinary gated commit from a subdirectory is still admitted, so neither control refuses the shape it is not aimed at; and a case asserting the gate resolves its green record through `git rev-parse --git-dir` so one worktree's green cannot authorise another worktree's commit. Expect twelve cases. `RefusalLineTests` gains one case: the hook started outside any repository refuses on one line that carries `not a git repository`. The class lives in `tests/test_commit_gate.py` rather than `tests/test_boundary_currency.py`, because acceptance condition 5 refuses a guard that lives only in the file that once caused the defect, and `tests/test_boundary_currency.py`'s `GitEnvironmentIsolation` class is left exactly as it is. Step audit runner contract is test command `python3 tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-3.json`.

**Why.** Finding S3-R4-01, low, from step 3 round 4. The previous Exit claimed that a work tree with no `.git` of its own nested inside another repository is refused, and the round measured that its control reaches only a proper subdirectory. With the second work tree at the enclosing repository's own root the prefix is empty, the control never fires, and the round drove the ordinary workflow with nothing hand-written: greenlight recorded tree `a493adb5` in E, and a commit through `--git-dir` and `--work-tree` was admitted at rc 0 into S, which holds no green record of its own, taking commit `6a283fe7` on that tree. E's `core.fsmonitor` also ran during the gate's own `write-tree` on every coincident-root attempt, which is the process class the same Exit forbids. That leaves `worktree-record-crossing` open on the route the depth-zero shape takes, so the consequence sentence is made true rather than narrowed. The index comparison is the control the round measured against seven ordinary shapes, which agree in all seven and differ only in the crossing; it is named here because the evidence for it already exists, and the prefix control stays because it fires earlier and names a different cause.

**Steps touched.** Step 3.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Tests: `tests/test_commit_gate.py` gains `HookIndexMutationTests`: the outer repository's index, working-tree status and refs are recorded, the gate is run with `GIT_INDEX_FILE` and `GIT_PREFIX` aimed at it, and that state is asserted unchanged; the same under `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT` carrying an override the gate would otherwise read; the same down the three configuration-file routes, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` and `$HOME/.gitconfig` with both selectors absent, for each half; the hook half under `GIT_DIR` naming another repository whose own configuration carries the override, asserting the command did not run and that repository's state is unchanged; the hook half under the same inherited `GIT_DIR` admitting the recorded green tree and refusing another tree in the repository it runs from; a case driving a `.git`-less work tree in a subdirectory of an enclosing repository whose `LAST_GREEN` names the staged tree, asserting the commit is refused, that the refusal names the prefix cause, that the enclosing repository's configured command did not run, and that its staged state is unchanged; a case driving the same crossing with the second work tree at the enclosing repository's own root, where the prefix is empty, asserting the commit is refused, that the refusal names the index cause, and the same two negative results; a case asserting an ordinary gated commit from a subdirectory is still admitted, so neither control refuses the shape it is not aimed at; a case driving the hook half's five configuration routes in a repository the anchoring controls admit, so that the gate reaches its own `git write-tree` and the case holds the controls that keep an inherited override out of it, asserting the override's command did not run and the commit is decided on the gate's own comparison; and a case asserting the gate resolves its green record through `git rev-parse --git-dir` so one worktree's green cannot authorise another worktree's commit. Expect thirteen cases. `RefusalLineTests` gains one case: the hook started outside any repository refuses on one line that carries `not a git repository`. The class lives in `tests/test_commit_gate.py` rather than `tests/test_boundary_currency.py`, because acceptance condition 5 refuses a guard that lives only in the file that once caused the defect, and `tests/test_boundary_currency.py`'s `GitEnvironmentIsolation` class is left exactly as it is. Step audit runner contract is test command `python3 tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-3.json`.

**Why.** Finding S3-R5-01, low, from step 3 round 5, raised by that round against its own fix. The index-anchoring control refuses before `git write-tree`, which is the command that made an inherited configuration override observable, so the hook half's configuration cases now stop earlier than the behaviour they were written to hold. The round measured the consequence: against the parent hook, cutting the in-band `unset` or the `/dev/null` pins turns a case red, and against `c8f88aa8` neither does, so those controls ship correct and unguarded in that half while the greenlight half keeps its own guards. The thirteenth case drives the same five routes in a repository the anchoring controls admit, which is where the gate reaches `write-tree` and the override becomes observable again. The Exit is unchanged: the gate's behaviour is what it already says, and this is the case that holds it.

**Steps touched.** Step 3.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit: `tests.test_commit_gate.HookIndexMutationTests` passes: driving the gate with `GIT_INDEX_FILE` and `GIT_PREFIX` pointing at an outer repository, with `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT` set, with `GIT_CONFIG_GLOBAL` or `GIT_CONFIG_SYSTEM` naming a configuration file, with both selectors absent and `$HOME/.gitconfig` carrying the override, and with `GIT_DIR` naming another repository whose own configuration carries the override, leaves that repository's staged state byte-identical and starts no command the override names. The gate starts no process other than fixed-argument `git` invocations against its own repository and reads no configuration an inherited override could redirect, whether the override arrives in-band, through a file selector or through a repository selector. The hook half drops `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES` and `GIT_NAMESPACE` and keeps `GIT_INDEX_FILE` and `GIT_PREFIX`, so under an inherited `GIT_DIR` it still admits the recorded green tree and refuses any other tree in the repository git runs it from. Both halves drop `CDPATH` before resolving any relative path, because `cd` searches it whenever its operand's first component is neither `.` nor `..` and both halves hand it exactly such an operand, so an inherited `CDPATH` moves neither where the hook half anchors nor which repository's suite and record the greenlight half runs and writes. The hook half refuses, on one line naming the cause it measured, in each of two cases, before it locates a record or reads an index. It refuses when `git rev-parse --show-prefix` answers a non-empty value: git runs a hook from the root of the working tree, so an empty prefix is the ordinary case, and a non-empty one means the gate was started somewhere other than the root of the repository discovery answers. It refuses when the index it is about to read does not belong to the repository discovery answers, which the gate decides by comparing the directory holding `GIT_INDEX_FILE`, resolved against the directory the hook runs in when the value is relative, with the directory `git rev-parse --git-dir` answers, resolved the same way. Those two together refuse a work tree with no `.git` of its own driven through `--git-dir` and `--work-tree` at any depth inside another repository, including at that repository's own root, where the prefix is empty and only the index comparison separates them; so no repository's green record can authorise a commit into a repository it does not hold, and the bypass token admits both. An ordinary gated commit is untouched by every one of these controls: a plain commit, a commit from a subdirectory, `commit -a`, `commit --amend`, `commit -a --amend`, a commit in a linked worktree and a commit in a subdirectory of one each answer an empty prefix and an index inside the git directory discovery answers, under an inherited `CDPATH` as well as without one. On the `git rev-parse --git-dir` refusal path the hook's one refusal line carries git's own first standard-error line, stripped of control characters and bounded, so `tests.test_commit_gate.RefusalLineTests` shows the hook started outside any repository refusing on one line that names `not a git repository`. `.hexaemeron/reports/hooks-path-plus-visibility-index-mutation-regression.json` exists as one closed `protasis-design-report/v1` object naming candidate `hooks-path-plus-visibility`, criterion `index-mutation-regression`, the resolver command the record declares, and `exit` zero. Proved by `python3 -m unittest tests.test_commit_gate.HookIndexMutationTests -v` at exit zero, `python3 tests/run_tests.py` at exit zero for `tests/test_boundary_currency.py`, and `python3 scripts/run_checks.py --full` at exit zero on the committed tree. Complete replacement Tests: `tests/test_commit_gate.py` gains `HookIndexMutationTests`: the outer repository's index, working-tree status and refs are recorded, the gate is run with `GIT_INDEX_FILE` and `GIT_PREFIX` aimed at it, and that state is asserted unchanged; the same under `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT` carrying an override the gate would otherwise read; the same down the three configuration-file routes, `GIT_CONFIG_GLOBAL`, `GIT_CONFIG_SYSTEM` and `$HOME/.gitconfig` with both selectors absent, for each half; the hook half under `GIT_DIR` naming another repository whose own configuration carries the override, asserting the command did not run and that repository's state is unchanged; the hook half under the same inherited `GIT_DIR` admitting the recorded green tree and refusing another tree in the repository it runs from; a case driving a `.git`-less work tree in a subdirectory of an enclosing repository whose `LAST_GREEN` names the staged tree, asserting the commit is refused, that the refusal names the prefix cause, that the enclosing repository's configured command did not run, and that its staged state is unchanged; a case driving the same crossing with the second work tree at the enclosing repository's own root, where the prefix is empty, asserting the commit is refused, that the refusal names the index cause, and the same two negative results; a case asserting an ordinary gated commit from a subdirectory is still admitted, so neither control refuses the shape it is not aimed at; a case driving the hook half's five configuration routes in a repository the anchoring controls admit, so that the gate reaches its own `git write-tree` and the case holds the controls that keep an inherited override out of it, asserting the override's command did not run and the commit is decided on the gate's own comparison; a case driving each half under an inherited `CDPATH` naming another repository's parent, asserting that the hook half still admits a commit its own recorded green names and that the greenlight half runs the suite of and records into the repository it was started from, leaving the other repository's record absent; and a case asserting the gate resolves its green record through `git rev-parse --git-dir` so one worktree's green cannot authorise another worktree's commit. Expect fourteen cases. `RefusalLineTests` gains one case: the hook started outside any repository refuses on one line that carries `not a git repository`. The class lives in `tests/test_commit_gate.py` rather than `tests/test_boundary_currency.py`, because acceptance condition 5 refuses a guard that lives only in the file that once caused the defect, and `tests/test_boundary_currency.py`'s `GitEnvironmentIsolation` class is left exactly as it is. Step audit runner contract is test command `python3 tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-3.json`.

**Why.** Finding S3-R7-01 from step 3 round 7. `cd` searches `CDPATH` when its operand's first component is neither `.` nor `..`, and both halves hand it exactly such an operand: the hook half resolves `.git`, which is what git answers for both sides of its index comparison in a plain checkout, and greenlight anchors with `cd "$here/.."` on `.githooks/..`. The round measured both consequences on git 2.50.1 against af92cbe9. With `CDPATH` naming a directory holding a `.git`, `commit -a` and `commit -a --amend` were refused on the index cause with the index inside the git directory all along, which is an ordinary shape refused for a reason that was not true. With `CDPATH` naming another clone's root, greenlight ran that clone's suite and wrote that clone's tree into that clone's record while printing `.git/LAST_GREEN` as though it were this one's, which is `worktree-record-crossing` reached through the shell rather than through git. The fix landed in the round as commit f815dd8d and is unguarded, because the previous Tests fixed the case counts; this amendment admits the case that holds it, and extends the Exit's ordinary-shape clause to the two shapes the defect refused and to the inherited-`CDPATH` condition, so the guard has something to check against.

**Steps touched.** Step 3.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: `tests.test_commit_gate.ActivationTests` fails in a checkout whose `core.hooksPath` is unset or points anywhere other than the tracked directory, and its failure message contains the literal `git config core.hooksPath .githooks`. `AGENTS.md` gains the activation command and the bypass token in its checks and lints section, added rather than rewritten. The draft decision record's consequences section names the visibility assertion, states that hosted execution cannot see whether a contributor activated the gate locally, and carries the first-execution cost the study records beside its steady-state budget. Every artefact under `docs/commit-gate/` is refreshed to the bytes receipted at this step's entry: the study and runbook so they carry every amendment recorded up to that point, and the design record with its reports so the shipped record holds no row the controller has since resolved. The study copy keeps its five rewritten phase-skill link targets and differs from its source in nothing else. Proved by `python3 -m unittest tests.test_commit_gate -v` at exit zero in an activated checkout and `python3 scripts/run_checks.py --full` at exit zero on the committed tree. The refresh is proved inside that suite rather than in prose, by assertions a fresh clone can run without reading anything outside the repository. Complete replacement Files: `tests/test_commit_gate.py`, `AGENTS.md`, `docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md`, `docs/commit-gate/study.md`, `docs/commit-gate/runbook.md`, `docs/commit-gate/design-evidence.json`, `docs/commit-gate/reports/`, `.horos/boundary.json`. Complete replacement Tests: `tests/test_commit_gate.py` gains `ActivationTests`: an unset `core.hooksPath` fails and the message names the activation command; a value pointing at another directory fails the same way; the tracked directory holds an executable `pre-commit`; and the assertion reads the checkout's own configuration rather than a fixture's, so it is the shipped checkout it reports on. Expect four cases. It also gains `ShippedCopyTests`, which prove the refresh from inside the repository: `docs/commit-gate/study.md` carries exactly the number of `### Amendment --` headings this step writes into the test as a literal, `docs/commit-gate/runbook.md` carries exactly its own literal count, every `.hexaemeron/` reference in the shipped study is accompanied somewhere in the same file by the mapping to `docs/commit-gate/`, and every report the shipped design record cites resolves under `docs/commit-gate/reports/` at the digest the record names. Expect four cases, eight in the file's new work for this step. Step audit runner contract is test command `python3 tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-4.json`.

**Why.** Re-issues step 4's Exit, Files and Tests unchanged, for the fourth time. Step 3's eight-round audit recorded further study amendments, and each one changed the study digest the previous issue was recorded against, so the packet step 4's Mason received carried the baseline step and no amendment at all. That worker built the baseline and stopped at its file list rather than widening the step, which is the correct behaviour and is why the larger step is unbuilt rather than half-built. The content here is identical to the previous issue; only its binding is new. Step 3's audit phase is closed and its pull request is open, so no further study amendment is expected to unbind it again.

**Steps touched.** Step 4.

**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Exit: `tests.test_commit_gate.ActivationTests` fails in a checkout whose `core.hooksPath` is unset or points anywhere other than the tracked directory, and its failure message contains the literal `git config core.hooksPath .githooks`. `AGENTS.md` gains the activation command and the bypass token in its checks and lints section, added rather than rewritten. The draft decision record's consequences section names the visibility assertion, states that hosted execution cannot see whether a contributor activated the gate locally, and carries the first-execution cost the study records beside its steady-state budget. Every artefact under `docs/commit-gate/` is refreshed to the bytes receipted at this step's entry: the study and runbook so they carry every amendment recorded up to that point, and the design record with its reports so the shipped record holds no row the controller has since resolved. The study copy keeps its five rewritten phase-skill link targets and differs from its source in nothing else. Proved by `python3 -m unittest tests.test_commit_gate -v` at exit zero in an activated checkout and `python3 scripts/run_checks.py --full` at exit zero on the committed tree. The refresh is proved inside that suite rather than in prose, by assertions a fresh clone can run without reading anything outside the repository. Complete replacement Files: `tests/test_commit_gate.py`, `AGENTS.md`, `docs/decisions/draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md`, `docs/commit-gate/study.md`, `docs/commit-gate/runbook.md`, `docs/commit-gate/design-evidence.json`, `docs/commit-gate/reports/`, `.horos/boundary.json`. Complete replacement Tests: `tests/test_commit_gate.py` gains `ActivationTests`: an unset `core.hooksPath` fails and the message names the activation command; a value pointing at another directory fails the same way; the tracked directory holds an executable `pre-commit`; and the assertion reads the checkout's own configuration rather than a fixture's, so it is the shipped checkout it reports on. Expect four cases. It also gains `ShippedCopyTests`, which prove the refresh from inside the repository: `docs/commit-gate/study.md` carries exactly the number of `### Amendment --` headings this step writes into the test as a literal, `docs/commit-gate/runbook.md` carries exactly its own literal count, every `.hexaemeron/` reference in the shipped study is accompanied somewhere in the same file by the mapping to `docs/commit-gate/`, and every report the shipped design record cites resolves under `docs/commit-gate/reports/` at the digest the record names. Expect four cases, eight in the file's new work for this step. Step audit runner contract is test command `python3 tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-857-step-4.json`.

**Why.** Re-issues step 4's Exit, Files and Tests unchanged, for the fifth time. The study amendment above corrects the report count that step 4 round 1 raised as S4-R1-05, and correcting it changed the study digest this step's contract was recorded against, which unbinds the contract from the worker packet. That ordering rule has now cost this run five re-issues, and the correction was still worth taking: the count sits in the paragraph a reader uses to resolve a `.hexaemeron/` citation into the shipped tree, and step 4's own refresh is what made it wrong. The content here is identical to the previous issue; only its binding is new. The shipped study copy must now carry nine amendment blocks rather than eight, which is a literal the step's `ShippedCopyTests` holds.

**Steps touched.** Step 4.

**Still holding.** Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Files: `docs/commit-gate/demonstration.md`, `docs/commit-gate/runbook.md`, `.githooks/README.md`, `.horos/boundary.json`. One addition to the Exit, leaving every existing clause as it stands: `.githooks/README.md` no longer says the visibility assertion is still to come. Its paragraph on an unactivated checkout describes what the shipped assertion does, rather than promising it with a future step, and the demonstration record's first acceptance condition is the observed run that shows it.

**Why.** Audit finding S4-R1-03, low, raised in step 4 round 1 and re-confirmed in rounds 3 and 4. `.githooks/README.md:16-18` says "That assertion arrives with step 4 of the run behind this directory. Until it lands, an unactivated checkout stays silent." Both sentences became false at commit 0cf49808, which is step 4's own first commit, and round 4 measured the opposite in a fresh clone at 21fb29ad: four cases, one failure, its message carrying the literal activation command. Step 4 could not correct it, because the file is untouched by that step's whole diff and sits outside its eight-path Files list, so the finding closed that phase open and named. It belongs here rather than in a step of its own: this step's subject is what a contributor meets on a clone that has never seen the gate, and that README is the first thing such a reader opens after being sent to the directory. The demonstration this step records drives the same assertion from a fresh clone, so the correction and the evidence for it land together.

**Steps touched.** Step 5.

**Still holding.** Step 5: entry holds; exit holds.

### Amendment -- 2026-09-06

**What changed.** Complete replacement Exit: `docs/commit-gate/demonstration.md` records one run of the demo path against a clone of the run branch made into a fresh directory: the root suite refused before activation and the transcript shows the activation command in its output; the activation command was run once; `.githooks/greenlight` recorded a green; a commit of that tree succeeded; a file was then edited and the next commit was refused; and `FIAT_SKIP_PRECOMMIT=1` let that same commit through. Each of the five acceptance conditions is answered with the exact command and its exit code, and anything the run could not establish is named. Proved by `python3 -m unittest tests.test_commit_gate -v` at exit zero and `python3 scripts/run_checks.py --full` at exit zero on the committed tree. Additionally, `.githooks/README.md` no longer says the visibility assertion is still to come: its paragraph on an unactivated checkout describes what the shipped assertion does, rather than promising it with a future step, and the demonstration record's second acceptance condition is the observed run that shows it. Complete replacement Files: `docs/commit-gate/demonstration.md`, `docs/commit-gate/runbook.md`, `.githooks/README.md`, `.horos/boundary.json`.

**Why.** Audit finding S5-R1-04, low, from step 5 round 1. The amendment of 2026-09-05 ended its Exit addition "the demonstration record's first acceptance condition is the observed run that shows it", and the study fixes the numbering at `docs/commit-gate/study.md:61-62`: condition 1 is "where the gate lives", proved by the decision record, and condition 2 is "survives a clone and absence is visible", proved by a fresh clone with no activation failing the root suite with a message naming the one activation command. The second is the condition the README paragraph describes; the first is a different subject. As numbered, the clause asked the step to satisfy something the study assigns elsewhere, and the step satisfies its substance at condition 2, which the round measured in its own independent reproduction. The shipped runbook copy is byte-identical to this source, so no byte on the step branch can carry the correction. The baseline Exit is restated unchanged above so the replacement is complete rather than a fragment.

**Steps touched.** Step 5.

**Still holding.** Step 5: entry holds; exit holds.
