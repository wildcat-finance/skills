# Runbook: admit the Anamnesis corpus projection, or record its boundary

Derived from [the study](study.md). The selected design is `boundary-record`:
change no Synkrisis schema, record the decision that corpus projections sit
outside the cohort boundary, and name what reads the projection instead.

Three steps. Step 1 commits the design records and pins this run's test runner.
Step 2 records the decision and ships the guard that makes the named reader more
than a description. Step 3 advances the ledger, reconciles the prose that has
gone stale, and runs the demo path from the study's problem statement.

The plugin's Elenchus runner numbers its steps by the plugin's own history, and
runbook steps 1 to 3 of this run are its steps 4 to 6. Each step's `Tests` line
names the exact command, so Warden takes the runner argument from there and does
not infer it from the heading.

```design-lock
schema | protasis-design-evidence/v1
sha256 | eed112189fa3a4983ab080b5e6809997af54dbe6cdc9b3f1191926a14ff2d0a4
candidate | boundary-record
```

## Step 1: Commit the design records and pin this run's step runner

**Goal.** Land the study, runbook, design record and resolved reports in the
plugin's docs, and admit this run's step numbers to the Elenchus runner, with no
product behaviour changed.

**Entry.** Exact commit `9783e2631de1614716eda5043cd843768d3baa06` on the run
branch, with `.hexaemeron/study.md`, `.hexaemeron/runbook.md`,
`.hexaemeron/design-evidence.json` and `.hexaemeron/reports/` receipted;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:1`
exits zero.

**Exit.** `plugins/anamnesis/docs/synkrisis-admission-study.md` and
`plugins/anamnesis/docs/synkrisis-admission-runbook.md` are byte-identical to
the receipted `.hexaemeron/` copies; the design record and its eighteen reports
are committed under `plugins/anamnesis/docs/synkrisis-admission/`;
`plugins/anamnesis/tests/elenchus.py` admits steps 4 to 6; the anamnesis suite
and the root suite are green; and
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:2`
exits zero before the pull request is ready.

**Files.** Create `plugins/anamnesis/docs/synkrisis-admission-study.md`,
`plugins/anamnesis/docs/synkrisis-admission-runbook.md`,
`plugins/anamnesis/docs/synkrisis-admission/design-evidence.json`,
`plugins/anamnesis/docs/synkrisis-admission/reports/` (eighteen report objects),
and `plugins/anamnesis/tests/test_s4_records.py`. Change
`plugins/anamnesis/tests/elenchus.py` (`STEPS`).

**Tests.** Add `plugins/anamnesis/tests/test_s4_records.py`: the committed
design record parses, declares schema `protasis-design-evidence/v1`, names three
candidates and six criteria covering all five concerns, selects
`boundary-record` under `unique-frontier`, and every result cell names a report
whose recorded SHA-256 matches the committed bytes. The audit runner contract is
`python3 plugins/anamnesis/tests/elenchus.py --step 4 {report}`, its format is
`elenchus.unittest.v1`, and Warden writes
`.hexaemeron/elenchus/anamnesis-step-4.json`. Also run the anamnesis suite from
the repository root, the synkrisis suite from `plugins/synkrisis`, and
`git diff --check`. Expected new focused tests: 4.

**Disciplines.** phylax: none, the step adds documents and a test and opens no
boundary. ephoros: none, nothing here runs unattended. metron: none, no
performance claim and no speed-motivated change. elenchus: none, no failure in
hand at entry. hypomnema: the design record's committed location is the one
choice here that is awkward to move later, and it is settled by this step rather
than left implicit.

## Step 2: Record the boundary decision and guard the named reader

**Goal.** State, as a decision record, that corpus projections sit outside the
Synkrisis cohort boundary, name what reads the projection instead, and prove by
test that the projection can be read honestly without Synkrisis.

**Entry.** Step 1's exit state;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:2`
exits zero.

**Exit.** `plugins/anamnesis/docs/decisions/ADR-005-corpus-projections-outside-the-cohort-boundary.md`
exists, lints clean under imprimatur, states Anamnesis's position without
asserting a decision on Synkrisis's behalf, names the reader, and leaves the
ADR-004 seam explicitly open for Synkrisis. The self-sufficiency guard passes
against the committed pilot projection and fails against a projection with any
denominator, exclusion set, unknowns map or `not_established` sentence removed.
The suites are green and
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:3`
exits zero.

**Files.** Create
`plugins/anamnesis/docs/decisions/ADR-005-corpus-projections-outside-the-cohort-boundary.md`
and `plugins/anamnesis/tests/test_s5_boundary.py`.

**Tests.** Add `plugins/anamnesis/tests/test_s5_boundary.py`: the committed
pilot projection declares producer `anamnesis-synkrisis-observation/v1` and not
Synkrisis's; every count in `cohort` has a denominator it can be read against;
`exclusions`, `unknowns` and `not_established` are all present and
`not_established` is non-empty; and a projection with each of those four removed
is refused in turn, one specimen per removal. The audit runner contract is
`python3 plugins/anamnesis/tests/elenchus.py --step 5 {report}`, its format is
`elenchus.unittest.v1`, and Warden writes
`.hexaemeron/elenchus/anamnesis-step-5.json`. Expected new focused tests: 7.

**Disciplines.** phylax: the guard reads a release projection and must not reach
material the projection's disclosure rules withheld; the existing Anamnesis
control covers it and is not reimplemented. ephoros: none, the guard runs from a
terminal and reports through its exit status. metron: none, no budget and no
speed-motivated change. elenchus: each refusal specimen is the guard's own bad
case, and every new guard runs against the parent commit to show it fails there.
hypomnema: this step is the decision record, so the discipline is the step.

## Step 3: Advance the ledger, reconcile the prose, and run the demo path

**Goal.** Record the completed frontier job in Anamnesis's ledger, correct every
first-party document that still says the question is open, and demonstrate the
whole path.

**Entry.** Step 2's exit state;
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:3`
exits zero.

**Exit.** `plugins/anamnesis/skills/anamnesis/EVOLUTION.md` carries exactly one
new row valid under the versioning contract: evolution incremented once,
generation and epoch retained, the prior revision and digest preserved in the
new row's generation fields, the header and row naming the same version, and
either one evidenced next job or `mature` with `None -- mature`. Every
first-party document that claims Synkrisis's decision "has not been made" is
reconciled, including `plugins/anamnesis/skills/anamnesis/SKILL.md` and
`plugins/anamnesis/README.md`. `plugins/synkrisis/` is unchanged and Synkrisis's
frontier tuple and digest are byte-identical. The demo path
`python3 plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py demo --specimen plugins/anamnesis/specimens/pilot`
runs and both views are read. Suites green;
`design_evidence.py ... --transition integration` exits zero.

**Files.** Change `plugins/anamnesis/skills/anamnesis/EVOLUTION.md`,
`plugins/anamnesis/skills/anamnesis/SKILL.md`, `plugins/anamnesis/README.md`,
and any other first-party document the cold read finds carrying the stale claim.
Create `plugins/anamnesis/tests/test_s6_ledger.py`.

**Tests.** Add `plugins/anamnesis/tests/test_s6_ledger.py`: the ledger's header
version matches its newest row, the new row's frontier digest recomputes over
the exact `{status}|{frontier revision}|{current frontier}|{next Fiat job}` line
including its final newline, the generation row retains the prior revision and
digest, and no first-party document under `plugins/anamnesis/` still asserts
that Synkrisis's decision has not been made. The audit runner contract is
`python3 plugins/anamnesis/tests/elenchus.py --step 6 {report}`, its format is
`elenchus.unittest.v1`, and Warden writes
`.hexaemeron/elenchus/anamnesis-step-6.json`. Also run the demo path above, the
anamnesis and root suites, `python3 scripts/portable_promise_machine.py check`,
and `git diff --check`. Expected new focused tests: 5.

**Disciplines.** phylax: none, the step edits documents and reads one specimen.
ephoros: none. metron: none, the demo prints its existing baselines and no
budget is declared. elenchus: the prose reconciliation is driven by a cold read
rather than by memory of what was written, so a missed document is a test
failure rather than an oversight. hypomnema: the ledger row is the durable
record of the decision and its home is fixed by the versioning contract.

### Amendment -- 2026-08-31

**What changed.** Complete replacement Exit: `plugins/anamnesis/docs/synkrisis-admission-runbook.md` is byte-identical to the receipted `.hexaemeron/runbook.md`; `plugins/anamnesis/docs/synkrisis-admission-study.md` is byte-identical to the receipted `.hexaemeron/study.md` except for the five discipline citations, which are commit-pinned absolute URLs at `9783e2631de1614716eda5043cd843768d3baa06` rather than relative paths that resolve to nothing; the design record and its eighteen reports are committed under `plugins/anamnesis/docs/synkrisis-admission/`; `plugins/anamnesis/tests/elenchus.py` admits steps 4 to 6; the anamnesis suite and the root suite are green; `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/anamnesis/docs/synkrisis-admission-study.md plugins/anamnesis/docs/synkrisis-admission-runbook.md` exits zero; and `python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition step:2` exits zero before the pull request is ready.

**Why.** Step 1 round 1 found the study's five discipline citations written as `../<skill>/SKILL.md`, which resolve from the Protasis skill directory they were copied from and from nowhere else. Hypomnema exits 1 on the committed copy. The receipted study is immutable and `amend study` only appends, so the body cannot be corrected in place; the committed copy carries the corrected links and the receipted copy keeps the originals. The prior Anamnesis study pins the same five citations to its own starting commit, so this restores the house convention rather than inventing one.

**Steps touched.** Step 1

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds.
