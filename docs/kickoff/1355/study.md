# Issue 1355 study: sealed Wildcat V2 layouts and selectors

Ready for runbook derivation. The design record selects `anchor-and-inspect`
by `unique-frontier`, and `design-lock` exits 0. No delivered Gate 1 exists
and no delivered Gate 5 rejection exists. The Hermes runs described below are
study-time rehearsals in disposable checkouts, kept under
`.hexaemeron/research/`; none of them is the sealed baseline.

Assuming, unless corrected:

1. The estate is registry row `wildcat-v2-ethereum-mainnet` in
   `docs/kickoff/1359/targets.json`: Ethereum chain 1, block `26006289`, hash
   `0x3d069f254a10d98ad19eff0f397cf28db3613fd98bff1df48c798920552f4ec5`,
   137 recorded contracts. The v2-protocol `plasma` branch is a source line
   for Ethereum deployments; the Plasma chain stays out of scope.
2. Each Gate 1 runs the repository's default Foundry profile. Where
   `foundry.toml` does not pin the deployed compiler, the run pins it through
   `FOUNDRY_SOLC` and `FOUNDRY_EVM_VERSION`, and `verify` later uses the same
   environment. Layout and method maps do not depend on optimiser or via-IR
   settings; criterion `profile-invariance` checks that before Step 2.
3. A deployed type whose source state has no Gate 1 of its own is covered
   when its canonical storage layout and method map are byte-equal to a type
   sealed at an anchor. This reading changes the selected design; the literal
   question is in section 4.
4. A test file may be excluded with `--no-match-path` only when Forge 1.7.1
   runs zero passing tests in it. No test source is edited.
5. Evidence lives under `docs/kickoff/1355/` in Skills. No target source is
   committed there, including Hermes's `baseline-sources/` copy; the source
   manifest and the pinned commit reproduce it.
6. For the two private repositories, the public tree carries layouts, method
   maps, counts and digests. Their complete Hermes directories stay in a
   restricted location outside Git, named by digest. The 2026-09-13 scope
   approval grants no redistribution.
7. An Ethereum RPC that serves `eth_getProof` and `eth_getCode` at block
   `26006289` is available for Step 2. Without one, Step 2 blocks.

## 1. Problem and proving path

Issue [1355](https://github.com/wildcat-finance/skills/issues/1355) asks for a
reviewable protected-contract inventory for the Wildcat V2 Ethereum estate,
a sealed Hermes Gate 1 whose layouts and selector maps cover every inventoried
type, and two separate candidates that pass Gates 2 to 4 and exit `50` at
Gate 5: one for a protected layout change, one for a selector change. The
reader is a Wildcat reviewer who must reproduce all three from pinned inputs.

The prototype works when these commands pass on the delivered tree:

1. `python3 scripts/kickoff_hermes_1355.py check` exits 0: every one of the
   137 registry addresses maps to one of 17 inventory types, each type points
   at a sealed Gate 1 snapshot or a byte-equal equivalence record, every
   exclusion names an owner and a reason, and every digest matches.
2. For each of the five Gate 1 runs, the committed `state.json` has status
   `baseline_ready`, and re-running the recorded `baseline` command on the
   pinned commit reproduces the same layout and method-map digests.
3. The selector and layout rejection records each show Gates 2, 3 and 4
   passed, exit `50`, a Gate 5 reason naming the intended contract, the diff,
   and a clean `git status` on the disposable copy afterwards.

## 2. Prior art and inherited work

**Registry.** `docs/kickoff/1359/targets.json` (SHA-256
`417f727d018ecbfa86efb23ea8c9cdfc53d429cf3f4a6285543ae24e89fc40ea`) holds the
estate: factory, 3 templates, 42 hooks instances, 80 markets, the one pull
role provider (31 borrower push providers are excluded), fee recipient, collateral factory with stored init code and lens,
two market lenses, the wrapper factory, and the shared V1 arch controller and
sanctions sentinel. Its `protected_set_exclusions` name eight items with
owner and reason; this study keeps all eight.

**Pull requests read.** The last two merged changes to the registry are
[#1751](https://github.com/wildcat-finance/skills/pull/1751) and
[#1750](https://github.com/wildcat-finance/skills/pull/1750); both concern the
V1 row. #1750 records that the V1 factory's exact deployer checkout cannot be
selected among five blob-identical commits and that the V1 sentinel's oracle
is already an excluded protected-set member; neither changes this estate's
members. The last two changes to the V2 row are
[#1735](https://github.com/wildcat-finance/skills/pull/1735) and
[#1736](https://github.com/wildcat-finance/skills/pull/1736). #1735 leaves the
collateral deployer checkout unestablished and keeps collateral instances
unenumerated; this study carries both as stated limits. #1736 reproduced the
fee recipient's 1649-byte runtime. The last two merged changes under
`plugins/hermes/` are
[#1833](https://github.com/wildcat-finance/skills/pull/1833) and
[#1638](https://github.com/wildcat-finance/skills/pull/1638). Both touch only
the plugin manifest or `PROMISE_MACHINE.md` copy; their `carryover` rows name
no Hermes item. [#1610](https://github.com/wildcat-finance/skills/pull/1610)
recorded an earlier Hermes acceptance on this estate's source, the CMP-10
emitter reference; this study does not reopen it.

**Audit history.** `python3.14
plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .` exited 0
over the whole set: 104 source and view pairs, every one `committed=match`.
The in-scope source is `audit/AUDIT.md`; its Hermes rule-corpus rounds were
read through `audit/AUDIT_SYNOPSIS.md`. Fixed findings `S3-R1-01`,
`S3-R1-02`, `S3-R1-03`, `S5-R1-01`, `S5-R1-02` and `S5-R1-03` stay closed.
`Covered`, `Not checked` and `Elenchus verdict` are
`[missing legacy field: ...]` in every Hermes round and remain unknown.
Leads not pursued, carried by name: the class-vocabulary gap is Hermes's held
frontier and out of scope; the transcription-extractor lead is closed for
transcribed fields; the 20-character obligation-answer minimum stays as
recorded; the Horos `files_walked` guard lead belongs to Horos. Five files
under `audit/rounds/` mention Hermes, each only as a suite name or test
count, so none is a Hermes source.

Lazarus and Alexandria are used for Step 2, so their per-run records were
read through verified synopses: `fiat-383`, `fiat-1360` (Lazarus) and
`fiat-1350`, `fiat-1731`, `fiat-1364` (Alexandria). Two findings stay open in
`fiat-383`: `S1-R1-01` (high, receipt-witness transaction hashes) and
`S2-R1-03` (medium, replay omits `eth_getBlockReceipts`). Step 2 uses only
`eth_getProof` and `eth_getCode`, so neither applies; both are carried by
name. The root synopsis has two finding rows on Lazarus or Alexandria paths,
both fixed. The root synopsis's untitled step sections were not read one by
one.

**The earlier run.** An earlier run of this issue lost its controller state.
Its output survives on branch
`fiat/1355-seal-wildcat-v2-protected-layouts-and-selec-step-1-scaffold-evidence-and-prepare-si`
at `430010f70282a31f227ed72e62cf1de385ad76aa` (PR
[#1856](https://github.com/wildcat-finance/skills/pull/1856), open). Its
round record raised `S1-R1-01` (high, fixed on that branch): prepared-harness
conformance accepted regression files by digest alone. It is treated here as
unverified prior art. This study departs from it in four places, each
re-derived from measurements in sections 3 and 4:

1. It ran suites under the `ir` profile and found two V2 failures. Under the
   default profile, v2-protocol `a70f297f` passes 723 of 723, so no V2
   timestamp repair exists in this design.
2. It sealed nine source groups, four of them only after test-only harness
   commits. This design seals five upstream commits and edits no test.
3. It mapped `OpenAccessRoleProvider` to the private repository. The public
   v2-protocol file `src/OpenAccessRoleProvider.sol` at `5838b2f3` and
   `e1f77540` has SHA-256
   `7a5b57852f433b876f0b43048c74158a740ce0f2708587b31eb682a7c390f84f`,
   equal to the Sourcify full-match source. The private blob differs.
4. It left Gate 5 feasibility to its fourth step. Here the selector
   rejection was rehearsed during the study, and the layout rejection is
   scheduled in the first Gate 1 step so that an infeasible candidate stops
   the run before more baselines are sealed.

It also used `wildcat-protocol` pins `da74452a` and `6164ddd4`, both red. The
upstream commit `488b30d08c73a93be3e4bf99128c774997411d3a` on `main` keeps
every `src/` blob of `6164ddd4` and carries the upstream escrow-test fix, so
it replaces both as the V1 anchor.

## 3. Constraints and source states

Skills starts at `main` `e9e95b891b3ae642516e017c46b97a18a1480164`. Python is
3.14.6. Forge is 1.7.1, commit `4072e48705af9d93e3c0f6e29e93b5e9a40caed8`.
Hermes is skill `0.1.1` (plugin `0.1.2`); `hermes.py` SHA-256
`36e80da4405645486e4f34caf6fa59ed795d864c685e04a9b37a959bc43c1805`; rule
corpus SHA-256
`5d1773f9a5f51e957bd769deb3b030b670fa10499e33fce4a8df3a2e221bd5ac`.
Fuzz seed `0x5EED` throughout.

Suite results below come from fresh clones at each commit, with submodules
at their recorded gitlinks, run by `.hexaemeron/design/resolve_1355.py` with
the listed compiler pins.

| Tree | Commit | Compiler pin | Unexcluded result | Role in this design |
| --- | --- | --- | --- | --- |
| v2 `a70f` | `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657` | `foundry.toml` 0.8.25, cancun | 723 pass, 0 fail | deployed state of 5 types; equivalence only |
| v2 `c7be` | `c7be4039f8f383a9dda4e45f63331c17d63f9ed9` | `foundry.toml` 0.8.25, cancun | 795 pass, 2 fail | **anchor**; excludes `test/vault/Wildcat4626WrapperStandard.t.sol` |
| v2 `5838` | `5838b2f3f5c0bb3489cd2ff16bb31ddd5194c7fa` | `foundry.toml` 0.8.25, cancun | 682 pass, 13 fail | deployed state of the 730-day hooks; equivalence only |
| v2 `e1f7` | `e1f77540fef65736374de6c847743d8ca2233fb4` | `foundry.toml` 0.8.25, cancun | 683 pass, 12 fail | deployed state of the app lens and role provider; equivalence only |
| V1 `da74` | `da74452aa7d1a0f024d99efd22cc6d950a8116b7` | `FOUNDRY_SOLC=0.8.22` | 338 pass, 7 fail | deployed state of the arch controller; equivalence only |
| V1 `6164` | `6164ddd4c75ef6da2181e5623b99795b9829e31c` | `FOUNDRY_SOLC=0.8.22` | 347 pass, 7 fail | deployed state of sentinel and escrow; equivalence only |
| V1 `488b` | `488b30d08c73a93be3e4bf99128c774997411d3a` | `FOUNDRY_SOLC=0.8.22` | 348 pass, 6 fail | **anchor**; excludes `test/market/WildcatMarketToken.t.sol` |
| fee `ac73` (private) | `ac73bda3642c9a7c8de64e39856b31af53f06068` | `FOUNDRY_SOLC=0.8.25`, cancun | 19 pass, 0 fail | **anchor** |
| role provider `5d7f` (private) | `5d7f8c889a8d29935838a3906172feb8d9861807` | `FOUNDRY_SOLC=0.8.25`, cancun | 5 pass, 0 fail | **anchor** for the role provider type |
| collateral `46db` | `46dba596fa111f868200358f551796e8f73b5fd7` | `FOUNDRY_SOLC=0.8.28`, cancun | 48 pass, 0 fail | **anchor** |

Every failure in the two excluded files is Forge's removed `testFail*`
convention: 2 inherited from `erc4626-tests` at `c7be`, 6 in
`WildcatMarketToken.t.sol` at `488b`. Each file runs zero passing tests, so
excluding it drops none. With those exclusions both anchors pass: 795 of 795
and 348 of 348. The non-anchor trees stay red after the same rule: at `5838`
and `e1f7`, six `testFail*` cases sit in
`test/market/FixedTermEquivalenceTests.t.sol` beside 141 passing tests; `5838`
also keeps the stale 366-day fixed-term input; `da74` and `6164` keep the
escrow fuzz oracle that `488b` fixes upstream.

The `c7be` `src/` tree adds `src/vault/` to `a70f` and changes no other
`src/` blob. `6164` differs from `da74` only in the SPDX line of 39 files.
`e1f7` and `5838` have identical `src/` trees. v2-protocol and
collateral-contract set `ffi=true`.

**Non-goals.** No gas candidate is promoted, merged or deployed. No test
source, production source, configuration, compiler setting or submodule pin is
changed in any Gate 1 tree. Hermes itself is not changed. Collateral, escrow
and wrapper instances are not enumerated; their types are protected. Whole-
target safety and the value of any later gas saving are not claimed.

**Always.** The root suite, `python3 scripts/run_checks.py`, and the
Imprimatur and Brevitas lints on every shipped document. Fresh disposable
checkouts for each Hermes run. **Ask first.** Adding a second Forge build.
Writing to a target repository. Publishing any private-repository payload.
Widening the protected set's exclusions. **Never.** Commit target source or an
RPC credential. Edit a test to make a suite green. Call a rehearsal a sealed
baseline. Merge a Gate 5 candidate.

## 4. Design options and checked selection

Seventeen protected types cover the 137 addresses (section 7). The question
is how many Hermes Gate 1 runs are needed and how the other deployed states
are covered.

`every-deployed-state` seals a Gate 1 at each of the eight deployed trees.
Every type is covered natively. The trade: four of the eight trees are red
after the zero-loss exclusion rule, so each needs a signed test-only harness
commit, which is what the earlier run built.

`anchor-and-inspect` seals a Gate 1 at five green upstream commits and
covers the other deployed states by comparing each type's canonical layout
and method map with the anchor's, byte for byte, using Hermes's own
canonicaliser. The trade: 11 of 17 types are covered by equivalence rather
than by a native Gate 1, so a later gas candidate made in a non-anchor tree
needs a new Gate 1 there first.

`legacy-forge-every-state` seals all eight deployed trees under a second,
pre-1.0 Forge that still executes `testFail*`. The trade: a second toolchain
download, and three trees still need a harness commit for real assertion
failures.

The record `.hexaemeron/design-evidence.json` carries 12 criteria over all
five concerns. Selection results, each from a zero-exit report written by the
resolver:

| Criterion | Concern | `every-deployed-state` | `anchor-and-inspect` | `legacy-forge-every-state` |
| --- | --- | --- | --- | --- |
| `protected-coverage` (gate, at least 1) | correctness | 1.0 | 1.0 | 1.0 |
| `executable-tests-dropped` (gate, at most 0) | correctness | 0 | 0 | 0 |
| `gate1-runs` (minimise) | time | 8 | 5 | 8 |
| `source-snapshot-bytes` (minimise) | space | 5,886,010 | 1,971,599 | 5,886,010 |
| `forge-builds` (minimise) | compatibility | 1 | 1 | 2 |
| `authored-harness-trees` (minimise) | recovery | 4 | 0 | 3 |

`anchor-and-inspect` is no worse on every metric and better on three, so it
is the unique frontier. The six conformance gates are pending with exact
resolvers: `profile-invariance` before Step 2, `owner-handoffs` before Step 3,
`selector-rejection` and `layout-rejection` before Step 4, `sealed-coverage`
before Step 5, and `evidence-custody` at integration. The resolver they name,
`scripts/kickoff_hermes_1355.py`, does not exist yet; Step 1 builds it.

**Rehearsals.** A Hermes `baseline` on the `c7be` anchor with seven
protected contracts reached `baseline_ready` in 27 s wall and wrote 2.1 MB,
most of it the source copy. On that rehearsal, a `verify` removing the
unbounded `getMarketsForHooksInstance(address)` overload from `HooksFactory`
and `IHooksFactory` under rule `MEM-16` (class `calldata-memory`) passed
Gates 2, 3 and 4 with no deterministic regression and a 22-gas saving on
`WildcatMarketTest:test_transfer_NotApprovedLender()`, then exited `50`:
`public method identifiers changed: src/HooksFactory.sol:HooksFactory`, diff
removing selector `4bd1acf3`. So the selector rejection is reachable. A layout
probe moving `fullLiquidationIndex` beside `totalShares` in
`SimpleMarketCollateralMultiParty` under `STO-01` saved gas in 15 tests but
regressed two by 19,892 and 15,912 gas, most likely because the shared slot
no longer clears on full liquidation and the refund is lost; Gate 3 would
reject it. That probe compared snapshots only and did not run `verify`.
The layout rejection is therefore not yet shown to be reachable. Step 3 tries
candidates in this order and records each attempt: `STO-18` on
`Wildcat4626Wrapper`'s constructor-only `_name` and `_symbol` with a retained
fallback; then any co-accessed field pair in a protected type. If none passes
Gates 2 to 4, `layout-rejection` fails before Step 4 and the run stops for an
amended study, which is the issue's "record the exact blocker" route.

**Question.** May a protected type whose deployed source differs from its
anchor only in bytes that leave the canonical storage layout and method map
byte-equal (a constant value, a view's return struct, a mutability keyword or
an SPDX line) share the anchor's Gate 1 snapshot? This study proceeds on yes.
If the answer is no, `every-deployed-state` is the only candidate that meets a
native-coverage gate, and the study must be amended before the runbook.

## 5. Risk register

```risk-register
equivalence-overreach | a deployed type covered through its anchor's snapshot | canonical layout and method map are byte-equal to the sealed anchor files, not to a study-time inspect
exclusion-loss | --no-match-path on an anchor | the excluded file runs zero passing tests on the pinned Forge and the run's pass count equals the unexcluded pass count
compiler-pin-drift | env-pinned solc and EVM version | baseline and verify record the same FOUNDRY_SOLC and FOUNDRY_EVM_VERSION and the same forge config digest
profile-assumption | default profile versus deployed build profile | profile-invariance compares maps under both profiles for all 17 types
protected-set-gap | factory, templates, CREATE and CREATE2 children, lenses and role provider | all 137 addresses map to a type; escrow, wrapper and collateral child types are inventoried; eight exclusions keep owner and reason
role-provider-source | public plasma-line copy versus private repository blob | the deployed copy digest equals the Sourcify source and its maps equal the private anchor's
chain-evidence-class | recorded registry reads versus Lazarus proofs | each inventory code hash is checked against a verified fixture, and recorded and proved values stay separate
wrong-gate-negative | the two Gate 5 demonstrations | Gates 2 to 4 passed, exit 50, and the Gate 5 reason names the intended contract and change
candidate-class-mixing | the demonstration diffs | every hunk belongs to the named rule's class and no test file changes
source-restoration | disposable demonstration copies | git status is clean and HEAD is the pinned commit after each run
private-payload | public docs tree | no private source, test source or complete private Hermes directory is committed
vendored-source | Hermes baseline-sources copies | no target source file appears under docs/kickoff/1355
ffi-execution | target suites with ffi enabled | runs use disposable checkouts at reviewed commits with no credential in the environment
partial-evidence | multi-run evidence set | the checker refuses a missing run, digest mismatch or unsealed directory
```

## 6. Glossary

- **Anchor.** An upstream commit whose own suite is green under this design's
  rules and on which one Gate 1 is sealed.
- **Deployed state.** The commit whose source the registry matches to
  deployed bytecode for a type.
- **Equivalence record.** The canonical layout and method map of a type at its
  deployed state, with digests equal to the anchor's sealed files.
- **Protected type.** One qualified `path:Contract` in the inventory; every
  instance created from it shares its snapshot.
- **Zero-loss exclusion.** A `--no-match-path` file in which the pinned Forge
  runs zero passing tests.
- **Rehearsal.** A study-time Hermes run on a disposable checkout; never
  delivery evidence.

## 7. Sources, inventory and owner handoffs

Registry, source-match and chain records are pinned at
[the starting tree](https://github.com/wildcat-finance/skills/tree/e9e95b891b3ae642516e017c46b97a18a1480164).
Target sources are the commits in section 3 in
[v2-protocol](https://github.com/wildcat-finance/v2-protocol),
[wildcat-protocol](https://github.com/wildcat-finance/wildcat-protocol),
[collateral-contract](https://github.com/wildcat-finance/collateral-contract)
and two private repositories, `wildcat-finance/fee-recipient-contract` and
`wildcat-finance/chainalysis-ofac-role-provider`. The Hermes contract is
[`SKILL.md` at the base](https://github.com/wildcat-finance/skills/blob/e9e95b891b3ae642516e017c46b97a18a1480164/plugins/hermes/skills/hermes/SKILL.md),
SHA-256 `90ee8281ba7bc8c7cbb77e13cfb9308275b3a351251184dd8dce7d140163348e`.
Study-time logs, reports and rehearsal outputs are under
`.hexaemeron/research/` and `.hexaemeron/design-reports/`.

**Inventory.** Anchors: `c7be` for v2 types, `488b` for V1 types, and the
repository's own commit for the rest.

| Type | Qualified contract | Deployed state | Coverage | Addresses |
| --- | --- | --- | --- | --- |
| hooks-factory | `src/HooksFactory.sol:HooksFactory` | v2 `a70f` | equivalent to `c7be` | 1 |
| wildcat-market | `src/market/WildcatMarket.sol:WildcatMarket` | v2 `a70f` | equivalent to `c7be` | 80 markets and 1 init-code store |
| open-term-hooks | `src/access/OpenTermHooks.sol:OpenTermHooks` | v2 `a70f` | equivalent to `c7be` | 1 template, 28 instances |
| fixed-term-hooks-365 | `src/access/FixedTermHooks.sol:FixedTermHooks` | v2 `a70f` | equivalent to `c7be` | 1 template, 3 instances |
| fixed-term-hooks-730 | `src/access/FixedTermHooks.sol:FixedTermHooks` | v2 `5838` | equivalent to `c7be` | 1 template, 11 instances |
| market-lens-core | `src/lens/MarketLens.sol:MarketLens` | v2 `a70f` | equivalent to `c7be` | 1 |
| market-lens-app | `src/lens/MarketLens.sol:MarketLens` | v2 `e1f7` | equivalent to `c7be` | 1 |
| wrapper-factory | `src/vault/Wildcat4626WrapperFactory.sol:Wildcat4626WrapperFactory` | v2 `c7be` | native | 1 |
| wrapper | `src/vault/Wildcat4626Wrapper.sol:Wildcat4626Wrapper` | v2 `c7be` | native | created by the wrapper factory; not enumerated |
| open-access-role-provider | `src/OpenAccessRoleProvider.sol:OpenAccessRoleProvider` | v2 `e1f7` | equivalent to private `5d7f` | 1, used by 37 hooks instances |
| arch-controller | `src/WildcatArchController.sol:WildcatArchController` | V1 `da74` | equivalent to `488b` | 1 |
| sanctions-sentinel | `src/WildcatSanctionsSentinel.sol:WildcatSanctionsSentinel` | V1 `6164` | equivalent to `488b` | 1 |
| sanctions-escrow | `src/WildcatSanctionsEscrow.sol:WildcatSanctionsEscrow` | V1 `6164` | equivalent to `488b` | created by the sentinel; not enumerated |
| fee-recipient | `src/WildcatFeeRecipient.sol:WildcatFeeRecipient` | private `ac73` | native | 1 |
| collateral-factory | `src/WildcatMarketCollateralFactory.sol:WildcatMarketCollateralFactory` | `46db` | native | 1 |
| collateral-multi-party | `src/SimpleMarketCollateralMultiParty.sol:SimpleMarketCollateralMultiParty` | `46db` | native | 1 init-code store; instances not enumerated |
| collateral-lens | `src/lens/CollateralLens.sol:CollateralLens` | `46db` | native | 1 |

The rows sum to the registry's 137 addresses. Libraries, interfaces and
inherited bases carry no storage or selector set of their own at a deployed
address; inherited storage is covered through each concrete type's layout.
The eight registry exclusions stand unchanged.

**Owner handoffs.**

| Handoff | Producer; reviewer | Artefact and SHA-256 | Status |
| --- | --- | --- | --- |
| Estate scope | Dave Coleman, target maintainer; recorded by kethcode | `docs/kickoff/1359/evidence/scope-approval.json`, `df147d44ba5cfbff58df62c91afc6937358701773ca760f84ff32ce7dcf73450` | complete; no capture budget or redistribution granted |
| Deployment-to-source registry | Dave Coleman with Surveyor under Protasis; PR #1583 review | `docs/kickoff/1359/targets.json`, `417f727d018ecbfa86efb23ea8c9cdfc53d429cf3f4a6285543ae24e89fc40ea` | complete as recorded evidence; this study corrects the role provider's source |
| Source matching | Surveyor; PR #1735 and #1736 review | `docs/kickoff/1359/evidence/source-match-1590.json`, `0bd8d53d351e46082dbb625a499bc7c6cebe1f1f43ab4c9ef2498f23fb79282e` | complete as recorded evidence |
| Chain observations | registry producer; target maintainer | `docs/kickoff/1359/evidence/ethereum-mainnet-1590.json`, `b7ce1e66f343a480ac64f8b6259e108638dc1fe473607b77f728980846d6ca70` | recorded responses, not proofs |
| Fixed-block fixture | Lazarus; Warden | none yet | blocked until Step 2 `lazarus.py verify` passes |
| Preserved release | Alexandria; Warden | none yet | blocked until Step 2 `alexandria.py verify` passes |
| Protected inventory, baselines, rejections | Hermes with this mapping; Warden and target maintainer | none yet | pending the conformance gates |
| Audit and delivery | Warden reviews; Fiat receipts | none yet | not started |

## 8. Signals and the questions behind them

[Ephoros](https://github.com/wildcat-finance/skills/blob/e9e95b891b3ae642516e017c46b97a18a1480164/plugins/hexaemeron/skills/ephoros/SKILL.md)
owns signals. Nothing here runs unattended, so no alert is deployed. A
reviewer re-running the evidence must be able to answer: which run or
equivalence record failed; which Hermes gate and exit code; which digest
moved; whether a disposable copy was restored. The checker's output names
those four fields per record, and each Hermes directory's `state.json` and
`result.json` answer the gate question.

## 9. Trust boundaries

[Phylax](https://github.com/wildcat-finance/skills/blob/e9e95b891b3ae642516e017c46b97a18a1480164/plugins/hexaemeron/skills/phylax/SKILL.md)
owns the controls. Four boundaries open:

1. Target test suites run with `ffi=true` in v2-protocol and
   collateral-contract, so test code can execute commands. Control: reviewed
   pinned commits, disposable checkouts, no credential in the environment.
2. The Lazarus capture takes an RPC credential. Control: an environment
   variable only; Lazarus keeps it out of output and digests.
3. Private repository payloads. Control: assumption 6; the checker refuses a
   private source or test file under `docs/kickoff/1355/`.
4. The checker reads committed JSON. Control: bounded reads, no-follow paths,
   closed schemas, no subprocess.

## 10. Budget

[Metron](https://github.com/wildcat-finance/skills/blob/e9e95b891b3ae642516e017c46b97a18a1480164/plugins/hexaemeron/skills/metron/SKILL.md)
owns non-gas budgets. No performance claim is made, so none applies. Observed
only: the resolver took 2 min 39 s wall for 12 suite runs and 52 inspect calls;
the `c7be` rehearsal Gate 1 took 27 s. Lazarus limits for requests, bytes
and time are declared in the Step 2 plan before capture. Hermes owns every
gas number.

## 11. Fail-closed posture

[Elenchus](https://github.com/wildcat-finance/skills/blob/e9e95b891b3ae642516e017c46b97a18a1480164/plugins/hexaemeron/skills/elenchus/SKILL.md)
owns triage and guards. A red anchor suite, an equivalence mismatch, a
failed fixture verification, or a demonstration that stops before Gate 5
halts the dependent transition. Failed Hermes directories are kept and a
retry uses a new directory. Each checker defect found in audit gets a focused
unittest under `tests/test_kickoff_hermes_1355.py` that fails without the
fix, run through the root suite command named in the runbook.

## 12. Decisions and their homes

[Hypomnema](https://github.com/wildcat-finance/skills/blob/e9e95b891b3ae642516e017c46b97a18a1480164/plugins/hexaemeron/skills/hypomnema/SKILL.md)
owns decision records. One decision is expensive to reverse: coverage by
anchor Gate 1 plus byte-equal equivalence, with the zero-loss exclusion rule.
Its record goes in
`docs/decisions/drafts/cover-wildcat-v2-protected-types-by-anchor-baselines.md`,
numberless until merge. The inventory and its exclusions live in
`docs/kickoff/1355/inventory.json`; reproduction commands and custody in
`docs/kickoff/1355/README.md`. The role-provider source correction belongs
to the registry's owner and is carried forward rather than edited here.
