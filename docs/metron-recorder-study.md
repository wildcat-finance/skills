# Metron recorder: time a command into the run file the check reads

Assuming, unless corrected:

1. The frontier text and its acceptance condition in
   `plugins/hexaemeron/skills/metron/EVOLUTION.md` are read verbatim and are
   not changed by this run: a timed command yields a run the check reads
   unedited, a repeat count reports the spread the variance is meant to be set
   from, and both suites pass.
2. Work starts from `main` at `7d12d63e13fe193fcc1f8827b393f8aa51161731` on
   branch `fiat/371-metron-recorder-a-time-verb-that-writes-the`, with the
   interpreter pinned in `.python-version` (3.14.6) and the standard library
   only. No dependency is added without asking.
3. The recorder is a third subcommand of the existing
   `plugins/hexaemeron/skills/metron/scripts/metron.py`, named `time`, rather
   than a new file. The design record below selects that mechanically; the
   name is chosen because the run file it writes is what `check` reads and
   `record` ledgers, and one file keeps the three verbs and their shared
   helpers together.
4. The value written into the measurements block is the median of the kept
   repetitions, in milliseconds as a float rounded to three decimals, with the
   aggregation named in the run file and `--aggregate p95` as the only
   alternative. There is no mean, because `SKILL.md` and the Ephoros lint
   (`E003`) both refuse one.
5. A failed repetition writes no run file. The recorder exits 1 and says which
   repetition failed and why; a partial run that the check could read would
   pass silently.
6. The completed job appends exactly one evolution row, `metron-v2.1.0`, and
   bumps the Hexaemeron plugin package version from 1.6.27 on the five
   surfaces `tests/test_version_propagation.py` checks, so installations
   receive the new subcommand. The concrete version token is the controller's
   statement; the runbook may declare a `version-relations` row for
   `metron` instead of the literal, which is Fiat's call.
7. Open issues [#328](https://github.com/wildcat-finance/skills/issues/328)
   (`metron-1`, attempt ledger home) and
   [#414](https://github.com/wildcat-finance/skills/issues/414) (`metron-3`,
   histogram-to-baseline path) stay open and untouched.
8. Inside this run worktree the root suite is red on two
   `test_agent_instruction_corpus` tests because the prover reads
   `.hexaemeron/design-evidence.json`
   ([skills#1228](https://github.com/wildcat-finance/skills/issues/1228)).
   Step exits are held against a clean detached snapshot of the committed
   head, never against the dirty worktree.

I will proceed on these unless corrected.

## 1. Problem statement

Metron ships a budget check that holds a declared budget mechanically and
measures nothing: `scripts/metron.py check` reads a run file that whatever
measured the workload wrote. The number a budget is held to is therefore only
as good as the caller's file, and `SKILL.md` asks the reader to "repeat enough
to see the spread" with no tool to do it.

This run ships the recorder. `python3 scripts/metron.py time --name <budget>
--repeat N --out run.json -- <argv...>` runs one fixed argv, no shell, N times
in its own process group under a timeout, records the wall clock of each
repetition from `time.monotonic_ns()`, and writes one run file in exactly the
shape `check` reads: a `measurements` block keyed by the budget name the caller
passed, holding the median, and a `recorder` block beside it carrying the
argv, the repetitions, every sample, the spread (`min`, `p50`, `p95`, `max`,
`relative_spread`), the aggregation rule, the timeout and the platform. The
relative spread is `(max - min) / p50`, which is the number a budget's
`variance` is set from.

The user is a contributor holding a wall-clock budget in a repository that
already declares one in `metron-budgets.json`, and the Fiat controller when a
step's Metron discipline asks for a measurement taken the same way twice.

A working prototype means all three of these commands exit 0 from the
repository root on a clean tree:

```bash
python3 plugins/hexaemeron/skills/metron/scripts/metron.py time \
  --name harvest.usdc.wall_clock --repeat 5 --out /tmp/run.json -- python3 -c pass
python3 plugins/hexaemeron/skills/metron/scripts/metron.py check \
  --budgets plugins/hexaemeron/tests/fixtures/metron/metron-budgets.json --run /tmp/run.json
python3 -m unittest plugins.hexaemeron.tests.test_metron_check
```

The second command proves the run is read unedited: with the shipped budget
file it reports `unmeasured` for the two other declared budgets and exits 1,
which is the correct verdict for a run that measured one budget; the proving
demo uses a one-budget file so the exit is 0. The design record's
`spread-read-by-check` gate encodes exactly that demo and resolves at step 3.
The registered demonstration path in `DEMONSTRATION.md` already runs the test
module, which gains the recorder tests, so the demo path does not change.

Success criteria, each checkable by a command:

- `time` with `--repeat 5` writes a run file whose `measurements` value equals
  the `p50` of the five recorded samples, and `check` reads it with no edit.
- `time` on a command that exits non-zero, exceeds its timeout, exceeds the
  output cap, or leaves a process outside its group holding the pipes exits 1
  and writes no run file.
- `time` never invokes a shell; the argv after `--` is passed as a list.
- `python3 -m unittest plugins.hexaemeron.tests.test_metron_check` and both
  suites named in section 3 pass on the committed head.

## 2. Prior art

**In the repository.** The last two merged pull requests that changed
`plugins/hexaemeron/skills/metron/` were read in full:

- [skills#1238](https://github.com/wildcat-finance/skills/pull/1238), merged
  2026-09-06 through the front-door run's integration merge
  [skills#1330](https://github.com/wildcat-finance/skills/pull/1330)
  (commits `b2f0b3da` and `c939a2b8`). It added and then re-cited
  `metron/DEMONSTRATION.md` on the demonstration lane, which is independent
  of the behaviour frontier. Its one accepted item, `S2-R1-03`, is the ADR
  number collision at sync, which belongs to that run and is refused here.
  Nothing it carried forward touches the recorder.
- [skills#211](https://github.com/wildcat-finance/skills/pull/211), merged
  2026-08-19, shipped the check and named this recorder as the next frontier.
  It carried one item forward by name, the plugin version bump, which
  [skills#212](https://github.com/wildcat-finance/skills/pull/212) closed
  the same day (1.4.0 to 1.5.0). This run carries that item forward as its
  own bump in the last step, because a subcommand that installations cannot
  see does not close the frontier.

The audit rounds of the run that shipped the check (`Metron budget check`,
2026-08-19, eight rounds) live in the root `audit/AUDIT.md`. They were read
through `audit/AUDIT_SYNOPSIS.md` lines 115 to 122, after
`python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .`
ran from the target root and exited 0 with every one of the 70 committed
synopses reported `committed=match`. The rounds carry no finding rows in the
synopsis view, four legacy fields `[missing legacy field: audit-schema]`,
`[missing legacy field: covered]`, `[missing legacy field: not-checked]` and
`[missing legacy field: elenchus-verdict]` on every round, which remain
unknown, and three leads not pursued:

- `MAX_BYTES` caps each file at 4 MiB and nothing caps the number of budgets
  a file may declare (step 1, rounds 1 to 3). Refused by name here: the
  recorder writes one budget per run and reads no budget file, so the lead is
  untouched and stays open with the check.
- `append_ledger` is atomic enough on a local filesystem but not across a
  network mount (step 2, rounds 1 and 2). Refused by name: the recorder does
  not append; it writes the run file through `write_atomically`, which the
  design record's `atomic-write-reused` gate checks.
- The plugin version was not bumped by that run (step 3, rounds 1 and 2).
  Carried forward: the last step bumps it.

The front-door run's per-run audit file,
`audit/rounds/fiat-shoggoth-front-door-derived.md`, is in scope because its
step 2 touched `metron/DEMONSTRATION.md`; its synopsis
`audit/rounds/fiat-shoggoth-front-door-derived.synopsis.md` was the read
view under the same exit-0 check. Every round there is `fiat-audit-round/v2`
with a `Covered` list; none names a metron finding.

The bounded runner this recorder copies is in `scripts/demonstrations.py`:
`execute_command` (lines 1571 to 1650) starts the child with
`start_new_session=True`, times it with `time.monotonic_ns()`, drains both
pipes on threads under `MAX_OUTPUT_BYTES`, kills the process group on every
path, and reports `escaped_group` when a reader is still blocked after the
group is down, which the runner refuses as `D085`. `_run_command` and
`run_record` (lines 1877 to 2031) aggregate `duration_ms` per repetition and
`slowest_ms` per record. `tests/test_demonstrations.py` lines 1740 to 1786
pin the two grandchild cases: one that forks and exits 0, one that calls
`setsid`. `_children_max_rss_bytes` (line 1653) reads `RUSAGE_CHILDREN` and
is the reason the rusage candidate below fails its gate.
`plugins/hexaemeron/skills/fiat/scripts/hexctl.py` `bounded_probe` and
`bounded_run` (lines 11762 to 11861) hold the same discipline for the
controller: fixed argv, `shell=False`, a hard timeout, a hard output cap.

The recorder cannot import any of that. `scripts/demonstrations.py` is
outside `plugins/hexaemeron/`, and the installed copy of the plugin under
`~/.claude/plugins/cache/wildcat-labs/hexaemeron/<version>/` ships only the
plugin tree. The design record's `standalone-from-plugin-cache` gate computes
that from the tree and removes the import candidate.

**In the organisation.** Nothing else in `wildcat-finance` times a command
into a Metron run; Hermes measures gas through Forge snapshots and is out of
scope by Metron's own boundary.

**Outside.** `hyperfine` (sharkdp) is the reference shape for a repeat-count
timer with warm-up runs, min/max/mean/stddev output and a JSON export. This
recorder takes its warm-up flag and per-run samples, and refuses its mean, as
above. Python's `timeit` measures in-process code and is not the subject.

## 3. Constraints and non-goals

Starting ref: `main` at `7d12d63e13fe193fcc1f8827b393f8aa51161731`, branch
`fiat/371-metron-recorder-a-time-verb-that-writes-the`. Toolchain: the
interpreter in `.python-version` (3.14.6), stdlib `unittest`, `git`, `gh`.
Hexaemeron plugin 1.6.27 on five version surfaces; Protasis 5.10.0 checked
this study.

Checks the repository requires (`AGENTS.md`): `python3 -m unittest discover
-s tests`, `python3 plugins/hexaemeron/tests/run_tests.py`, the imprimatur,
brevitas, phylax, ephoros and hypomnema lints over changed prose and code,
the commit gate, and Horos boundary regeneration where the census moves.
The metron test module runs 84 tests on the starting ref.

Constraints:

- POSIX only, matching `scripts/demonstrations.py`: process groups and
  `os.killpg` have no Windows equivalent, and the plugin's secure reporter
  already refuses Windows.
- The run file's top level carries no number outside `measurements`.
  `load_measurements` refuses a document that carries a number beside the
  block, so every recorder field lives under one `recorder` object.
- Milliseconds only. A budget held by the recorder declares `"unit": "ms"`;
  the check does not compare units, so a budget written in seconds against a
  recorder run is a caller error the reference names and the risk register
  carries.
- The child inherits the caller's environment and working directory, because
  the command is the caller's workload. The recorder adds nothing to the
  environment and reads no credential.
- The per-repetition timeout is `--timeout-seconds`, default 600, range 1 to
  3600, the same bounds `demonstrations.py` enforces on `timeout_seconds`.
- The output cap is 1 MiB per stream, as `MAX_OUTPUT_BYTES` there; the
  recorder keeps neither stream, only their byte counts.

Non-goals, deferred past the prototype or refused:

- A canonical home for the attempt ledger (#328) and the histogram-to-baseline
  path (#414): both open, both untouched.
- Child rusage (CPU time, max RSS) per repetition: refused by the design
  record's `per-repetition-attributable` gate; see section 4.
- Network denial or sandboxing of the timed command: the workload may need
  the network. Phylax's boundary is stated in section 9.
- Any change to `check`, `record`, the six verdicts or the budget file.
- Statistics beyond min, p50, p95, max and the relative spread; no
  confidence intervals, no outlier removal.
- Changes to the demonstration lane: `DEMONSTRATION.md` keeps its command,
  and its pinned source digest is untouched because `metron-budgets.json`
  does not change.

Always: both suites before a commit; imprimatur on every shipped document;
a recorded measurement before any performance claim. Ask first: any new
dependency; any change to the run-file shape after step 3; touching CI.
Never: commit a credential; delete a failing test to make a suite pass;
claim a command ran when it did not.

## 4. Design options

Four candidates; the record at `.hexaemeron/design-evidence.json` selects one
under `unique-frontier`, from reports every one of which
`.hexaemeron/measure_design.py --all` computed from the tree and from the
candidate's declared model in `.hexaemeron/design-model.json`.

1. `subcommand-wall-clock` (selected). A `time` subcommand in `metron.py`,
   wall clock per repetition, median into the block, spread beside it. Trade:
   `metron.py` grows by one verb and one runner, roughly doubling its size,
   in exchange for one file, one parser and four reused helpers.
2. `subcommand-wall-clock-rusage`. The same, also recording `RUSAGE_CHILDREN`
   user time, system time and max RSS per repetition. Trade: more evidence in
   the run file, but `ru_maxrss` is a high-water mark over every child so far
   and cannot be attributed to one repetition. The record's probe shows the
   counter does not fall after a small child follows a large one, so the
   candidate fails `per-repetition-attributable`.
3. `standalone-script`. A separate `scripts/metron_time.py` importing the
   check's helpers by path. Trade: the check stays the size it is, at the cost
   of one new file, a second entry point to document and inventory, and one
   fewer reused helper. It survives every gate and is dominated on `new-files`.
4. `import-demonstration-runner`. A `time` subcommand importing
   `execute_command` from `scripts/demonstrations.py`. Trade: no copied
   runner, but the import resolves only inside this repository and fails
   `standalone-from-plugin-cache`.

The criteria and what each computes:

| Criterion | Concern | Form | Computed how |
| --- | --- | --- | --- |
| `check-reads-unedited` | correctness | gate, equals true | the candidate's modelled run at repeat 5 is written to disk, read by `metron.load_measurements`, compared by `metron.compare` against a one-budget file, and run through `check`; all three must agree |
| `per-repetition-attributable` | correctness | gate, equals true | true when the model records no cumulative counter; otherwise a probe spawns a 64 MiB child then an empty one and reports whether `ru_maxrss` fell |
| `timing-overhead-ms` | time | gate, at most 250 ms | median of 11 bounded launches of `python3 -c pass` with the recorder's method (own group, pipes drained, group killed, readers joined) |
| `run-file-under-check-cap` | space | gate, at most 4194304 bytes | bytes of the candidate's modelled run at repeat 1000 |
| `standalone-from-plugin-cache` | compatibility | gate, equals true | every modelled non-stdlib import is a file under `plugins/hexaemeron/` |
| `atomic-write-reused` | recovery | gate, equals true | the model reuses `write_atomically` and `ast` finds it defined in `metron.py` |
| `new-files` | compatibility | metric, minimise | modelled files absent from the tree |
| `helpers-reused` | compatibility | metric, maximise | modelled helper names `ast` finds defined at the top level of `metron.py` |
| `prior-art-controls` | recovery | metric, maximise | modelled control tokens found in `scripts/demonstrations.py` |
| `recorder-suite-green` | correctness | conformance gate, blocks step:2 | pending; `python3 -m unittest plugins.hexaemeron.tests.test_metron_check` exits 0 |
| `spread-read-by-check` | correctness | conformance gate, blocks step:3 | pending; the built `time --repeat 5` run carries five repetitions and the five spread fields, its block value equals `p50`, and `check` exits 0 on it |

Results at design lock: candidate 2 fails `per-repetition-attributable`
(probe value false); candidate 4 fails `standalone-from-plugin-cache`; the
timing floor measured 26, 28, 30 and 31 ms; the modelled run at repeat 1000
is 88932 bytes for the wall-clock candidates and 170932 for rusage;
`prior-art-controls` is 6 of 7 for every candidate, because
`demonstrations.py` never writes `shell=False` (it omits the keyword) while
`hexctl.py` writes it. Among the two survivors, candidate 1 has 0 new files
and 4 reused helpers against candidate 3's 1 and 3, so the frontier holds one
candidate. `design_evidence.py --transition design-lock` exits 0.

The selected construction, in enough detail to build:

- Argument surface: `time --name NAME --out PATH [--repeat N=1] [--warmup
  K=0] [--timeout-seconds S=600] [--expect-exit E=0] [--aggregate
  median|p95] [--cwd DIR] [--note TEXT] -- ARGV...`. Repeat is 1 to 1000,
  warm-up 0 to 100, both integers; a warm-up repetition runs under the same
  bounds and records nothing.
- Runner: `Popen(argv, stdin=DEVNULL, stdout=PIPE, stderr=PIPE,
  start_new_session=True, close_fds=True)`, no shell, no string command.
  Two drain threads with a 1 MiB cap per stream. Poll at 20 ms against a
  `monotonic_ns` deadline. On timeout or overflow, `killpg` and mark the
  repetition failed. After the child is reaped, `finished_ns` is taken, then
  the group is killed on every path and the readers joined for up to 5 s; a
  reader still alive marks the repetition escaped.
- Run file, `metron-timed-run/v1`: `{"measurements": {NAME: value},
  "recorder": {schema, argv, cwd, repeat, warmup, timeout_ms, expect_exit,
  unit, aggregation, repetitions[{index, wall_clock_ms, exit, stdout_bytes,
  stderr_bytes}], spread{samples, min, p50, p95, max, relative_spread},
  recorded_at, platform, python}, "note": TEXT?}`. Percentiles use nearest
  rank, so p95 of five samples is the maximum. `relative_spread` is `null`
  when fewer than two samples were kept or `p50` is zero.
- Exit codes: 0 with the file written atomically; 1 when any repetition
  failed, timed out, overflowed or escaped, with no file written and one
  stderr line per failed repetition; 2 on a bad invocation, a command that
  cannot start, or a file that cannot be written.

## 5. Risk register seed

The audit loop looks hardest at the subprocess boundary and at what the run
file can be made to say. Each id is stable within this study.

```risk-register
subprocess-argv | the argv after -- handed to Popen | no shell, no string command, the list is passed unchanged and nothing from the caller's environment is interpolated
process-group-teardown | the child's session after each repetition | the group is killed on every exit path and a grandchild that forked does not outlive the run
group-escape | a grandchild that called setsid and holds the pipes | the repetition is refused as escaped rather than recorded with an inflated duration, as demonstrations.py D085 does
output-cap | the child's stdout and stderr pipes | each stream is capped at 1 MiB, the child is killed on overflow and the repetition fails
timeout-bound | the per-repetition deadline | a repetition past --timeout-seconds is killed and fails, and the deadline is read from monotonic_ns rather than wall time
partial-run-file | the --out path while writing | a killed or failing recorder leaves either no file or the previous file, never a half-written one the check could read
failed-repetition-hidden | the measurements block after a failure | no run file is written when any repetition failed, so a run the check passes has every repetition green
stray-top-level-number | the run file's top level | every recorder number sits under the recorder object and load_measurements accepts the file unedited
aggregation-declared | the value in the measurements block | the value equals the named aggregation of the recorded samples and the run file names that aggregation
spread-from-samples | the spread object | min, p50, p95 and max are computed from the recorded samples by nearest rank and relative_spread is (max - min) / p50 or null
unit-mismatch | a budget declared in seconds held to a millisecond run | the reference states the unit and the check's detail line shows both numbers with the budget's unit
repeat-bounds | --repeat and --warmup | integers within 1 to 1000 and 0 to 100 are accepted and anything else exits 2 before any command runs
demo-source-digest | DEMONSTRATION.md's pinned fixture digest | metron-budgets.json is unchanged, so the demonstration record still verifies
version-surfaces | the five plugin version surfaces | tests/test_version_propagation.py passes after the bump and the README count is unchanged because metron already ships a check
```

Prose the block cannot carry: `group-escape` and `process-group-teardown`
are the two the prior art found the hard way, and the two tests at
`tests/test_demonstrations.py` lines 1740 to 1786 are the shape the guard
tests copy. `failed-repetition-hidden` is the one that changes a verdict; the
others change a number.

## 6. Glossary seeds

- `run file`: the JSON document `check` and `record` read; bare mapping or
  `measurements` block plus metadata.
- `recorder block`: the `recorder` object beside `measurements` that the
  `time` subcommand writes; its schema is `metron-timed-run/v1`.
- `repetition`: one bounded execution of the argv; `--repeat` counts the
  kept ones, `--warmup` the discarded ones.
- `sample`: one repetition's wall clock in milliseconds, float, three
  decimals, from `monotonic_ns`.
- `aggregation`: the rule that turns samples into the block value; `median`
  by default, `p95` on request, never the mean.
- `spread`: `min`, `p50`, `p95`, `max` by nearest rank over the samples,
  plus `relative_spread = (max - min) / p50`.
- `variance`: the budget-file fraction of the baseline inside which a move
  is another sample; set from the relative spread.
- `escaped`: a repetition whose pipes are still held after its process
  group was killed.
- `fail closed`: no run file on any failed repetition.

## 7. Sources

- `plugins/hexaemeron/skills/metron/EVOLUTION.md`, the held frontier text.
- `plugins/hexaemeron/skills/metron/scripts/metron.py`, `load_measurements`
  lines 165 to 199, `write_atomically` lines 374 to 400, `build_parser` line 402.
- `plugins/hexaemeron/skills/metron/SKILL.md` ("Measure how you will
  re-measure", "Budgets"), `references/budget-check.md`, `DEMONSTRATION.md`.
- `plugins/hexaemeron/tests/test_metron_check.py` (84 tests;
  `test_both_subcommands_are_offered` at line 358 pins the parser to two
  verbs) and `plugins/hexaemeron/tests/fixtures/metron/`.
- `scripts/demonstrations.py` lines 1095 to 1110, 1550 to 1650, 1653, 1855 to
  2031; `tests/test_demonstrations.py` lines 1740 to 1786.
- `plugins/hexaemeron/skills/fiat/scripts/hexctl.py` lines 11762 to 11861.
- `audit/AUDIT_SYNOPSIS.md` lines 115 to 122 (view of `audit/AUDIT.md`);
  `audit/rounds/fiat-shoggoth-front-door-derived.synopsis.md`.
- Pull requests [#211](https://github.com/wildcat-finance/skills/pull/211),
  [#212](https://github.com/wildcat-finance/skills/pull/212),
  [#1238](https://github.com/wildcat-finance/skills/pull/1238),
  [#1330](https://github.com/wildcat-finance/skills/pull/1330); issues
  [#371](https://github.com/wildcat-finance/skills/issues/371),
  [#328](https://github.com/wildcat-finance/skills/issues/328),
  [#414](https://github.com/wildcat-finance/skills/issues/414),
  [#1228](https://github.com/wildcat-finance/skills/issues/1228).
- `plugins/hexaemeron/skills/VERSIONING.md` "What every frontier run owes";
  `tests/test_version_propagation.py`; `plugins/hexaemeron/README.md` line 81
  and `plugins/hexaemeron/tests/test_fiat_skill.py`
  `PhaseSkillInventoryTests`.
- `AGENTS.md` lines 272 to 331, the checks and lints.
- `plugins/hexaemeron/skills/hypomnema/SKILL.md` lines 72 to 78, the draft
  decision-record convention.
- hyperfine, `github.com/sharkdp/hyperfine`, README: warm-up runs and JSON
  export.
- `.hexaemeron/design-model.json`, `.hexaemeron/measure_design.py`,
  `.hexaemeron/reports/*.json`, `.hexaemeron/design-evidence.json`.

## 8. Signals, and the questions behind them

The recorder is a terminal tool; nothing runs unattended and there is no
alert. The questions arrive later, when somebody reads a run file or a
ledger line that a run file produced:

1. Which command produced this number, how many times, under what timeout?
   Answered by the recorder block's `argv`, `cwd`, `repeat`, `warmup`,
   `timeout_ms`, `platform` and `python`, written at step 2.
2. Was any repetition killed, and did anything escape? Answered by the
   absence of the file: a run file exists only when every repetition exited
   as expected inside its bounds. The stderr line at step 2 names the
   repetition and the cause (`exit`, `timeout`, `output-cap`, `escaped`).
3. Is the block value one sample or a spread, and how wide? Answered by
   `aggregation`, `spread.samples` and `relative_spread`, written at step 3.

[ephoros](../plugins/hexaemeron/skills/ephoros/SKILL.md) owns what a signal
must carry; its `E003` rule is why no mean is recorded, and no log line here
is built by formatting values into a message.

## 9. Boundaries, per capability

One boundary opens: the recorder runs an argv the caller chose, as
`hexctl` runs a lint the caller named. What is worth taking at it is the
caller's own machine, which the caller already has, so the controls are about
what the recorder itself can be made to do:

- Argv: passed as a list to `Popen`, never through a shell, never assembled
  from the environment or a file (`subprocess-argv`).
- Process lifetime: own session, group killed on every path, escape refused
  (`process-group-teardown`, `group-escape`).
- Output: 1 MiB cap per stream, kill on overflow, neither stream stored
  (`output-cap`).
- Filesystem: one atomic write to `--out`; nothing else is written and no
  file is read except through the caller's command (`partial-run-file`).
- Secrets: none read, none written; the environment is inherited, not
  recorded, so a token in the caller's shell does not land in the run file.

[phylax](../plugins/hexaemeron/skills/phylax/SKILL.md) owns the boundary list
and the controls; its lint runs over `plugins` and `tests` at every step and
its `P001` and `P002` rules are the shell and string-command refusals.

## 10. The budget, or its absence

The recorder itself has one budget: the per-repetition overhead of its
method, measured at design time as the median of 11 bounded launches of an
empty interpreter, 26 ms on this machine against a 250 ms gate. The command
that measures it, from the target root:

```bash
python3 .hexaemeron/measure_design.py --candidate subcommand-wall-clock \
  --criterion timing-overhead-ms
```

The timed workload's budget is the caller's, declared in the caller's budget
file; the recorder produces the number and `check` holds it. No other budget:
the run file for 1000 repetitions is 88932 bytes against the check's 4 MiB
cap, and the test module runs in under two seconds.
[metron](../plugins/hexaemeron/skills/metron/SKILL.md) owns what a budget
carries and how it is checked.

## 11. The fail-closed posture

What stops the run: a repetition that exits other than `--expect-exit`, a
repetition past its timeout, a stream past its cap, a process left holding
the pipes after teardown, an argument outside its bounds, a command that
cannot start, an `--out` that cannot be written. Each exits non-zero and
leaves no run file, so the check can never read a run the recorder did not
finish.

Guard convention: every fix in this run lands with a test in
`plugins/hexaemeron/tests/test_metron_check.py` that fails on the tree
before the fix, run through `python3 plugins/hexaemeron/tests/run_tests.py
{report}` with the report in `elenchus.unittest.v1`. Step exits are held
against a clean detached snapshot of the committed head, because the run
worktree's `.hexaemeron/design-evidence.json` reddens two root-suite tests
(#1228). [elenchus](../plugins/hexaemeron/skills/elenchus/SKILL.md) owns the
triage order and the guard rule.

## 12. Decisions and their homes

Two decisions are expensive to reverse, because a run file outlives its
writer and a ledger line copies it:

1. The run-file shape `metron-timed-run/v1`: the median in the block, the
   spread beside it, no mean, no rusage, no run file on failure. Home: a
   draft record `docs/decisions/drafts/record-timed-runs-at-the-median-with-spread.md`
   in the repository's draft shape, numbered at the integration composition.
   Its reference copy is `references/budget-check.md`'s new "Timing a
   command" section, and `SKILL.md`'s current-state line points at it.
2. The verb lives in `metron.py` rather than a second script. Home: the
   design record at `.hexaemeron/design-evidence.json`, published beside the
   study as `docs/metron-recorder-study.md`; `EVOLUTION.md`'s `metron-v2.1.0`
   row cites this run.

Not recorded as decisions: flag defaults and bounds, which the reference
documents and the tests pin. [hypomnema](../plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns which decisions earn a record and where each one lives.

## Recommended runbook

Four steps, each one pull request, both suites green at each end, the
design-lock block before step 1 binding sha256
`578d33bbf14a32dd663ee4df52c60c6350b5d1adde0956851f91e75518b16843` and
candidate `subcommand-wall-clock`.

1. Scaffold. Commit `docs/metron-recorder-study.md` and
   `docs/metron-recorder-runbook.md`; imprimatur and hypomnema exit 0 on
   both. No code. Disciplines: hypomnema only.
2. The bounded runner and the `time` verb, single repetition: argv after
   `--`, own process group, timeout, output cap, teardown, escape refusal,
   atomic write, exit codes. Tests: the three-verb parser, exit and file
   presence for the clean, non-zero, timeout, overflow, forked-grandchild and
   `setsid`-grandchild cases; `recorder-suite-green` resolves. Disciplines:
   phylax and elenchus.
3. Repetitions, warm-up, aggregation and spread: `--repeat`, `--warmup`,
   `--aggregate`, the spread object, `relative_spread`, the reference's
   "Timing a command" section and the draft decision record. Tests: value
   equals `p50`, `p95` by nearest rank, `null` spread at one sample, bounds
   refused; `spread-read-by-check` resolves. Disciplines: metron, hypomnema,
   elenchus.
4. Demonstrate and close: run the proving demo, append the `metron-v2.1.0`
   row, set `SKILL.md` current state and metadata version 2.1.0, bump the
   plugin package version on its five surfaces, reconcile mutable first-party
   marketplace prose as `VERSIONING.md` owes, and confirm
   `DEMONSTRATION.md`'s digest still verifies. Disciplines: hypomnema and
   metron.
