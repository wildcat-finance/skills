# Issue 1355 runbook: sealed Wildcat V2 layouts and selectors

This runbook derives from the receipted study, SHA-256
`1ba10293ea33adba9faec45ee58aeae43c80a3d09c9ba4d98ca8eddbf05703d0`, and its
selected construction `anchor-and-inspect`. The run branch
`fiat/1355-fresh-seal-wildcat-v2-layouts-and-selectors` starts at Skills
`main` `e9e95b891b3ae642516e017c46b97a18a1480164`. Python is 3.14.6, Forge is
1.7.1, the fuzz seed is `0x5EED`, and every Hermes run uses the compiler pins
in study section 3. Each step is one signed, audited pull request in the
stack.

No target source, test, configuration, compiler setting or submodule pin is
changed in any Gate 1 tree. Every Hermes run uses a fresh disposable checkout
at its pinned commit. Private repository payloads, including complete Hermes
directories for the fee recipient and role provider, stay in the ignored
restricted directory `.hexaemeron/restricted/` and are named in the public
tree by digest only. A Gate 5 candidate is never merged, promoted or
deployed. Study-time rehearsals are never delivery evidence.

The operator confirmed on 2026-09-23 that a protected type may share its
anchor's Gate 1 snapshot when its canonical storage layout and method map are
byte-equal to the anchor's (study section 4, question).

```design-lock
schema | protasis-design-evidence/v1
sha256 | 3d3f5097938b422f1d77d9c6ffb46448038a51bd2704674a3375145d5a80d650
candidate | anchor-and-inspect
```

```command-interfaces
schema | protasis-command-interfaces/v1
tests/run_tests.py | report_target | aa577d63846e947944c04506ca9985b18bf3bac21c6d360bdbc18fd1f8360258
```

## Step 1: Scaffold the inventory, checker and profile evidence

**Goal.** Commit the specification, the protected inventory and the evidence checker, and prove that layouts and method maps do not depend on the build profile.

**Entry.** Run branch at `e9e95b891b3ae642516e017c46b97a18a1480164` with the study and runbook receipted, no Hermes Gate 1 sealed, and the target commits of study section 3 reachable.

**Exit.** Repository copies of the study, runbook, design record and its selection reports live under docs/kickoff/1355/. The inventory maps all 137 registry addresses to the 17 study types, names each type's deployed state, anchor and coverage mode, and keeps the eight registry exclusions with owner and reason. The checker's check subcommand validates the inventory, digests and custody rules, and its conformance subcommand writes the profile-invariance design report, which passes for all 17 types under the default and deployed profiles before Step 2 opens. The decision draft records anchor coverage and the zero-loss exclusion rule. Prove the repository exit with:

```sh
python3 scripts/run_checks.py --base fiat/1355-fresh-seal-wildcat-v2-layouts-and-selectors --scope root --format json
```

**Files.** Create `docs/kickoff/1355/study.md`, `docs/kickoff/1355/runbook.md`, `docs/kickoff/1355/design-evidence.json`, `docs/kickoff/1355/design-reports/`, `docs/kickoff/1355/README.md`, `docs/kickoff/1355/inventory.json`, `docs/kickoff/1355/evidence/profile-invariance.json`, `scripts/kickoff_hermes_1355.py`, `tests/test_kickoff_hermes_1355.py` and `docs/decisions/drafts/cover-wildcat-v2-protected-types-by-anchor-baselines.md`. Update `tests/check-map-v1.json`, `.horos/census.json` and `.horos/boundary.json` only as their owners require.

**Tests.** Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-1.json`
Add checker cases for a missing, duplicate or unmapped address; a type without anchor or coverage mode; an unowned exclusion; a digest mismatch; a path escape or symlink; a target or private source file under the docs tree; and a profile-invariance record whose two profiles disagree. Expect at least 12 new tests, all run through the root suite.

**Disciplines.** phylax: the checker reads committed JSON and must bound reads, refuse symlinks and closed-schema violations, and run no subprocess. ephoros: every refusal names the record, field and digest that failed. metron: none, no performance claim. elenchus: each checker defect found in audit gets a focused test that fails without the fix. hypomnema: anchor coverage with zero-loss exclusion is expensive to reverse and gets its decision draft.

## Step 2: Capture fixed-block chain evidence and close the owner handoffs

**Goal.** Bind the inventory's code identities to a verified Lazarus fixture at block 26006289 and preserve the admitted inputs in a verified Alexandria release.

**Entry.** The receipted Step 1 head with the profile-invariance report passing, the inventory checker green and no Gate 1 sealed.

**Exit.** A Lazarus fixture on Ethereum chain 1 at block 26006289, hash 0x3d069f254a10d98ad19eff0f397cf28db3613fd98bff1df48c798920552f4ec5, carries account proofs and code for every inventoried address, declares its request, byte and time limits before capture, and passes Lazarus verify and offline replay. An Alexandria raw release preserves the registry, source-match and chain-observation inputs and the fixture by digest and passes Alexandria verify. Every inventory code hash matches the fixture, with recorded and proved values kept separate. The owner-handoff table names producer, reviewer, artefact and digest for scope, registry, source matching, fixture, release and inventory, and the owner-handoffs design report passes before Step 3 opens. Prove the repository exit with:

```sh
python3 scripts/run_checks.py --base fiat/1355-fresh-seal-wildcat-v2-layouts-and-selectors --scope root --format json
```

**Files.** Create `docs/kickoff/1355/evidence/fixture.json`, `docs/kickoff/1355/evidence/release.json` and `docs/kickoff/1355/evidence/owner-handoffs.json`; extend `scripts/kickoff_hermes_1355.py`, `tests/test_kickoff_hermes_1355.py` and `docs/kickoff/1355/README.md`. The complete fixture and release payloads are committed only where their owners' formats allow and are otherwise retained by digest under `.hexaemeron/restricted/`.

**Tests.** Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-2.json`
Add cases for a wrong chain, block or hash; an inventory code hash absent from or different to the fixture; a recorded value presented as proved; an unverified fixture or release; and an incomplete handoff row. Expect at least 6 new tests.

**Disciplines.** phylax: the capture takes an RPC credential through an environment variable only, and provider replies are hostile input bounded by Lazarus's declared limits. ephoros: the fixture and release records name request count, byte count, verification result and coverage totals. metron: none, capture limits are safety budgets, not performance claims. elenchus: a verification failure halts the step with its evidence preserved. hypomnema: the evidence-class boundary between recorded and proved values goes in the README.

## Step 3: Seal the V2 anchor and demonstrate both Gate 5 rejections

**Goal.** Seal Hermes Gate 1 on v2-protocol `c7be4039` and show that a selector change and a layout change each pass Gates 2 to 4 and exit 50 at Gate 5.

**Entry.** The receipted Step 2 head with the owner-handoffs report passing and the fixture and release verified.

**Exit.** One canonical Hermes baseline on a fresh checkout of v2-protocol c7be4039f8f383a9dda4e45f63331c17d63f9ed9 passes every v2 protected contract through repeated protected-contract operands, excludes only the zero-loss file, reaches baseline_ready, and records its command, environment, corpus digest, layouts and method maps. On separate disposable copies, a selector candidate and a layout candidate each pass Gates 2, 3 and 4 and exit 50 with a Gate 5 reason naming the intended contract; each record keeps its patch, rule, class, invocation, gate records, output and exit status, and the copy shows a clean status at the pinned commit afterwards. Layout candidates are tried in the study's order and every attempt is recorded; if none reaches Gate 5, the layout-rejection report fails, the step halts and the study is amended. The selector-rejection and layout-rejection design reports pass before Step 4 opens. Prove the repository exit with:

```sh
python3 scripts/run_checks.py --base fiat/1355-fresh-seal-wildcat-v2-layouts-and-selectors --scope root --format json
```

**Files.** Create `docs/kickoff/1355/baselines/v2-c7be/` holding the Hermes run's layouts, method maps, state and manifest without the baseline-sources copy, `docs/kickoff/1355/rejections/selector/` and `docs/kickoff/1355/rejections/layout/`; extend `scripts/kickoff_hermes_1355.py`, `tests/test_kickoff_hermes_1355.py` and `docs/kickoff/1355/README.md`.

**Tests.** Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-3.json`
Add cases for a baseline not at baseline_ready; a missing protected contract; a rejection that stopped before Gate 5 or exited other than 50; a Gate 5 reason naming the wrong contract; a candidate diff touching a test file or mixing classes; and an unrestored copy. Expect at least 6 new tests.

**Disciplines.** phylax: v2-protocol sets ffi=true, so suites run only in disposable checkouts at the reviewed commit with no credential in the environment. ephoros: each record names the gate reached, exit code, reason and restoration result. metron: none, Hermes owns every gas number and no other performance claim is made. elenchus: a candidate that fails before Gate 5 is kept as a failed attempt with its evidence, never retried in the same directory. hypomnema: the candidate order and any blocker go in the README.

## Step 4: Seal the remaining anchors and record every equivalence

**Goal.** Seal Hermes Gate 1 on the V1, fee recipient, role provider and collateral anchors, and record byte-equal equivalence for the eleven types that share an anchor snapshot.

**Entry.** The receipted Step 3 head with the selector-rejection and layout-rejection reports passing.

**Exit.** Four canonical Hermes baselines reach baseline_ready on fresh checkouts of wildcat-protocol 488b30d08c73a93be3e4bf99128c774997411d3a, fee-recipient-contract ac73bda3642c9a7c8de64e39856b31af53f06068, chainalysis-ofac-role-provider 5d7f8c889a8d29935838a3906172feb8d9861807 and collateral-contract 46dba596fa111f868200358f551796e8f73b5fd7, each with its study compiler pin, every protected contract of that tree and only its zero-loss exclusions. For each of the eleven equivalence types, the canonical layout and method map at the deployed state are byte-equal to the sealed anchor files, computed with Hermes's own canonicaliser. The private runs' public records carry layouts, method maps, counts and digests only. The sealed-coverage design report passes before Step 5 opens. Prove the repository exit with:

```sh
python3 scripts/run_checks.py --base fiat/1355-fresh-seal-wildcat-v2-layouts-and-selectors --scope root --format json
```

**Files.** Create `docs/kickoff/1355/baselines/v1-488b/`, `docs/kickoff/1355/baselines/fee-ac73/`, `docs/kickoff/1355/baselines/role-provider-5d7f/`, `docs/kickoff/1355/baselines/collateral-46db/` and `docs/kickoff/1355/equivalence/`; extend `scripts/kickoff_hermes_1355.py`, `tests/test_kickoff_hermes_1355.py` and `docs/kickoff/1355/README.md`. Complete private Hermes directories go under `.hexaemeron/restricted/`.

**Tests.** Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-4.json`
Add cases for an equivalence record whose layout or method map differs by one byte; a type pointing at an unsealed anchor; a compiler pin that differs between record and run; an excluded file that runs a passing test; and a private payload in the public tree. Expect at least 5 new tests.

**Disciplines.** phylax: two repositories are private and collateral-contract sets ffi=true, so private payloads stay restricted and suites run only in disposable checkouts. ephoros: the checker names which type, anchor and digest failed. metron: none, no performance claim. elenchus: an equivalence mismatch halts the step and is worked to its cause before any coverage claim. hypomnema: the restricted-custody rule for private runs goes in the README.

## Step 5: Reproduce and deliver the sealed evidence set

**Goal.** Reproduce every baseline and both rejections from the documented commands and deliver the complete, checked evidence set.

**Entry.** The receipted Step 4 head with the sealed-coverage report passing.

**Exit.** Re-running each recorded baseline command on a fresh checkout reproduces the committed layout and method-map digests for all five anchors, and re-running both Gate 5 candidates reproduces exit 50 with the same Gate 5 reasons. The README gives a reviewer the full reproduction path, including the compiler pins and restricted-custody steps. The checker's check subcommand passes on the delivered tree, and the evidence-custody design report is ready for integration. The demonstration names its controller and source commands and reports its positive and negative observations without claiming sufficiency. Prove the repository exit with:

```sh
python3 scripts/run_checks.py --base fiat/1355-fresh-seal-wildcat-v2-layouts-and-selectors --scope root --format json
```

**Files.** Create `docs/kickoff/1355/evidence/reproduction.json`; finish `docs/kickoff/1355/README.md`; extend `scripts/kickoff_hermes_1355.py` and `tests/test_kickoff_hermes_1355.py` for reproduction and custody checks.

**Tests.** Elenchus command: `python3 tests/run_tests.py --elenchus-report {report}`; format: `unittest-json-v1`; report file: `.hexaemeron/elenchus-step-5.json`
Add cases for a reproduction digest that differs from the sealed record, a rejection that no longer exits 50, and a custody record naming an absent restricted payload. Expect at least 3 new tests.

**Disciplines.** phylax: reproduction repeats the disposable-checkout and restricted-custody controls. ephoros: the reproduction record names each run, digest and verdict. metron: none, no performance claim. elenchus: a failed reproduction halts delivery with its evidence preserved. hypomnema: the README is the reviewer's starting point and records every command.

### Amendment -- 2026-09-23

**What changed.** Complete replacement Exit: Two canonical Hermes baselines reach baseline_ready on fresh checkouts, each passing every protected contract of its tree through repeated protected-contract operands, excluding only that tree's zero-loss file, with seed 0x5EED, and recording its command, environment, corpus digest, layouts and method maps. The first is v2-protocol c7be4039f8f383a9dda4e45f63331c17d63f9ed9 with its seven v2 protected contracts and the exclusion test/vault/Wildcat4626WrapperStandard.t.sol. The second is wildcat-protocol 488b30d08c73a93be3e4bf99128c774997411d3a under FOUNDRY_SOLC=0.8.22 with WildcatArchController, WildcatSanctionsSentinel and WildcatSanctionsEscrow protected and the exclusion test/market/WildcatMarketToken.t.sol. On separate disposable copies, a selector candidate against the c7be anchor and a layout candidate against the 488b anchor each pass Gates 2, 3 and 4 and exit 50 with a Gate 5 reason naming the intended contract, src/HooksFactory.sol:HooksFactory for the selector and src/WildcatSanctionsSentinel.sol:WildcatSanctionsSentinel for the layout; each record keeps its patch, rule, class, invocation, gate records, output and exit status, and each copy shows a clean status at its pinned commit afterwards. Every earlier layout attempt, including the three that stopped at Gate 3, stays recorded with its gate, exit and reason. The selector-rejection and layout-rejection design reports pass before Step 4 opens. Proved by `python3 scripts/run_checks.py --base fiat/1355-fresh-seal-wildcat-v2-layouts-and-selectors --scope root --format json` at exit zero on the committed tree.

Complete replacement Files: Create docs/kickoff/1355/baselines/v2-c7be/ and docs/kickoff/1355/baselines/v1-488b/, each holding its Hermes run's layouts, method maps, state and manifest without the baseline-sources copy, and docs/kickoff/1355/rejections/selector/ and docs/kickoff/1355/rejections/layout/; extend scripts/kickoff_hermes_1355.py, tests/test_kickoff_hermes_1355.py and docs/kickoff/1355/README.md; refresh docs/kickoff/1355/runbook.md to the canonical runbook bytes at this step's exit.

**Why.** The study scheduled the layout rejection on the v2 anchor and named the order of candidates to try. On v2-protocol c7be4039 all three attempts stopped at Gate 3 with exit 30: two STO-18 variants on Wildcat4626Wrapper grow initcode that the wrapper factory and constructor-revert tests deploy inside measured bodies, and an STO-01 pair on SimpleMarketCollateralMultiParty changed five invariant rows. No other split co-accessed field pair exists in a v2 protected type. The study's fallback, any co-accessed pair in a protected type, found one in the V1 anchor: STO-04 packing WildcatSanctionsSentinel's three-slot TmpEscrowParams into two words passed Gates 2 to 4 in a disposable rehearsal and exited 50 at Gate 5 with the layout reason, while its method identifiers stayed unchanged. The operator chose on 2026-09-23 to widen the search rather than halt. Gate 5 compares against the anchor's own sealed Gate 1, so the 488b baseline moves from Step 4 into this step.

**Steps touched.** Step 3's Exit and Files.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.

### Amendment -- 2026-09-23

**What changed.** Complete replacement Goal: Seal Hermes Gate 1 on the fee recipient, role provider and collateral anchors, and record byte-equal equivalence for the eleven types that share an anchor snapshot.

Complete replacement Exit: Three canonical Hermes baselines reach baseline_ready on fresh checkouts of fee-recipient-contract ac73bda3642c9a7c8de64e39856b31af53f06068, chainalysis-ofac-role-provider 5d7f8c889a8d29935838a3906172feb8d9861807 and collateral-contract 46dba596fa111f868200358f551796e8f73b5fd7, each with its study compiler pin, every protected contract of that tree and only its zero-loss exclusions. For each of the eleven equivalence types, the canonical layout and method map at the deployed state are byte-equal to the sealed anchor files, computed with Hermes's own canonicaliser; the V2 types compare with the c7be anchor and the V1 types with the 488b anchor, both sealed in Step 3. The private runs' public records carry layouts, method maps, counts and digests only. The sealed-coverage design report passes before Step 5 opens. Proved by `python3 scripts/run_checks.py --base fiat/1355-fresh-seal-wildcat-v2-layouts-and-selectors --scope root --format json` at exit zero on the committed tree.

Complete replacement Files: Create docs/kickoff/1355/baselines/fee-ac73/, docs/kickoff/1355/baselines/role-provider-5d7f/, docs/kickoff/1355/baselines/collateral-46db/ and docs/kickoff/1355/equivalence/; extend scripts/kickoff_hermes_1355.py, tests/test_kickoff_hermes_1355.py and docs/kickoff/1355/README.md. Complete private Hermes directories go under .hexaemeron/restricted/.

**Why.** The Step 3 amendment of the same date moved the wildcat-protocol 488b30d0 anchor into Step 3, because the layout rejection's Gate 5 compares against that anchor's own sealed Gate 1. Step 4 therefore seals the remaining three anchors and consumes both Step 3 anchors for equivalence. The eleven equivalence types, the private-custody rule and the sealed-coverage gate are unchanged.

**Steps touched.** Step 4's Goal, Exit and Files.

**Still holding.** Step 3: entry holds; exit holds. Step 4: entry holds; exit holds. Step 5: entry holds; exit holds.
