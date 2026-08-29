# Runbook: disposable fixture signing and affected-scope parallel checks

Source: `.hexaemeron/study.md`, receipted at SHA-256 `df417331fcc80b79305244cb957b417f740dd0eb47c5805cba72851abfdf909d`.

The repository begins at `e2200b6a04bbf639c3d5ec37f01a7aa63ce58f16` on the run branch `fiat/622-fix-disposable-fixture-signing-and-add-affec`. The existing Python-standard-library toolchain, Apache-2.0 licence and hosted workflows remain unchanged. Every step starts from the green, signed step below it and leaves a separately reviewable pull request.

## Step 1: Isolate disposable Git signing and publish the design record

**Goal.** Make non-signature fixture commits independent of every contributor's signing configuration, guard the observed hostile-inheritance failure, and put the receipted design in the repository's established homes.

**Entry.** `e2200b6a04bbf639c3d5ec37f01a7aa63ce58f16` on `fiat/622-fix-disposable-fixture-signing-and-add-affec`, with the study and this runbook receipted and no tracked changes.

**Exit.** Every current disposable repository that creates non-signature fixture history sets repository-local `commit.gpgsign=false` immediately after `git init` and before its first commit; a hostile inherited configuration with a recording failing signer leaves the sentinel untouched while the affected fixture matrix passes; signature-verification matrices are unchanged; `python3 -m unittest discover -s tests`, `python3 plugins/hermes/skills/hermes/scripts/test_hermes.py`, `python3 plugins/hexaemeron/tests/run_tests.py`, and `python3 -m unittest discover -s plugins/horos/tests -t plugins/horos` exit zero; committed copies of the study and runbook plus ADR-036 explain the chosen boundary.

**Files.** `tests/test_boundary_currency.py`; `plugins/hermes/skills/hermes/scripts/test_hermes.py`; `plugins/hexaemeron/tests/test_elenchus_checker.py`; `plugins/hexaemeron/tests/test_kronos_scoreboard.py`; applicable ad hoc fixtures in `plugins/hexaemeron/tests/test_hexctl.py`; `plugins/horos/tests/test_demonstration.py`; `plugins/horos/tests/test_scoped_entry.py`; `plugins/horos/tests/test_universe.py`; one focused hostile-signing regression under `plugins/hexaemeron/tests/`; `docs/affected-scope-test-runner/study.md`; `docs/affected-scope-test-runner/runbook.md`; `docs/decisions/ADR-036-select-and-schedule-repository-checks-from-one-graph.md`.

**Tests.** Extend the Hexaemeron suite with a hostile inherited-signing regression that executes the affected fixture histories and verifies the sentinel, outer checkout and global config remain unchanged. Re-run the current positive, unsigned and invalid-signature tests without editing their expectations. Test counts are always taken from fresh discovery. Elenchus runner contract: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; report format `unittest-json-v1`; report file `.elenchus/step-1.json`.

**Disciplines.** phylax: fixed-argv Git subprocesses, inherited environment and repository-local configuration are the boundary. ephoros: none, this step adds no unattended runtime. metron: compare the hostile fixture command before and after under the same configuration, while treating isolation as the correctness result. elenchus: the inherited signer failure is reproduced on the parent and the hostile regression must turn red there. hypomnema: ADR-036 and the shipped study/runbook copies preserve the design and rejected alternatives.

## Step 2: Add fresh-manifest parallel execution to the Hexaemeron runner

**Goal.** Extend the self-contained Hexaemeron unittest entrypoint with quota-aware parallel coordination and private workers while retaining dynamic tests, complete failure evidence and the hardened Elenchus report interface.

**Entry.** Step 1's signed commit, with disposable fixture signing isolated and ADR-036 present.

**Exit.** `plugins/hexaemeron/tests/run_tests.py` supports a positive `--jobs` override and an automatic CPU/quota-aware budget; coordinator and worker discovery produce the same ordered manifest digest; assignments and executions are exact disjoint unions; generated and otherwise non-importable IDs run by selected discovered objects; output is replayed in stable shard order; all shards drain after failures; timing data affects balance only; positional and `--elenchus-report` forms retain their secure behavior; `python3 plugins/hexaemeron/tests/run_tests.py --jobs 1` and `python3 plugins/hexaemeron/tests/run_tests.py` both exit zero with identical discovered and executed manifests.

**Files.** `plugins/hexaemeron/tests/run_tests.py`; focused parallel-runner, manifest, dynamic-ID, accounting, cache, output-order, capacity and report-compatibility tests under `plugins/hexaemeron/tests/`; ADR-036 only if implementation evidence requires a factual clarification without changing the accepted decision.

**Tests.** Add generated-ID, add/remove/rename, duplicate/missing/unexecuted, stale worker, corrupt timing, small-manifest, all-failures-drain, stable-output and secure-report regressions. Observe the guard tests red on the parent wherever Elenchus can isolate them. Run both serial-control and automatic-policy commands from Exit and compare manifest identities rather than a fixed count. Elenchus runner contract: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; report format `unittest-json-v1`; report file `.elenchus/step-2.json`.

**Disciplines.** phylax: private worker arguments, assignment files, cache paths and report paths cross subprocess and filesystem boundaries. ephoros: structured console and JSON summaries must answer source, capacity, assignment, cache and failure questions. metron: the parallel policy is kept only after same-command serial and automatic samples beat measured spread with green correctness gates. elenchus: every scheduler refusal and report regression needs a parent-red guard. hypomnema: versioned protocol docstrings and ADR-036 are the durable interface record.

## Step 3: Add the checked impact map and one global executor

**Goal.** Make declared scope plus actual changed paths choose the complete applicable check graph, then execute its independent work under one shared process budget.

**Entry.** Step 2's signed commit, with the parallel Hexaemeron runner green in serial and automatic modes.

**Exit.** `tests/check-map-v1.json` validates as `wildcat.check-map.v1`; `scripts/run_checks.py` accepts repeated `--scope`, a base, `--full`, plan-only output, human or versioned JSON output, a positive jobs override and a repository-relative JSON report; tracked and relevant untracked paths have one declared ownership rule; dependency edges close deterministically and reject cycles; missing owners, stale commands and unknown paths refuse before execution; plugin-local, shared-contract, test-infrastructure, Hexctl, Pandects, Janus and prose fixtures select the exact expected checks; the executor uses one global slot counter across suite jobs, shards and ordered groups; source movement supersedes and retries once before returning `unstable-source`; `python3 scripts/run_checks.py --full --plan --format json` and `python3 -m unittest discover -s plugins/hexaemeron/tests -p 'test_check_runner.py'` exit zero.

**Files.** `tests/check-map-v1.json`; `scripts/run_checks.py`; `plugins/hexaemeron/tests/test_check_runner.py` and its bounded fixtures; `.gitignore` only if the existing ignored `tmp/` rule does not already cover runner-owned snapshots and timing data; ADR-036 only for factual implementation clarifications.

**Tests.** Cover every acceptance selection and refusal from #622, duplicate-key and path safety, fixed argv without shell, ordered groups, global concurrency high-water marks, bounded output, atomic report/cache writes, single-change supersession, repeated-change `unstable-source`, snapshot sentinel cleanup, exact executed-once aggregation and timing-only authority. Re-derive the plan from the actual step diff before exit. Elenchus runner contract: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; report format `unittest-json-v1`; report file `.elenchus/step-3.json`.

**Disciplines.** phylax: the map parser, Git reads, snapshot clone, untracked-file copy, subprocess queue, report writer and cleanup path each need bounded controls and hostile cases. ephoros: the run report records source, map, reasons, capacity, queue, shards, cache, supersession and distinct failure classes. metron: planner and snapshot overhead plus composed parallel time are measured against the same frozen workload and neutral changes are removed. elenchus: unknown ownership, cycles, accounting faults and moving-source cases each retain a parent-red regression. hypomnema: the versioned map and report schemas document their interfaces beside the code and remain consistent with ADR-036.

## Step 4: Demonstrate, measure and document the complete runner

**Goal.** Prove the complete #621/#622 behavior from a stable current tree, publish the measured limits, and make the checked runner the contributor entrypoint without changing hosted CI.

**Entry.** Step 3's signed commit, with signing isolation, parallel Hexaemeron execution, the checked impact map and the global executor green.

**Exit.** Three alternating `python3 plugins/hexaemeron/tests/run_tests.py --jobs 1` and `python3 plugins/hexaemeron/tests/run_tests.py` samples on one frozen tree record equal manifests, wall time, spread, process high-water mark and available peak memory; the automatic median beats the serial median beyond combined spread or the unproven scheduling policy is reverted; the hostile signer matrix and existing signature-verification cases pass; `python3 scripts/run_checks.py --base e2200b6a04bbf639c3d5ec37f01a7aa63ce58f16 --plan --format json` selects every actual changed surface; `python3 scripts/run_checks.py --full` exits zero and accounts for every selected assertion; `AGENTS.md`, ADR-036 and the benchmark record agree with the executable interfaces; hosted workflows remain unchanged.

**Files.** `AGENTS.md`; `docs/decisions/ADR-036-select-and-schedule-repository-checks-from-one-graph.md`; `docs/affected-scope-test-runner/benchmark.md`; any implementation file changed only to repair a failure reproduced by the final demonstration; committed study/runbook copies if their presentation needs a content-preserving prose correction.

**Tests.** Run the exact Exit commands from a stable tree, retain all six raw sample summaries and the full-run structured report under run-local evidence, and publish their bounded aggregate in `docs/affected-scope-test-runner/benchmark.md`. Test counts come from each manifest and are compared for equality, never to a repository constant. Elenchus runner contract: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; report format `unittest-json-v1`; report file `.elenchus/step-4.json`.

**Disciplines.** phylax: inspect final reports and sample output for unsafe paths, unbounded data or signing material. ephoros: verify every promised run-summary field from real output and keep no secret or high-cardinality metric label. metron: make the keep-or-revert verdict from the six same-workload samples and recorded spread. elenchus: stop and work any final red result to cause before changing code or recording green. hypomnema: `AGENTS.md`, ADR-036 and the benchmark record are the established homes for operation, decision and measured consequence.
