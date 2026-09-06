# Runbook: Metron recorder, time a command into the run file the check reads

Derived from `.hexaemeron/study.md`. The selected design is the one the record
below locks; no step reopens that choice.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 578d33bbf14a32dd663ee4df52c60c6350b5d1adde0956851f91e75518b16843
candidate | subcommand-wall-clock
```

### Source receipts

```text
starting ref: 7d12d63e13fe193fcc1f8827b393f8aa51161731
run branch: fiat/371-metron-recorder-a-time-verb-that-writes-the
task issue: https://github.com/wildcat-finance/skills/issues/371
frontier ledger: plugins/hexaemeron/skills/metron/EVOLUTION.md at metron-v1.1.0, 2 rows
```

The topic is one capability with four dependency-ordered steps, so there is
no module table. Step 1 freezes the accepted proposition in the tracked tree.
Step 2 lands the bounded runner and the `time` verb for a single repetition,
which is where every subprocess boundary opens. Step 3 adds the repeat count,
the aggregation and the spread, which is the frontier's acceptance surface,
and records the run-file decision. Step 4 demonstrates, appends the evolution
row, and moves every surface an installation reads. No `version-relations`
block is declared: the ledger row this run owes is an evolution row, and the
declared relation covers generation rows only, so the literal `metron-v2.1.0`
stands. The plugin package version is a global identifier that concurrent
runs take first, so step 4 picks it after enumerating every local and remote
ref and re-checks it before the integration push.

Two suites are named in every step. The repository-wide suite is
`python3 -m unittest discover -s tests`, which hosted CI gates on. Inside this
run worktree it is red on two `test_agent_instruction_corpus` tests because
the prover reads the run's own `.hexaemeron/design-evidence.json`
([skills#1228](https://github.com/wildcat-finance/skills/issues/1228)), so
every step holds that suite's exit against a clean detached snapshot of the
committed head:

```bash
git worktree add --detach tmp/snapshot <sha>
(cd tmp/snapshot && GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false python3 -m unittest discover -s tests)
git worktree remove --force tmp/snapshot
```

The plugin suite is `python3 plugins/hexaemeron/tests/run_tests.py <fresh
report path>`, whose report path must not already exist. Both must exit 0 at
every step's exit, and the Horos boundary is rescanned after staging and
before every commit, because every added file moves `files_walked`.

## Step 1: Publish the accepted recorder specification

**Goal.** Commit byte-identical tracked copies of the receipted study and
runbook so the accepted proposition is in the repository before any code
changes.

**Entry.** The run branch `fiat/371-metron-recorder-a-time-verb-that-writes-the`
at starting ref `7d12d63e13fe193fcc1f8827b393f8aa51161731`, working tree
clean. No tracked file from this run exists at entry.

**Exit.** The following all hold on the committed head:

1. `docs/metron-recorder-study.md` is byte-identical to the receipted
   `.hexaemeron/study.md`, and `docs/metron-recorder-runbook.md` is
   byte-identical to the receipted `.hexaemeron/runbook.md`, proved by
   `cmp -s` on each pair exiting 0.
2. `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study docs/metron-recorder-study.md`
   and `python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py docs/metron-recorder-runbook.md`
   exit 0.
3. `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/metron-recorder-study.md docs/metron-recorder-runbook.md`
   reports no defect, and
   `python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py README.md AGENTS.md .agents/skills/promise-machine/SKILL.md .agents/skills/promise-machine/PORTABLE.md plugins docs`
   exits 0.
4. `python3 plugins/horos/skills/horos/scripts/horos.py check .` exits 0.
5. The repository-wide suite `python3 -m unittest discover -s tests` exits 0
   on the clean detached snapshot, `python3 plugins/hexaemeron/tests/run_tests.py .hexaemeron/test-reports/step-1-exit.json`
   exits 0, and `git diff --check` exits 0.

**Files.** Create `docs/metron-recorder-study.md` and
`docs/metron-recorder-runbook.md`. Rewrite `.horos/boundary.json` only through
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`. Append
to `audit/rounds/fiat-371-metron-recorder-time-a-command-into-the-run.md`
and its synopsis only for Warden round records. No script, test, manifest,
ledger or dependency changes.

**Tests.** None written; the two receipted artefacts are copied without
rewriting. The source-bound Elenchus runner contract for any audit repair is:
test command `python3 plugins/hexaemeron/tests/run_tests.py {report}`, whose
report path must stay inside the worktree and must not already exist; report
format `elenchus.unittest.v1`; report file
`.hexaemeron/test-reports/step-1.json`. A missing, stale, empty, malformed or
infrastructure-failed report is `inconclusive`, never evidence that a repair
is guarded.

**Disciplines.** phylax: none, this step adds static Markdown and opens no
input or execution boundary. ephoros: none, nothing here runs unattended.
metron: none, no performance claim is made. elenchus: a byte-identity, link,
structural, boundary or suite regression stops the step and any repair uses
the runner above. hypomnema: the tracked study and runbook are the durable
homes the accepted proposition selected.

## Step 2: Time one command in a bounded process group

**Goal.** `scripts/metron.py time` runs one fixed argv without a shell, once,
in its own process group under a timeout and an output cap, and writes a run
file that `check` reads unedited, or exits non-zero and writes nothing.

**Entry.** Step 1's signed, audited, prose-checked branch tip. `metron.py`
offers exactly two subcommands, `check` and `record`, and
`test_both_subcommands_are_offered` pins that count; nothing in the plugin
starts a subprocess.

**Exit.** The following all hold on the committed head:

1. `python3 plugins/hexaemeron/skills/metron/scripts/metron.py time --name harvest.usdc.wall_clock --out <tmp>/run.json -- python3 -c pass`
   exits 0 and writes a run file whose top level is exactly `measurements`,
   `recorder` and an optional `note`; `measurements` holds the budget name
   mapped to one finite float in milliseconds; and `recorder` carries schema
   `metron-timed-run/v1`, `argv`, `cwd`, `repeat` 1, `warmup` 0,
   `timeout_ms`, `expect_exit`, `unit` `ms`, `aggregation`, one entry in
   `repetitions` with `index`, `wall_clock_ms`, `exit`, `stdout_bytes` and
   `stderr_bytes`, `recorded_at`, `platform` and `python`. No number sits at
   the top level, so `load_measurements` reads it unedited (study risks
   `stray-top-level-number`, `subprocess-argv`).
2. `python3 plugins/hexaemeron/skills/metron/scripts/metron.py check --budgets <tmp>/one-budget.json --run <tmp>/run.json`
   exits 0 against a one-budget file declaring `harvest.usdc.wall_clock` in
   `ms` with a limit the run sits under.
3. A command that exits other than `--expect-exit`, a command past
   `--timeout-seconds`, a stream past the 1 MiB cap, a grandchild that forked
   and outlived its parent, and a grandchild that called `setsid` and holds
   the pipes each make `time` exit 1 with one stderr line naming the
   repetition and the cause (`exit`, `timeout`, `output-cap`, `escaped`),
   and no run file exists afterwards; a pre-existing `--out` file is left
   with its previous bytes (study risks `process-group-teardown`,
   `group-escape`, `output-cap`, `timeout-bound`, `partial-run-file`,
   `failed-repetition-hidden`).
4. `--timeout-seconds` outside 1 to 3600, a missing `--`, an empty argv, and
   a command that cannot start each exit 2 before any command runs.
5. `python3 -m unittest plugins.hexaemeron.tests.test_metron_check` exits 0
   and `python3 .hexaemeron/measure_design.py --candidate subcommand-wall-clock --criterion recorder-suite-green`
   exits 0 and writes
   `.hexaemeron/reports/subcommand-wall-clock--recorder-suite-green.json`,
   resolving the design record's `recorder-suite-green` gate.
6. `python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins tests scripts docs`,
   `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins tests scripts docs`
   and the hypomnema lint from step 1 exit 0;
   `python3 plugins/horos/skills/horos/scripts/horos.py check .` exits 0; the
   repository-wide suite exits 0 on the clean detached snapshot;
   `python3 plugins/hexaemeron/tests/run_tests.py .hexaemeron/test-reports/step-2-exit.json`
   exits 0; `git diff --check` exits 0.

**Files.** Change `plugins/hexaemeron/skills/metron/scripts/metron.py` (the
`time` parser, the bounded runner, the run-file writer through
`write_atomically`) and `plugins/hexaemeron/tests/test_metron_check.py`.
Rewrite `.horos/boundary.json` only through the Horos scan. Append to the
run's audit file and synopsis only for Warden round records. No new file, no
dependency, no change to `check`, `record`, the verdicts or the fixtures.

**Tests.** Extend `plugins/hexaemeron/tests/test_metron_check.py`: the parser
offers three subcommands; the clean case writes the file with the fields
above and `check` reads it; the non-zero exit, timeout, output-cap,
forked-grandchild and `setsid`-grandchild cases exit 1 and leave no file; the
previous `--out` bytes survive a failure; the argument-bound cases exit 2;
the argv is passed as a list and never through a shell. Expected count 14 to
20 new tests, taking the module from 84 to between 98 and 104. The
source-bound Elenchus runner contract is: test command
`python3 plugins/hexaemeron/tests/run_tests.py {report}`, whose report path
must stay inside the worktree and must not already exist; report format
`elenchus.unittest.v1`; report file `.hexaemeron/test-reports/step-2.json`.

**Disciplines.** phylax: this step opens the subprocess boundary, and its
controls are the argv list, the process group, the timeout, the output cap
and the atomic write. ephoros: the run file's `recorder` block answers which
command produced the number under what bounds, and the stderr line answers
what failed. metron: none, no performance change is made; the recorder's own
overhead gate was measured at design lock. elenchus: each refusal case begins
red and is guarded by a test in the runner above. hypomnema: none, the
run-file decision is recorded in step 3 once the spread fields exist.

## Step 3: Repeat, aggregate and report the spread

**Goal.** `time` runs the command `--repeat` times after `--warmup` discarded
runs, writes the declared aggregation of the samples into the measurements
block and the spread beside it, and the reference and a decision record say
why the median and never the mean.

**Entry.** Step 2's signed, audited, prose-checked branch tip. `time` accepts
one repetition and writes `repeat` 1 with one sample.

**Exit.** The following all hold on the committed head:

1. `python3 plugins/hexaemeron/skills/metron/scripts/metron.py time --name harvest.usdc.wall_clock --repeat 5 --out <tmp>/run.json -- python3 -c pass`
   exits 0; the run file carries five entries in `repetitions`, `repeat` 5,
   `aggregation` `median`, and a `spread` object with `samples` 5, `min`,
   `p50`, `p95`, `max` and `relative_spread` equal to `(max - min) / p50`;
   the measurements value equals `p50`; percentiles are by nearest rank so
   `p95` of five samples equals `max` (study risks `aggregation-declared`,
   `spread-from-samples`).
2. `--aggregate p95` puts `p95` in the block and names it in `aggregation`;
   `--warmup 2` runs two discarded repetitions under the same bounds and
   records `warmup` 2 with five kept samples; a single kept sample writes
   `relative_spread` `null`.
3. `--repeat` outside 1 to 1000 and `--warmup` outside 0 to 100 exit 2
   before any command runs; a failure in any repetition, warm-up included,
   exits 1 and writes no file (study risks `repeat-bounds`,
   `failed-repetition-hidden`).
4. `python3 .hexaemeron/measure_design.py --candidate subcommand-wall-clock --criterion spread-read-by-check`
   exits 0 and writes
   `.hexaemeron/reports/subcommand-wall-clock--spread-read-by-check.json`,
   resolving the design record's `spread-read-by-check` gate.
5. `plugins/hexaemeron/skills/metron/references/budget-check.md` carries a
   "Timing a command" section stating the argument surface, the run-file
   shape, the `ms` unit, the aggregation rule, how `relative_spread` sets a
   budget's `variance`, and the exit codes (study risk `unit-mismatch`);
   `docs/decisions/drafts/record-timed-runs-at-the-median-with-spread.md`
   exists in the Hypomnema draft shape, that section cites it by its stable
   slug in the code-span form Hypomnema prescribes, and the hypomnema lint
   from step 1 exits 0.
6. `python3 -m unittest plugins.hexaemeron.tests.test_metron_check` exits 0;
   the phylax and ephoros lints from step 2 exit 0;
   `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/hexaemeron/skills/metron/references/budget-check.md docs/decisions/drafts/record-timed-runs-at-the-median-with-spread.md`
   reports no defect; `python3 plugins/horos/skills/horos/scripts/horos.py check .`
   exits 0; the repository-wide suite exits 0 on the clean detached snapshot;
   `python3 plugins/hexaemeron/tests/run_tests.py .hexaemeron/test-reports/step-3-exit.json`
   exits 0; `git diff --check` exits 0.

**Files.** Change `plugins/hexaemeron/skills/metron/scripts/metron.py`,
`plugins/hexaemeron/tests/test_metron_check.py` and
`plugins/hexaemeron/skills/metron/references/budget-check.md`. Create
`docs/decisions/drafts/record-timed-runs-at-the-median-with-spread.md`.
Rewrite `.horos/boundary.json` only through the Horos scan. Append to the
run's audit file and synopsis only for Warden round records.

**Tests.** Extend `plugins/hexaemeron/tests/test_metron_check.py`: the block
value equals `p50` at repeat 5; `p95` by nearest rank; `--aggregate p95`;
warm-up runs are discarded and counted; `null` spread at one sample; the
bound cases exit 2; a failing warm-up writes no file; `relative_spread`
arithmetic on fixed samples. Expected count 8 to 12 new tests. The
source-bound Elenchus runner contract is: test command
`python3 plugins/hexaemeron/tests/run_tests.py {report}`, whose report path
must stay inside the worktree and must not already exist; report format
`elenchus.unittest.v1`; report file `.hexaemeron/test-reports/step-3.json`.

**Disciplines.** phylax: none new, the warm-up repetitions reuse step 2's
bounded runner unchanged. ephoros: `aggregation`, `spread.samples` and
`relative_spread` answer whether the block value is one sample or a spread
and how wide. metron: this is the acceptance surface, the spread is the
number a `variance` is set from, and the reference says how. elenchus: each
arithmetic and bound case begins red and is guarded in the runner above.
hypomnema: the run-file shape outlives its writer, so the median-with-spread
decision gets a draft record cited by stable slug.

## Step 4: Demonstrate the recorder and close the frontier

**Goal.** Run the proving demo from the study's problem statement, append the
`metron-v2.1.0` evolution row, move the skill and package versions every
installation reads, and reconcile the marketplace prose the frontier run
owes.

**Entry.** Step 3's signed, audited, prose-checked branch tip. The ledger
holds two rows at `metron-v1.1.0`; `SKILL.md` declares version `1.1.0`; the
Hexaemeron package declares `1.6.27` on five surfaces and in two test
literals.

**Exit.** The following all hold on the committed head:

1. From the repository root on a clean tree, the three demo commands from
   the study's problem statement exit 0:
   `python3 plugins/hexaemeron/skills/metron/scripts/metron.py time --name harvest.usdc.wall_clock --repeat 5 --out <tmp>/run.json -- python3 -c pass`,
   `python3 plugins/hexaemeron/skills/metron/scripts/metron.py check --budgets <tmp>/one-budget.json --run <tmp>/run.json`
   against a one-budget file in `ms`, and
   `python3 -m unittest plugins.hexaemeron.tests.test_metron_check`.
2. `plugins/hexaemeron/skills/metron/EVOLUTION.md` carries exactly one new
   history row, `metron-v2.1.0`, axis `evolution`, a new frontier revision,
   a digest recomputed over the frontier line it describes, and either one
   evidenced next job or `mature`; the header names the same version, and
   `python3 -m unittest tests.test_evolution_contract` exits 0.
3. `plugins/hexaemeron/skills/metron/SKILL.md` declares version `2.1.0`, its
   current-state line describes the recorder, its "Measure how you will
   re-measure" and "Budgets" prose point at `time`, and
   `plugins/hexaemeron/skills/metron/DEMONSTRATION.md` still verifies under
   `python3 scripts/demonstrations.py check --root .` (study risk
   `demo-source-digest`).
4. The Hexaemeron package version exceeds `1.6.27` and every version any
   local or remote ref claims in `plugins/hexaemeron/.claude-plugin/plugin.json`,
   is identical in `plugins/hexaemeron/.codex-plugin/plugin.json`,
   `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`,
   `tests/test_version_propagation.py` and
   `plugins/hexaemeron/tests/test_phylax_model_proxy.py`, and
   `python3 -m unittest tests.test_version_propagation` exits 0 (study risk
   `version-surfaces`). The number is re-checked against every ref before the
   integration push.
5. Every mutable first-party marketplace prose surface that describes
   Metron was cold-read and reconciled: `plugins/hexaemeron/README.md`,
   root `README.md`, `plugins/hexaemeron/AGENTS.md`, the marketplace
   descriptions, and `plugins/hexaemeron/skills/metron/references/budget-check.md`;
   `python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py`
   reports no defect on each changed file, and
   `python3 scripts/check_public_front_door.py` exits 0 where the root README
   changed.
6. `python3 scripts/portable_promise_machine.py check` and
   `python3 scripts/promise_machine.py check` exit 0; the phylax, ephoros and
   hypomnema lints exit 0; `python3 plugins/horos/skills/horos/scripts/horos.py check .`
   exits 0; the repository-wide suite exits 0 on the clean detached snapshot;
   `python3 plugins/hexaemeron/tests/run_tests.py .hexaemeron/test-reports/step-4-exit.json`
   exits 0; `git diff --check` exits 0.

**Files.** Change `plugins/hexaemeron/skills/metron/EVOLUTION.md`,
`plugins/hexaemeron/skills/metron/SKILL.md`,
`plugins/hexaemeron/.claude-plugin/plugin.json`,
`plugins/hexaemeron/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`,
`.agents/plugins/marketplace.json`, `tests/test_version_propagation.py`,
`plugins/hexaemeron/tests/test_phylax_model_proxy.py`, and only those prose
files under `plugins/hexaemeron/`, `README.md` and `AGENTS.md` that the cold
read finds stale. Rewrite `.horos/boundary.json` only through the Horos
scan. Append to the run's audit file and synopsis only for Warden round
records. No change to `metron.py` or its tests beyond what the demo proves
already exists.

**Tests.** No new test module. `tests/test_evolution_contract.py` and
`tests/test_version_propagation.py` pin the ledger and the version surfaces,
and `plugins/hexaemeron/tests/test_fiat_skill.py` derives the README count of
phase skills that ship a check, which stays at six. The source-bound Elenchus
runner contract is: test command
`python3 plugins/hexaemeron/tests/run_tests.py {report}`, whose report path
must stay inside the worktree and must not already exist; report format
`elenchus.unittest.v1`; report file `.hexaemeron/test-reports/step-4.json`.

**Disciplines.** phylax: none, this step changes versions and prose and opens
no boundary. ephoros: none, nothing here runs unattended. metron: the demo
runs the recorder and holds its run to a budget, which is the measurement the
frontier asked for. elenchus: a ledger, version-propagation or
demonstration regression stops the step and any repair uses the runner
above. hypomnema: the evolution row is the ledger's own record of this job,
and the plugin version bump is the release note an installation reads.

### Amendment -- 2026-09-06

**What changed.** Complete replacement Files: Create `docs/metron-recorder-study.md` and `docs/metron-recorder-runbook.md`. Rewrite `.horos/boundary.json` only through `python3 plugins/horos/skills/horos/scripts/horos.py scan . --write` and `.horos/census.json` only through `python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`. Append to `audit/rounds/fiat-371-metron-recorder-a-time-verb-that-writes-the.md` and its synopsis only for Warden round records. No script, test, manifest, ledger or dependency changes.
**Why.** The receipted Files clause named the audit log of the halted predecessor run, `audit/rounds/fiat-371-metron-recorder-time-a-command-into-the-run.md`, where the controller derives this run's log as `audit/rounds/fiat-371-metron-recorder-a-time-verb-that-writes-the.md`; step 1 round 1 recorded the discrepancy as a lead. The same clause named `--census --write` as the command that rewrites `.horos/boundary.json`, and that flag writes `.horos/census.json` while the plain `--write` rewrites the boundary, so both generated files are now named with the command that owns each.
**Steps touched.** Step 1's Files field only.
**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds.
