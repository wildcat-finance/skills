# Wildcat withdrawal-batch canonical meaning runbook

This runbook implements issue 2087's receipted study, SHA-256 `2726baaa8e4cb92b24ecb0c53041d81d524543e76a124d0781556a53845b3a8b`, from Skills `50d71a2e8c1777f8eb26db32dd8adeadb34063bd`. The selected `adjacent-burn` design maps `WithdrawalBatchCreated`, `WithdrawalBatchPayment`, `WithdrawalBatchExpired` and `WithdrawalBatchClosed` for both Wildcat generations as native market events and joins each payment to the market-to-zero `Transfer` at the log index before it. Python `3.14.6`, stdlib production code, signed commits and the repository's checked runner remain required. Queue replay and unpaid-status projection stay with issue 1926, accounting replay with issue 1386 and function reconciliation with issue 1387.

Always: preserve native bytes, actual parties and exact native units; leave a named gap where the burn is missing, reordered, differently valued or claimed twice; keep the two published Wildcat specimens, the six Aave and Euler releases and schema 2 byte-identical; run the declared checks and sign commits. Ask first: a new dependency, a schema envelope change, an adapter version bump, a CI change, a live RPC fetch, publishing any count derived from the retained releases. Never: infer a batch event's cause from the action sharing its transaction; read `normalizedAmountPaid` as lender receipt, spendable cash or execution; commit a staging path, private report or retained payload; edit a published release; claim an unrun check.

```design-lock
schema | protasis-design-evidence/v1
sha256 | d13ace405808ba920cc911b4578ef133b88d7103244cbb9cf1c794478432bc6a
candidate | adjacent-burn
```

```command-interfaces
schema | protasis-command-interfaces/v1
plugins/tabularium/tests/prove_wildcat_batches.py | build_parser | step:1
plugins/tabularium/tests/emit_wildcat_batch_report.py | build_parser | step:1
```

```version-relations
tabularium | plugins/tabularium/skills/tabularium/EVOLUTION.md | next-generation-after-integration-base
```

Step 1 supplies both thin registered interfaces, and their complete bytes stay fixed after its push binding. Later behaviour belongs in the imported implementation module `plugins/tabularium/tests/wildcat_batch_reports.py` and in focused test modules. The proof interface accepts exactly the candidate, criterion and report arguments the design record names. It writes one closed `protasis-design-report/v1` object only after the matching implementation check ran and passed; an unknown pair, an unbuilt criterion, missing custody or an unexpected error exits 2 and writes no report. The Elenchus interface accepts a Step number and report path, runs only that Step's focused test classes in process without subprocesses, and writes `unittest-json-v1` with actual tests, failures, errors and skips.

The retained-conformance criterion reads the two staging trees named by `ALEXANDRIA_WILDCAT_V1_STAGING` and `ALEXANDRIA_WILDCAT_V2_STAGING`. It rebuilds each raw release through the public example builder and runs `wildcat-canonical` and `verify` in a private temporary directory outside the repository, then removes it. Its report value is one boolean; its sidecar carries only raw release identifiers and canonical and coverage digests. No path, count, address, transaction, block or amount from the retained releases enters a report, a test output that is committed, or any public record, under Laurence's 2026-10-13 ruling recorded in the study. The driver restores the staging trees from custody into a private directory before Step 4 and purges them after the run no longer needs them.

The generation relation preserves Tabularium's held Compound Phase 1 frontier. Step 2 adds one evidenced generation row and the matching skill metadata version; integration rechecks the exact current base and resolves any generation drift through the controller's signed sync and revalidation path. Do not advance the evolution counter, change the held job or bump `ADAPTER_VERSION`, which stays `1.0.0` with four new `.v1` rules per generation.

The study's checked inventory assigns no failure to any Step. Each Step still opens through its controller-issued inoculation packet and exact no-known-findings record before product edits. A real failure found mid-step follows Elenchus and, where it changes a receipted requirement, the append-only amendment path.

Every Step bumps the Tabularium package once, above its pull request base and above every version any local or remote ref claims, re-checked before its push; the planned sequence is 0.5.8, 0.6.0, 0.6.1 and 0.6.2. The version surfaces are `plugins/tabularium/.claude-plugin/plugin.json`, `plugins/tabularium/.codex-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json` and `tests/test_version_propagation.py`; prove each bump with `python3 scripts/plugin_release.py --base <PR base> --head HEAD` before the push. Before every commit, finish the written-record sequence on new prose, regenerate portable copies when a copied source changes, stage, then regenerate `.horos/boundary.json` and `.horos/census.json` and stage them.

## Step 1: Scaffold batch proof runners and commit the specification

**Goal.** Supply the two registered runner interfaces, their honest refusals, the public specification bundle and the decision draft, without claiming that the mapping exists.

**Entry.** The controller's exact Step 1 parent on the run branch at the starting commit, with study and design receipts and the completed no-known-findings inoculation receipt.

**Exit.** The Step 1 focused tests pass, every conformance criterion refuses with status 2 and writes no report, and the checked runner is green:

```sh
python3 plugins/tabularium/tests/emit_wildcat_batch_report.py --step 1 --report .hexaemeron/steps/1/focused.json
python3 scripts/run_checks.py --base 50d71a2e8c1777f8eb26db32dd8adeadb34063bd --scope root --scope tabularium --scope repo-lints --format json
```

**Files.** Add `plugins/tabularium/tests/prove_wildcat_batches.py`, `plugins/tabularium/tests/emit_wildcat_batch_report.py`, `plugins/tabularium/tests/wildcat_batch_reports.py` and `plugins/tabularium/tests/test_wildcat_batch_scaffold.py`. Add `docs/kickoff/2087/` with byte-exact copies of the receipted `study.md`, `runbook.md` and `design-evidence.json`, the selection reports under `design-reports/`, the two design probes under `design/`, and a README stating what is and is not yet implemented. Add `docs/decisions/drafts/give-wildcat-withdrawal-batch-events-native-meaning.md`. Bump the five version surfaces to 0.5.8. Update `tests/check-map-v1.json` only where ownership is missing, and regenerate `.horos/boundary.json` and `.horos/census.json`.

**Tests.** Parser cases accept every candidate and criterion pair the design record names and refuse any other; each conformance criterion refuses with exit 2 and no report while its implementation is absent; Step selection runs only the named classes, keeps errors apart from failures and refuses an unknown Step; the report path refuses an existing file and a symlinked parent; the bundle copies equal the receipted artefacts byte for byte. Expect at least 12 tests. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_batch_report.py --step 1 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2087-step-1.json`.

**Disciplines.** phylax: the runners write only fresh report files and launch no subprocess. ephoros: reports carry actual counters so a missing test is visible. metron: none, no performance change. elenchus: preserve a failing guard for any runner defect found. hypomnema: the decision draft records the join rule, family, units, expiry placement and unchanged adapter version.

## Step 2: Map the four batch events and join each payment's burn

**Goal.** Give the four batch events their native canonical meaning in both generations and join each `WithdrawalBatchPayment` to its adjacent market burn, with named gaps for every unmatched case.

**Entry.** Step 1's verified push head, with both runner interfaces bound.

**Exit.** The Step 2 focused tests pass, both conformance reports that block Step 3 are written with value true, and the checked runner is green:

```sh
python3 plugins/tabularium/tests/emit_wildcat_batch_report.py --step 2 --report .hexaemeron/steps/2/focused.json
python3 plugins/tabularium/tests/prove_wildcat_batches.py --candidate adjacent-burn --criterion semantic-conformance --report .hexaemeron/design-reports/adjacent-burn-semantic-conformance.json
python3 plugins/tabularium/tests/prove_wildcat_batches.py --candidate adjacent-burn --criterion schema-parity --report .hexaemeron/design-reports/adjacent-burn-schema-parity.json
python3 scripts/run_checks.py --base 50d71a2e8c1777f8eb26db32dd8adeadb34063bd --scope root --scope tabularium --scope repo-lints --format json
```

**Files.** `plugins/tabularium/scripts/tabularium_lib/wildcat_rules.py`, `wildcat_validation.py` and `wildcat_rows.py` in the same directory; `plugins/tabularium/schemas/canonical-event-v3.json`; `plugins/tabularium/tests/wildcat_batch_reports.py` for the two `step:3` criteria; new focused modules such as `plugins/tabularium/tests/test_wildcat_batch_mapping.py`; existing Wildcat tests whose closed expectations enumerate the seventeen rules or the schema branches, including `plugins/tabularium/tests/test_wildcat_v3_schema_parity.py`; `plugins/tabularium/docs/wildcat-canonical.md`; the generation row in `plugins/tabularium/skills/tabularium/EVOLUTION.md` with the matching `metadata.version` in `plugins/tabularium/skills/tabularium/SKILL.md`; the decision draft where the build changes it; the five version surfaces at 0.6.0; owner-generated portable copies; `.horos/boundary.json` and `.horos/census.json`.

**Tests.** Created, payment, expired and closed rows for both generations carry party `pool` only, family `exit-queue`, the study's units and the expiry in the decoded record. A payment joins only the log at index minus one that is `Transfer(market, 0x0, normalizedAmountPaid)` from the same emitter in the same transaction, and both rows carry each other's selector. Hostile cases stay gaps with no join: reordered burn, changed value, burn without payment, two burns before one payment, payment without burn. Two payments with equal amounts in one transaction both join their own burns. A malformed batch log refuses, and only created, closed and `market-closed` admit empty amounts. Schema and Python parity covers the eight new branches. `verify` refuses edited events, selectors, join records and coverage. The two published Wildcat specimens, the six Aave and Euler releases and schema 2 rebuild byte-identical. Expect at least 30 tests. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_batch_report.py --step 2 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2087-step-2.json`.

**Disciplines.** phylax: the four signatures reach the existing bounded decoder and the join reads only records of one transaction. ephoros: coverage keeps the burn and unclaimed-burn gaps countable per release. metron: none, the join is one lookup per payment and no speed claim is made. elenchus: guard any wrong join or lost gap before fixing it. hypomnema: the user guide states the four meanings, the join rule and that reserved assets are not receipt, cash or execution.

## Step 3: Publish constructed batch specimens

**Goal.** Publish one constructed batch specimen per generation that exercises all four events, a joined burn, two same-expiry payments in one transaction and the gap cases, rebuilds byte-identically and verifies offline after a move.

**Entry.** Step 2's verified push head, with both `step:3` conformance cells passing at that push.

**Exit.** The Step 3 focused tests rebuild and verify both new specimens and the checked runner is green:

```sh
python3 plugins/tabularium/tests/emit_wildcat_batch_report.py --step 3 --report .hexaemeron/steps/3/focused.json
python3 scripts/run_checks.py --base 50d71a2e8c1777f8eb26db32dd8adeadb34063bd --scope root --scope tabularium --scope repo-lints --format json
```

**Files.** New example directories `plugins/tabularium/examples/wildcat-v1-batches-v0/` and `plugins/tabularium/examples/wildcat-v2-batches-v0/`, each with its constructed raw release, generated release, README and rebuild script on the pattern of the existing Wildcat examples; focused specimen tests; the public-specimen section of `plugins/tabularium/docs/wildcat-canonical.md`; the five version surfaces at 0.6.1; `tests/check-map-v1.json` only where ownership is missing; `.horos/boundary.json` and `.horos/census.json`.

**Tests.** Each specimen's raw release follows the source emission order of both generations, including V1's queue transfer before `WithdrawalBatchCreated` and V2's created event first, and V2 `closeMarket`'s created, expired and closed sequence. Rebuild equals the committed bytes; a moved release verifies; every specimen record keeps its constructed-fixture qualification; the four signatures are absent from unsupported coverage; each payment carries its join and each hostile transaction its named gap. Expect at least 10 tests. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_batch_report.py --step 3 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2087-step-3.json`.

**Disciplines.** phylax: specimens are synthetic and carry no credential or retained payload. ephoros: each specimen's coverage shows mapped rows and gaps separately. metron: none, no performance claim. elenchus: a specimen that fails to rebuild is reproduced and guarded before repair. hypomnema: each README states that the specimen is constructed and what it does not establish.

## Step 4: Demonstrate retained conformance and record the reproduction

**Goal.** Run the selected design's retained-conformance check on both retained releases held in custody and publish the reproduction record with digests and pass or refuse results only.

**Entry.** Step 3's verified push head, with the driver-exported staging variables naming the restored V1 and V2 staging trees.

**Exit.** The Step 4 focused tests pass, the integration conformance report is written with value true, and the checked runner is green:

```sh
python3 plugins/tabularium/tests/emit_wildcat_batch_report.py --step 4 --report .hexaemeron/steps/4/focused.json
python3 plugins/tabularium/tests/prove_wildcat_batches.py --candidate adjacent-burn --criterion retained-conformance --report .hexaemeron/design-reports/adjacent-burn-retained-conformance.json
python3 scripts/run_checks.py --base 50d71a2e8c1777f8eb26db32dd8adeadb34063bd --scope root --scope tabularium --scope repo-lints --format json
```

**Files.** `plugins/tabularium/tests/wildcat_batch_reports.py` for the retained criterion; focused retained tests whose ordinary discovery runs constructed controls and refuses absent custody by name; `docs/kickoff/2087/reproduction.md` with the commands, raw release identifiers, canonical and coverage digests and pass or refuse results; the README in `docs/kickoff/2087/`; the saved-release paragraph of `plugins/tabularium/docs/wildcat-canonical.md`; the five version surfaces at 0.6.2; `.horos/boundary.json` and `.horos/census.json`.

**Tests.** Absent or unreadable staging variables refuse with exit 2 and no report; a staging tree that fails its staging manifest refuses; the report holds a boolean and its sidecar only identifiers and digests, with no path or count; a constructed control with an unclaimed market burn or a payment without its burn yields false rather than a passing report; the temporary build directory is gone after success and after refusal. Expect at least 8 tests. Elenchus command: `python3 plugins/tabularium/tests/emit_wildcat_batch_report.py --step 4 --report {report}`; format: `unittest-json-v1`; report file: `.elenchus/2087-step-4.json`.

**Disciplines.** phylax: the resolver reads two operator-named directories without following links and writes no path or payload. ephoros: the private run keeps its counts locally while the public report states which generation passed. metron: record the resolver's wall-clock duration as an observation with no claim. elenchus: a false retained result is reproduced on a constructed case and guarded before any repair. hypomnema: the reproduction record names what the retained check establishes and what stays unestablished.
