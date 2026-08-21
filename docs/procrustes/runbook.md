# Runbook: Procrustes

Four steps. Each one is a pull request against the step below it, and each leaves
the root contract suites green. The order is dependency order: the spec is
committed before anything reads it, the baseline exists before a candidate is
compared to it, the gates exist before a run is demonstrated.

Two facts from the study govern the shape. A governed first-party skill outside
Hexaemeron must carry Promise Machine declarations from the moment it exists, so
the skill directory arrives with its first promise rather than before it. And a
promise at consequence 2 needs a runtime map bound to bytes that already exist,
so the acceptance promise lands with the command that writes them.

## Step 1: Commit the spec

**Goal.** Put the study and the runbook in the tree, so every later step reads a
committed document rather than controller state.
**Entry.** `fiat/procrustes-a-fail-closed-eip-170-code-size-optim` at the run
branch head, cut from `main` at `3c061c2e15df085cf300220250b421bbd03f664c`.
**Exit.** `docs/procrustes/study.md` and `docs/procrustes/runbook.md` exist and
are byte-identical to the run copies after the prose pass. Proved by
`python3 -m unittest discover -s tests`, `python3 scripts/promise_machine.py
check`, `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py
docs/procrustes/study.md docs/procrustes/runbook.md`, and
`python3 plugins/horos/skills/horos/scripts/horos.py check .`, each exiting 0.
**Files.** `docs/procrustes/study.md`, `docs/procrustes/runbook.md`.
**Tests.** None added. The existing root suites are the proof that two Markdown
files changed nothing else.
**Disciplines.** phylax: none, no boundary opens. ephoros: none, nothing runs
unattended. metron: none, no performance claim. elenchus: none, no failure in
hand. hypomnema: this is the step whose whole content is a record, and the study
is the home item 12 names.

## Step 2: Seal a size baseline

**Goal.** The skill exists and can seal a green baseline of per-contract runtime
and initcode sizes, with the sources, layouts and selectors that make a later
comparison meaningful.
**Entry.** Step 1's branch, spec committed.
**Exit.** `procrustes.py baseline --repo <foundry-root> --size-target <regex>`
writes an evidence directory holding `sizes.json`, the sealed sources, storage
layouts, method identifiers, the resolved Foundry config, the Git revision and a
green test log, and exits non-zero on a dirty tree, a red suite, an unparsable
`forge build --sizes`, or a `--size-target` matching no contract. Proved by
`python3 plugins/hermes/skills/procrustes/scripts/test_procrustes.py`,
`python3 -m unittest discover -s tests`, and
`python3 scripts/promise_machine.py check`, each exiting 0.
**Files.** `plugins/hermes/skills/procrustes/SKILL.md`,
`plugins/hermes/skills/procrustes/EVOLUTION.md`,
`plugins/hermes/skills/procrustes/references/size-catalogue.md`,
`plugins/hermes/skills/procrustes/scripts/procrustes.py`,
`plugins/hermes/skills/procrustes/scripts/test_procrustes.py`,
`plugins/hermes/AGENTS.md`, `tests/test_promise_machine_contract.py`,
`tests/promise_machine_coverage.json`, `.horos/boundary.json` if the scan drifts.
**Tests.** `test_procrustes.py`, new, with a fake `forge` on `PATH` as
`test_hermes.py` uses: the sizes parse, both refusal cases above, the dirty-tree
and red-suite refusals, and the import-coupling guard that pins every name and
signature taken from `hermes.py`. Expect roughly a dozen.
**Disciplines.** phylax: this step spawns `forge` and `git` in a directory the
caller names and writes an evidence tree, which are the subprocess and filesystem
boundaries of item 9. ephoros: the evidence directory and its failure record are
what somebody reads afterwards, so the refusal reason is written before the
process exits. metron: none, no performance claim; the sizes are measurements,
not a budget. elenchus: none yet, no failure in hand. hypomnema: the promise
declarations and the ledger baseline row are both records this step is the first
to owe.

## Step 3: The gates

**Goal.** A candidate is accepted only when the bytes fell, behaviour held, the
protected interfaces did not move, no check was deleted, and no code moved behind
`delegatecall` unannounced.
**Entry.** Step 2's branch, baseline sealing green.
**Exit.** `procrustes.py verify --run-dir <dir> --class <size class>` writes
`result.json` and exits 0 only on status `accepted`. It refuses, each with its own
exit path: no measured reduction on a declared target; any contract still over
24576 bytes when the run declared it would come under; a red pinned or unpinned
suite; a moved protected layout or selector; a removed `require`, `revert`,
`assert`, modifier use or custom-error throw that the declared class does not
name; a new external library link or `delegatecall` site that the run did not
declare; and a gas regression above the declared ceiling. Proved by the harness
tests, `python3 -m unittest discover -s tests`, and
`python3 scripts/promise_machine.py check`.
**Files.** `plugins/hermes/skills/procrustes/scripts/procrustes.py`,
`scripts/test_procrustes.py`, `SKILL.md`, `EVOLUTION.md`,
`references/size-catalogue.md`, `tests/promise_machine_coverage.json`,
`tests/test_promise_machine_contract.py`.
**Tests.** One refusal test per gate, each named for what it refuses and each
failing without its gate. Plus the acceptance path, and a runtime-binding test
that `result.json` carries promise identity, subject, scope, evidence, unknowns
and transition where the coverage map says it does.
**Disciplines.** phylax: the diff parser reads attacker-shaped source, so it
classifies rather than executes, and it fails closed on a diff it cannot parse.
ephoros: `result.json` carries the gate index, the refusal reason and the
per-contract byte deltas, which are the two questions item 8 keeps. metron: none;
the gas number is recorded against a declared ceiling, not tuned. elenchus: every
fix from an audit round lands with a `test_<gate>_refuses_<case>` guard.
hypomnema: the gate list is the part a caller needs before a run, so it lives in
`SKILL.md` rather than in the study.

## Step 4: Demonstrate on a contract over the limit

**Goal.** Run the demo path from the study's problem statement with real `forge`,
and record what it did.
**Entry.** Step 3's branch, gates green.
**Exit.** A fixture Foundry project in the plugin holds a contract whose deployed
runtime code exceeds 24576 bytes. Two recorded runs with `forge 1.7.1`: one
accepts a declared size class that brings it under the limit, and one refuses a
candidate that reaches the same number by deleting a `require`. Both evidence
records are committed, and the refusal names the `deleted-check` gate. Proved by
the committed evidence, the harness tests, both root suites and the Horos check.
**Files.** `plugins/hermes/skills/procrustes/fixtures/**`,
`plugins/hermes/skills/procrustes/SKILL.md` for the demo path,
`plugins/hermes/skills/procrustes/EVOLUTION.md`, `README.md` under
`plugins/hermes` if the plugin's own prose has to name the second skill,
`.horos/boundary.json` if the fixture earns a boundary entry.
**Tests.** A test that runs the demo end to end when `forge` is on `PATH` and
skips with a stated reason when it is not, so the demo cannot rot silently.
**Disciplines.** phylax: the fixture is a target repository the harness runs, so
its `foundry.toml` states plainly that `ffi` stays off. ephoros: the committed
evidence is the record that shows the two runs happened. metron: none. elenchus:
if the real `forge` disagrees with the fake one, that failure is the step's own
and gets worked to its cause rather than papered over by loosening the parse.
hypomnema: the demo path belongs in `SKILL.md`, and the fixture's reason for
existing belongs beside it in the fixture directory.
