# Bounded-memory interval build and check runbook

The accepted study is `.hexaemeron/study.md`, SHA-256
`05612ef303bb45ac01c51a8d452c5b6a924ea79cb76f16cbd1e387009de44129`. This run
implements https://github.com/wildcat-finance/skills/issues/1891 on the run
branch `fiat/1891-bounded-memory-interval-build-and-check`, cut from `main` at
`150943da240837040478a76c3611d150fa04f2b6`, with Python 3.14.6 and the
standard library only. The controller is `fiat-v6.76.1`.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 526ff5839522b129cf86da32b76793d295c1667a5777c22683f68219a6ec4fce
candidate | range-streamed-logs
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/alexandria/tests/run_tests.py | report_target | 37c096a9f4a079c4c4c0b6cdad965f8a33ca4945fff1fd59802759e518eea4f2
```

```version-relations
alexandria | plugins/alexandria/skills/alexandria/EVOLUTION.md | next-generation-after-integration-base
```

## Rules every step keeps

**Scope.** `build` and `check` come to hold one journal or part component at a
time, as the study's section 4 selects. No step changes the release format, a
receipt, a schema or a limit #1888 set, and no step makes `collect`,
`reconcile`, `derive`, `index` or `statement` stream. The security suite is
waived because the run ships no Solidity.

**Existing releases keep their bytes.** Every identifier in the study's
section 3 reproduces at every step. Before an Exit, export
`ALEXANDRIA_WILDCAT_V1_STAGING` to the V1 staging tree the study's section 3
locates, so `StagedRebuildTests` in `tests/test_wildcat_v1_interval_demo.py`
rebuilds the V1 identifier. Leave `ALEXANDRIA_WILDCAT_V2_STAGING` unset, for
the reason under the known-failure inventory. Run every gate with `NO_COLOR=1`
and `FORCE_COLOR` unset, because this shell sets `FORCE_COLOR=3`.

**Known-failure inventory.** No audit record names a failure this run must
guard, so the study and this runbook carry no formal inventory fence. Four
tests are red at the base with both staging variables exported, each with
"Wildcat V2 registry bytes do not match the pinned registry", because #1960
made `build` refuse the pre-#1880 registry the preserved V2 staging carries:

- `setUpClass` of `WholePreservedRebuildTests` in
  `plugins/alexandria/tests/test_wildcat_estates_interval_demo.py`;
- `test_actual_shared_logs_agree_across_both_captures_and_keep_sentinel_absence`
  in `plugins/alexandria/tests/test_wildcat_v1_interval_demo.py`;
- `test_the_rebuild_reproduces_the_pinned_identifier` and
  `test_verify_compares_every_pinned_identity_and_the_cli_agrees` in
  `plugins/alexandria/tests/test_wildcat_v2_interval_demo.py`.

They belong to https://github.com/wildcat-finance/skills/issues/2023, which
this run does not fix. With only the V1 variable exported the four skip, as
they do in hosted CI; the study measured `Ran 6 tests, FAILED (errors=4)`
with both exported and 2 skipped with V1 alone. No step counts them green. V2
identity comes from the `pinned-release-identities-reproduce` cell instead:
`check` of the preserved V2 release, and a rebuild of the preserved V2
staging through the new `Builder` inside `wildcat_registry.checking_release()`,
which returns `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`
at the base. If #2023 has merged by the integration sync, that cell also runs
the estates demonstration, and the Alexandria runner must pass whole with both
variables exported.

**Versions.** Every step changes `plugins/alexandria/`, so every step raises
Alexandria's package version in four places:

- `plugins/alexandria/.claude-plugin/plugin.json`;
- `plugins/alexandria/.codex-plugin/plugin.json`;
- the Alexandria entry in `.claude-plugin/marketplace.json`;
- the pin in `tests/test_version_propagation.py`.

The number is a checked property, not a literal. It must sit above the step's
pull request base and above every Alexandria version any local or `origin`
ref claims, read again immediately before each push with
`python3 .hexaemeron/design/version_floor.py`, which Step 1 adds. At runbook
time `main` claims 0.7.31, #1872's Step 7 branch 0.7.33 and #1892's branch
0.7.31, and #1892 runs beside this one, so the first rise is at least 0.7.34
and every later claim moves the floor. The skill generation moves once, in
Step 5, through the block above; no concrete skill version appears in this
runbook.

**Horos.** Every commit that changes the tree stages its change, runs
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`, stages
`.horos/boundary.json`, runs
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`,
stages `.horos/census.json`, and only then runs `.githooks/greenlight` and
commits.

**Pinned digests.** The study grepped the base SHA-256 of every file a step
may change. `tests/test_release.py`, `tests/test_demo.py` and
`plugins/alexandria/tests/run_tests.py` are pinned by root fixtures and
demonstration evidence, and no step edits them; new tests go in new modules.
`venues/wildcat_v1.py`, `venues/wildcat_v2.py`, `venues/compound_v3.py` and
`venues/__init__.py` are pinned by
`plugins/ariadne/examples/wildcat-datasets-v0/inputs.json`, its
`preserved/v1/` and `preserved/v2/` `provenance.json` and `statement.json`,
and `plugins/alexandria/examples/wildcat-v1-interval-v0/rebuild-record.json`,
at historical revision `104f6f82c390003fb61039d3023d07c1abe05086`. Those
records read no working file, so Step 2's venue edits leave them unchanged;
the Ariadne and Alexandria suites prove it. No step edits the #1888 draft
`docs/decisions/drafts/split-interval-log-attributions-across-components.md`,
whose phrases `HostileManifestRecordTests` pins. Before a Mason starts, grep
the step's changed files' digests again across `tests/` and `plugins/*/tests`.

**Checks.** Every Exit runs the Alexandria runner and
`scripts/run_checks.py --base fiat/1891-bounded-memory-interval-build-and-check --scope root --scope alexandria`.
At the base that plans twelve checks, among them `root-suite` (the root
`python3 -m unittest discover -s tests`) and `alexandria-suite`, with the
dead-code, demonstrations, front-door, Probitas, Tabularium and three lint
checks. Hosted CI does not run the Alexandria suite, so these local runs are
its only gate. Other sessions run heavy suites on this host: take turns rather
than running a full suite beside another session's, and never run
`run_checks.py` on a tree that is still changing.

**Conformance cells.** The operator, not a step's worker, runs
`python3 .hexaemeron/design/conformance.py <criterion> --candidate range-streamed-logs`
after a step's audit closes and before its push, from the run worktree's
root:

- `todays-model-projects-past-the-host` before Step 1's push;
- `walk-matches-whole-list-derivation` before Step 2's push;
- `streamed-check-keeps-every-refusal` and `check-peak-independent-of-size`
  before Step 3's push;
- `build-peak-independent-of-size` and `killed-build-installs-nothing` before
  Step 4's push;
- `acceptance-release-within-stated-peak`, `v2-check-peak-halved`,
  `v2-check-cpu-within-budget` and `pinned-release-identities-reproduce`,
  with `ALEXANDRIA_WILDCAT_V1_RELEASE`, `ALEXANDRIA_WILDCAT_V2_RELEASE` and
  both staging variables exported, before the last `done merge-step`.

Each report is create-only, under `.hexaemeron/design/reports/conformance/`.
No Exit runs the resolver and no worker writes a report. The record's stop
points are `step:3` to `step:6`; this runbook has five steps, so the two cells
that block `step:6` are checked at integration, and every cell's report exists
before the transition that checks it.

**Measurement.** A peak is `/usr/bin/time -l` maximum resident set size, with
`uptime`'s load averages recorded beside it. The base `check` never runs on the
acceptance release. The generator refuses to start without 2.5 times its
planned bytes of free disk, writes only under a fresh directory it creates, and
removes that directory when it finishes. It never writes under the capture
directories, another run's tree, or the staging and release trees the study
names.

**Overlap with #1872 and #1892.** 14 of this design's 27 edit sites are ones
#1872's Step 7 head `5d5ec5e142d83140a0967fe13ad3498df3df2015` also changes,
among them `Builder.build`, `_check_interval` (as `check_interval`),
`replay_opening`, `proxy_log_positions`, `attribute_logs` and
`venues/__init__.py`. Whichever run merges second syncs. It merges the
other's `main`, keeps both behaviours at those sites, declares the Aave
venue's opening logs under Step 2's rule, reruns both suites, and moves its
Alexandria version and generation row above the merged values. #1892 edits
`statement.py`, which no step here changes; the two runs share only the
version surfaces.

**Copies.** Step 1's copies of the study and runbook stay byte-identical to
`.hexaemeron/study.md` and `.hexaemeron/runbook.md`. A step that follows an
amendment re-copies both in the same commit, and every later step lists them.

## The decision record

The four decisions in study item 12 share one unnumbered draft,
`docs/decisions/drafts/stream-interval-build-and-check-one-component-at-a-time.md`.
Step 1 creates it whole, because the design bridge names it: the memory model
and its per-transaction key, the held-refusal rule, the venue opening-log
declaration with its 1,048,576 limit, and the supersession of the third
decision in the #1888 draft. No step writes a number into its bytes or its
filename, and no document cites it by anything but that path.

## Step 1: Preserve the design records, add the conformance harness and measure today's model

**Goal.** Commit the receipted study and runbook, the locked design record with its selection reports and resolvers, the conformance harness, the synthetic generator and the decision draft, and measure today's memory model on generated releases, with no product change.

**Entry.** The run branch `fiat/1891-bounded-memory-interval-build-and-check` at `150943da240837040478a76c3611d150fa04f2b6`, with the study, design-lock and runbook receipts accepted and the Alexandria runner passing there.

**Exit.** The design records sit under the Alexandria docs tree byte-identical to their controller sources, the harness and generator refuse and run as below, the decision draft exists, and every command below exits 0.

- The study, runbook and record are copied to
  `plugins/alexandria/docs/bounded-memory-interval/study.md`, `runbook.md` and
  `design-evidence.json`, and `.hexaemeron/design/`, less any `evidence/`
  directory and less `reports/conformance/`, to
  `plugins/alexandria/docs/bounded-memory-interval/design/`, holding the 24
  `reports/selection/*.json` at the paths the record binds.
- `.hexaemeron/design/conformance.py <criterion> --candidate <id>` resolves the
  record's ten conformance criteria. It refuses every candidate but
  `range-streamed-logs` by name with exit 2, refuses a cell whose test module
  or generator does not exist yet by name with exit 1, writes each report
  create-only, and supports `--no-report`.
- `.hexaemeron/design/synthetic_interval.py` writes, from its arguments alone,
  a deterministic staging tree for a constructed Wildcat V2 split plan through
  `Collector` and `Reconciler` over a generating transport that opens no
  socket, then optionally builds it. Two runs with the same arguments give the
  same release identifier.
- The `todays-model-projects-past-the-host` cell extracts the base commit's
  `plugins/alexandria` with `git archive`, runs that tree's `check` under
  `/usr/bin/time -l` on three generated releases of different sizes, fits peak
  bytes against release bytes, and reports the projected peak for the
  acceptance parameters, which it chooses so the projection is at least 1.1
  times 137,438,953,472 bytes, and records them. It refuses by name when the
  disk cannot hold that acceptance release.
- `.hexaemeron/design/version_floor.py` prints the highest Alexandria version
  `main` and every local and `origin` ref claims, and exits 1 unless the
  working tree's four surfaces agree and sit above it.
- The draft carries the status `Accepted`, no number, and the sections
  Context, Decision, Alternatives and Consequences.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1891-bounded-memory-interval-build-and-check --scope root --scope alexandria --format json
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study plugins/alexandria/docs/bounded-memory-interval/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/alexandria/docs/bounded-memory-interval/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study plugins/alexandria/docs/bounded-memory-interval/study.md --design-evidence plugins/alexandria/docs/bounded-memory-interval/design-evidence.json --repo-root .
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/decisions/drafts/stream-interval-build-and-check-one-component-at-a-time.md plugins/alexandria/docs/bounded-memory-interval
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/alexandria/docs/bounded-memory-interval
python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins/alexandria/docs/bounded-memory-interval
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/drafts/stream-interval-build-and-check-one-component-at-a-time.md plugins/alexandria/docs/bounded-memory-interval/study.md plugins/alexandria/docs/bounded-memory-interval/runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/decisions/drafts/stream-interval-build-and-check-one-component-at-a-time.md
```

**Files.**

- Create under `plugins/alexandria/docs/bounded-memory-interval/`:
  `study.md`, `runbook.md`, `design-evidence.json`, `design/resolve.py`,
  `design/build_design_evidence.py`, `design/conformance.py`,
  `design/synthetic_interval.py`, `design/version_floor.py`,
  `design/observations.json` and the 24 `design/reports/selection/*.json`.
- Create `.hexaemeron/design/conformance.py`,
  `.hexaemeron/design/synthetic_interval.py` and
  `.hexaemeron/design/version_floor.py`, the sources of those copies.
- Create `docs/decisions/drafts/stream-interval-build-and-check-one-component-at-a-time.md`
  and `plugins/alexandria/tests/test_bounded_memory_records.py`.
- Raise the version in `plugins/alexandria/.claude-plugin/plugin.json`,
  `plugins/alexandria/.codex-plugin/plugin.json`,
  `.claude-plugin/marketplace.json` and `tests/test_version_propagation.py`.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`.
- Pinned, not edited: `tests/test_release.py`, `tests/test_demo.py`,
  `plugins/alexandria/tests/run_tests.py`.

**Tests.** Add `DesignRecordCopyTests` and `GeneratorTests` to `plugins/alexandria/tests/test_bounded_memory_records.py`. `test_the_record_copy_is_the_locked_design_record` asserts the copy's SHA-256 is the design-lock value above. `test_every_selection_report_the_record_binds_is_committed` asserts each resolved cell's report exists at its bound path with its bound SHA-256. `test_the_conformance_harness_refuses_every_other_candidate` asserts the committed `conformance.py` exits 2 for each of the three rejected candidates, names the refusal and writes no report. `test_the_generator_is_deterministic_at_a_small_size` builds a small generated release twice in a temporary directory and compares identifiers. `test_the_generator_refuses_without_disk_headroom` patches the free-disk reading and expects the named refusal before any file is written. The full count is set by execution. Also run by hand before the commit, outside the suite:

- `cmp` of every copy against its `.hexaemeron/` source;
- `python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py plugins/alexandria/docs/bounded-memory-interval/design-evidence.json --transition design-lock`, which prints `clean`;
- `python3 scripts/portable_promise_machine.py measure`, which stays under the 1,600-file tripwire with a positive byte margin;
- `python3 scripts/plugin_release.py --base fiat/1891-bounded-memory-interval-build-and-check --head HEAD` and `python3 .hexaemeron/design/version_floor.py`, which name the Alexandria rise.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`

**Disciplines.** phylax: the committed resolvers enter the `lint-phylax` walk under `plugins/`, and the generator and harness run fixed `git`, `/usr/bin/time` and interpreter argv with no shell, read only pinned objects and preserved releases, and write only fresh directories they create; lint the `.hexaemeron/design/` sources with Phylax before copying them. ephoros: none, nothing in this step runs unattended. metron: this step records today's model, the baseline every later peak is compared with, three runs per size with the load beside each. elenchus: a copy that differs from its source, or a generator that does not repeat its identifier, is a failure to reproduce and repair, never a value to re-pin. hypomnema: the step opens the decision record the design bridge names and ships the study and runbook under the repository's lint.

## Step 2: Walk preserved logs with bounded state and give venues only their opening logs

**Goal.** Add a shared log walk that validates positions and derives attribution rows with bounded state, make `proxy_log_positions` and `attribute_logs` whole-list wrappers over it, and let each venue declare the opening logs it reads, with every caller's result unchanged.

**Entry.** Step 1's branch with its `--audit` head merged into it, and the `todays-model-projects-past-the-host` report written.

**Exit.** The walk reproduces the base derivation on every fixture and hostile case, every pinned identifier still reproduces, and every command below exits 0.

- `plugins/alexandria/scripts/alexandria_lib/log_walk.py` holds `LogWalk`,
  fed logs in plan order one shard's result at a time. It keeps the previous
  position, the current block's and transaction's hashes, the upgrade
  positions and the current transaction's ordinary logs, and one 8-byte key
  per distinct transaction in 256 `array("Q")` buckets. After the pass it
  sorts each bucket alone; a repeated key triggers one more read of the logs,
  collecting full hashes for those keys only, and then refuses with today's
  message and coordinate or continues.
- Given epochs, the walk attributes each log with one cursor per subject, as
  `_attribute_into` does, and yields each row.
- `proxy_log_positions` and `attribute_logs` keep their signatures, rows, row
  order and refusal text, now built on the walk.
- Each venue declares the logs its opening phase and gaps read: `Upgraded`
  announcements for the single-proxy plan, the factory's `MarketDeployed`
  logs for Wildcat V2, none for V1. A helper returns them from a walk, and a
  count above 1,048,576 (`MAX_SUBJECTS` × `MAX_EPOCHS`) refuses by name.
  `opening_phase`, `epochs_from_opening`, `discover_epochs` and each venue's
  `evidence_gaps` give today's results when handed only those logs, and no
  caller hands them only those logs until Step 3.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1891-bounded-memory-interval-build-and-check --scope root --scope alexandria --format json
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/alexandria/scripts
```

**Files.**

- Create `plugins/alexandria/scripts/alexandria_lib/log_walk.py` and
  `plugins/alexandria/tests/test_log_walk.py`.
- Change `plugins/alexandria/scripts/alexandria_lib/interval.py` at
  `proxy_log_positions`, `attribute_logs`, `_attribute_into` and
  `discover_epochs`.
- Change `plugins/alexandria/scripts/alexandria_lib/venues/__init__.py`,
  `venues/compound_v3.py` at `evidence_gaps`, `venues/wildcat_v1.py` and
  `venues/wildcat_v2.py` at `ImmutableCodeOpening.__init__`,
  `ImmutableCodeOpening.epochs`, `evidence_gaps` and, for V2,
  `market_deploy_report`.
- Change `plugins/alexandria/scripts/usdc_interval.py` at
  `OpeningPhase.__init__` only where the venue declaration requires it.
- Raise the version in `plugins/alexandria/.claude-plugin/plugin.json`,
  `plugins/alexandria/.codex-plugin/plugin.json`,
  `.claude-plugin/marketplace.json` and `tests/test_version_propagation.py`.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`. Re-copy
  `plugins/alexandria/docs/bounded-memory-interval/study.md` and `runbook.md`
  if an amendment has landed since the last copy.
- Pinned, not edited: `plugins/ariadne/examples/wildcat-datasets-v0/inputs.json`,
  its `preserved/v1/` and `preserved/v2/` `provenance.json` and
  `statement.json`, and
  `plugins/alexandria/examples/wildcat-v1-interval-v0/rebuild-record.json`,
  which name the venue files at a historical revision.

**Tests.** The resolver loads `plugins/alexandria/tests/test_log_walk.py` for `walk-matches-whole-list-derivation`. `WalkEquivalenceTests` compares the walk's rows and the wrappers' rows with the base commit's `proxy_log_positions` and `attribute_logs`, read from a `git show` of the base into a temporary module, on the constructed V1 and V2 fixtures, the Compound fixtures and the preserved V1 and V2 releases' logs when their variables are set. `WalkRefusalTests` covers each existing refusal (unordered, duplicated, contradictory block hash, contradictory transaction pair, ordinary log in an upgrade transaction, log outside the interval, undeclared emitter, malformed topics) with the base text. `TransactionKeyTests` covers a repeated transaction hash across blocks and a forced key collision with truncated keys, which refuses nothing. `OpeningLogTests` covers each venue's declaration, today's epochs and gaps from the opening logs alone, and the 1,048,576 refusal with a patched limit. The full count is set by execution. The local version proof is `python3 scripts/plugin_release.py --base fiat/1891-bounded-memory-interval-build-and-check --head HEAD`, with `python3 .hexaemeron/design/version_floor.py` before the push.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-2.json`

**Disciplines.** phylax: preserved logs are untrusted release bytes, and the walk must refuse every shape the base refuses before any row is derived; a key collision may only cost a read, never admit a log. ephoros: every refusal keeps its base text, which names the position or subject, so a refusal points at its log. metron: none yet, the wrappers keep today's whole-list memory until Step 3 streams through the walk. elenchus: each rule the walk takes over has a guard that fails on a walk without it. hypomnema: the opening-log declaration and its limit are the third decision in the Step 1 draft.

## Step 3: Check an interval release one component at a time

**Goal.** Make `check` read, verify and drop each journal and part component in turn, keeping only the resident set the study names, while every refusal keeps its text and its order.

**Entry.** Step 2's branch with its `--audit` head merged into it, and the `walk-matches-whole-list-derivation` report written.

**Exit.** The check command holds one component at a time, its traced peak does not grow with the release beyond the stated bound, every existing check test passes unchanged, and every command below exits 0.

- The manifest, plan, registry, reconciliation and epoch table stay
  resident. The implementation code is read, re-hashed against the receipt
  and dropped.
- The parts are read one at a time for their shape. The journals are read one
  at a time in today's order; for each shard `check` keeps its record counts,
  its boundary block number and hash, and the SHA-256 of the
  `trace_transaction` request its logs derive, in place of `logs_by_shard` and
  `boundary_headers`.
- Each logs range goes through the walk and is attributed with the receipt's
  epochs, then compared with its part, read again and bound again to the
  manifest's size and SHA-256, or with its slice of an unsplit receipt's rows.
- Each refusal found early is held and raised where the base raises it:
  position refusals just before the opening replay, the code-digest refusal
  after it, then the epoch comparison, any row mismatch, the first-code rows,
  the venue gaps, the scopes and the journal bindings.
- The opening replay, `epochs_from_opening` and `evidence_gaps` receive only
  the venue's opening logs.
- `plugins/alexandria/docs/usdc-interval-collector.md` states `check`'s memory
  model: the resident set, the per-transaction key, the opening-log rule and
  its limit, and the second read of each part.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1891-bounded-memory-interval-build-and-check --scope root --scope alexandria --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/alexandria/docs/usdc-interval-collector.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/alexandria/docs/usdc-interval-collector.md
```

**Files.**

- Change `plugins/alexandria/scripts/usdc_interval.py` at `_check_interval`,
  `_replay_release_opening`, `_check_attribution_parts`, `_component`,
  `attribution_part_rows`, `epochs_from_opening` and `_gaps`.
- Change `plugins/alexandria/docs/usdc-interval-collector.md`.
- Create `plugins/alexandria/tests/test_streamed_check.py`.
- Raise the version in `plugins/alexandria/.claude-plugin/plugin.json`,
  `plugins/alexandria/.codex-plugin/plugin.json`,
  `.claude-plugin/marketplace.json` and `tests/test_version_propagation.py`.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`. Re-copy
  `plugins/alexandria/docs/bounded-memory-interval/study.md` and `runbook.md`
  if an amendment has landed since the last copy.
- Pinned, not edited: `tests/test_release.py`, `tests/test_demo.py`,
  `plugins/alexandria/tests/run_tests.py`.

**Tests.** The resolver loads `plugins/alexandria/tests/test_streamed_check.py` and the existing check tests in `tests/test_usdc_interval.py`, `tests/test_log_attribution_parts.py`, `tests/test_check_verified_reads.py`, `tests/test_wildcat_venue.py` and `tests/test_release_limits.py`, which pass unchanged. `RefusalOrderTests` builds releases with two defects each (a forged epoch table whose rows also mismatch, an unordered log beside a wrong boundary hash, a wrong code digest beside a row mismatch) and asserts the base message comes first, comparing with the base commit's `check` extracted by `git archive`. `SecondReadTests` changes a part between its two reads and expects the named refusal. `CheckPeakTests.test_the_traced_peak_does_not_grow_with_the_release` traces `check` with `tracemalloc` on a generated release and on one four times larger, and asserts the difference is at most 8,388,608 bytes plus 16 bytes per added log. The full count is set by execution. By hand before the push, record `/usr/bin/time -l python3 plugins/alexandria/scripts/usdc_interval.py check <preserved V2 release>` three times with the load beside each. The local version proof is `python3 scripts/plugin_release.py --base fiat/1891-bounded-memory-interval-build-and-check --head HEAD`, with `python3 .hexaemeron/design/version_floor.py` before the push.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-3.json`

**Disciplines.** phylax: a release is untrusted bytes, #1945's binding holds for every read including each part's second read, and a component changed between reads refuses by name. ephoros: every refusal keeps its base text, naming its component, shard or part, and its base position in the order. metron: this step claims the stated check bound, proven in process by the traced-peak test and on V2 by the recorded runs. elenchus: each held refusal has a guard showing its base position, and each fix lands with a test that fails on the parent. hypomnema: the resident set and the held-refusal rule are the first two decisions in the Step 1 draft, and the collector document states them.

## Step 4: Build an interval release one component at a time

**Goal.** Make `build` write each component in turn from its own staged file, holding only the resident set, so its peak no longer grows with the release, while every release that builds today keeps its bytes.

**Entry.** Step 3's branch with its `--audit` head merged into it, and the `streamed-check-keeps-every-refusal` and `check-peak-independent-of-size` reports written.

**Exit.** The build command holds one component at a time, a killed build installs nothing, every pinned identifier still reproduces, and every command below exits 0.

- Pass one reads each staged logs journal once through the walk and collects
  the opening logs; the opening replay and the epochs follow as today.
- Pass two writes components one at a time into the plan directory. Each
  range's logs component and part come from one more read of that staged
  file, bound again to the reconciliation record's journal digest; other
  journals are written from their own files.
- The epoch table is written last, once the part row counts are known. An
  unsplit plan's rows stay in memory until its epoch table is written, as the
  64 MiB ceiling already bounds them.
- `ingest` and `verify` run as today, and the capture plan lists components in
  today's order, so the manifest bytes do not change.
- `plugins/alexandria/docs/usdc-interval-collector.md` states `build`'s memory
  model and its two reads of each staged logs journal.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1891-bounded-memory-interval-build-and-check --scope root --scope alexandria --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/alexandria/docs/usdc-interval-collector.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/alexandria/docs/usdc-interval-collector.md
```

**Files.**

- Change `plugins/alexandria/scripts/usdc_interval.py` at `Builder.build`,
  `Builder._journal`, `Builder._epoch_receipt`, `replay_opening` and
  `staged_log_records`.
- Change `plugins/alexandria/docs/usdc-interval-collector.md`.
- Create `plugins/alexandria/tests/test_streamed_build.py`.
- Raise the version in `plugins/alexandria/.claude-plugin/plugin.json`,
  `plugins/alexandria/.codex-plugin/plugin.json`,
  `.claude-plugin/marketplace.json` and `tests/test_version_propagation.py`.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`. Re-copy
  `plugins/alexandria/docs/bounded-memory-interval/study.md` and `runbook.md`
  if an amendment has landed since the last copy.
- Pinned, not edited: `tests/test_release.py`, `tests/test_demo.py`,
  `plugins/alexandria/tests/run_tests.py`.

**Tests.** The resolver loads `plugins/alexandria/tests/test_streamed_build.py`. `BuildBytesTests` rebuilds the `TODAYS_BYTES` and `PRE_1880_RELEASE_IDS` fixtures and the demonstrations' identifiers and compares them with the pinned values. `SecondReadTests` changes a staged logs journal between the two reads and expects the named refusal. `BuildPeakTests.test_the_traced_peak_does_not_grow_with_the_release` traces `build` on a generated release and on one four times larger, with the same bound as Step 3. `KilledBuildTests` starts a child build, sends it SIGKILL at the start of pass one, in pass two and inside `ingest`, and asserts that no directory exists at the output path and that a rerun builds the same identifier. The full count is set by execution. The local version proof is `python3 scripts/plugin_release.py --base fiat/1891-bounded-memory-interval-build-and-check --head HEAD`, with `python3 .hexaemeron/design/version_floor.py` before the push.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-4.json`

**Disciplines.** phylax: the staging tree is read twice, and the second read is bound to the reconciliation record's digest, so a tree changed between reads refuses by name; the killed-build test starts only the interpreter with fixed argv. ephoros: a build refusal names the staged journal and the digest it expected. metron: this step claims the stated build bound, proven in process by the traced-peak test. elenchus: a pinned identifier that moves stops the step as a regression to localise, and each fix lands with a guard that fails on the parent. hypomnema: the build's two reads are part of the memory model the Step 1 draft records.

## Step 5: Demonstrate the acceptance release and record the Alexandria generation

**Goal.** Run the study's proving path, record its evidence in a proof document, and write the Alexandria generation row the version-relations block declares.

**Entry.** Step 4's branch with its `--audit` head merged into it, and the `build-peak-independent-of-size` and `killed-build-installs-nothing` reports written.

**Exit.** The proof records the acceptance release's two peaks within the stated bound, the V2 figures within their ceilings and every pinned identifier reproduced; the generation row and the skill version agree; and every command below exits 0.

- `plugins/alexandria/docs/bounded-memory-interval/proof.md` records each run
  the Tests field lists, made at this step's tree, with its exit, identifier,
  peak, seconds and load averages.
- The acceptance release, generated with the parameters Step 1's report
  records and at least the bytes that report plans, builds and checks with
  each peak at most 4,294,967,296 bytes.
- `check` of the preserved V2 release peaks at most 620,273,664 bytes and
  uses at most 9,400 ms of user plus system time.
- `EVOLUTION.md` gains one generation row, the next after the integration
  base, keeping the frontier revision and its SHA-256 byte for byte.
  `SKILL.md`'s `metadata.version` equals that row, and the skill's interval
  section states the memory model.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1891-bounded-memory-interval-build-and-check --scope root --scope alexandria --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/alexandria/docs/bounded-memory-interval/proof.md plugins/alexandria/skills/alexandria/SKILL.md plugins/alexandria/skills/alexandria/EVOLUTION.md
for file in plugins/alexandria/docs/bounded-memory-interval/proof.md plugins/alexandria/skills/alexandria/SKILL.md; do python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$file"; done
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/alexandria/docs/bounded-memory-interval/proof.md plugins/alexandria/skills/alexandria
```

**Files.**

- Create `plugins/alexandria/docs/bounded-memory-interval/proof.md`.
- Change `plugins/alexandria/skills/alexandria/EVOLUTION.md` and
  `plugins/alexandria/skills/alexandria/SKILL.md`.
- Raise the version in `plugins/alexandria/.claude-plugin/plugin.json`,
  `plugins/alexandria/.codex-plugin/plugin.json`,
  `.claude-plugin/marketplace.json` and `tests/test_version_propagation.py`.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`. Re-copy
  `plugins/alexandria/docs/bounded-memory-interval/study.md` and `runbook.md`
  if an amendment has landed since the last copy.
- Pinned, not edited: `tests/test_release.py`, `tests/test_demo.py`,
  `plugins/alexandria/tests/run_tests.py`.

**Tests.** No new test module. `tests/test_evolution_contract.py` in the root suite checks the new row and the skill version. The proof records these runs from the run worktree's root with `NO_COLOR=1`, each with `uptime` beside it and never beside another session's suite:

- `python3 .hexaemeron/design/conformance.py acceptance-release-within-stated-peak --candidate range-streamed-logs --no-report`, which generates the acceptance staging tree, runs `/usr/bin/time -l python3 plugins/alexandria/scripts/usdc_interval.py build` and then `... check` on the result, and removes its directory;
- `/usr/bin/time -l python3 plugins/alexandria/scripts/usdc_interval.py check <preserved V2 release>`, three times, beside the base median of 1,240,547,328 bytes and 4.70 CPU seconds;
- `python3 plugins/alexandria/examples/<demo>/demo.py build --output <fresh directory>`, then `verify` on it, for `usdc-interval-v0`, `usdc-interval-epochs-v0`, `usdc-interval-live-v0`, `credit-history-v0` and `wildcat-v1-interval-v0`, and the V2 demonstration's `build()` inside `wildcat_registry.checking_release()`;
- `check` of both preserved releases, and `python3 plugins/alexandria/scripts/alexandria.py verify` of `plugins/alexandria/examples/compound-v3-phase0-v0/release` and `plugins/alexandria/examples/proof-backed-state-v0/release`.

The integration cells repeat these against the constants in `conformance.py`. The local version proof is `python3 scripts/plugin_release.py --base fiat/1891-bounded-memory-interval-build-and-check --head HEAD`, with `python3 .hexaemeron/design/version_floor.py` before the push.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-5.json`

**Disciplines.** phylax: none new, the demonstrations read committed and preserved bytes offline and write only fresh directories the generator removes. ephoros: none, nothing in this step runs unattended. metron: the step measures the stated peaks the same way the base was measured, with the load beside each figure, and compares the V2 figures with the base median. elenchus: a peak over its budget or an identifier that does not reproduce stops the step as a regression to localise, never a budget or pin to move. hypomnema: the generation row is the ledger home the study names, and the proof records the evidence the integration cells repeat.
