# Runbook: bind delegated task identity to step and role

Three steps build `envelope-identity` from the study at `.hexaemeron/study.md`.
Step 1 builds the value and its grammar with nothing wired in. Step 2 puts it on
the envelope and adds the refusal. Step 3 binds the prose, the conformance
evidence and the digest cascade the controller edit forces.

Each step is green at both ends: the root suite and the Hexaemeron suite pass
before it opens and after it closes. Three lints are not CI, so every Exit names
both suites.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 59fb40505301c90732cc7def91b629fddff00ac2b24437bf3bbac9c900ad2d59
candidate | envelope-identity
```

## Step 1: Build the task identity value and its grammar

**Goal.** Add the pure functions that derive a `fiat-task-identity/v1` object
and its `fiat-<task>-<phase>-<role>` handle from controller state, plus the
bounded reader that accepts or refuses an observed handle string. Nothing calls
them yet.

**Entry.** Main at the run's recorded base, root suite and Hexaemeron suite
green, no `task_identity` symbol in the tree.

**Exit.** `hexctl.py` carries the derivation and the comparison as pure
functions with no clock, pid, hostname or absolute path in their output, and
identical state yields identical bytes. The observed-handle reader accepts at
most 200 bytes, refuses control and whitespace characters, compares by exact
equality only, and never echoes an unbounded string in a diagnostic. A run with
no task issue derives `<task>` from the 48-character topic slug and never
fabricates an issue number. Prove the green exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_task_identity -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
git diff --check
```

**Files.** Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`. Create
`plugins/hexaemeron/tests/test_task_identity.py`. Touch no receipt, no ledger
and no digest record; the cascade belongs to Step 3.

**Tests.** `test_task_identity` covers the grammar for an issue-backed run and a
topic-only run, the `study` and `step-<n>` phases, all four roles, round held in
the object and absent from the handle, byte-identical output across two
processes, and refusal of an oversized, control-bearing or whitespace-bearing
observed handle.

**Disciplines.** phylax: the observed handle is untrusted argv, so bound it,
reject control characters and never echo it unbounded. ephoros: a refusal names
which of length, character class or equality failed. metron: none; no speed
claim is made. elenchus: any failure works to its cause before the step closes.
hypomnema: the grammar's rationale is a comment on the deriving function, not a
decision record.

## Step 2: Put the identity on the envelope and refuse a stale handle

**Goal.** Emit `task_identity` beside `agent` on every delegated envelope, and
make `next --task-handle <observed>` exit 2 before printing when the observed
handle differs, is malformed, or the directive has no delegate.

**Entry.** Step 1 merged and verified green; the derivation exists and nothing
calls it.

**Exit.** Every envelope carrying a non-null `agent` carries `task_identity`;
an inline directive carries `agent: null` and refuses `--task-handle` with a
named diagnostic rather than accepting it silently. The four pinned brief key
sets are unchanged, because the identity sits at the envelope level. A Warden
continued across the rounds of one step sees the same handle, and a step change
refuses. Refusal exits 2 before any directive bytes reach stdout, and writes no
state and no ledger entry. Prove the green exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_task_identity plugins.hexaemeron.tests.test_hexctl -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
git diff --check
```

**Files.** Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`,
`plugins/hexaemeron/tests/test_task_identity.py`,
`plugins/hexaemeron/tests/test_hexctl.py` and
`plugins/hexaemeron/tests/test_version_relations.py`, whose literal directive
comparison gains the new key. Create nothing. The digest cascade stays in
Step 3.

**Tests.** Cases cover a delegated envelope carrying the object, an inline
directive carrying nulls, `--task-handle` matching and exiting 0, differing and
exiting 2 with nothing printed, malformed and refused, supplied against an
inline directive and refused, the same handle across two rounds of one step, a
different handle across two steps, and identical envelope bytes before and
after a checkpoint restore.

**Disciplines.** phylax: refuse before printing, so a stale handle never sees a
brief. ephoros: the refusal names the expected and observed handles within their
byte bound. metron: `next` stays inside its wall-clock budget, measured at
Step 3. elenchus: a red literal-dict comparison is repaired at its cause rather
than loosened. hypomnema: the envelope change earns a comment where the key is
added, not a record of its own.

## Step 3: Bind the prose, the conformance evidence and the digest cascade

**Goal.** Make the contract unconditional in the prose the orchestrator reads,
produce the three `step:3` conformance reports, and re-pin every digest the
controller edit moved.

**Entry.** Step 2 merged and verified green; the behaviour exists and no
document requires it.

**Exit.** Fiat `SKILL.md` states that the orchestrator runs the handle check
before continuing any existing handle, unconditionally, and the four agent files
name the identity they are spawned under. `.hexaemeron/resolve_conformance.py`
produces `stale-handle-regression-guarded`, `resume-identity-reproducible` and
`next-wall-clock-bound`, the last as the median of five `next` runs at most
1000 ms. Every digest the `hexctl.py` edit moved is re-pinned in this step:
`tests/promise_machine_coverage.json`, the evaluation run record recomputed from
its committed answers rather than a fresh model run, both demonstration records,
and the Horos boundary and census. Prove the green exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_task_identity plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md --max-defects 0
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write
git diff --check
```

**Files.** Change `plugins/hexaemeron/skills/fiat/SKILL.md`,
`plugins/hexaemeron/agents/surveyor.md`,
`plugins/hexaemeron/agents/mason.md`, `plugins/hexaemeron/agents/warden.md`,
`plugins/hexaemeron/agents/scribe.md`, `plugins/hexaemeron/tests/test_fiat_skill.py`,
`tests/promise_machine_coverage.json`,
`docs/promise-machine/obligation-gates/evaluation-run.json`,
`docs/promise-machine/obligation-gates/demonstration-run.json`,
`docs/promise-machine/obligation-gates/demonstration-evidence.md`,
`.horos/boundary.json` and `.horos/census.json`.

**Tests.** `test_fiat_skill` pins that the SKILL.md sentence makes the check
unconditional before any continuation, and that each agent file names its
identity. The conformance resolver writes only to its `--out` path and runs each
check as a no-shell subprocess. The evaluation record is re-tallied with
`tests/promise_evaluation_driver.py` from its committed answers, keeping the
recorded model string and date, and packets emitted from the base and from this
tree are proved to differ in `tree_sha256` alone before that reuse is accepted.

**Disciplines.** phylax: the resolver takes no shell and writes one path.
ephoros: the wall-clock measurement records its five samples, not only a median.
metron: the 1000 ms budget is measured before and after, on the same machine.
elenchus: a red digest test is repaired by recomputing the record, never by
loosening the assertion. hypomnema: the frontier ledger row is owed at
integration and is not written here.

### Amendment -- 2026-09-13

**What changed.**

Complete replacement Files: Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `tests/promise_machine_coverage.json`, `docs/promise-machine/obligation-gates/evaluation-run.json`, `docs/promise-machine/obligation-gates/demonstration-run.json`, `docs/promise-machine/obligation-gates/demonstration-evidence.md`, `.horos/boundary.json` and `.horos/census.json`. Create `plugins/hexaemeron/tests/test_task_identity.py`. Touch no file under `plugins/hexaemeron/agents/` and not `plugins/hexaemeron/skills/fiat/SKILL.md`; the prose contract remains Step 3.

Complete replacement Exit: `hexctl.py` carries the derivation and the comparison as pure functions with no clock, pid, hostname or absolute path in their output, and identical state yields identical bytes. The observed-handle reader accepts at most 200 bytes, refuses control and whitespace characters, compares by exact equality only, and never echoes an unbounded string in a diagnostic. A run with no task issue derives `<task>` from the 48-character topic slug and never fabricates an issue number. Every digest the `hexctl.py` edit moved is re-pinned in this step, because the root suite reads them and a step is green at both ends: the coverage pin, the evaluation run record recomputed from its committed answers rather than a fresh model run, both demonstration records, and the Horos boundary and census. Prove the green exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_task_identity -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write
git diff --check
```

**Why.** The runbook deferred the whole digest cascade to Step 3, but the cascade is a consequence of editing `hexctl.py`, and Step 1 edits it. `tests/promise_machine_coverage.json` pins that file's whole-file SHA-256, so the edit reddens `test_unique_identifiers` and its two siblings the moment it lands. Measured on 2026-09-13 against the staged Step 1 tree: `test_unique_identifiers` failed while `scripts/promise_machine.py check` still reported clean, which is the first stage of the chain only. A step that cannot pass the root suite at its own exit is not green at both ends, so the cascade is paid where the edit happens.

**Steps touched.** Step 1

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-13

**What changed.**

Complete replacement Files: Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `tests/promise_machine_coverage.json`, `docs/promise-machine/obligation-gates/evaluation-run.json`, `docs/promise-machine/obligation-gates/demonstration-run.json`, `docs/promise-machine/obligation-gates/demonstration-evidence.md`, `.horos/boundary.json`, `.horos/candidates.json` and `.horos/census.json`. Create `plugins/hexaemeron/tests/test_task_identity.py`, `docs/fiat-delegated-task-identity-study.md` and `docs/fiat-delegated-task-identity-runbook.md`, the last two as byte copies of `.hexaemeron/study.md` and `.hexaemeron/runbook.md`. Touch no file under `plugins/hexaemeron/agents/` and not `plugins/hexaemeron/skills/fiat/SKILL.md`; the prose contract remains Step 3.

Complete replacement Exit: `hexctl.py` carries the derivation and the comparison as pure functions with no clock, pid, hostname or absolute path in their output, and identical state yields identical bytes. The observed-handle reader accepts at most 200 bytes, refuses whitespace and non-printable characters, lone surrogates included, without raising, compares by exact equality only, and never echoes an unbounded string in a diagnostic. A run with no task issue derives `<task>` from the 48-character topic slug, prefixed `topic-` when the slug is digits alone, and never fabricates an issue number. Every digest the `hexctl.py` edit moved is re-pinned in this step, because the root suite reads them and a step is green at both ends: the coverage pin, the evaluation run record recomputed from its committed answers rather than a fresh model run, both demonstration records, and the Horos artefacts. The two committed copies are byte-identical to the canonical study and runbook and pass Hypomnema. Prove the green exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_task_identity -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
cmp .hexaemeron/study.md docs/fiat-delegated-task-identity-study.md
cmp .hexaemeron/runbook.md docs/fiat-delegated-task-identity-runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/fiat-delegated-task-identity-study.md docs/fiat-delegated-task-identity-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write
git diff --check
```

Complete replacement Tests: `test_task_identity` covers the grammar for an issue-backed run and a topic-only run, a digits-only topic slug taking the `topic-` prefix, the `study` and `step-<n>` phases, all four roles, round held in the object and absent from the handle, byte-identical output across two processes, and refusal of an oversized, control-bearing, whitespace-bearing, non-printable or lone-surrogate observed handle, without raising and without echoing it. The audit-fix runner is `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `.elenchus/fiat-363-step-1.json`; a guard under the root `tests/` uses `python3 tests/run_tests.py --elenchus-report {report}` with the same format and report file.

**Why.** Step 1 audit round 1 recorded S1-R1-05 and S1-R1-06 in `audit/rounds/fiat-363-bind-delegated-task-identity-to-step-and-rol.md`. Step 1 declared no runner, report format or report file, so the Elenchus check of fixes commit `370866012205b6d0378e656ecc089b390b435db4` returned `inconclusive`. No step created the copies study decision 12.3 assigns to Step 1. The Exit and Tests also carry the reader rules that commit introduced for S1-R1-01 and S1-R1-03 and the slug rule for S1-R1-02, which the study amendment of 2026-09-13 records. `.horos/candidates.json` is listed because adding the copies can move it.

**Steps touched.** Step 1

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-13

**What changed.**

Complete replacement Files: Change `plugins/hexaemeron/skills/fiat/scripts/hexctl.py`, `plugins/hexaemeron/tests/test_task_identity.py`, `plugins/hexaemeron/tests/test_hexctl.py`, `plugins/hexaemeron/tests/test_version_relations.py`, whose literal directive comparison gains the new key, `tests/promise_machine_coverage.json`, `docs/promise-machine/obligation-gates/evaluation-run.json`, `docs/promise-machine/obligation-gates/demonstration-run.json`, `docs/promise-machine/obligation-gates/demonstration-evidence.md`, `.horos/boundary.json`, `.horos/candidates.json` and `.horos/census.json`. Refresh `docs/fiat-delegated-task-identity-study.md` and `docs/fiat-delegated-task-identity-runbook.md` from `.hexaemeron/study.md` and `.hexaemeron/runbook.md` when an amendment has moved either. Create nothing.

Complete replacement Exit: Every envelope carrying a non-null `agent` carries `task_identity`; an inline directive carries `agent: null` and refuses `--task-handle` with a named diagnostic rather than accepting it silently. The four pinned brief key sets are unchanged, because the identity sits at the envelope level. A Warden continued across the rounds of one step sees the same handle, and a step change refuses. Refusal exits 2 before any directive bytes reach stdout, and writes no state and no ledger entry. Every digest the `hexctl.py` edit moved is re-pinned in this step: the coverage pin, the evaluation run record recomputed from its committed answers rather than a fresh model run, both demonstration records, and the Horos artefacts. The two committed copies are byte-identical to the canonical study and runbook. Prove the green exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_task_identity plugins.hexaemeron.tests.test_hexctl -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
cmp .hexaemeron/study.md docs/fiat-delegated-task-identity-study.md
cmp .hexaemeron/runbook.md docs/fiat-delegated-task-identity-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write
git diff --check
```

Complete replacement Tests: Cases cover a delegated envelope carrying the object, an inline directive carrying nulls, `--task-handle` matching and exiting 0, differing and exiting 2 with nothing printed, malformed and refused, supplied against an inline directive and refused, the same handle across two rounds of one step, a different handle across two steps, and identical envelope bytes before and after a checkpoint restore. The audit-fix runner is `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `.elenchus/fiat-363-step-2.json`; a guard under the root `tests/` uses `python3 tests/run_tests.py --elenchus-report {report}` with the same format and report file.

**Why.** S1-R1-05 in `audit/rounds/fiat-363-bind-delegated-task-identity-to-step-and-rol.md` applies to every step: with no declared runner, report format and report file, each Step 2 fix would classify `inconclusive`. Step 2 also edits `hexctl.py`, whose whole-file SHA-256 `tests/promise_machine_coverage.json` pins, so any Step 2 edit to it reddens the root suite until the digest cascade is re-pinned, the same cascade the earlier amendment to Step 1 moved into Step 1. The refresh keeps the copies study decision 12.3 requires byte-identical after any later amendment.

**Steps touched.** Step 2

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.

### Amendment -- 2026-09-13

**What changed.**

Complete replacement Files: Change `plugins/hexaemeron/skills/fiat/SKILL.md`, `plugins/hexaemeron/agents/surveyor.md`, `plugins/hexaemeron/agents/mason.md`, `plugins/hexaemeron/agents/warden.md`, `plugins/hexaemeron/agents/scribe.md`, `plugins/hexaemeron/tests/test_fiat_skill.py`, `tests/promise_machine_coverage.json`, `docs/promise-machine/obligation-gates/evaluation-run.json`, `docs/promise-machine/obligation-gates/demonstration-run.json`, `docs/promise-machine/obligation-gates/demonstration-evidence.md`, `.horos/boundary.json`, `.horos/candidates.json` and `.horos/census.json`. Create one unnumbered decision record draft under `docs/decisions/drafts/` for study decisions 12.1 and 12.2. Refresh `docs/fiat-delegated-task-identity-study.md` and `docs/fiat-delegated-task-identity-runbook.md` from `.hexaemeron/study.md` and `.hexaemeron/runbook.md` when an amendment has moved either.

Complete replacement Exit: Fiat `SKILL.md` states that the orchestrator runs the handle check before continuing any existing handle, unconditionally, and the four agent files name the identity they are spawned under. `.hexaemeron/resolve_conformance.py` produces `stale-handle-regression-guarded`, `resume-identity-reproducible` and `next-wall-clock-bound`, the last as the median of five `next` runs at most 1000 ms. Every digest the `hexctl.py` edit moved is re-pinned in this step: `tests/promise_machine_coverage.json`, the evaluation run record recomputed from its committed answers rather than a fresh model run, both demonstration records, and the Horos boundary and census. The decision record draft states the handle grammar, including the `topic-` prefix for a digits-only topic slug, and the envelope-level placement with its accepted signal gap. The two committed copies are byte-identical to the canonical study and runbook. Prove the green exit with:

```bash
python3 -m unittest plugins.hexaemeron.tests.test_task_identity plugins.hexaemeron.tests.test_hexctl plugins.hexaemeron.tests.test_fiat_skill -v
python3 plugins/hexaemeron/tests/run_tests.py
python3 -m unittest discover -s tests
python3 scripts/promise_machine.py check
python3 scripts/portable_promise_machine.py sync
python3 scripts/portable_promise_machine.py check
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents plugins docs
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/fiat/SKILL.md --max-defects 0
cmp .hexaemeron/study.md docs/fiat-delegated-task-identity-study.md
cmp .hexaemeron/runbook.md docs/fiat-delegated-task-identity-runbook.md
python3 plugins/horos/skills/horos/scripts/horos.py scan . --write
python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write
git diff --check
```

Complete replacement Tests: `test_fiat_skill` pins that the SKILL.md sentence makes the check unconditional before any continuation, and that each agent file names its identity. The conformance resolver writes only to its `--out` path and runs each check as a no-shell subprocess. The evaluation record is re-tallied with `tests/promise_evaluation_driver.py` from its committed answers, keeping the recorded model string and date, and packets emitted from the base and from this tree are proved to differ in `tree_sha256` alone before that reuse is accepted. The audit-fix runner is `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`, report format `unittest-json-v1`, report file `.elenchus/fiat-363-step-3.json`; a guard under the root `tests/` uses `python3 tests/run_tests.py --elenchus-report {report}` with the same format and report file.

**Why.** S1-R1-05 in `audit/rounds/fiat-363-bind-delegated-task-identity-to-step-and-rol.md` applies to Step 3's fixes as well. Study decisions 12.1 and 12.2 name one decision record under `docs/decisions/` as their home, and no step created it; the `topic-` prefix fixed for S1-R1-02 is part of the grammar that record carries. The refresh keeps the copies study decision 12.3 requires byte-identical through integration.

**Steps touched.** Step 3

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
