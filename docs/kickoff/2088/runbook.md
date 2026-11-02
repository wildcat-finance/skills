# Wildcat accrual and state-update canonical meaning runbook

This runbook implements issue 2088's receipted study, SHA-256 `86bfb87324bb2e3292de19b6821c11b73292fe07d5d27a31769687342f326d85`, from Skills `1fc995e72cc61267273abd8339a9c1fb2289b068`. The selected `abi-named-amounts` design maps `InterestAndFeesAccrued` and `StateUpdated` for both Wildcat generations as native market events with the market as `pool` party: each numeric field becomes one amount named after its ABI field (`scale-factor`, `base-interest-ray`, `delinquency-fee-ray`, `protocol-fees`) in its native unit, and the two timestamps and `isDelinquent` stay in the decoded record as native state, the way `MarketClosed` keeps its timestamp. Python `3.14.6`, stdlib production code, signed commits and the repository's checked runner remain required.

Always: preserve native bytes, native field names and exact native units; leave a named gap where the source does not establish a unit or asset; keep the published Wildcat specimens, #2087's batch specimens, the Aave and Euler releases and schema 2 byte-identical; run the declared checks; sign commits as `Dr Laurence E. Day <laurence@wildcat.finance>`, author and committer, with no trailer. Ask first: a new dependency, a schema envelope change, an adapter version bump, a CI change, a live RPC fetch, publishing any count derived from the retained releases. Never: infer an event's cause from events sharing its transaction; convert a ray ratio or a fee into another unit; treat `scaleFactor` in the two events as one quantity unless the source shows it; commit a staging path, private report or retained payload; edit a published release; claim an unrun check.

```design-lock
schema | protasis-design-evidence/v1
sha256 | 0b1f75f607b65713394d90fc75be442bf946e0cf3b0c243c5318550914936bbc
candidate | abi-named-amounts
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/tabularium/tests/prove_wildcat_accrual.py | build_parser | step:1
plugins/tabularium/tests/emit_wildcat_accrual_report.py | build_parser | step:1
```

```version-relations
tabularium | plugins/tabularium/skills/tabularium/EVOLUTION.md | next-generation-after-integration-base
```

Step 1 supplies both thin registered interfaces, and their complete bytes stay fixed after its push binding. Each resolves its own directory before importing `plugins/tabularium/tests/wildcat_accrual_reports.py`, so it runs under `python3 -P` and under Elenchus's safe-path runner. Later behaviour belongs in that implementation module and in focused test modules. The proof interface accepts exactly the candidate, criterion and report arguments the design record names and writes one closed `protasis-design-report/v1` object only after the matching implementation check ran and passed; an unknown pair, an unbuilt criterion, missing custody or an unexpected error exits 2 and writes no report. The Elenchus interface accepts a Step number and report path, runs only that Step's focused test classes in process without subprocesses, and writes `unittest-json-v1` with actual tests, failures, errors and skips.

The two `step:3` cells, `semantic-conformance` and `schema-parity`, are produced by Step 2's Exit and consumed when Step 2 pushes; no later worker reruns them into the same path. The `retained-conformance` cell blocks integration and is produced by Step 4's Exit. It reads the two staging trees named by `ALEXANDRIA_WILDCAT_V1_STAGING` and `ALEXANDRIA_WILDCAT_V2_STAGING`, reusing the custody, staging-manifest and private-scratch helpers in `plugins/tabularium/tests/wildcat_batch_retained.py` by import, and refuses by generation name when a generation maps no row of either event. Its report value is one boolean; its sidecar carries only raw release identifiers and canonical and coverage digests. No path, count, address, transaction, block or amount from the retained releases enters a report, a committed test output or any public record. The driver restores the staging trees from internal custody, the route ADR-110 records, into a private directory before Step 4 and purges them after the run no longer needs them.

The generation relation preserves Tabularium's held frontier. Step 2 adds one evidenced generation row and the matching skill metadata version; integration rechecks the exact current base and resolves any generation drift through the controller's signed sync and revalidation path. Do not advance the evolution counter, change the held job or bump `ADAPTER_VERSION`, which stays `1.0.0` with new `.v1` rules per generation.

The study's checked known-failure inventory assigns no failure to any Step. Each Step still opens through its controller-issued inoculation packet and exact no-known-findings record before product edits. A real failure found mid-step follows Elenchus and, where it changes a receipted requirement, the append-only amendment path.

Every Step bumps the Tabularium package once, above its pull request base and above every version any local or remote ref or open pull request claims, re-checked before its push; the planned sequence is 0.6.4, 0.7.0, 0.7.1 and 0.7.2. The version surfaces are `plugins/tabularium/.claude-plugin/plugin.json`, `plugins/tabularium/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` and `tests/test_version_propagation.py`; prove each bump with `python3 scripts/plugin_release.py --base <PR base> --head HEAD` before the push. Before every commit, finish the written-record sequence on new prose, regenerate portable copies when a copied source changes, stage, then regenerate `.horos/boundary.json` and `.horos/census.json` and stage them.

## Step 1: Scaffold accrual proof runners and commit the specification

**Goal.** Supply the two registered runner interfaces, their honest refusals, the public specification bundle and the decision draft, without claiming that the mapping exists.

**Entry.** The controller's exact Step 1 parent on the run branch at the starting commit, with study and design receipts and the completed no-known-findings inoculation receipt.

**Exit.** The Step 1 focused tests pass, every conformance criterion refuses with status 2 and writes no report, and the checked runner is green:

```sh
python3 plugins/tabularium/tests/emit_wildcat_accrual_report.py --step 1 --report .hexaemeron/steps/1/focused.json
python3 scripts/run_checks.py --base 1fc995e72cc61267273abd8339a9c1fb2289b068 --scope root --scope tabularium --scope repo-lints --format json
```

**Files.** Add `plugins/tabularium/tests/prove_wildcat_accrual.py`, `plugins/tabularium/tests/emit_wildcat_accrual_report.py`, `plugins/tabularium/tests/wildcat_accrual_reports.py` and `plugins/tabularium/tests/test_wildcat_accrual_scaffold.py`. Add `docs/kickoff/2088/` with byte-exact copies of the receipted `study.md`, `runbook.md` and `design-evidence.json`, the selection reports under `design/reports/`, the probe `design/accrual_probe.py`, and a README stating what is and is not yet implemented. Add `docs/decisions/drafts/give-wildcat-accrual-and-state-update-events-native-meaning.md`. Bump the five version surfaces to 0.6.4. Update `tests/check-map-v1.json` only where ownership is missing, and regenerate `.horos/boundary.json` and `.horos/census.json`.

**Tests.** Parser cases accept every candidate and criterion pair the design record names and refuse any other; each conformance criterion refuses with exit 2 and no report while its implementation is absent; Step selection runs only the named classes, keeps errors apart from failures and refuses an unknown Step; the report path refuses an existing file and a symlinked parent; both runners write a report under `python3 -P`; the bundle copies equal the receipted artefacts byte for byte. Expect at least 12 tests. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_accrual_report.py --step 1 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2088-step-1.json`.

**Disciplines.** phylax: the runners write only fresh report files and launch no subprocess. ephoros: reports carry actual counters so a missing test is visible. metron: none, no performance change. elenchus: preserve a failing guard for any runner defect found. hypomnema: the decision draft records the two actions and families, the `pool`-only party, the ABI-named amount kinds, the native-state fields, the declared field order and the unchanged adapter version.

## Step 2: Map the two events in both generations

**Goal.** Give `InterestAndFeesAccrued` and `StateUpdated` their native canonical meaning in both generations, with ABI-named amounts in native units and the timestamps and `isDelinquent` as decoded native state.

**Entry.** Step 1's verified push head, with both runner interfaces bound.

**Exit.** The Step 2 focused tests pass, both conformance reports that block Step 3 are written with value true, and the checked runner is green:

```sh
python3 plugins/tabularium/tests/emit_wildcat_accrual_report.py --step 2 --report .hexaemeron/steps/2/focused.json
python3 plugins/tabularium/tests/prove_wildcat_accrual.py --candidate abi-named-amounts --criterion semantic-conformance --report .hexaemeron/design/reports/abi-named-amounts-semantic-conformance.json
python3 plugins/tabularium/tests/prove_wildcat_accrual.py --candidate abi-named-amounts --criterion schema-parity --report .hexaemeron/design/reports/abi-named-amounts-schema-parity.json
python3 scripts/run_checks.py --base 1fc995e72cc61267273abd8339a9c1fb2289b068 --scope root --scope tabularium --scope repo-lints --format json
```

**Files.** `plugins/tabularium/scripts/tabularium_lib/wildcat_rules.py`, `wildcat_validation.py` and `wildcat_rows.py` in the same directory; `plugins/tabularium/schemas/canonical-event-v3.json`; `plugins/tabularium/tests/wildcat_accrual_reports.py` for the two `step:3` criteria; new focused modules such as `plugins/tabularium/tests/test_wildcat_accrual_mapping.py`; the existing tests whose closed expectations enumerate rules, schema branches, specimen rows or nullable-asset kinds (`plugins/tabularium/tests/test_wildcat_batch_mapping.py`, `test_wildcat_batch_parity.py`, `test_schemas.py`, `test_wildcat_v3_schema_parity.py` and `wildcat_v3_fixtures.py`); `plugins/tabularium/docs/wildcat-canonical.md`; the generation row in `plugins/tabularium/skills/tabularium/EVOLUTION.md` with the matching `metadata.version` in `plugins/tabularium/skills/tabularium/SKILL.md`; the Promise Machine pins on `EVOLUTION.md` (`tests/fixtures/promise-machine/runtime/tabularium-release-verification.json`, `tests/promise_machine_coverage.json`, `docs/promise-machine/obligation-gates/evaluation-run.json`, `integration-projection.json` and `integration-projection.md`); the decision draft where the build changes it; the five version surfaces at 0.7.0; owner-generated portable copies; `.horos/boundary.json` and `.horos/census.json`. `wildcat_abi.py` does not change.

**Tests.** Both events map in both generations with party `pool` only, the four ABI-named amount kinds in native units, the three ray or ratio kinds assetless and `protocol-fees` with the market's asset where the release establishes it and a named gap where it does not, and `fromTimestamp`, `toTimestamp` and `isDelinquent` in the decoded record. A moved field declaration, a non-boolean `isDelinquent` word and a truncated log each refuse; an unknown asset leaves the asset gap. Schema and Python parity covers the four new branches. `verify` refuses edited events, amounts and coverage. The published Wildcat and batch specimens, the Aave and Euler releases and schema 2 rebuild byte-identical. Expect at least 25 tests. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_accrual_report.py --step 2 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2088-step-2.json`.

**Disciplines.** phylax: the two signatures reach the existing bounded decoder, and a malformed word refuses by name. ephoros: coverage keeps every unit and asset gap countable per release. metron: none, one row per event and no speed claim. elenchus: guard any wrong unit, lost gap or silent conversion before fixing it. hypomnema: the user guide states the two meanings, the ray and fee unit sentences and that the timestamps and `isDelinquent` are native state, not amounts.

## Step 3: Publish constructed accrual specimens

**Goal.** Publish one constructed accrual specimen per generation that exercises both events and the gap cases, rebuilds byte-identically and verifies offline after a move.

**Entry.** Step 2's verified push head, with both `step:3` conformance cells passing at that push.

**Exit.** The Step 3 focused tests rebuild and verify both new specimens and the checked runner is green:

```sh
python3 plugins/tabularium/tests/emit_wildcat_accrual_report.py --step 3 --report .hexaemeron/steps/3/focused.json
python3 scripts/run_checks.py --base 1fc995e72cc61267273abd8339a9c1fb2289b068 --scope root --scope tabularium --scope repo-lints --format json
```

**Files.** New example directories `plugins/tabularium/examples/wildcat-v1-accrual-v0/` and `plugins/tabularium/examples/wildcat-v2-accrual-v0/`, each with its constructed raw release, generated release, README and rebuild script on the pattern of the existing Wildcat examples; focused specimen tests; the public-specimen section of `plugins/tabularium/docs/wildcat-canonical.md`; the five version surfaces at 0.7.1; `tests/check-map-v1.json` only where ownership is missing; `.horos/boundary.json` and `.horos/census.json`.

**Tests.** Each specimen's raw release follows the source emission order of its generation for both events. Rebuild equals the committed bytes; a moved release verifies; every specimen record keeps its constructed-fixture qualification; both signatures are absent from unsupported coverage; each gap case carries its named gap. Expect at least 10 tests. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_accrual_report.py --step 3 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2088-step-3.json`.

**Disciplines.** phylax: specimens are synthetic and carry no credential or retained payload. ephoros: each specimen's coverage shows mapped rows and gaps separately. metron: none, no performance claim. elenchus: a specimen that fails to rebuild is reproduced and guarded before repair. hypomnema: each README states that the specimen is constructed and what it does not establish.

## Step 4: Demonstrate retained conformance and record the reproduction

**Goal.** Run the selected design's retained-conformance check on both retained releases held in custody and publish the reproduction record with identifiers, digests and pass or refuse results only.

**Entry.** Step 3's verified push head, with the driver-exported staging variables naming the restored V1 and V2 staging trees.

**Exit.** The Step 4 focused tests pass, the integration conformance report is written with value true, and the checked runner is green:

```sh
python3 plugins/tabularium/tests/emit_wildcat_accrual_report.py --step 4 --report .hexaemeron/steps/4/focused.json
python3 plugins/tabularium/tests/prove_wildcat_accrual.py --candidate abi-named-amounts --criterion retained-conformance --report .hexaemeron/design/reports/abi-named-amounts-retained-conformance.json
python3 scripts/run_checks.py --base 1fc995e72cc61267273abd8339a9c1fb2289b068 --scope root --scope tabularium --scope repo-lints --format json
```

**Files.** `plugins/tabularium/tests/wildcat_accrual_reports.py` for the retained criterion; focused retained tests whose ordinary discovery runs constructed controls and refuses absent custody by name; `docs/kickoff/2088/reproduction.md` with the commands, raw release identifiers, canonical and coverage digests and pass or refuse results; the README in `docs/kickoff/2088/`; the saved-release paragraph of `plugins/tabularium/docs/wildcat-canonical.md`; the five version surfaces at 0.7.2; `.horos/boundary.json` and `.horos/census.json`.

**Tests.** Absent or unreadable staging variables refuse with exit 2 and no report; a staging tree that fails its staging manifest refuses; the report holds a boolean and its sidecar only identifiers and digests, with no path or count; a constructed control whose generation maps no row of either event yields false rather than a passing report; the temporary build directory is gone after success and after refusal. Expect at least 8 tests. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_accrual_report.py --step 4 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2088-step-4.json`.

**Disciplines.** phylax: the resolver reads two operator-named directories without following links and writes no path or payload. ephoros: the private run keeps its counts locally while the public report states which generation passed. metron: record the resolver's wall-clock duration as an observation with no claim. elenchus: a false retained result is reproduced on a constructed case and guarded before any repair. hypomnema: the reproduction record names what the retained check establishes and what stays unestablished.
