# Runbook: test the remaining Atlas hand-offs before adding README buttons

Derived from `.hexaemeron/study.md` for issue
[#856](https://github.com/wildcat-finance/skills/issues/856). Base ref
`8dc3aca54adeca49387a2bdfc174cf6e72d02a11` on `main`, run branch
`fiat/856-framework-13-test-the-remaining-atlas-hand-o`.

The study's open question was put to the user, who chose the outcome rather than
a reading of the boundary: no account is enrolled in any Copilot plan, and
GitHub Copilot is classified `manual route` with its blocker recorded. The
choice costs nothing either way here, because every client is absent from this
host. No step attempts a harness client run, and no step creates an Atlas route.

## Where the pending gates land

Three conformance gates were left pending in the design record. Fiat runs the
design checker at a `step:N` transition before opening that step, so the work
that produces each report sits in the step before its stop point.

- `killed-probe-recovery` blocks `step:3`. Step 2 builds the probe's atomic
  write and the guard test that proves it, so the report exists before step 3
  runs the probe for real.
- `roster-single-source` and `wording-regen-budget` block `step:4`. Step 3
  generates the three wording surfaces from the manifest and measures the
  regeneration, so both reports exist before step 4 binds the surfaces to the
  repository suite.

The study calls step 4 the step that makes the surfaces generated. Step 4 is
where generated surfaces become the shipped, suite-bound state; step 3 is where
they are first produced, because that is what makes the declared stop point
real. This reading is recorded here rather than resolved silently.

## The runner contract every step shares

Test command `python3 tests/run_tests.py --elenchus-report {report}`, report
format `elenchus.unittest.v1`, report file `.elenchus/fiat-856-step-<N>.json`.
Warden receives those three inputs and may not substitute a nearby suite.

Every step's exit runs the root suite, `python3 scripts/run_checks.py --full`,
at exit zero, against a committed tree. Three lints passing is not the suite.

Two known false reds, from the study's constraints. A `run_checks.py` failure
reported as `WAI-E-ADAPTER.TIMEOUT` is parallel load, not a defect; rerun with
`--jobs 1`. A Python pin check that comes back one short is usually a stale
sibling under `.claude/worktrees/`, not the diff. The dead-code check needs a
clean tree, so each step commits before running the suite.

No step edits any file under `audit/`. Those bytes are pinned.

```design-lock
schema | protasis-design-evidence/v1
sha256 | dc945d47bd56ee1ef71051fb86fd93d8a63242806bf9a8a41d1bbc5d193552fe
candidate | probe-manifest
```

## Step 1: Scaffold the harness record and commit the run documents

**Goal.** Put the study, this runbook, the decision record and the manifest
schema in the repository so every later step has a fixed home to write into.

**Entry.** `main` at `8dc3aca54adeca49387a2bdfc174cf6e72d02a11`, clean tree.

**Exit.** `docs/atlas-harness-handoff/study.md` and
`docs/atlas-harness-handoff/runbook.md` are byte-identical copies of the two
`.hexaemeron/` artefacts. `schemas/harness-classification-v1.json` validates the
four classification names and the per-harness observation fields.
`docs/decisions/ADR-074-generate-the-harness-roster-from-one-probed-manifest.md`
records the schema, the four names and the acceptance-condition-2 reading.
`tests/test_harness_manifest.py` exists and its schema cases pass. Proved by
`python3 scripts/run_checks.py --full` at exit zero on the committed tree.

**Files.** `docs/atlas-harness-handoff/study.md`,
`docs/atlas-harness-handoff/runbook.md`,
`schemas/harness-classification-v1.json`,
`docs/decisions/ADR-074-generate-the-harness-roster-from-one-probed-manifest.md`,
`tests/test_harness_manifest.py`, and the check-map entry that binds the new
paths to a declared scope.

**Tests.** `tests/test_harness_manifest.py` gains `SchemaTests`: the four
classification names are exactly `Atlas launcher`, `tested local route`,
`manual route` and `unsupported`; an unknown name is refused; each of the six
harness entries requires `client_present`, `client_version`, `auth_configured`,
`launcher_contract` and `blocker`; a missing field is refused; a null
`client_version` is admitted only when `client_present` is false. Expect eight
cases. Step audit runner contract is test command
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-856-step-1.json`.

**Disciplines.** phylax: none, this step adds no input path and spawns nothing.
ephoros: none, nothing here runs unattended. metron: none, no performance claim
is made. elenchus: none, no failure is in hand. hypomnema: the schema and the
four classification names are costly to reverse once prose is generated from
them, so ADR-074 is their home.

## Step 2: Build the probe and prove it cannot lie or half-write

**Goal.** Write the probe that observes this host, and the guards that stop it
awarding a class it did not earn or leaving a torn manifest behind.

**Entry.** Step 1's exit state.

**Exit.** `scripts/probe_harnesses.py --out <path>` writes a manifest that
validates against the step 1 schema, using a fixed argv per client, no shell,
and a bounded timeout. The classifier cannot return `Atlas launcher` or
`tested local route` from any input that carries no recorded client run. The
manifest write is atomic: a temporary file in the destination directory
followed by a rename. `killed-probe-recovery` is resolved by
`python3 -m unittest tests.test_harness_manifest.KilledProbeTests`, writing
`.hexaemeron/reports/probe-manifest-killed-probe-recovery.json`. Proved by
`python3 scripts/run_checks.py --full` at exit zero on the committed tree.

**Files.** `scripts/probe_harnesses.py`, `tests/test_harness_manifest.py`.

**Tests.** `ClassifierTests`: every input shape that lacks a recorded client run
returns `manual route` or `unsupported`, and no input returns a tested class;
absence from the host and a failed authentication produce different records and
never collapse. `SubprocessTests`: argv is a fixed list, no shell is used, no
probe argument is read from a manifest, and a client that does not answer inside
the timeout is recorded as unread with its reason rather than as absent.
`CredentialTests`: a pattern sweep over the manifest and the probe log finds no
token, key, cookie or session shape, using a client output fixture that contains
one. `KilledProbeTests`: a probe killed mid-write leaves the previous manifest
intact, or nothing when there was none, and never a partial file the renderer
would accept. Expect around eighteen cases. Step audit runner contract is test
command `python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-856-step-2.json`.

**Disciplines.** phylax: this step spawns client binaries and reads what they
print, so the fixed argv, the bounded timeout and the credential sweep all
apply. ephoros: the manifest carries the probe command and result per harness,
which is the signal answering why a harness got its class. metron: none, the
probe's cost is dominated by client startup this repository does not control.
elenchus: the killed-write guard is a cause-level test that fails without the
atomic rename. hypomnema: none, ADR-074 already holds the decision this step
implements.

## Step 3: Record this host and generate the three wording surfaces

**Goal.** Run the probe for real, land the checked-in record for all six
harnesses, and produce the README block, the guide table and the PDF harness
page from it.

**Entry.** Step 2's exit state, with the `step:3` design transition recorded.

**Exit.** `docs/harness-classification.json` exists and carries all six
harnesses, each with its observation fields and, where it could not be run, its
exact blocker: Copilot no seat and an unconfigured organisation policy, Cursor
and Gemini CLI and Cline absent and unauthenticated, Windsurf absent and now
published as Cascade inside Devin Desktop, Roo Code sunset and archived.
`scripts/render_harness_roster.py` writes the three surfaces from that manifest
and `--check` exits non-zero on drift. `roster-single-source` is resolved by
`python3 .hexaemeron/design/count_roster_copies.py --report
.hexaemeron/reports/probe-manifest-roster-single-source.json` at a count of one.
`wording-regen-budget` is resolved by `python3
.hexaemeron/design/time_wording_regen.py --report
.hexaemeron/reports/probe-manifest-wording-regen-budget.json` inside 60000
milliseconds. Proved by `python3 scripts/run_checks.py --full` at exit zero on
the committed tree.

**Files.** `docs/harness-classification.json`,
`scripts/render_harness_roster.py`, `README.md`,
`docs/how-to-help-shoggoth.md`, `scripts/build_contributor_guide.py`,
`docs/pdf/how-to-help-shoggoth.pdf`,
`.hexaemeron/design/count_roster_copies.py`,
`.hexaemeron/design/time_wording_regen.py`, `tests/test_harness_manifest.py`.

**Tests.** `RecordTests`: the landed manifest validates, names all six
harnesses, carries no tested class, and every entry whose `testable_here` is
false carries a non-empty blocker. `RenderTests`: the renderer is deterministic
across two runs; `--check` passes on freshly written surfaces and fails when one
character of any surface is changed; the PDF comparison reads the harness page's
text rather than the whole file, so a timestamp does not fail it. Expect around
twelve new cases. Step audit runner contract is test command
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-856-step-3.json`.

**Disciplines.** phylax: the probe runs here for real, so the credential sweep
and the unread-contract rule are exercised rather than only tested. ephoros: the
manifest's recorded host, date and base ref are the staleness signal the
renderer later checks against. metron: the regeneration budget is measured here
and the 60000-millisecond ceiling either holds or the gate fails. elenchus:
none, no failure is in hand at this step. hypomnema: none, the per-harness
classifications belong in the regenerated manifest and not in a decision record.

## Step 4: Bind the surfaces to the suite and correct the Atlas claim

**Goal.** Make roster drift a normal test failure, and stop the guide claiming
Atlas route tests that do not exist.

**Entry.** Step 3's exit state, with the `step:4` design transition recorded.

**Exit.** `scripts/render_harness_roster.py --check` runs inside the repository
suite through a declared scope, so a drifted surface reddens an ordinary run.
The guide sentence claiming the two web routes are covered by Atlas launcher
tests is replaced by what the Atlas repository holds at
`ce866e3d7e8b489fcb8b70c608f7af72d9b7a673`, which is six test files and no route
test. Proved by `python3 scripts/run_checks.py --full` at exit zero on the
committed tree, with a deliberate one-character edit to a generated surface
shown to redden it and then reverted.

**Files.** `docs/how-to-help-shoggoth.md`, `scripts/build_contributor_guide.py`,
`docs/pdf/how-to-help-shoggoth.pdf`, the check map, `tests/test_harness_manifest.py`.

**Tests.** `DriftTests`: the check mode is reachable from the repository suite,
fails on a changed surface, fails on a missing manifest, and fails when the
manifest's recorded run does not match the surfaces being checked.
`AtlasClaimTests`: neither the README nor the guide asserts that a route test
covers `/go/chatgpt` or `/go/claude`. Expect around six new cases. Step audit
runner contract is test command
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-856-step-4.json`.

**Disciplines.** phylax: none, this step opens no boundary the earlier steps did
not already close. ephoros: the drift check is the on-call signal answering
whether the published roster is still true, and this step is where it starts
firing. metron: none, the budget was measured and gated at step 3. elenchus: the
deliberate-edit demonstration is the guard proving the check fails without the
binding. hypomnema: none, no new costly decision is taken here.

## Step 5: Demonstrate the record end to end

**Goal.** Run the study's demo path on a clean checkout and show the four
commands producing the record, the surfaces and a green suite.

**Entry.** Step 4's exit state.

**Exit.** These four commands run in order at exit zero, and the tree is clean
afterwards:

```bash
python3 scripts/probe_harnesses.py --out docs/harness-classification.json
python3 scripts/render_harness_roster.py --check
python3 scripts/build_contributor_guide.py
python3 -m unittest tests.test_harness_manifest -v
```

The run transcript, the six per-harness verdicts and the five named blockers are
recorded in the pull-request body. Proved by
`python3 scripts/run_checks.py --full` at exit zero on the committed tree.

**Files.** `docs/atlas-harness-handoff/demonstration.md`, and any regenerated
surface the demo run produces.

**Tests.** No new test module. The demonstration re-runs
`tests/test_harness_manifest` in full and the root suite behind it. Step audit
runner contract is test command
`python3 tests/run_tests.py --elenchus-report {report}`, report format
`elenchus.unittest.v1`, report file `.elenchus/fiat-856-step-5.json`.

**Disciplines.** phylax: the probe spawns clients again on a clean checkout, so
the credential sweep runs once more against real output. ephoros: the
demonstration is where the two recorded questions get their answers read back.
metron: none, step 3 holds the budget evidence. elenchus: none, no failure is in
hand. hypomnema: none, the demonstration record is evidence rather than a
decision.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Exit: `docs/atlas-harness-handoff/study.md` and `docs/atlas-harness-handoff/runbook.md` are byte-identical copies of the two `.hexaemeron/` artefacts. `schemas/harness-classification-v1.json` validates the four classification names and the per-harness observation fields. `docs/decisions/ADR-076-generate-the-harness-roster-from-one-probed-manifest.md` records the schema, the four names and the acceptance-condition-2 reading. `tests/test_harness_manifest.py` exists and its schema cases pass. Proved by `python3 scripts/run_checks.py --full` at exit zero on the committed tree. Complete replacement Files: `docs/atlas-harness-handoff/study.md`, `docs/atlas-harness-handoff/runbook.md`, `schemas/harness-classification-v1.json`, `docs/decisions/ADR-076-generate-the-harness-roster-from-one-probed-manifest.md`, and `tests/test_harness_manifest.py`. No check-map row is added: `scripts/run_checks.py --plan` reports no unowned path, because `docs`, `schemas` and `tests` already own all five by longest prefix, and a row exists in this repository only to override that default. Complete replacement Disciplines: phylax: none, this step adds no input path and spawns nothing. ephoros: none, nothing here runs unattended. metron: none, no performance claim is made. elenchus: none, no failure is in hand. hypomnema: the schema and the four classification names are costly to reverse once prose is generated from them, so ADR-076 is their home.

**Why.** The decision record was authored as ADR-074 when that number was free. Pull request 1181 merged `ADR-074-shape-every-written-record-through-sapheneia.md` into `main` ninety minutes later, and `tests/test_decision_records.py` compares numbers against the default branch, so the step's own exit gate went red for a reason outside this run. ADR-075 is already claimed by open pull request 1185, so this record takes 076. Issue 888 is reconstructing ADR numbering to assign at merge rather than at authoring, which is the systemic answer; this amendment is the local one. The Files field also now states the check-map position that was already true rather than requiring a row the repository's own convention does not use.

**Steps touched.** Step 1.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-04

**What changed.** Complete replacement Disciplines: phylax: this step spawns client binaries and reads what they print, so the fixed argv, the bounded timeout and the credential sweep all apply. ephoros: the manifest carries the probe command and result per harness, which is the signal answering why a harness got its class. metron: none, the probe's cost is dominated by client startup this repository does not control. elenchus: the killed-write guard is a cause-level test that fails without the atomic rename. hypomnema: none, ADR-076 already holds the decision this step implements.

**Why.** Step 2's Disciplines field named the decision record by its old number. The record is ADR-076 for the reason the previous amendment gives, so this reference is corrected to match. Nothing about step 2's work changes.

**Steps touched.** Step 2.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.
