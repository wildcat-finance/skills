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
