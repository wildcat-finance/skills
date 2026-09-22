# Issue 1355 runbook: protected Wildcat V2 layouts and selectors

This runbook derives from the receipted study at SHA-256
`d403d403978feb9d941df5e80fb764c202f4eed7683b8a7deeefe7a19d265fe4`.
The implementation baseline is synced `main` at
`8b0a7abbf80e2466dc32e477733e1aa7471d7af7`. Use Python `3.14.6`, Forge
`1.7.1`, the exact source and compiler profiles in the study, and the selected
`prepared-source-group` construction. Each step is one signed, audited pull
request in the Fiat stack.

Production Solidity, build configuration, dependency pins and deployed source
identities remain fixed. Test-only harness revisions are separate signed Git
objects. Private fee-recipient and role-provider source stays outside the
public Skills tree; public records carry only bounded metadata and digests.
Negative candidates exist only in disposable copies. No Gate 1, Gate 5,
fixture, release or redistribution claim is valid before its named evidence
gate passes.

```design-lock
schema | protasis-design-evidence/v1
sha256 | ee56a6dabd1e73c60786cdceda665ebfdaa8b570b54f063de3a860aacdaab108
candidate | prepared-source-group
```

## Step 1: Scaffold evidence and prepare signed harnesses

**Goal.** Commit the checked specification and evidence checker, then establish a green signed test-only harness revision for every source/build group without changing production bytes.

**Entry.** Run branch `fiat/1355-seal-wildcat-v2-protected-layouts-and-selec` at `8b0a7abbf80e2466dc32e477733e1aa7471d7af7`, with the study and design record receipted, the unmodified V1 and V2 failures preserved, no Hermes baseline sealed, and the repository hooks, Python pin, dependency locks, CI and Apache-2.0 licence unchanged.

**Exit.** Repository copies of the study, runbook and immutable design record live under docs/kickoff/1355/. The bounded evidence checker and focused tests validate source-group identity, compiler profile, exact paths, signatures, source parity, test results, report schemas, digests and access classes. Nine prepared revisions are recorded against their original pins. Unchanged groups use signed same-tree revisions. The V1 revision changes only the admitted test files: it applies the upstream escrow-oracle correction and migrates the six active legacy failure tests to explicit revert assertions immediately before the intended calls while preserving their earlier assertions and fuzz domains. The V2 revision changes only the admitted timestamp read to the pinned VM interface while preserving expected event values and assertions. Full fixed-seed suites pass for all nine groups, every prepared commit verifies, and original-versus-prepared comparisons show zero production, configuration, compiler-setting, dependency-pin or submodule difference. The prepared-state report passes before Step 2. Prove the repository exit with `python3 scripts/run_checks.py`.

**Files.** Create `docs/kickoff/1355/{study.md,runbook.md,design-evidence.json,README.md}`, `docs/kickoff/1355/evidence/prepared-harnesses.json`, `scripts/kickoff_hermes_1355.py` and focused tests under `tests/`. Refresh `tests/check-map-v1.json`, `.horos/census.json` and `.horos/boundary.json` only as required by their owners. Test-only commits and complete private-source evidence remain in the run's restricted local evidence root, outside the Skills Git tree.

**Tests.** Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-1355-step-1.json`. Add checker cases for all nine groups, altered production or configuration bytes, unsigned or wrong-parent revisions, missing tests, red or skipped suites, weakened fuzz metadata, path escape, digest drift and private payload leakage. Retain parent-red and prepared-green reports for the V1 escrow, V1 legacy failure convention and V2 timestamp oracle.

**Disciplines.** phylax: source repositories, subprocesses, report paths and private outputs cross trust boundaries and require fixed arguments, bounded reads, no-follow destinations and secret-safe logs. ephoros: manifests expose group, stage, command exit, test counts, digest and parity verdict without private source. metron: record suite duration and evidence size as observations only; no speed claim is made. elenchus: preserve each reproduced parent failure and prove the minimal test-only correction without weakening assertions or domains. hypomnema: the source/prepared split, admitted test paths and evidence custody belong in the tracked specification and README.

## Step 2: Capture the fixed block and close the protected inventory

**Goal.** Produce verified fixed-block and source-preservation evidence, then map every admitted estate address and dependency type to one reviewed protected source group.

**Entry.** The controller-receipted Step 1 head, with `prepared-state` passing, nine signed prepared revisions recorded, all full suites green, production parity established, and no Gate 1 run started.

**Exit.** A finite Lazarus fixture binds Ethereum chain 1, block 26006289, block hash 0x3d069f254a10d98ad19eff0f397cf28db3613fd98bff1df48c798920552f4ec5, the declared account and slot set, exact RPC requests, proofs, limits and offline replay result. A verified Alexandria raw release preserves the admitted recorded inputs and the verified fixture by digest without interpreting deployment-to-source mappings. The protected inventory maps all 137 registry addresses to qualified types and exact source/build groups, includes the sanctions escrow and wrapper implementation dependencies, and preserves every named exclusion with owner and reason. Producer, reviewer, artifact and digest fields are complete for scope, source mapping, fixture, release and protected inventory. The owner-handoffs report passes before Step 3. Prove the repository exit with `python3 scripts/run_checks.py`.

**Files.** Create bounded public records under `docs/kickoff/1355/evidence/` for the protected inventory, instance mapping, exclusion register, owner handoffs and public fixture/release metadata. Extend `scripts/kickoff_hermes_1355.py` and its tests for inventory and handoff validation. Store complete proof material and any restricted source-bearing release in the run's local restricted evidence root; never copy private source into tracked docs or test fixtures. Refresh owned generated records only when their inputs change.

**Tests.** Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-1355-step-2.json`. Add missing, duplicate and conflicting address/type mappings; wrong chain, block or hash; absent or invalid proof/replay/verification status; incomplete owner handoff; unowned exclusion; escrow or wrapper omission; source-group drift; unsafe path; and private-source disclosure cases. Preserve the accepted registry and source-match digests unchanged.

**Disciplines.** phylax: provider replies, proofs, Git objects, archive inputs and evidence destinations are hostile or restricted inputs with explicit limits and no credential logging. ephoros: reports name capture stage, request and byte counts, verification state, coverage totals and missing owner without raw payloads. metron: capture limits are safety budgets and recorded durations are observations, with no performance claim. elenchus: every false-accept or incomplete-coverage case gets a minimal checker specimen while canonical owner verifiers remain authoritative. hypomnema: the protected-set decision, exclusions, evidence-class boundaries and owner handoffs live in the tracked inventory and README.

## Step 3: Seal all source-group baselines

**Goal.** Run canonical Hermes Gate 1 once for every reviewed source/build group and bind every protected layout and selector snapshot to its original source and prepared harness identities.

**Entry.** The controller-receipted Step 2 head, with `owner-handoffs` passing, verified fixture and release digests retained, complete reviewed inventory and exclusions, all prepared suites green, and no baseline directory called sealed.

**Exit.** Nine independent canonical Hermes baseline runs succeed under the exact compiler and build profiles. Every group names all of its protected qualified contracts through repeated protected-contract operands and records its original source pin, signed prepared harness revision, fixed seed, corpus identity, rule, gas target, layouts, method identifiers, test and snapshot outputs. Instance mappings point only to successful matching group records. Failed attempts remain unsealed evidence. A public manifest carries safe metadata and digests while private complete bundles remain restricted. The sealed-baselines report passes before Step 4. Prove the repository exit with `python3 scripts/run_checks.py`.

**Files.** Create `docs/kickoff/1355/evidence/baselines.json` and safe per-group summaries; extend the evidence checker and focused tests for canonical Gate 1 records, full protected-set coverage, original/prepared identity joins and access separation. Keep full Hermes run directories in the restricted evidence root and commit no private source snapshots.

**Tests.** Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-1355-step-3.json`. Cover a missing group or protected contract, wrong original or prepared ref, failed or partial Gate 1, compiler/profile drift, mismatched measurement sets, absent layout or selector snapshot, unsealed failed run, instance mapped to the wrong group, digest mutation and restricted payload in public output.

**Disciplines.** phylax: Hermes executes repository tests and captures source-bearing outputs, so fixed commands, isolated directories, bounded manifests and access classes apply. ephoros: each group reports stage, Gate 1 status, protected count, test count, snapshot identity and digest without source payloads. metron: Hermes owns gas measurements; retain exact before values and do not generalise suite duration. elenchus: any failed baseline is investigated and preserved rather than omitted or relabelled. hypomnema: baseline composition, protected contracts, source joins and limitations belong in the tracked manifest and reproduction guide.

## Step 4: Demonstrate independent Gate 5 refusals

**Goal.** Produce separate disposable layout and selector candidates that save gas, pass Hermes Gates 2 through 4 and are rejected for the intended difference at Gate 5.

**Entry.** The controller-receipted Step 3 head, with `sealed-baselines` passing for all nine groups, immutable baseline digests recorded, clean production source copies available, and no negative candidate promoted.

**Exit.** One layout candidate and one selector candidate use separate disposable copies, one supported corpus rule and one optimisation class each. Each candidate records a real gas saving for every named target, no deterministic regression, unchanged tests and matching measurements through Gates 2 to 4, then exits 50 at Gate 5 with the intended protected layout or selector difference and offending qualified contract identified. Complete patches, commands, gate records and comparison outputs are retained. Production source digests are restored and match the clean baselines after each run. The separate-rejections report is complete for integration. Prove the repository exit with `python3 scripts/run_checks.py`.

**Files.** Create `docs/kickoff/1355/evidence/rejections.json` and safe layout/selector summaries; extend the checker and focused tests for independent candidates, Gates 2 to 5, intended differences, exit status, patch class, gas savings and source restoration. Store complete private candidate bundles in the restricted evidence root and never merge their Solidity changes.

**Tests.** Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-1355-step-4.json`. Cover rejection at the wrong gate, missing gas saving, test or measurement drift, mixed optimisation classes, shared candidate copy, wrong protected contract, exit other than `50`, absent patch or comparison output, restoration mismatch, digest drift and accidental negative-source inclusion.

**Disciplines.** phylax: candidate copies and source-bearing outputs stay isolated, bounded and classified, with exact restoration checks. ephoros: safe summaries report candidate, rule, class, gate exits, target savings, offending contract and restoration verdict. metron: Hermes supplies same-method gas evidence before Gate 5; no unrelated runtime claim is admitted. elenchus: an earlier-gate failure is a different failure and must be reduced before rerunning the intended specimen. hypomnema: the two rejected candidates, their exact limits and the prohibition on promotion belong in the evidence record.

## Step 5: Reproduce and deliver the sealed evidence set

**Goal.** Re-run the complete public verification path, reconcile restricted custody and publish a reviewer-readable record of the estate baseline and both Gate 5 refusals.

**Entry.** The controller-receipted Step 4 head, with nine sealed baselines, two complete independent rejection records, restored source digests, all prior conformance reports green and no private source in the public tree.

**Exit.** A clean reproduction validates the registry and protected inventory, all owner handoffs, fixture and release verification receipts, nine baseline manifests, both rejection demonstrations, source restoration, access classes and every referenced digest. The public README gives exact bounded reproduction and recovery instructions, states coverage and exclusions, separates original source pins from prepared test harnesses, and makes no private-source or redistribution claim. The restricted evidence index names a local authorised destination, complete bundle digests and readback results; public records reveal no private source. The restricted-delivery and separate-rejections reports both pass at integration. The full checked repository runner is green, generated Horos records match the final tree, and the Git worktree is clean after the signed commit. Prove the final repository exit with `python3 scripts/run_checks.py`.

**Files.** Finalise `docs/kickoff/1355/README.md`, the public evidence manifests and safe summaries, the restricted index outside Git, `scripts/kickoff_hermes_1355.py` and focused tests. Update `.horos/census.json`, `.horos/boundary.json` and `tests/check-map-v1.json` only through their owning checks. Do not add private source, raw credentials, negative Solidity candidates or complete restricted Hermes snapshots to Git.

**Tests.** Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-1355-step-5.json`. Add an end-to-end clean-copy verification and hostile cases for omitted groups, stale or altered digests, unavailable restricted bundle, wrong access class, leaked source, unverified fixture or release, mapping drift, missing Gate 5 record and source-restoration failure. Re-run all focused cases and the selected full repository checks without weakening limits or fixtures.

**Disciplines.** phylax: final publication and restricted custody require exact paths, access classes, secret scanning, digest readback and no private payload in Git. ephoros: the final report answers group, coverage, gate, restoration and custody status with safe counts and digests. metron: record actual reproduction time and evidence volume without a performance commitment. elenchus: any final mismatch reopens its owning step and retains the failing specimen before correction. hypomnema: the README and manifests are the durable reviewer handoff for scope, evidence, limitations, recovery and remaining custody boundary.

### Amendment -- 2026-09-22

**What changed.** Complete replacement Files: Create `docs/kickoff/1355/{study.md,runbook.md,design-evidence.json,README.md}`, `docs/kickoff/1355/evidence/prepared-harnesses.json`, `scripts/kickoff_hermes_1355.py`, focused tests under `tests/`, and one numberless cross-cutting decision record under `docs/decisions/drafts/` for the selected signed-preparation and source-group construction. The tracked study copy carries one Hypomnema design bridge to that record; the controller-owned receipted study remains unchanged. Refresh `tests/check-map-v1.json`, `.horos/census.json` and `.horos/boundary.json` only as required by their owners. Test-only commits and complete private-source evidence remain in the run's restricted local evidence root, outside the Skills Git tree.

**Why.** Step 1 ships the study, so Hypomnema requires its selected expensive-to-reverse design and rejected alternatives to have one established decision home. The earlier Files field named the study copy but omitted that standing record and bridge.

**Steps touched.** Step 1 Files.

**Still holding.** Step 1: entry holds; exit holds. Step 2: entry holds; exit holds. Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-22

**What changed.** Complete replacement Exit: Repository copies of the study, runbook and immutable design record live under docs/kickoff/1355/. The bounded evidence checker and focused tests validate source-group identity, compiler profile, exact paths, signatures, source parity, test results, report schemas, digests and access classes. Nine prepared revisions are recorded against their original pins. Unchanged groups use signed same-tree revisions. The two V1 revisions change only the admitted escrow and BaseERC20 test files: they apply the upstream escrow-oracle correction, replace the six active legacy failure methods with explicit arithmetic-panic assertions immediately before the intended calls, and constrain the insufficient-allowance fuzz case to valid allowance and amount ranges that reach that call. The V2 revisions may change only the admitted timestamp read, the same BaseERC20 legacy-failure convention and range repair, and the 5838 fixed-term test input from 366 to 731 days against its unchanged 730-day maximum. The c7 wrapper source, configuration and submodule pins remain unchanged; its full fixed-seed suite runs only through an isolated Foundry 0.3.0 binary after archive and binary SHA-256 values are recorded. Full fixed-seed suites pass for all nine groups, every prepared commit verifies, and original-versus-prepared comparisons show zero production, configuration, compiler-setting, dependency-pin or submodule difference. Each wrapper result records its runner version and verified binary digest. The prepared-state report passes before Step 2. Prove the repository exit with `python3 scripts/run_checks.py`.

Complete replacement Tests: Elenchus command: `python3 plugins/hexaemeron/tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.elenchus/fiat-1355-step-1.json`. Add checker cases for all nine groups, altered production or configuration bytes, unsigned or wrong-parent revisions, missing tests, red or skipped suites, weakened fuzz metadata, path escape, digest drift, historical-runner digest drift and private payload leakage. Retain parent-red and prepared-green reports for the V1 escrow, V1 and V2 legacy failure convention and V2 timestamp oracle, fixed-term boundary and unchanged vendored wrapper suite.

**Why.** The preserved fixed-seed parent-red results localise three additional test-only repairs and two vendored wrapper failures. The signed preparations and later baseline records must name their precise test boundaries and the historical wrapper runner so that a green suite cannot conceal a production, configuration, dependency, submodule or toolchain substitution.

**Steps touched.** Step 1 Exit and Tests.

**Still holding.**
Step 1: entry holds; exit holds.
Step 2: entry holds; exit holds.
Step 3: entry holds; exit holds.
Step 4: entry holds; exit holds.
Step 5: entry holds; exit holds.
