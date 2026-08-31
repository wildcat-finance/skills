# Runbook: stage the portable sync before the Horos scan and check mirror import closure

Derived from `.hexaemeron/study.md`, receipted at the start of this run. The
study's two defects are independent and get one step each, between a scaffold
step that commits the spec and a demonstration step that runs the study's demo
path and records the decision.

Every step ends green. The exit commands below are the whole gate; a step whose
exit command does not pass is not finished.

The Elenchus runner contract is the same for all four steps, because the
repository has one checked runner and every fix in this run is Python under it:

- Test command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`
- Report format: `unittest-json-v1`
- Expected report schema: `elenchus.unittest.v1`
- Report file: `.elenchus/fiat-854-step-<N>.json`, fresh per step

The report path must not already exist when the runner is called. A missing,
stale, empty or malformed report is `inconclusive`, not evidence that a repair
is guarded.

## Step 1: Commit the study and the runbook

**Goal.** Put the receipted spec in the repository so every later step can be
reviewed against a document a reader can open.

**Entry.** The run branch `fiat/854-stage-the-portable-sync-before-the-horos-sca`
at `4fe374dd33d43b86d800abe9240d62e09ed7d395`, the tip of `origin/main` when the
run was cut.

**Exit.** `docs/portable-sync-boundary-order-study.md` and
`docs/portable-sync-boundary-order-runbook.md` exist and are byte-identical to
the receipted artefacts in `.hexaemeron/`. The committed boundary describes the
tree that now holds them. Proved by:
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/portable-sync-boundary-order-study.md docs/portable-sync-boundary-order-runbook.md`,
`python3 plugins/hexaemeron/tests/run_tests.py`,
`python3 -m unittest discover -s tests`,
`python3 scripts/portable_promise_machine.py check`,
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
and `git diff --check`, each exiting 0.

**Files.** `docs/portable-sync-boundary-order-study.md`,
`docs/portable-sync-boundary-order-runbook.md`, `.horos/boundary.json`.

**Tests.** No new test. The existing suites must stay green, and
`tests/test_boundary_currency.py::test_the_committed_boundary_matches_a_fresh_scan`
is the one that notices if the boundary was not regenerated after the two
documents landed. Runner contract as declared above, report file
`.elenchus/fiat-854-step-1.json`.

**Disciplines.** phylax: none, the step adds two documents and opens no
boundary. ephoros: none, nothing here runs unattended. metron: none, no
performance claim. elenchus: none, no failure in hand at entry. hypomnema: this
step is Hypomnema's own output, the spec landing where a reader finds it, and
it earns no separate record.

## Step 2: Stage the mirror the sync writes

**Goal.** Make the obvious order correct, so that `sync` followed directly by
`scan --write` leaves a boundary that describes the tree.

**Entry.** The step 1 branch at its exit state, with the spec committed and all
suites green.

**Exit.** `sync` stages exactly the mirror directory after replacing it, through
the existing `_git_environment()`, with a fixed pathspec naming
`.agents/skills/promise-machine/runtime` and nothing else. Where the root is not
a git work tree, staging is skipped, `sync` says so on stdout and still exits 0.
A new test drives the study's obvious order over a temporary repository and
requires the boundary to match a fresh scan without any manual staging between
the two commands; that test fails against the entry tree and passes against the
exit tree, and the red result is recorded before the fix. Proved by:
`python3 plugins/hexaemeron/tests/run_tests.py`,
`python3 -m unittest discover -s tests`,
`python3 scripts/portable_promise_machine.py sync`,
`python3 scripts/portable_promise_machine.py check`,
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
and `git diff --check`, each exiting 0.

**Files.** `scripts/portable_promise_machine.py`,
`tests/test_portable_skills.py`, `.horos/boundary.json`.

**Tests.** Four new cases, all over a temporary git repository so the outer
index is never touched: the obvious order leaves no boundary drift; the staging
pathspec covers the mirror and leaves an unrelated unstaged file unstaged; a
mirror file deleted by a later sync is staged as a deletion; and a root that is
not a git work tree skips staging, prints its reason and exits 0. Expected
count: four added. Runner contract as declared above, report file
`.elenchus/fiat-854-step-2.json`.

**Disciplines.** phylax: this step opens a write to the git index, which is the
only new boundary in the run, and it carries the fixed pathspec, the stripped
environment and the skip-rather-than-fail control. ephoros: the skip path prints
its reason, because a copy-mode user who reads a silent success as a staged
sync has been misled. metron: none, no performance claim and no change made in
the name of speed. elenchus: the ordering defect is a failure in hand, so the
fix arrives with a case that fails without it. hypomnema: that `sync` writes to
the index is expensive to reverse and earns a record, written in step 4 with
the run's other decision.

## Step 3: Refuse a mirror that loses an import its source resolved

**Goal.** Make `check` fail when a mirrored source's relative import resolves in
the canonical source and not in the mirror.

**Entry.** The step 2 branch at its exit state, with the ordering fix landed and
all suites green.

**Exit.** `check` resolves every relative import in the mirrored sources against
both the mirror and the canonical source, and refuses when a target resolves in
the source but not in the mirror, naming the importing mirrored file and the
unresolved target in the message. A target carrying a `..` segment or an
absolute form is refused rather than resolved. The check exits 0 on the tree as
it stands, including the two imports in
`plugins/horos/examples/fixture-sol/Market.sol` that resolve in neither tree.
Proved by:
`python3 plugins/hexaemeron/tests/run_tests.py`,
`python3 -m unittest discover -s tests`,
`python3 scripts/portable_promise_machine.py check`,
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
and `git diff --check`, each exiting 0.

**Files.** `scripts/portable_promise_machine.py`,
`tests/test_portable_skills.py`, `.horos/boundary.json`.

**Tests.** Four new cases over fixture trees: a source whose sibling import
resolves canonically and is missing from the mirror is refused, which is the
skills#329 `IRoleProvider.sol` case reproduced; an import that resolves in
neither tree is accepted, which is the `Market.sol` case; a target containing
`..` is refused without being opened; and the message names both the importing
file and the target. Expected count: four added. Runner contract as declared
above, report file `.elenchus/fiat-854-step-3.json`.

**Disciplines.** phylax: this step reads path strings out of repository files
and decides what to open from them, so the traversal refusal is its control.
ephoros: the refusal names the importing file and the target, which is the
question a reader has at the moment it fires. metron: none, the pass is a
bounded read over files already on disk and no budget gates it. elenchus: the
closure defect is a failure in hand and the fix arrives with a case that fails
without it. hypomnema: that closure is checked differentially rather than
absolutely is expensive to reverse and earns a record, written in step 4.

## Step 4: Run the demo path and record the decision

**Goal.** Show the study's problem statement answered end to end, and write down
the two decisions that would be expensive to reverse.

**Entry.** The step 3 branch at its exit state, with both fixes landed and all
suites green.

**Exit.** The study's demo path runs from the repository root with every command
exiting 0 and no manual staging between `sync` and `scan --write`:

```bash
python3 scripts/portable_promise_machine.py sync
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
git add -A
python3 -m unittest tests.test_boundary_currency -v
python3 scripts/portable_promise_machine.py check
```

One decision record is committed under `docs/decisions/`, carrying both
decisions: that `sync` writes to the git index, and that closure is checked
differentially against the source. Its number is taken immediately before merge
against the highest record on live `origin/main`, and its filename and `# ADR-NNN:`
heading move together. Proved by:
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py <record>`,
`python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py --mode report <record>`,
`python3 -m unittest tests.test_decision_records -v`,
`python3 plugins/hexaemeron/tests/run_tests.py`,
`python3 -m unittest discover -s tests`,
`python3 scripts/portable_promise_machine.py check`,
`python3 plugins/horos/skills/horos/scripts/horos.py check .`,
and `git diff --check`, each exiting 0.

**Files.** `docs/decisions/ADR-NNN-stage-the-portable-sync-and-check-mirror-closure.md`,
`.horos/boundary.json`.

**Tests.** No new test. `tests/test_decision_records.py` is the gate on the
record's number and heading, and it is run against current `origin/main` rather
than against this branch's base, because a free number at authoring time is
stale by the time a pull request lands. Runner contract as declared above,
report file `.elenchus/fiat-854-step-4.json`.

**Disciplines.** phylax: none, the step adds one document and runs commands that
earlier steps already gated. ephoros: none, nothing here runs unattended.
metron: none, the demo path is a correctness demonstration and claims no timing.
elenchus: none expected, and any failure the demo path surfaces is worked to its
cause before the step closes rather than worked around. hypomnema: this step is
Hypomnema's output, the decision record itself.

### Amendment -- 2026-08-30

**What changed.** Complete replacement Exit: `docs/portable-sync-boundary-order-study.md` and `docs/portable-sync-boundary-order-runbook.md` exist and are byte-identical to the receipted artefacts in `.hexaemeron/`, and the committed boundary describes the tree that now holds them. Prove those claims with the complete replacement Tests commands below. Complete replacement Tests: No new test is added. Copy the two receipted artefacts without rewriting them, then run `cmp -s .hexaemeron/study.md docs/portable-sync-boundary-order-study.md`, `cmp -s .hexaemeron/runbook.md docs/portable-sync-boundary-order-runbook.md`, `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/portable-sync-boundary-order-study.md docs/portable-sync-boundary-order-runbook.md`, `python3 scripts/run_checks.py`, `python3 scripts/portable_promise_machine.py check`, `python3 plugins/horos/skills/horos/scripts/horos.py check .`, and `git diff --check`, each exiting 0. The source-bound Elenchus runner contract for any audit repair is exact: test command `python3 tests/run_tests.py --elenchus-report {report}`; report format `unittest-json-v1`; expected report schema `elenchus.unittest.v1`; report file `.elenchus/fiat-854-step-1.json`. The report path must be fresh. A missing, stale, empty, malformed, or infrastructure-failed report is `inconclusive`, not evidence that a repair is guarded.
**Why.** The baseline runbook named `python3 plugins/hexaemeron/tests/run_tests.py` as a step gate. That suite fails on `main` itself, at the run base `4fe374dd` and at the current tip `7e97b519`, with five failures reproduced on a worktree carrying no local changes and filed as wildcat-finance/skills#932. It is also the wrong gate for this run: `tests/check-map-v1.json` maps every path this run touches to the `root-suite` check, and `python3 scripts/run_checks.py --plan` lists `hexaemeron-suite` among its omitted checks for this diff. The replacement names the repository's own declared entrypoint, which selects checks from the diff through that ownership graph and refuses when a changed path has no declared owner, so it is a stricter gate than a hand-listed command rather than a weaker one. The Elenchus runner moves to the root runner `tests/run_tests.py`, which writes the same `elenchus.unittest.v1` schema and owns the paths this run changes.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
