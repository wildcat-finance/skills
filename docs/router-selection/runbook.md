# Runbook: grade router selection, not just router resolution

## Source

Derived from the receipted study at `.hexaemeron/study.md`, sha256
`e4273b0fb93ddeac4844e46c0396481bf08a9f7ac4cc96b06cd5da2bb71e19fe`. That study
is the completed spec; nothing here adds a design decision it does not carry,
and a change to either needs a receipted amendment.

Task issue: [skills#499](https://github.com/wildcat-finance/skills/issues/499).
Base ref: `2477db1352a4099445867216f6fd9a2e84963f3a`. Run branch:
`fiat/499-grade-router-selection-not-just-resolution`.

## The interpreter

Every command below names CPython 3.13.15, the pin in `.python-version`, as the
shim `/Users/kethcode/.local/bin/python3.13`. Obtain it with `uv self update`
to 0.12 or newer, then `uv python install 3.13.15`; a uv older than 0.12 cannot
fetch it. Where a project environment is needed, the form is `uv run --python
3.13.15 python ...`, which writes an untracked `uv.lock` into the checkout.
Every step's exit therefore ends by removing it.

## Scope boundary

The `Files` field of each step is that step's complete scope. No other path may
be created or changed without a receipted amendment to the study. In
particular, no step touches `plugins/hexaemeron/skills/fiat/`: this run owes no
skill ledger row, and a step that edited that directory would also owe a
`fiat-v5.31.1` generation row.

What the run owes instead, all of it in step 1: the
`promise-machine-router-selection` block in `PROMISE_MACHINE.md`, the
`router_selection` capability entry in `tests/promise_machine_coverage.json`,
and both syncs in the same commit as the files they copy.

## The Hexaemeron suite

No step owes the 1,379-test Hexaemeron suite in its exit, and the reason is
evidence rather than convenience. That suite reads `plugins/hexaemeron/**`.
Step 1 changes one file inside that tree, the generated
`plugins/hexaemeron/PROMISE_MACHINE.md`, and no test in
`plugins/hexaemeron/tests/` reads it: the only match for `PROMISE_MACHINE`
across that directory is the string constant
`promise-machine-run-observation/v1` in `test_run_observation_binding.py`, which
is a schema identity and not a path. The generated copies are checked by
`scripts/promise_machine.py check`, which the root suite already runs through
`tests/test_promise_machine_contract.py`. Steps 2 and 3 touch nothing under
`plugins/`. The suite still supplies the Elenchus runner contract below,
because that is the runner that writes a report.

## Step 1: Scaffold the corpus and bind the promise

**Goal.** Land the router-selection corpus, its deterministic checker, its
reporter and the root promise that binds them, with one case for each of the
router's 24 rows.

**Entry.** The run branch at `2477db1352a4099445867216f6fd9a2e84963f3a`, a
clean worktree, and the eight baselines the study records, every one on CPython
3.13.15: the root suite 438 of 438 exit 0; the Hexaemeron suite 1,379 of 1,379
exit 0; `promise_machine.py check` reporting 14 plugins and 14 copies;
`promise_machine.py coverage --check` reporting 72 promises, 72 rows and 72
selected; `portable_promise_machine.py check` clean;
`horos.py check .` reporting that the boundary matches the tree;
`audit_synopsis.py --check .` reporting 23 records all `budget=pass` and
`committed=match`; and `git status --short` empty. None of
`tests/test_router_selection.py`, `tests/emit_router_selection_report.py`,
`tests/fixtures/router-selection/`, `docs/router-selection/` or
`docs/promise-machine/router-selection-v1.md` exists. `PROMISE_MACHINE.md`
declares four `promise-machine-*` promises and
`tests/promise_machine_coverage.json` holds 72 rows and three capability keys.
The newest decision record is ADR-040, so ADR-041 is free.

**Exit.** Six surfaces, then the commands. The corpus exists under schema
`promise-machine-router-selection/v1` carrying a `pairs` block and 24 cases,
one for each router row, with the Pashov row's case naming one of the five
vendored canonical skills rather than the row's unnamed phrase. The checker
holds the corpus to its shape, to real canonical skill names, and to sentences
that still occur verbatim in the file each case names. The reporter prints the
coverage table and, with no run recorded yet, the word `not-run`.
`PROMISE_MACHINE.md` carries `### promise-machine-router-selection` with all
nine required fields, its `Evidence classes` naming `checked` and `recorded`
and never `proved`, and its `Boundary` stating in one sentence that a recorded
score is never a gate. `tests/promise_machine_coverage.json` carries the
`router_selection` capability entry naming that promise id, the corpus fixture
with its digest, `tests/test_router_selection.py` with its six selectors, and
`docs/promise-machine/router-selection-v1.md` with its digest. ADR-041 records
why the promise sits in the root law and why the router gets none. Both syncs
have run, in the order law then mirror then boundary. Then:

```bash
/Users/kethcode/.local/bin/python3.13 scripts/promise_machine.py sync --check
/Users/kethcode/.local/bin/python3.13 scripts/promise_machine.py check
/Users/kethcode/.local/bin/python3.13 scripts/promise_machine.py coverage --check
/Users/kethcode/.local/bin/python3.13 scripts/portable_promise_machine.py check
/Users/kethcode/.local/bin/python3.13 plugins/horos/skills/horos/scripts/horos.py check .
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
/Users/kethcode/.local/bin/python3.13 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.13 tests/emit_router_selection_report.py
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py PROMISE_MACHINE.md docs/router-selection/study.md docs/router-selection/runbook.md docs/promise-machine/router-selection-v1.md docs/decisions/ADR-041-grade-router-selection-as-a-root-capability.md
/Users/kethcode/.local/bin/python3.13 plugins/brevitas/skills/brevitas/scripts/brevitas.py PROMISE_MACHINE.md docs/promise-machine/router-selection-v1.md docs/decisions/ADR-041-grade-router-selection-as-a-root-capability.md
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
git diff --check
rm -rf .elenchus uv.lock
git status --short
```

Every one exits zero, the root suite reporting 444 tests, `git diff --check`
printing nothing and `git status --short` printing nothing. The two committed
study and runbook copies are linted rather than rewritten: they are the
receipted bytes, and Imprimatur already scores the study clean at 100.

**Files.** Twelve entries, and nothing outside them.

- `docs/router-selection/study.md`, create: the receipted study, committed
  because Protasis requires step 1 to carry it.
- `docs/router-selection/runbook.md`, create: this runbook, same reason.
- `docs/decisions/ADR-041-grade-router-selection-as-a-root-capability.md`,
  create: the study's first expensive-to-reverse decision, that the promise
  lives in the root law and the router gets none.
- `docs/promise-machine/router-selection-v1.md`, create: the versioned contract
  document for the corpus schema, which
  `test_every_contract_document_is_bound_to_evidence` then requires a coverage
  entry to bind.
- `tests/fixtures/router-selection/cases.json`, create: the corpus, written
  multi-line so it is not a single-line blob.
- `tests/test_router_selection.py`, create: the deterministic checker.
- `tests/emit_router_selection_report.py`, create: the reporter, matching the
  existing `tests/emit_*_report.py` convention.
- `PROMISE_MACHINE.md`, change: the new promise block.
- `tests/promise_machine_coverage.json`, change: the `router_selection`
  capability entry.
- `plugins/*/PROMISE_MACHINE.md`, change, 14 files: generated byte-identical
  copies of the root law, written only by `scripts/promise_machine.py sync`.
- `.agents/skills/promise-machine/runtime/`, change: the portable mirror, whose
  payload includes `PROMISE_MACHINE.md` and every non-omitted plugin file, so
  `scripts/portable_promise_machine.py sync` runs in this same commit.
- `.horos/boundary.json`, change: its
  `.agents/skills/promise-machine/runtime/` entry records `bytes` and `files`,
  both of which move when the mirror is resynced, so
  `horos.py scan . --write` runs in this same commit.

**Tests.** Red first, in this order. Write
`test_every_deciding_sentence_occurs_in_the_file_it_names` against a corpus
whose first case quotes a sentence that is not in `AGENTS.md`; observe it red;
correct the case to the verbatim sentence and observe it green. That order is
deliberate, because a prose-binding check that never failed proves only that it
ran. The six methods this step adds to `tests/test_router_selection.py`:
`test_the_corpus_declares_the_supported_schema`,
`test_every_case_carries_the_required_fields_and_a_unique_id`,
`test_every_expected_canonical_name_is_a_real_canonical_skill`,
`test_every_deciding_sentence_occurs_in_the_file_it_names`,
`test_a_recorded_run_block_matches_the_corpus_digest`, which passes vacuously
while no run is recorded, and
`test_a_malformed_corpus_fails_by_name_rather_than_reading_as_empty`. Count
arithmetic: 438 at entry plus 6 is 444 at exit. A step landing another number
names the method it added or dropped and why. The Elenchus runner contract for
any audit round claiming a fix:

```text
npx --yes --package=node@26.6.0 --call 'uv run --python 3.13.15 --with-requirements plugins/lazarus/requirements.txt python plugins/hexaemeron/tests/run_tests.py {report}'
```

with `{report}` as one whole argv element, report format `unittest-json-v1`
and report file `.elenchus/router-selection-step-1.json`. That runner refuses a
path that already exists, so a rerun uses a fresh name. Every guard this step
writes lives in the root suite, which that runner does not report on, so a fix
also records the complete output of
`/Users/kethcode/.local/bin/python3.13 -m unittest discover -s tests` beside
the verdict.

**Disciplines.** phylax: this step opens the corpus-reading boundary, so the
checker resolves one fixed repository-relative path with no caller-supplied
component, and a truncated, non-UTF-8 or non-JSON corpus fails by name rather
than parsing as an empty case set. ephoros: `emit_router_selection_report.py`
is the signal surface, and it answers which cases exist and whether a run was
recorded, naming the subject and path in every line and echoing no corpus
payload. metron: none, no performance claim; a file read and a substring search
per case sit inside a suite that runs in about 32 seconds. elenchus: the
red-first order above, and the step stops on any non-zero exit in its command
list. hypomnema: two records are earned here, ADR-041 for the promise's home
and `docs/promise-machine/router-selection-v1.md` for the schema, both
expensive to reverse because a later move invalidates every digest bound to
them.

## Step 2: Add the hard cases and the ambiguity rule

**Goal.** Cover every sibling boundary the marketplace prose names and every
near neighbour inside the Hexaemeron table with a contested case, and give the
router the ambiguity rule those cases grade against.

**Entry.** Step 1's exit: the run branch carrying the corpus, the checker, the
reporter, the promise, the capability entry, ADR-041 and both syncs, with the
root suite at 444 of 444 exit 0, the six checker and lint commands from step 1
exit 0, and `git status --short` empty. The corpus holds 24 cases and its
`pairs` block is declared by the schema but not yet populated. The router at
`.agents/skills/promise-machine/SKILL.md` still carries only the no-match rule
at its closing paragraph.

**Exit.** Four surfaces, then the commands. The corpus's `pairs` block names
every pair the study's prior-art table lists, each pair's two members checked
to be real canonical skills, plus the intra-Hexaemeron near neighbours the
study names. Each pair carries at least one case whose `contested` list holds
its members and whose `deciding_sentence` is the verbatim sentence that
separates them. The checker gains the two coverage checks and their two guards,
each guard reading its own fixture and failing when the corpus is degraded in
exactly the way the check exists to catch. The router carries an ambiguity
paragraph beside the existing no-match rule: name both candidate rows and the
boundary sentence that separates them, select only where one row's sentence
excludes the other, and otherwise stop at inspection naming the two rows and
the sentence. It adds no Markdown link and no version line, so `check_routers`
stays clean on PM041, PM042 and PM043. Then:

```bash
/Users/kethcode/.local/bin/python3.13 scripts/portable_promise_machine.py check
/Users/kethcode/.local/bin/python3.13 scripts/promise_machine.py check
/Users/kethcode/.local/bin/python3.13 scripts/promise_machine.py coverage --check
/Users/kethcode/.local/bin/python3.13 plugins/horos/skills/horos/scripts/horos.py check .
/Users/kethcode/.local/bin/python3.13 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.13 tests/emit_router_selection_report.py
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py .agents/skills/promise-machine/SKILL.md
/Users/kethcode/.local/bin/python3.13 plugins/brevitas/skills/brevitas/scripts/brevitas.py .agents/skills/promise-machine/SKILL.md
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
git diff --check
rm -rf .elenchus uv.lock
git status --short
```

Every one exits zero and the root suite reports 448 tests. `audit_synopsis.py
--check .` is absent because this step writes no audit source, and the
Hexaemeron suite is absent for the reason stated above the steps.

**Files.** Eight entries, and nothing outside them.

- `tests/fixtures/router-selection/cases.json`, change: the populated `pairs`
  block and the contested cases.
- `tests/fixtures/router-selection/guard-altered-sentence.json`, create: a
  corpus whose deciding sentence has been reworded, so the prose-binding guard
  has something to fail against.
- `tests/fixtures/router-selection/guard-missing-row.json`, create: a corpus
  with one router row uncovered, so the coverage guard has something to fail
  against.
- `tests/test_router_selection.py`, change: the two coverage checks and the two
  guards.
- `tests/promise_machine_coverage.json`, change: the corpus digest moved, the
  two guard fixtures gained digests, and four selectors were added.
- `.agents/skills/promise-machine/SKILL.md`, change: the ambiguity rule.
- `.agents/skills/promise-machine/runtime/`, change: the router is one of the
  eighteen fixed root paths the portable payload copies, so
  `scripts/portable_promise_machine.py sync` runs in this same commit.
- `.horos/boundary.json`, change: the mirror entry's `bytes` moves with the
  router, so `horos.py scan . --write` runs in this same commit.

**Tests.** Red first, in this order. Write
`test_a_router_row_with_no_case_fails_the_coverage_check` against the real
corpus before the coverage check exists; observe it fail to fail, which is the
point; then add the coverage check, point the guard at
`guard-missing-row.json`, and observe it green while the same check over the
real corpus stays green. Repeat for the altered-sentence guard. The four
methods this step adds: `test_every_router_row_is_named_by_at_least_one_case`,
`test_every_declared_pair_has_at_least_one_contested_case`,
`test_an_altered_deciding_sentence_fails_the_prose_binding_check` and
`test_a_router_row_with_no_case_fails_the_coverage_check`. Count arithmetic:
444 at entry plus 4 is 448 at exit. The Elenchus runner contract:

```text
npx --yes --package=node@26.6.0 --call 'uv run --python 3.13.15 --with-requirements plugins/lazarus/requirements.txt python plugins/hexaemeron/tests/run_tests.py {report}'
```

with `{report}` as one whole argv element, report format `unittest-json-v1`
and report file `.elenchus/router-selection-step-2.json`. This step's guards
also live in the root suite alone, so a fix records the complete output of
`/Users/kethcode/.local/bin/python3.13 -m unittest discover -s tests` beside
the verdict.

**Disciplines.** phylax: this step widens the corpus boundary opened in step 1
by adding two fixtures the checker also parses, so each guard fixture is read
through the same fixed-path, fail-by-name reader and no guard reads a path a
test computes from case data. ephoros: the reporter gains the pair coverage
table, which is what a maintainer reads after rewording a boundary sentence,
and it names the pair and the case id rather than reprinting the sentence.
metron: none, no performance claim; four more methods over the same fixture.
elenchus: the red-first order above, and the guards exist because a check that
cannot fail is worth nothing, which is the principle
`tests/test_boundary_currency.py` already states for the Horos boundary.
hypomnema: none, and the reason is that the ambiguity rule is a rule rather
than a decision with alternatives, and the study already records where the
schema and promise decisions live.

## Step 3: Grade the corpus and record one run

**Goal.** Present every request to a fresh agent context, record one run block
against the corpus digest, and prove the demo path from the study's problem
statement.

**Entry.** Step 2's exit: the run branch carrying the populated corpus, the ten
checker methods, the two guard fixtures and the router's ambiguity rule, with
the root suite at 448 of 448 exit 0, the eleven commands from step 2 exit 0,
and `git status --short` empty. The corpus records no run, so the reporter
still prints `not-run`.

**Exit.** Two surfaces, then the commands. The corpus carries one run block
naming `model`, `date`, `prompt_template_sha256`, `corpus_sha256`, `cases`,
`passed`, `failed` and `failures`, where `failures` lists each failing case id
with the canonical skill actually selected. The grading was performed as the
study specifies: each `request` field alone was presented to a fresh agent
context loaded with the router, `AGENTS.md` and the plugin runtime contracts,
and with neither the corpus nor the study. The score is recorded evidence about
one model on one date and is not a gate; no surface calls it proved. The
checker gains the method that refuses an incomplete block. Then:

```bash
/Users/kethcode/.local/bin/python3.13 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.13 tests/emit_router_selection_report.py
/Users/kethcode/.local/bin/python3.13 scripts/promise_machine.py coverage --check
/Users/kethcode/.local/bin/python3.13 scripts/promise_machine.py check
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
git diff --check
rm -rf .elenchus uv.lock
git status --short
```

Every one exits zero and the root suite reports 449 tests. The second command
is the demo path: it prints the coverage table and then the run block rather
than `not-run`, which is how this step is checkable even though the score
inside the block is not. The two syncs, the Horos check and the prose lints are
absent because this step changes no mirrored path and ships no prose.

**Files.** Three entries, and nothing outside them. None is mirrored, so this
step runs neither sync and touches neither boundary file.

- `tests/fixtures/router-selection/cases.json`, change: the recorded run block.
- `tests/test_router_selection.py`, change: the run-block completeness method.
- `tests/promise_machine_coverage.json`, change: the corpus digest moved and
  one selector was added.

**Tests.** Red first, in this order. Write
`test_the_recorded_run_block_is_complete_and_names_its_failures` against a
block missing its `model` field; observe it red; supply the real block from the
grading run and observe it green. The digest check from step 1 stops being
vacuous at the same moment, so run it against a block whose `corpus_sha256` is
one byte wrong and confirm it refuses, which is the lesson audit finding
`B5-R1-01` recorded: a report is believed only after it is graded against the
bytes on disk. The one method this step adds:
`test_the_recorded_run_block_is_complete_and_names_its_failures`. Count
arithmetic: 448 at entry plus 1 is 449 at exit. The Elenchus runner contract:

```text
npx --yes --package=node@26.6.0 --call 'uv run --python 3.13.15 --with-requirements plugins/lazarus/requirements.txt python plugins/hexaemeron/tests/run_tests.py {report}'
```

with `{report}` as one whole argv element, report format `unittest-json-v1`
and report file `.elenchus/router-selection-step-3.json`. This step's guard
lives in the root suite alone, so a fix records the complete output of
`/Users/kethcode/.local/bin/python3.13 -m unittest discover -s tests` beside
the verdict.

**Disciplines.** phylax: this step writes model output into a committed file,
so the block carries no model prose and each failure entry holds one case id
and one canonical skill name drawn from the closed set the checker already
validates. ephoros: the reporter is the on-call surface and now answers the
second of the study's two questions, which model produced the standing score
and against which corpus digest. metron: none, no performance claim; one method
and one JSON block. elenchus: the red-first order above, and the step stops if
the grading cannot be performed as specified, because a block recorded from a
context that saw the expected selections would be evidence about nothing.
hypomnema: none, and the reason is that this step records a measurement rather
than a decision, and the boundary that governs how it may be cited was written
into `PROMISE_MACHINE.md` in step 1.
### Amendment -- 2026-08-27

**What changed.** Complete replacement Exit: Six surfaces, then the commands. The corpus exists under schema
`promise-machine-router-selection/v1` carrying a `pairs` block and 24 cases,
one for each router row, with the Pashov row's case naming one of the five
vendored canonical skills rather than the row's unnamed phrase. The checker
holds the corpus to its shape, to real canonical skill names, and to sentences
that still occur verbatim in the file each case names. The reporter prints the
coverage table and, with no run recorded yet, the word `not-run`.
`PROMISE_MACHINE.md` carries `### promise-machine-router-selection` with all
nine required fields, its `Evidence classes` naming `checked`, `measured`,
`recomputed` and `recorded` and never `proved`, and its `Boundary` stating in one sentence that a recorded
score is never a gate. `tests/promise_machine_coverage.json` carries the
`router_selection` capability entry naming that promise id, the corpus fixture
with its digest, `tests/test_router_selection.py` with its six selectors, and
`docs/promise-machine/router-selection-v1.md` with its digest. ADR-041 records
why the promise sits in the root law and why the router gets none. Both syncs
have run, in the order law then mirror then boundary. Then:

```bash
/Users/kethcode/.local/bin/python3.13 scripts/promise_machine.py sync --check
/Users/kethcode/.local/bin/python3.13 scripts/promise_machine.py check
/Users/kethcode/.local/bin/python3.13 scripts/promise_machine.py coverage --check
/Users/kethcode/.local/bin/python3.13 scripts/portable_promise_machine.py check
/Users/kethcode/.local/bin/python3.13 plugins/horos/skills/horos/scripts/horos.py check .
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .
/Users/kethcode/.local/bin/python3.13 -m unittest discover -s tests
/Users/kethcode/.local/bin/python3.13 tests/emit_router_selection_report.py
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py PROMISE_MACHINE.md docs/router-selection/study.md docs/router-selection/runbook.md docs/promise-machine/router-selection-v1.md docs/decisions/ADR-041-grade-router-selection-as-a-root-capability.md
/Users/kethcode/.local/bin/python3.13 plugins/brevitas/skills/brevitas/scripts/brevitas.py PROMISE_MACHINE.md
/Users/kethcode/.local/bin/python3.13 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/promise-machine/router-selection-v1.md
/Users/kethcode/.local/bin/python3.13 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/decisions/ADR-041-grade-router-selection-as-a-root-capability.md
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests
/Users/kethcode/.local/bin/python3.13 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs
git diff --check
rm -rf .elenchus uv.lock
git status --short
```

Every one exits zero, the root suite reporting 444 tests, `git diff --check`
printing nothing and `git status --short` printing nothing. The two committed
study and runbook copies are linted rather than rewritten: they are the
receipted bytes, and Imprimatur already scores the study clean at 100.

**Why.** Two corrections to step 1's exit, both found by its own audit round.
The receipted study assigns the recorded grading run the evidence class
`measured`, which the root law defines as a value observed under a recorded
method and environment, and the task issue asks for the corpus to be scored at
that class and never at `proved`. This exit named only `checked` and
`recorded`, so the promise as landed understated the evidence the delivery
produces, and step 3, which records the run, cannot reach `PROMISE_MACHINE.md`
under its own files. The same sentence settles the parallel case the round
raised: the promise's own promise and evidence lines say the corpus digest is
derived again from named inputs, which is `recomputed` rather than `checked`.
The second correction is mechanical. `brevitas.py` takes one optional
positional argument, so the single line naming three documents exits 2 with
`unrecognized arguments`, and the three documents are now named one per line,
which is the form that was actually run.

**Steps touched.** Step 1 only. Steps 2 and 3 are unchanged.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.
### Amendment -- 2026-08-27

**What changed.** Complete replacement Files: Twelve entries, and nothing outside them.

- `docs/router-selection/study.md`, create: the receipted study, committed
  because Protasis requires step 1 to carry it.
- `docs/router-selection/runbook.md`, create: this runbook, same reason.
- `docs/decisions/ADR-041-grade-router-selection-as-a-root-capability.md`,
  create: the study's first expensive-to-reverse decision, that the promise
  lives in the root law and the router gets none.
- `docs/promise-machine/router-selection-v1.md`, create: the versioned contract
  document for the corpus schema, which
  `test_every_contract_document_is_bound_to_evidence` then requires a coverage
  entry to bind.
- `tests/fixtures/router-selection/cases.json`, create: the corpus, written
  multi-line so it is not a single-line blob.
- `tests/test_router_selection.py`, create: the deterministic checker.
- `tests/emit_router_selection_report.py`, create: the reporter, matching the
  existing `tests/emit_*_report.py` convention.
- `PROMISE_MACHINE.md`, change: the new promise block.
- `tests/promise_machine_coverage.json`, change: the `router_selection`
  capability entry.
- `plugins/*/PROMISE_MACHINE.md`, change, 14 files: generated byte-identical
  copies of the root law, written only by `scripts/promise_machine.py sync`.
- `.agents/skills/promise-machine/runtime/`, change: the portable mirror, whose
  payload includes `PROMISE_MACHINE.md` and every non-omitted plugin file, so
  `scripts/portable_promise_machine.py sync` runs in this same commit.
- `.horos/boundary.json` and `.horos/candidates.json`, change: the boundary's
  `.agents/skills/promise-machine/runtime/` entry records `bytes` and `files`,
  both of which move when the mirror is resynced, so
  `horos.py scan . --write` runs in this same commit, and that one command
  writes the candidate record beside the boundary.

**Why.** The entry named `.horos/boundary.json` as the artefact a resync moves
and named `horos.py scan . --write` as the command that moves it. That command
writes two files, the boundary and the candidate record beside it. This step's
own work has already moved both, because the audit log's synopsis grew past
the size the candidate record held, so the tree carries a change to a path the
field did not name while the field forbids exactly that. The entry now names
what the sanctioned command writes, which leaves the scope sentence true
rather than nearly true. The step keeps twelve entries and gains no command.

**Steps touched.** Step 1 only. Steps 2 and 3 are unchanged.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.
### Amendment -- 2026-08-27

**What changed.** Complete replacement Files: Eight entries, and nothing outside them.

- `tests/fixtures/router-selection/cases.json`, change: the populated `pairs`
  block and the contested cases.
- `tests/fixtures/router-selection/guard-altered-sentence.json`, create: a
  corpus whose deciding sentence has been reworded, so the prose-binding guard
  has something to fail against.
- `tests/fixtures/router-selection/guard-missing-row.json`, create: a corpus
  with one router row uncovered, so the coverage guard has something to fail
  against.
- `tests/test_router_selection.py`, change: the two coverage checks and the two
  guards.
- `tests/promise_machine_coverage.json`, change: the corpus digest moved, the
  two guard fixtures gained digests, and four selectors were added.
- `.agents/skills/promise-machine/SKILL.md`, change: the ambiguity rule.
- `.agents/skills/promise-machine/runtime/`, change: the router is one of the
  eighteen fixed root paths the portable payload copies, so
  `scripts/portable_promise_machine.py sync` runs in this same commit.
- `.horos/boundary.json` and `.horos/candidates.json`, change: the mirror
  entry's `bytes` moves with the router, so `horos.py scan . --write` runs in
  this same commit and writes both files.

**Why.** The same correction the previous amendment made to step 1, applied to
the step that resyncs the mirror for the router's ambiguity rule.
`horos.py scan . --write` writes the candidate record beside the boundary, so
naming only the boundary would leave this step in the position step 1 reached:
a changed path its own files field did not name. The step keeps eight entries
and gains no command.

**Steps touched.** Step 2 only. Steps 1 and 3 are unchanged.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds.
