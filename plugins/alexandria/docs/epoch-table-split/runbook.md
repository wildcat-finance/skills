# Epoch table split and release caps runbook

The accepted study is `.hexaemeron/study.md`, SHA-256
`7deb74791f9a8b996f4a01f873b997ac01665e0fb81f56d8be567d1b78e172c4`. This run
implements https://github.com/wildcat-finance/skills/issues/1888 on the run
branch `fiat/1888-epoch-table-split-and-release-caps`, cut from `main` at
`17ea8d2ab5e52081370b13b92390b64849ed880d`, with Python 3.14.6 and the
standard library only. The controller is `fiat-v6.74.1`.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 94a3d5293c5b03a73cc584a3ea2e1843c4e4659676819d4bff293e4a75850eb5
candidate | split-attribution-parts
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/alexandria/tests/run_tests.py | report_target | 37c096a9f4a079c4c4c0b6cdad965f8a33ca4945fff1fd59802759e518eea4f2
```

```version-relations
alexandria | plugins/alexandria/skills/alexandria/EVOLUTION.md | next-generation-after-integration-base
```

## Rules every step keeps

**Scope.** On 2026-09-23 Laurence kept this run to the format's limits. No
step changes how much of a release `build` or `check` holds in memory; that
work is the study's carried-forward `bounded-memory-build-and-check`. The
security suite is waived because the run ships no Solidity.

**The limits are an interface.** The values in the study's section 1 table
and its split rule are what #1872 sizes its segment table to if it waits for
this run. A change to any of them after merge is a notice owed to #1872.

**Existing releases keep their bytes.** A plan without `log_attribution_parts`
takes today's code path, and the seven identifiers and two committed releases
in the study's section 3 reproduce at every step. Export
`ALEXANDRIA_WILDCAT_V1_STAGING` and `ALEXANDRIA_WILDCAT_V2_STAGING` to the two
staging trees the study's section 3 locates before running an Exit. Then
`StagedRebuildTests` in `tests/test_wildcat_v1_interval_demo.py` and
`tests/test_wildcat_v2_interval_demo.py` rebuild both Wildcat identifiers
instead of skipping. The checked runner passes both variables through.

**Versions.** Every step changes `plugins/alexandria/`, so every step raises
Alexandria's package version in four places:

- `plugins/alexandria/.claude-plugin/plugin.json`;
- `plugins/alexandria/.codex-plugin/plugin.json`;
- the Alexandria entry in `.claude-plugin/marketplace.json`;
- the pin in `tests/test_version_propagation.py`.

Each number sits above the step's pull request base and above every Alexandria
version any local or remote ref claims when the step commits. At runbook time
the highest claim is 0.7.16, on #1872's Step 4 and Step 5 branches, and
#1872's later steps will claim more, so recheck before each commit. Each
step's Tests field names the local proof. The skill generation moves once, in
Step 4, through the block above; no concrete skill version appears in this
runbook.

**Horos.** Every commit that changes the tree stages its change, runs
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --write`, stages
`.horos/boundary.json`, runs
`python3 plugins/horos/skills/horos/scripts/horos.py scan . --census --write`,
stages `.horos/census.json`, and only then commits.

**Pinned digests.** The base SHA-256 of every file a step changes was grepped
across the tree. Two live pins exist, and no step edits either file:
`tests/test_release.py` is pinned by
`tests/fixtures/promise-machine/runtime/law-runtime-result-binding.json`, and
`tests/test_demo.py` by the runtime fixtures, `tests/promise_machine_coverage.json`
and the agent-instruction demonstration evidence. New tests go in new modules.
The remaining hits sit in `plugins/ariadne/examples/wildcat-datasets-v0/`,
`plugins/alexandria/examples/wildcat-v1-interval-v0/rebuild-record.json` and
`docs/kickoff/1389/evidence/sources.json`. They name historical revisions and
read no working file, so they do not move.

**Checks.** Every Exit runs the Alexandria runner and
`scripts/run_checks.py --base fiat/1888-epoch-table-split-and-release-caps --scope root --scope alexandria`,
which at the base plans ten checks: the Alexandria and root suites, both
dead-code checks, the demonstrations, front-door and joined front-door checks,
and the Phylax, Ephoros and Hypomnema lints. Run every gate with `NO_COLOR=1`,
because this shell sets `FORCE_COLOR`. At the base the Alexandria runner
passed 1,086 tests with 7 skipped when the staging variables were unset, and
1,088 with none skipped when both were exported.

**Conformance cells.** The operator, not a step's worker, runs
`python3 .hexaemeron/design/conformance.py <criterion> --candidate split-attribution-parts`
after a step's audit closes and before its push:

- `split-parts-rederive-and-refuse` before Step 2's push;
- `release-limits-hold-at-the-cap` and `split-release-over-128-components`
  before Step 3's push;
- `pinned-release-identities-reproduce`, with both staging variables exported,
  before the last `done merge-step`.

No Exit runs the resolver, and no worker writes these reports. Each report is
create-only.

**Overlap with #1872.** Three of this design's edit sites are also changed by
#1885 or #1889: `check_interval`, `Builder._epoch_receipt` and
`plugins/alexandria/docs/usdc-interval-collector.md`. No step changes the
signature or ordering of `attribute_logs` or `proxy_log_positions`, so #1885's
keyword-only `order_upgrade_transactions=False` passes through unchanged, and
the rows are split after `attribute_logs` returns. Whichever run merges second
syncs: it merges the other's `main`, keeps both behaviours at those three
sites, reruns both suites, and moves its Alexandria package version and
generation row above the merged values.

**Copies.** Step 1's copies of the study and runbook stay byte-identical to
`.hexaemeron/study.md` and `.hexaemeron/runbook.md`. A step that follows an
amendment re-copies both in the same commit, and every later step lists them.
The study carries no known-failure inventory fence.

## The decision record

The three decisions in study item 12 share one unnumbered draft,
`docs/decisions/drafts/split-interval-log-attributions-across-components.md`.
Step 1 creates it whole, because the design bridge names it and the study
check needs it to exist: the split format, the published limits, and
Laurence's 2026-09-23 decision to keep today's memory model. No step writes a
number into its bytes or its filename, and no document cites it by anything
but that path.

## Step 1: Preserve the design records and open the decision draft

**Goal.** Commit the receipted study and runbook, the locked design record with its 36 selection reports, resolvers and observations, and the decision draft the design bridge names, with no product change.

**Entry.** The run branch `fiat/1888-epoch-table-split-and-release-caps` at `17ea8d2ab5e52081370b13b92390b64849ed880d`, with the study, design-lock and runbook receipts accepted and the Alexandria suite passing there.

**Exit.** The design records sit under the Alexandria docs tree byte-identical to their controller sources, the decision draft exists, and every command below exits 0.
The study, runbook and record are copied to
`plugins/alexandria/docs/epoch-table-split/study.md`, `runbook.md` and
`design-evidence.json`. The folder `.hexaemeron/design/` is copied, less its
`evidence/` directory, to `plugins/alexandria/docs/epoch-table-split/design/`.
The copy holds the 36 `reports/selection/*.json` at the relative paths the
record binds. The draft carries the status `Accepted, 2026-09-23`, no number,
and the sections Context, Decision, Alternatives and Consequences.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1888-epoch-table-split-and-release-caps --scope root --scope alexandria --format json
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py --study plugins/alexandria/docs/epoch-table-split/study.md
python3 plugins/hexaemeron/skills/protasis/scripts/protasis.py plugins/alexandria/docs/epoch-table-split/runbook.md
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py --study plugins/alexandria/docs/epoch-table-split/study.md --design-evidence plugins/alexandria/docs/epoch-table-split/design-evidence.json --repo-root .
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py docs/decisions/drafts/split-interval-log-attributions-across-components.md plugins/alexandria/docs/epoch-table-split
python3 plugins/hexaemeron/skills/phylax/scripts/phylax.py plugins/alexandria/docs/epoch-table-split
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py docs/decisions/drafts/split-interval-log-attributions-across-components.md plugins/alexandria/docs/epoch-table-split/study.md plugins/alexandria/docs/epoch-table-split/runbook.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py docs/decisions/drafts/split-interval-log-attributions-across-components.md
```

**Files.**

- Create under `plugins/alexandria/docs/epoch-table-split/`: `study.md`,
  `runbook.md`, `design-evidence.json`, `design/resolve.py`,
  `design/conformance.py`, `design/build_design_evidence.py`,
  `design/observations.json` and the 36 `design/reports/selection/*.json`.
- Create `docs/decisions/drafts/split-interval-log-attributions-across-components.md`
  and `plugins/alexandria/tests/test_epoch_table_split_records.py`.
- Raise the version in the four places the rules list.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`.

**Tests.** Add `DesignRecordCopyTests` to `plugins/alexandria/tests/test_epoch_table_split_records.py` with three tests. `test_the_record_copy_is_the_locked_design_record` asserts the copy's SHA-256 is the design-lock value above. `test_every_selection_report_the_record_binds_is_committed` asserts that each resolved cell's report exists at its bound path with its bound SHA-256. `test_the_conformance_harness_refuses_every_other_candidate` asserts that the committed `conformance.py` exits 2 for each of the three rejected candidates, names the refusal and writes no report. The full count is set by execution. Also run by hand before the commit, outside the suite:

- `cmp` of every copy against its `.hexaemeron/` source;
- `python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py plugins/alexandria/docs/epoch-table-split/design-evidence.json --transition design-lock`, which prints `clean`;
- `python3 plugins/hexaemeron/skills/ephoros/scripts/ephoros.py plugins/alexandria/docs/epoch-table-split`;
- `python3 scripts/plugin_release.py --base fiat/1888-epoch-table-split-and-release-caps --head HEAD`, which names the Alexandria rise.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`

**Disciplines.** phylax: the committed resolvers enter the `lint-phylax` walk under `plugins/`, read only pinned git objects and preserved releases through fixed argv, and the Phylax run above keeps them clean. ephoros: none, nothing in this step runs unattended. metron: none, this step makes no performance claim. elenchus: a copy that differs from its source is a failure to reproduce and repair, never a copy to re-pin. hypomnema: the step opens the decision record the design bridge names and ships the study and runbook under the repository's lint.

## Step 2: Split log attributions into plan-derived parts under the current caps

**Goal.** Let a subject-set plan declare `log_attribution_parts` with the value `journal-ranges`, so its release carries attribution rows in plan-derived `log-attributions.<k>` parts under receipt v4 that `check` re-derives offline, while every plan without the field builds today's bytes.

**Entry.** Step 1's branch with its `--audit` head merged into it; `MAX_COMPONENTS` is still 128.

**Exit.** A split plan builds and checks at today's caps, every plan without the field keeps its bytes, and every command below exits 0.

- `validate_plan` admits `log_attribution_parts` only on an
  `alexandria-interval-plan/v2` plan that declares `shards_per_component`,
  with the single value `journal-ranges`, and refuses it elsewhere by name.
- Part `k` is `log-attributions.<k>`. It holds, in `attribute_logs` order, the
  rows of every preserved log in the shards of the plan's `k`th journal range,
  the range `logs.<k>` covers. An empty range gives an empty part.
- `journal_components` still returns the journals. A sibling derivation returns
  the parts, and the plan-time refusal counts fixed, journal and part
  components against `MAX_COMPONENTS` before any request.
- `_epoch_receipt` calls `attribute_logs` exactly as today, with whatever
  keywords #1885 adds, and validates the rows. For a split plan it slices the
  returned list by each range's blocks and writes
  `alexandria-interval-receipt/v4`. That receipt keeps v3's `epochs`,
  `first_code`, `format`, `implementation_code`, `reconciliation` and
  `shards`. It drops `log_attributions` and adds `log_attribution_parts`, one
  `{component, first_shard, last_shard, rows}` entry per part in order.
- Each part is an `alexandria-interval-log-attributions/v1` document,
  `{first_shard, format, last_shard, part, rows}`. Its capture is header-bound
  like the epoch table's, counts `/rows`, and names its shards and blocks in
  one gap sentence the plan derives. A part above 67,108,864 bytes or
  2,000,000 nodes refuses in the build, naming the part.
- `check` requires receipt v4 exactly when the plan declares the split. The
  receipt's part list must equal the plan's. Each part's shape, index, range
  and gap sentence must be the plan's, every row must be valid and inside its
  part's blocks, and each part must equal the derived rows for its range.
  Missing and extra parts reach the existing component refusals, and every
  refusal names the part.
- The schemas gain `interval-receipt-v4.schema.json`,
  `interval-log-attributions-v1.schema.json` and the optional field in
  `interval-plan-v2.schema.json`. `schemas/README.md` catalogues them, and
  `docs/usdc-interval-collector.md` states the part rule, receipt v4 and the
  component count.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1888-epoch-table-split-and-release-caps --scope root --scope alexandria --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/alexandria/docs/usdc-interval-collector.md plugins/alexandria/schemas/README.md
python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py plugins/alexandria/docs/usdc-interval-collector.md
```

**Files.**

- Change `plugins/alexandria/scripts/alexandria_lib/interval.py` at
  `validate_plan` and beside `SPLIT_FIELD`.
- Change `plugins/alexandria/scripts/usdc_interval.py` at `journal_components`
  and its new sibling, `component_gap` or a part gap helper beside it,
  `Builder.build`, `Builder._epoch_receipt`, `Builder._capture`, `_role` and
  `check_interval`.
- Change `plugins/alexandria/schemas/interval-plan-v2.schema.json`,
  `plugins/alexandria/schemas/README.md` and
  `plugins/alexandria/docs/usdc-interval-collector.md`.
- Create `plugins/alexandria/schemas/interval-receipt-v4.schema.json`,
  `plugins/alexandria/schemas/interval-log-attributions-v1.schema.json` and
  `plugins/alexandria/tests/test_log_attribution_parts.py`.
- Raise the version in the four places the rules list. Re-copy
  `plugins/alexandria/docs/epoch-table-split/study.md` and `runbook.md` if an
  amendment has landed since the last copy.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`.

**Tests.** The resolver loads seven tests for `split-parts-rederive-and-refuse`, so `plugins/alexandria/tests/test_log_attribution_parts.py` carries exactly these names. `AttributionPartBuildTests` holds `test_a_split_plan_writes_one_part_per_journal_range` and `test_a_plan_without_the_field_builds_todays_bytes`. `AttributionPartCheckTests` holds `test_check_rederives_every_part_from_its_own_shards`, `test_a_missing_part_refuses_by_name`, `test_an_extra_part_refuses_by_name`, `test_reordered_parts_refuse_by_name` and `test_an_altered_part_refuses_by_name`. Build them on `WildcatCase` from `tests/test_wildcat_venue.py`, whose V2 fixture is a set of 137 subjects over 80 blocks, re-planned with `shards_per_component`. Cover in addition:

- the field refusing by name on a single-proxy plan, without `shards_per_component`, or with another value;
- receipt v4 under a plan without the field, and v3 under a split plan, refusing;
- a row outside its part's blocks refusing;
- a part over a patched byte or node budget refusing by name in the build and in `check`;
- a part capture without its gap sentence refusing;
- the v2 plan schema admitting the optional field, and both new schemas closed, named and catalogued;
- the Wildcat V1 and V2 fixtures still building v3 releases, with `plan_digest` and the checkpoint unchanged for plans without the field.

At least the seven named tests; the full count is set by execution. The local version proof is `python3 scripts/plugin_release.py --base fiat/1888-epoch-table-split-and-release-caps-step-1-preserve-the-design-records-and --head HEAD`.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-2.json`

**Disciplines.** phylax: a split release is untrusted input to `check`, and each part is read under the unchanged component byte and node bounds and a closed shape before its rows are compared. ephoros: every part refusal names `log-attributions.<k>` and its shard range, and the plan-time count names the total and the cap, because a refusal after hours of collection must say which part and why. metron: none, the rows are sliced from the list `attribute_logs` already returns and no budget is claimed. elenchus: each part fault is a fail-closed refusal with a guard test that fails on the parent. hypomnema: the plan field, part format and receipt v4 are the first decision in the Step 1 draft, and the collector document states them.

## Step 3: Raise the component and capture caps with the manifest and checkpoint limits

**Goal.** Raise `MAX_COMPONENTS` and `MAX_CAPTURES` to 16,384 with manifest, capture-plan and checkpoint limits sized for them, so a split release of more than 128 components builds, checks and verifies offline.

**Entry.** Step 2's branch with its `--audit` head merged into it, and the `split-parts-rederive-and-refuse` report written.

**Exit.** The published limits hold at their values, every reader uses them, and every command below exits 0.

- `release.py` sets `MAX_COMPONENTS` and `MAX_CAPTURES` to 16,384 and adds the
  manifest limits beside them: 134,217,728 bytes and 2,000,000 nodes.
- These read and write capture plans and manifests under those limits:
  `ingest` and `verify`; `check_interval`; `index.py` at `_load_release`,
  `_load_manifest` and `_insert_release`; `derivation.py` at `_read_manifest`,
  `derive` and `verify_derivation`; `compound_phase0.py` at `load_phase0`;
  `statement.py` at `_verified_manifest`; and `Builder.build` for
  `capture-plan.json`. Each refusal names the document and the limit.
- `Staging` writes and reads its checkpoint under 2,000,000 nodes and the
  unchanged 8,388,608 bytes.
- `MAX_RAW_COMPONENT_BYTES`, `MAX_JOURNAL_BYTES`, `MAX_SHARDS` and
  `MAX_STATEMENT_BYTES` keep their values, and `statement` still refuses a
  statement above 8,388,608 bytes by name.
- The schemas move with the constants. `capture-plan-v1` and
  `archive-manifest-v1` admit 16,384 components and captures,
  `address-query-v1` 16,384 captures, and `interval-checkpoint-v2` 12,289
  offsets. `schemas/README.md` states the 12,289 offsets, and the comment
  above `MIN_SHARD_WIDTH` in `interval.py` no longer names a 128-component
  ceiling.
- `docs/raw-releases.md` states the caps and manifest limits, and
  `docs/usdc-interval-collector.md` the component count and checkpoint limit.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1888-epoch-table-split-and-release-caps --scope root --scope alexandria --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/alexandria/docs/raw-releases.md plugins/alexandria/docs/usdc-interval-collector.md plugins/alexandria/schemas/README.md
for file in plugins/alexandria/docs/raw-releases.md plugins/alexandria/docs/usdc-interval-collector.md; do python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$file"; done
```

**Files.**

- Change `plugins/alexandria/scripts/alexandria_lib/release.py` at
  `MAX_COMPONENTS`, `MAX_CAPTURES`, the new manifest limits, `ingest` and
  `verify`.
- Change `plugins/alexandria/scripts/alexandria_lib/index.py`,
  `derivation.py`, `compound_phase0.py` and `statement.py` at the functions
  the Exit names.
- Change `plugins/alexandria/scripts/alexandria_lib/interval.py` at `Staging`
  and the comment above `MIN_SHARD_WIDTH`.
- Change `plugins/alexandria/scripts/usdc_interval.py` at `Builder.build` and
  `check_interval`.
- Change `plugins/alexandria/schemas/capture-plan-v1.schema.json`,
  `archive-manifest-v1.schema.json`, `address-query-v1.schema.json`,
  `interval-checkpoint-v2.schema.json` and `README.md`.
- Change `plugins/alexandria/docs/raw-releases.md`,
  `plugins/alexandria/docs/usdc-interval-collector.md` and
  `plugins/alexandria/tests/test_usdc_interval.py`.
- Create `plugins/alexandria/tests/test_release_limits.py`.
- Raise the version in the four places the rules list. Re-copy
  `plugins/alexandria/docs/epoch-table-split/study.md` and `runbook.md` if an
  amendment has landed since the last copy.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`.

**Tests.** The resolver loads six tests for `release-limits-hold-at-the-cap` and `split-release-over-128-components`. Five are new in `plugins/alexandria/tests/test_release_limits.py`. `ReleaseCapTests` holds `test_the_component_cap_admits_its_value_and_refuses_one_more` and `test_the_capture_cap_admits_its_value_and_refuses_one_more`. `ManifestLimitTests` holds `test_every_manifest_reader_admits_the_limits_and_refuses_above`, `CheckpointLimitTests` holds `test_a_checkpoint_for_the_largest_admitted_plan_round_trips`, and `SplitReleaseTests` holds `test_a_release_over_128_components_builds_checks_and_verifies_offline`. The sixth is `tests.test_usdc_interval.JournalSplitTests.test_a_split_beyond_the_release_component_limit_refuses_before_any_request`, re-derived for the new cap under its own name. What each one exercises:

- the re-derived test: a subject-set plan declaring the split, with 4,096 one-block shards and one shard per range, derives 16,391 components and refuses in the collector and builder constructors before any request, while two shards per range, 8,199 components, fits;
- the cap tests: `validate_plan` and `validate_manifest` with 16,384 entries pass and with 16,385 refuse by name;
- the reader test: it may patch the shared limits lower, and it also asserts their published values;
- the checkpoint test: it commits a full 16-entry history for a plan of 4,094 ranges across three classes, 12,283 journals, and reads it back through `Staging`;
- the over-128 test: it re-plans the V2 fixture with one-block shards and one shard per range, 327 components, and runs the build, `check` and `verify` with Python socket construction denied.

The near-limit refusal in `tests/test_statement.py` keeps passing unchanged. At least these six named tests; the full count is set by execution. The local version proof is `python3 scripts/plugin_release.py --base fiat/1888-epoch-table-split-and-release-caps-step-2-split-log-attributions-into-plan --head HEAD`.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-3.json`

**Disciplines.** phylax: the manifest parse budget widens sixteen times for untrusted releases, and the control is that every reader enforces the byte bound before reading and the node bound before accepting, with named refusals above both. ephoros: every limit refusal names the document, its size and the limit. metron: none, the step moves ceilings, not algorithms; Step 4 re-measures the base memory baseline. elenchus: each cap and limit has a guard at its value and one above it. hypomnema: the published limits are the second decision in the Step 1 draft, and `docs/raw-releases.md` states them.

## Step 4: Rebuild every pinned release and record the Alexandria generation

**Goal.** Run the study's proving path, record its evidence in a proof document, and write the Alexandria generation row the version-relations block declares.

**Entry.** Step 3's branch with its `--audit` head merged into it, and the `release-limits-hold-at-the-cap` and `split-release-over-128-components` reports written.

**Exit.** The proof document records every pinned identifier rebuilt, the split fixture passing and the V2 memory re-measured, the generation row and the skill version agree, and every command below exits 0.

- `plugins/alexandria/docs/epoch-table-split/proof.md` records each run the
  Tests field lists, made at this step's tree, with its exit and identifiers.
- The seven identifiers and two committed releases in the study's section 3
  reproduce.
- `EVOLUTION.md` gains one generation row, the next after the integration
  base, keeping the frontier revision and its SHA-256 byte for byte.
  `SKILL.md`'s `metadata.version` equals that row, and the skill's interval
  section names the part rule and receipt v4.

```sh
python3 plugins/alexandria/tests/run_tests.py
python3 scripts/run_checks.py --base fiat/1888-epoch-table-split-and-release-caps --scope root --scope alexandria --format json
python3 plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py plugins/alexandria/docs/epoch-table-split/proof.md plugins/alexandria/skills/alexandria/SKILL.md plugins/alexandria/skills/alexandria/EVOLUTION.md
for file in plugins/alexandria/docs/epoch-table-split/proof.md plugins/alexandria/skills/alexandria/SKILL.md; do python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py "$file"; done
python3 plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py plugins/alexandria/docs/epoch-table-split/proof.md plugins/alexandria/skills/alexandria
```

**Files.**

- Create `plugins/alexandria/docs/epoch-table-split/proof.md`.
- Change `plugins/alexandria/skills/alexandria/EVOLUTION.md` and
  `plugins/alexandria/skills/alexandria/SKILL.md`.
- Raise the version in the four places the rules list. Re-copy
  `plugins/alexandria/docs/epoch-table-split/study.md` and `runbook.md` if an
  amendment has landed since the last copy.
- Regenerate `.horos/boundary.json`, then `.horos/census.json`.

**Tests.** No new test module. `tests/test_evolution_contract.py` in the root suite checks the new row and the skill version. The demonstration tests already in the Alexandria suite rebuild the synthetic and live Compound identifiers, and `StagedRebuildTests` rebuilds both Wildcat identifiers with the staging variables exported. The proof records these runs, made from the run worktree's root with `NO_COLOR=1`:

- `python3 plugins/alexandria/examples/<demo>/demo.py build --output <fresh directory>`, then `verify` on that directory, for `usdc-interval-v0`, `usdc-interval-epochs-v0`, `usdc-interval-live-v0` and `wildcat-estates-interval-v0`, the last with both staging variables exported;
- `python3 plugins/alexandria/scripts/alexandria.py verify plugins/alexandria/examples/compound-v3-phase0-v0/release`, and the same for `proof-backed-state-v0`;
- the `SplitReleaseTests` run from Step 3;
- `/usr/bin/time -l python3 plugins/alexandria/scripts/usdc_interval.py check <preserved V2 release>`, beside the base's 1,208,811,520 bytes in 4.36 seconds.

The integration cell repeats the rebuilds against the constants in `conformance.py`. The local version proof is `python3 scripts/plugin_release.py --base fiat/1888-epoch-table-split-and-release-caps-step-3-raise-the-component-and-capture --head HEAD`.

Elenchus command: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-4.json`

**Disciplines.** phylax: none new, the demonstrations read committed and preserved bytes offline and write only fresh output directories. ephoros: none, nothing in this step runs unattended. metron: the step repeats the recorded base memory measurement on the same release, so a reader can see the memory model did not move; no budget is claimed. elenchus: a pinned identifier that does not reproduce stops the step as a regression to localise, never a pin to update. hypomnema: the generation row is the ledger home the study names, and the proof document records the evidence the integration cell repeats.
