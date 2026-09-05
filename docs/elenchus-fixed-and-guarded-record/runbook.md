# Runbook: Elenchus emits the fixed-and-guarded result as a structured record

Derived from `.hexaemeron/study.md`. Three steps, in dependency order. Each one
is a single pull request whose entry and exit states are both green.

Assuming, unless corrected:

1. The pinned interpreter the repository already uses, with stdlib `unittest`
   and no dependency outside the standard library.
2. `python3 scripts/run_checks.py --base origin/main` is the root suite, and a
   step is not finished until it exits zero on the committed tree.
3. `elenchus.py`'s command-line interface, its defaults and its four state
   strings do not change in this run.
4. Decision-record numbers are assigned at merge under ADR-077, so the draft
   lands numberless and takes its number immediately before the run's
   integration push.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 2f5de1b70a60b60c4bb4d775f65e11df05f465e9c8970fbefdebf6f395d776bb
candidate | skill-emitter
```

## Step 1: Land the specification and the emitter

**Goal.** Commit the run documents and the numberless decision draft, and add
the emitter and its test module beside `elenchus.py`.

**Entry.** Clean run branch `fiat/1275-elenchus-emits-the-fixed-and-guarded-result`
at `0fefcc986107ed66ff43c6572b7aa1c7351f12f4`, with `elenchus.py` and
`test_elenchus_checker.py` present and green.

**Exit.** `docs/elenchus-fixed-and-guarded-record/study.md` and
`docs/elenchus-fixed-and-guarded-record/runbook.md` are byte-identical to the
controller artefacts. `plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py`
reads a draft and an `elenchus.py --format json` result and writes one closed
`elenchus-fixed-and-guarded/v1` record holding the nine fields named in the
study, refusing an unknown key, an over-cap or non-printable text field, a
guard naming a test absent from the repair's changed test files, an output path
that is not a symlink-free relative worktree descendant, and any verdict other
than `guarded`; `--check` validates a record on its own. The record is staged
and renamed into place, so an interrupted emit leaves no file `--check`
accepts. The numberless draft at
`docs/decisions/drafts/emit-the-fixed-and-guarded-result-as-a-closed-record.md`
records the nine-field shape, its derivation from the Promise's two clauses,
what the record does not establish, and why the schema carries no cross-record
identifier. `elenchus.py` is unchanged. Proved by
`python3 -m unittest plugins.hexaemeron.tests.test_elenchus_fixed_and_guarded`
and `python3 scripts/run_checks.py --base origin/main`, both at exit zero on the
committed tree.

**Files.** `docs/elenchus-fixed-and-guarded-record/study.md`,
`docs/elenchus-fixed-and-guarded-record/runbook.md`,
`docs/decisions/drafts/emit-the-fixed-and-guarded-result-as-a-closed-record.md`,
`plugins/hexaemeron/skills/elenchus/scripts/fixed_and_guarded.py`,
`plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py`, and
`.horos/boundary.json` only if the tracked-file count requires it.

**Tests.** `plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py` is new
and covers the closed key set, each refusal path named in the exit, the staged
rename under an interrupted write, and one accepted record. Existing
decision-record, documentation, Horos-boundary and root checks stay green, and
`test_elenchus_checker.py` is not edited. Step audit runner contract is test
command `python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-1275-step-1.json`.

**Disciplines.** phylax: the emitter opens two untrusted input paths, the draft
JSON and the result JSON, and one filesystem write boundary, so bounded strict
parsing with a closed key set, a duplicate-key refusal and a symlink-free
relative destination are this step's controls. ephoros: Warden runs the emitter
inside an unattended Fiat audit round, so every refusal names its rule and its
field on stderr and exits non-zero rather than writing a partial record. metron:
none, this step makes no performance claim. elenchus: none, no failure is in
hand. hypomnema: the nine-field shape and the absence of a cross-record
identifier are expensive to reverse once records exist, so the numberless draft
is their home.

## Step 2: Document the emission and record the generation row

**Goal.** Give the emitter a section in the skill that owns it, and add the
`elenchus-v1.4.0` generation row.

**Entry.** Step 1's exit state, with the emitter and its tests committed.

**Exit.** `plugins/hexaemeron/skills/elenchus/SKILL.md` carries one new section
that names the emitter, its two inputs, its output, the nine fields, the four
refusals a caller meets most, and what an emitted record does not establish;
`## Hand back` gains one sentence pointing at it, and no other section changes.
`plugins/hexaemeron/skills/elenchus/EVOLUTION.md` carries `elenchus-v1.4.0` as
current version and one new `generation` history row whose frontier revision
`observed-failure-root-cause`, frontier SHA-256
`08e77bae576b3351d6f38e60ce9da88327014bcaa7459e319b8e51d79caeda8b`,
`Frontier status: mature` and `Next Fiat job: None -- mature` are byte-identical
to `elenchus-v1.3.0`. Proved by
`python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/elenchus/SKILL.md`
reporting clean, and by
`python3 scripts/run_checks.py --base origin/main` at exit zero on the committed
tree.

**Files.** `plugins/hexaemeron/skills/elenchus/SKILL.md`,
`plugins/hexaemeron/skills/elenchus/EVOLUTION.md`.

**Tests.** `plugins.hexaemeron.tests.test_evolution` covers the row's axis
arithmetic and retained frontier line and is not edited. No new executable
behaviour is added, so no new test module is written; the emitter's own suite
from step 1 stays green. Step audit runner contract is test command
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-1275-step-2.json`.

**Disciplines.** phylax: none, this step adds no input, process or write
boundary. ephoros: none, no unattended behaviour starts here. metron: none, no
performance claim is made. elenchus: none, no failure is in hand. hypomnema: the
ledger row is the ledger's own durable record of a behaviour change, and the
skill section is the runbook the emitter's callers read.

## Step 3: Demonstrate the record end to end

**Goal.** Run the demo path from the study's problem statement and write down
what it produced.

**Entry.** Step 2's exit state, with the emitter, its section and the ledger row
committed.

**Exit.** `docs/elenchus-fixed-and-guarded-record/demonstration.md` records one
end-to-end run against a scratch repository the test harness builds: a repaired
failure whose record `--check` accepts, and the same record with one evidence
field removed and again with a verdict other than `guarded`, each refused with
the rule and the field named. The demonstration states the commands, their exit
codes and the exact refusal text, and says what the record does not establish.
Proved by `python3 -m unittest plugins.hexaemeron.tests.test_elenchus_fixed_and_guarded`
and `python3 scripts/run_checks.py --base origin/main`, both at exit zero on the
committed tree.

**Files.** `docs/elenchus-fixed-and-guarded-record/demonstration.md`,
`plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py`.

**Tests.** The existing test module gains the end-to-end case that builds the
scratch repository, repairs the failure, emits the record and asserts both the
acceptance and the two refusals, so the demonstration is reproduced by the suite
rather than only by hand. Step audit runner contract is test command
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-1275-step-3.json`.

**Disciplines.** phylax: the scratch repository is built by the test harness
inside a temporary directory and no path outside it is written, which is the
control this step needs. ephoros: none, the demonstration is run on demand and
nothing new starts running unattended. metron: none, no performance claim is
made. elenchus: the demonstration is exactly the reproduce-and-guard shape the
skill describes, so its recorded run follows that procedure rather than a
narrative of it. hypomnema: none, the demonstration records an observation and
reverses no decision.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Tests: `plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py` is new and covers the closed key set, each refusal path named in the exit, the staged rename under an interrupted write, and one accepted record. Existing decision-record, documentation, Horos-boundary and root checks stay green, and `test_elenchus_checker.py` is not edited. Step audit runner contract is test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-1275-step-1.json`. That runner is the one that reaches this step's tests: `tests/run_tests.py` discovers only the `tests/` directory, so it collects nothing under `plugins/hexaemeron/tests/` and cannot observe the guard a fix to this step claims. The report path must be fresh; a missing, stale, empty, malformed or infrastructure-failed report is `inconclusive` rather than evidence that a repair is guarded.

**Why.** Warden finding S1-R1-06 in round 1 of step 1, restated in round 2. The declared runner could not collect this step's tests, so round 2's `guarded` verdict rested on two failures in the boundary tests rather than on the emitter's own module. The replacement names the runner whose discovery root contains that module, which I confirmed by reading both runners' `discover` calls rather than from the report.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Tests: `plugins.hexaemeron.tests.test_evolution` covers the row's axis arithmetic and retained frontier line and is not edited. No new executable behaviour is added, so no new test module is written; the emitter's own suite from step 1 stays green. Step audit runner contract is test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-1275-step-2.json`. That runner is the one that reaches this step's tests: `tests/run_tests.py` discovers only the `tests/` directory, so it collects nothing under `plugins/hexaemeron/tests/` and cannot observe the guard a fix to this step claims. The report path must be fresh; a missing, stale, empty, malformed or infrastructure-failed report is `inconclusive` rather than evidence that a repair is guarded.

**Why.** Warden finding S1-R1-06, which names a defect in the runner contract every step of this runbook declared, not one peculiar to step 1. Step 2's tests are `plugins.hexaemeron.tests.test_evolution` and the step-1 emitter suite, both under `plugins/hexaemeron/tests/`, so the same replacement applies before the step is built.

**Steps touched.** Step 2.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-05

**What changed.** Complete replacement Tests: The existing test module gains the end-to-end case that builds the scratch repository, repairs the failure, emits the record and asserts both the acceptance and the two refusals, so the demonstration is reproduced by the suite rather than only by hand. Step audit runner contract is test command `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format `elenchus.unittest.v1`, report file `.elenchus/fiat-1275-step-3.json`. That runner is the one that reaches this step's tests: `tests/run_tests.py` discovers only the `tests/` directory, so it collects nothing under `plugins/hexaemeron/tests/` and cannot observe the guard a fix to this step claims. The report path must be fresh; a missing, stale, empty, malformed or infrastructure-failed report is `inconclusive` rather than evidence that a repair is guarded.

**Why.** Warden finding S1-R1-06, applied to the last step for the same reason as the first two. Step 3 extends `plugins/hexaemeron/tests/test_elenchus_fixed_and_guarded.py`, which the previously declared runner does not collect, so a fix during its audit would have been graded against a suite that never ran the case it repaired.

**Steps touched.** Step 3.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
