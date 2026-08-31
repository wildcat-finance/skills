# Runbook: establish a report-only dead-code baseline

This run starts from `main` at
`0698092d27871031b6d5521d77f6e8d8dc5dc937`. Every command below uses the
repository's Python 3.14.6 interpreter. The four steps implement the chosen
design from the receipted study; none may turn a candidate count into a merge
gate or deletion authority.

## Step 1: Commit the specification and scaffold the report contract

**Goal.** Publish the accepted design and create the deterministic universe,
report model, schema, root check, and report-only workflow without claiming any
reachability result.

**Entry.** `fiat/437-establish-a-report-only-dead-code-baseline` at
`0698092d27871031b6d5521d77f6e8d8dc5dc937`, with the study receipt verified and
no product changes in the worktree. Before editing, confirm ADR-051 is still the
next free decision identity on `origin/main`; a collision stops the step for a
receipted runbook amendment.

**Exit.** `docs/dead-code/study.md` and `docs/dead-code/runbook.md` are
byte-identical copies of the receipted artefacts. ADR-051 records the
report-only authority, Horos and checked-runner ownership boundaries, and the
rejected per-plugin and Horos-widening designs. `scripts/dead_code.py report`
discovers a non-empty Git-tree universe, applies hard Horos file and directory
classifications, emits equivalent text and schema-valid JSON from one ordered
model, and reports that no analyser has run rather than calling the tree clean.
The schema fixes finding, status, universe and tool identities. The `dead-code`
scope and report-only workflow invoke the focused suite and fail only on command
or report failure. `python3 tests/emit_dead_code_report.py
.elenchus/fiat-437-step-1.json`, `python3 scripts/run_checks.py --scope
dead-code`, both Protasis checks, Imprimatur over shipped prose, and `git diff
--check` exit 0.

**Files.** Create `docs/dead-code/study.md`, `docs/dead-code/runbook.md`,
`docs/decisions/ADR-051-keep-dead-code-discovery-report-only.md`,
`schemas/dead-code-report-v1.schema.json`, `scripts/dead_code.py`,
`tests/test_dead_code.py`, `tests/emit_dead_code_report.py`, and
`.github/workflows/dead-code.yml`. Update `.gitignore` and
`tests/check-map-v1.json`. Regenerate `.horos/boundary.json`,
`.horos/candidates.json`, and `.horos/census.json` last if the Horos scan changes
them.

**Tests.** Add at least twenty focused cases for clean-tree binding, empty-walk
refusal, malformed and duplicate-key Horos input, hard file and descendant tree
exclusion, prefix siblings, evidence carriage, sorted output, text/JSON parity,
schema shape, analyser-status wording, unsafe output paths, partial writes,
workflow report-only semantics, and check-map ownership. The Elenchus runner
contract is test command `python3 tests/emit_dead_code_report.py {report}`;
report format `unittest-json-v1`; expected schema `elenchus.unittest.v1`;
report file `.elenchus/fiat-437-step-1.json`. A missing, stale, empty, malformed
or infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: tracked Git bytes, Horos JSON and output paths cross
input and filesystem boundaries, so reads are bounded and writes are confined
and atomic. ephoros: report headers and workflow summaries must identify the
tree, universe and analyser states. metron: none, this step makes no speed
change. elenchus: the historical classified-directory bug is reproduced red on
the entry construction and retained as a guard. hypomnema: ADR-051 owns the
expensive authority and ownership decision; the schema owns the record shape.

## Step 2: Add bounded Python reachability and execution signals

**Goal.** Add Python static candidates and a Python 3.14 execution probe over
the exact check plan without importing analysed modules or replacing the
checked runner.

**Entry.** Step 1's signed, audited and prose-checked branch tip. Its report
model, universe and schema are the only output surface this step extends.

**Exit.** The Python analyser parses bounded tracked source without importing
it and reports unused imports and locals, unreachable statements and constant
branches, import-graph reachability, dynamic-reference downgrades, and per-file
parse status. The execution probe wraps only Python commands selected by
`scripts/run_checks.py`, uses Python 3.14 `sys.monitoring`, records named lines
and branches per process, restores callbacks and masks on exit, and marks a
failed or incomplete check `degraded` without producing never-executed
findings. A fixture demonstrates one observed and one unobserved branch while a
dynamic registration, CLI entry point, decorator registration, `__all__`, and
intentional test fixture survive as negative cases. `python3
tests/emit_dead_code_report.py .elenchus/fiat-437-step-2.json`, `python3
scripts/dead_code.py coverage --scope dead-code --output
.dead-code/coverage.json`, `python3 scripts/dead_code.py report --json
--coverage .dead-code/coverage.json --analyser python,coverage`, `python3
scripts/run_checks.py --scope dead-code`, and `git diff --check` exit 0.

**Files.** Extend `scripts/dead_code.py`,
`schemas/dead-code-report-v1.schema.json`, `tests/test_dead_code.py`, and
`tests/emit_dead_code_report.py`. Create only the minimum checked-in monitoring
helper under `scripts/` if process isolation requires one. Update
`.gitignore` for ignored coverage records. Regenerate the three `.horos/`
records last if their deterministic scan changes them.

**Tests.** Extend the focused suite by at least twenty-five cases covering
scope-plan binding, wrapper recursion refusal, monitoring cleanup, line and
branch identity, multiple processes, failed and skipped checks, syntax errors,
unused imports and locals, unreachable statements, computed imports,
decorators, `getattr`, `__all__`, CLI seeds, output bounds and deterministic
aggregation. Each fixed failure is red against Step 1's tree. The Elenchus
runner contract is test command `python3 tests/emit_dead_code_report.py
{report}`; report format `unittest-json-v1`; expected schema
`elenchus.unittest.v1`; report file `.elenchus/fiat-437-step-2.json`. A missing,
stale, empty, malformed or infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: Python source and check argv are untrusted; parsing
never imports source, the existing runner owns selection and subprocess
budgets, and instrumentation writes only bounded process records. ephoros:
status records answer which checks ran, degraded, failed or were unavailable
and which coverage bytes they produced. metron: the 60-second static-report
budget is measured before and after any speed-motivated change; otherwise no
optimisation is authorised. elenchus: each parser, graph or monitoring failure
is reduced to a fixture, shown red, fixed at its cause and guarded.
hypomnema: implementation comments record why dynamic references lower
confidence and why failed coverage cannot imply absence.

## Step 3: Add repository-graph and optional Solidity signals

**Goal.** Report orphan candidates across repository declarations and bounded
Slither/Forge evidence while preserving every unavailable or degraded state.

**Entry.** Step 2's signed, audited and prose-checked branch tip with Python
signals stable under the v1 schema.

**Exit.** The repository analyser reports candidates for fixtures, schemas,
documents, CLI declarations, generated copies, routers, manifests and check-map
objects only when it can name the parsed edge set and nearest computed-reference
boundary. Existing Promise Machine, Hypomnema, Horos and check-map checks are
invoked or consumed rather than copied. Foundry projects are discovered from
tracked configuration; Slither `dead-code` and `unused-state` JSON and Forge
coverage are run through fixed argv with project attribution and version
capture when available. Tool absence is `not-available`; build, timeout or
parse failure is `degraded` or `failed`, never zero findings. `python3
tests/emit_dead_code_report.py .elenchus/fiat-437-step-3.json`, `python3
scripts/dead_code.py report --json --analyser repository,solidity`, `python3
scripts/run_checks.py --scope dead-code`, all existing Promise Machine and
check-map validation selected by the changed scope, and `git diff --check` exit
0.

**Files.** Extend `scripts/dead_code.py`,
`schemas/dead-code-report-v1.schema.json`, `tests/test_dead_code.py`, and
`tests/emit_dead_code_report.py`. Add bounded fixture files below
`tests/fixtures/dead-code/` only when inline temporary repositories cannot
prove a case. Regenerate the three `.horos/` records last if required.

**Tests.** Extend the focused suite by at least twenty cases: one positive and
one retained negative case for every repository object family; dynamic and
computed references; malformed declarations; empty discovery; absent Slither
or Forge; non-zero, timed-out, oversized and malformed tool output; multiple
Foundry projects; fixed argv and cwd; detector mapping; and finding/report
parity. The Elenchus runner contract is test command `python3
tests/emit_dead_code_report.py {report}`; report format `unittest-json-v1`;
expected schema `elenchus.unittest.v1`; report file
`.elenchus/fiat-437-step-3.json`. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: repository declarations and external tool output are
bounded hostile input, and Slither/Forge use fixed argv, no shell, declared cwd
and time/output ceilings. ephoros: each project and object family reports its
version, status, duration, evidence count and refusal reason. metron: no speed
claim; subprocess deadlines are termination controls, not performance results.
elenchus: every adapter failure is reproduced at the parser or process boundary
and its guard stays in the focused suite. hypomnema: no new standing decision;
the v1 schema and ADR-051 already own the adapter and authority boundaries.

## Step 4: Pin the baseline, check suppressions and demonstrate the prototype

**Goal.** Bind the current candidate inventory to exact evidence, publish the
operator path, and prove the complete report-only prototype on a clean tree.

**Entry.** Step 3's signed, audited and prose-checked branch tip with every
analyser represented in the report model.

**Exit.** `.dead-code/baseline.json` binds commit, Git tree, universe digest,
analyser versions and statuses, stable finding identities, and suppression
digest. `.dead-code/suppressions.json` uses a closed schema whose entries name
one exact candidate, reason, owner and still-present target; broad, duplicate,
unknown, stale and unused suppressions refuse. `baseline --write` uses a
confined atomic replacement and `baseline --check` is read-only. Operator docs
state that findings are candidates, counts do not gate development, and a diff
gate needs a separate decision. The four study demo commands run from a clean
tree; text and JSON identities agree; all positive and negative fixtures pass;
the static Python plus repository report has three warm runs recorded and stays
within the study's 60-second budget; the complete selected repository check
plan, prose gates, audit-synopsis currency, Horos check and `git diff --check`
exit 0. No source candidate is deleted or rewritten.

**Files.** Extend `scripts/dead_code.py`,
`schemas/dead-code-report-v1.schema.json`, `tests/test_dead_code.py`, and
`tests/emit_dead_code_report.py`. Create
`schemas/dead-code-suppressions-v1.schema.json`,
`.dead-code/baseline.json`, `.dead-code/suppressions.json`,
`docs/promise-machine/dead-code-v1.md`, and
`docs/dead-code/measurement.md`. Update `.github/workflows/dead-code.yml` and
`tests/check-map-v1.json` only if the demonstrated command differs from the
Step 1 stub. Regenerate `.horos/boundary.json`, `.horos/candidates.json`, and
`.horos/census.json` last.

**Tests.** Extend the focused suite by at least twenty cases for canonical
identity, commit/tree/universe/version/status/suppression drift, unknown and
duplicate fields, broad or stale suppressions, symlink and interrupted writes,
stable rereads, text/JSON/baseline parity, finding-count non-gating, dirty-tree
refusal and the exact four-command demo. The Elenchus runner contract is test
command `python3 tests/emit_dead_code_report.py {report}`; report format
`unittest-json-v1`; expected schema `elenchus.unittest.v1`; report file
`.elenchus/fiat-437-step-4.json`. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`.

**Disciplines.** phylax: baseline and suppression reads and writes use closed
schemas, confined no-follow paths, stable rereads and atomic replacement.
ephoros: the final report and workflow summary carry tree, analyser, change and
non-gating status for operators. metron: three warm static-report runs record
command, commit, interpreter, median and spread against the 60-second budget.
elenchus: every final failure keeps its smallest red reproducer and guard;
candidate count alone remains a green result. hypomnema: the operator guide is
the durable home for commands and failure recovery, measurement owns the
runtime observation, and ADR-051 remains the standing decision.

### Amendment -- 2026-08-29

**What changed.** Complete replacement Exit: `docs/dead-code/study.md` and
`docs/dead-code/runbook.md` are byte-identical copies of the receipted
artefacts, including this amendment in the runbook copy. ADR-051 records the
report-only authority, Horos and checked-runner ownership boundaries, and the
rejected per-plugin and Horos-widening designs. `scripts/dead_code.py report`
discovers a non-empty Git-tree universe, applies hard Horos file and directory
classifications, emits equivalent text and schema-valid JSON from one ordered
model, and reports that no analyser has run rather than calling the tree clean.
The schema fixes finding, status, universe and tool identities. The `dead-code`
scope and report-only workflow invoke the focused suite and fail only on command
or report failure. The workflow follows the repository Python contract, and
`tests/test_python_contract.py` registers and checks it. `python3
tests/emit_dead_code_report.py .elenchus/fiat-437-step-1.json`, `python3 -m
unittest tests.test_dead_code tests.test_python_contract.PythonRuntimeContractTests
-v`, both Protasis checks, Imprimatur over shipped prose, Phylax, Ephoros,
Hypomnema, the Horos check, and `git diff --check` exit 0. `python3
scripts/run_checks.py --scope dead-code` runs the complete changed-path closure;
its only permitted failed checks are `hexaemeron-suite`, `lazarus-suite`,
`root-suite`, and `synkrisis-suite`, each reproduced at entry commit
`0698092d27871031b6d5521d77f6e8d8dc5dc937` and attributed respectively to the
Darwin `/var` symlink, missing locked Lazarus dependencies, the same Darwin
`MP407` path handling, and Darwin RSS units. Every other selected check exits 0.
Complete replacement Files: Create `docs/dead-code/study.md`,
`docs/dead-code/runbook.md`,
`docs/decisions/ADR-051-keep-dead-code-discovery-report-only.md`,
`schemas/dead-code-report-v1.schema.json`, `scripts/dead_code.py`,
`tests/test_dead_code.py`, `tests/emit_dead_code_report.py`, and
`.github/workflows/dead-code.yml`. Update `.gitignore`,
`tests/check-map-v1.json`, and `tests/test_python_contract.py`. Regenerate
`.horos/boundary.json`, `.horos/candidates.json`, and `.horos/census.json` last
if the Horos scan changes them. Complete replacement Tests: Add at least twenty
focused cases for clean-tree binding, empty-walk refusal, malformed and
duplicate-key Horos input, hard file and descendant tree exclusion, prefix
siblings, evidence carriage, sorted output, text/JSON parity, schema shape,
analyser-status wording, unsafe output paths, partial writes, workflow
report-only semantics, check-map ownership, and the repository Python workflow
contract. The Elenchus runner contract is test command `python3
tests/emit_dead_code_report.py {report}`; report format `unittest-json-v1`;
expected schema `elenchus.unittest.v1`; report file
`.elenchus/fiat-437-step-1.json`. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`. Run the focused suite and Python
workflow contract directly. Run the complete checked-runner closure and compare
any failure with the exact entry commit; only the four host or dependency
failures named in the replacement Exit are admissible, and every other check
must pass.
**Why.** Editing the check-map authority correctly expands the requested
`dead-code` scope to the complete changed-path closure. The entry commit already
fails four selected suites on this macOS host, so requiring the aggregate runner
to exit 0 confused inherited environment failures with Step 1 regressions. The
first run also exposed two Step 1 integration defects: the workflow did not use
the exact quoted Python pin form, and the closed workflow inventory did not know
about it. This amendment keeps the full closure visible, adds the missing
contract file to scope, and admits only failures reproduced at the exact entry
commit.
**Steps touched.** Step 1.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit
holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
