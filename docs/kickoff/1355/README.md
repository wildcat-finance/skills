# Issue 1355: Wildcat V2 protected inventory

This directory holds the protected-contract inventory for the Wildcat V2
Ethereum estate and the evidence behind it. Step 1 of the delivery adds the
inventory, the checker and the profile-invariance evidence. Step 2 adds the
fixed-block fixture, the preserved release and the owner-handoff table. Step 3
seals Hermes Gate 1 on the v2-protocol and wildcat-protocol anchors and
records the selector rejection and every layout attempt; see
[Gate 5 rejections](#gate-5-rejections). The other three anchors are sealed in
a later step.

## Check it

```sh
python3 scripts/kickoff_hermes_1355.py check
```

The command reads committed files only and starts no subprocess. It exits 0
when all of the following hold:

1. `inventory.json` maps each of the 137 contracts in registry row
   `wildcat-v2-ethereum-mainnet` of `docs/kickoff/1359/targets.json`
   (SHA-256 `417f727d018ecbfa86efb23ea8c9cdfc53d429cf3f4a6285543ae24e89fc40ea`)
   to one of 17 protected types. Each type's registry role, template or lens
   source must match.
2. Each type names its deployed state, anchor, coverage mode and deployed
   compiler profile. The profile must agree with every Sourcify or registry
   record of those settings.
3. The eight registry exclusions are kept unchanged, each with owner and
   reason.
4. `study.md`, `runbook.md` and `design-evidence.json` are byte-identical to
   the receipted run files, and every selection report under `design-reports/`
   matches the digest the design record names.
5. `evidence/profile-invariance.json` records every type's canonical storage
   layout and method map under both profiles, and the two are byte-equal.
6. Nothing under this directory is a symlink, a Solidity source (including
   one carried inside a JSON string or pasted into Markdown as escaped JSON),
   a Hermes `baseline-sources` copy or a private-repository build input.
7. `evidence/fixture.json` names chain 1, block 26006289 and its hash, the
   four capture limits, a passing Lazarus verify and replay, and one row per
   inventory address whose proved code hash equals the inventory's.
8. `evidence/release.json` names a passing Alexandria verify and preserves
   the registry, source-match and chain-observation files and the fixture by
   digest. The checker hashes each named file itself.
9. `evidence/owner-handoffs.json` has one row for each of scope, registry,
   source matching, chain observations, fixture, release and inventory. Each
   row names its producer, reviewer and artefact, and the artefact's SHA-256
   matches its bytes. Every row is `complete` except the inventory's, whose
   status is `target-maintainer-review-outstanding`: no target-maintainer
   review of the mapping is recorded, and that review is carried forward to
   the run pull request. No other row may take that status.
10. `baselines/v2-c7be/` and `baselines/v1-488b/` each hold a Hermes Gate 1
    at `baseline_ready` over every protected type anchored at that tree, as
    described in [Anchor baselines](#anchor-baselines).
11. `rejections/selector/record.json` and `rejections/layout/record.json`
    record every attempt with its patch, gates, exit and restoration, as
    described in [Gate 5 rejections](#gate-5-rejections).

Each refusal prints the record, the field and the digest that failed.

## Profile invariance

Hermes Gate 1 runs each anchor under its default Foundry profile with the
study's compiler pins. The deployed contracts were built with other optimiser
and via-IR settings. The `profile-invariance` criterion checks that those
settings do not move a storage layout or method map.

For every type, the evidence inspects the contract at its deployed state and,
where different, at its anchor: 28 comparisons over 22 builds in 10 trees.
Each comparison runs `forge inspect <identifier> storageLayout --json` and
`forge inspect <identifier> methodIdentifiers --json` twice. The first run
uses the tree's Gate 1 pins; the second adds `FOUNDRY_SOLC`,
`FOUNDRY_EVM_VERSION`, `FOUNDRY_OPTIMIZER=true`, `FOUNDRY_OPTIMIZER_RUNS` and
`FOUNDRY_VIA_IR` for the deployed profile. Layouts pass through Hermes's
`canonical_storage_layout`. The record keeps the canonical maps themselves,
the `forge config --json` settings each build resolved and the compiler
settings each artefact reports. The checker recomputes every map digest from
the recorded content rather than trusting the stated digest.

The design report is written by:

```sh
python3 scripts/kickoff_hermes_1355.py conformance --criterion profile-invariance \
  --candidate anchor-and-inspect \
  --report .hexaemeron/design-reports/anchor-and-inspect-profile-invariance.json
```

It writes one `protasis-design-report/v1` with value `true` only when every
comparison is byte-equal, refuses an existing report path, and writes nothing
otherwise. `sealed-coverage` and `evidence-custody` refuse by name until the
step that owns their evidence lands.

To reproduce a comparison, check out the tree at its recorded commit with
submodules, then run the two `forge inspect` commands with each build's
recorded `environment` and a separate `FOUNDRY_OUT` and `FOUNDRY_CACHE_PATH`.
The captures used Forge 1.7.1, commit
`4072e48705af9d93e3c0f6e29e93b5e9a40caed8`. The capture script is kept with
the run's files; its SHA-256 is in the record.

## Chain evidence

The Lazarus fixture holds, at block 26006289, an EIP-1186 account proof and
the runtime code for each of the 137 inventory addresses, plus one recorded
`eth_getCode` per address so that replay can serve it. The plan declared its
limits before capture: 600 requests, 33,554,432 bytes per component,
67,108,864 bytes in total and 1,800 seconds. The capture script reported 414
requests, 12,106,815 response bytes and 51.4 seconds. Those counts, the
capture time and the attempt list in `evidence/fixture.json` are recorded, and
nothing retained recomputes them. The limits bind because the plan that
carries them is a fixture component and Lazarus enforces them during capture.
The capture called `capture_fixture`, the function behind `lazarus.py
capture`, from a script that reads the RPC URL and bearer from environment
variables, because the command-line form puts the URL in argv.

`lazarus.py verify` reports 137 proof-backed accounts, one header-bound header
and 137 recorded responses. Offline replay served all 137 code reads
byte-equal to the proof records and answered a request for another block with
miss `-32070`.

The two open `fiat-383` findings, `S1-R1-01` and `S2-R1-03`, concern
receipts. This fixture carries no receipt witness and no receipt request, so
neither applies.

The Alexandria release preserves the registry, source-match and
chain-observation files and the five fixture files by digest. Its
`proof-backed-state` capture earns that class only because `alexandria.py
verify` reruns Lazarus over the fixture.

Neither payload fits the committed tree: custody allows only `.md` and
`.json` here. Both stay in the run worktree's ignored `.hexaemeron/restricted/`
directory. The committed records name them by digest.

The `owner-handoffs` design report is written by:

```sh
python3 scripts/kickoff_hermes_1355.py conformance --criterion owner-handoffs \
  --candidate anchor-and-inspect \
  --report .hexaemeron/design-reports/anchor-and-inspect-owner-handoffs.json
```

It runs `check`, then re-verifies both retained payloads in-process with
Lazarus's and Alexandria's own verifiers. From those bytes it recomputes every
fixture row, component digest, plan limit and replayable response. It writes
value `true` only when all of them match the committed records and every
owner handoff is handed on. That `true` does not say the target maintainer
reviewed the inventory; the inventory row's status says that review is
outstanding.

## Evidence classes and custody

Two classes stay apart. A recorded value is what someone wrote down: the
registry's `code_keccak256` and the chain observations' code hash and length
come from provider responses and prove nothing. A proved value comes from the
fixture's proof records, where Lazarus checked the account against the
header's state root and hashed the captured code against the proved
`codeHash`. Each `fixture.json` row keeps both recorded values and the proved
value in separately labelled fields, and the checker refuses a recorded value
labelled `proof-backed` or a proved value from any other source.

Replayed `eth_getCode` responses are recorded evidence. The owner-handoffs
check compares their bytes with the proved code. The capture's request, byte
and time counts are recorded too. The header is self-consistent and matches
the registry's recorded hash, which does not establish that it belongs to the
canonical chain.

Maps for the fee recipient and role provider come from private repositories.
The public tree carries their layouts, method maps and digests only. Private
source, test source and complete private Hermes directories stay outside Git.

The role provider's registry source commit names the private blob. This
inventory records the public v2-protocol copy at `e1f77540` as its deployed
state, per study section 2. The override names the Sourcify source SHA-256,
and the checker requires it to equal the digest that
`docs/kickoff/1359/evidence/source-match-1590.json` records for the role
provider's address, with that file matching the registry's evidence digest.
The registry itself is unchanged; that correction belongs to its owner.

## Anchor baselines

- `v2-c7be`: v2-protocol `c7be4039f8f383a9dda4e45f63331c17d63f9ed9`, 7
  protected contracts, excluding `test/vault/Wildcat4626WrapperStandard.t.sol`.
  `foundry.toml` pins solc 0.8.25 and cancun. 795 tests passed.
- `v1-488b`: wildcat-protocol `488b30d08c73a93be3e4bf99128c774997411d3a`, 3
  protected contracts, excluding `test/market/WildcatMarketToken.t.sol`.
  `FOUNDRY_SOLC=0.8.22`; `foundry.toml` sets shanghai. 348 tests passed.

Each `baselines/<tree>/run/` holds the Hermes files of one Gate 1 on a fresh
clone at the pinned commit, with submodules at their recorded gitlinks. The
files are `state.json`, `result.json`, the source manifest, the Foundry
config, and the canonical and raw storage layout and method map for each
protected contract. The `baseline-sources/` copy and the logs are not
committed. `baselines/<tree>/record.json` names the checkout, the argv, the
environment, the Hermes and corpus digests, and the pass count. It also
carries the forge version, the git status and the gas snapshot as text.

Each run passed one `--protected-contract` operand per protected type anchored
at the tree, excluded only the tree's zero-loss file, and used seed `0x5EED`.
Hermes ran under `env -i` with only `HOME`, `PATH`, `NO_COLOR`, `LANG` and the
tree's compiler pin set, because v2-protocol sets `ffi=true`. Copies and run
directories sat under `/private/tmp/fiat1355-hermes/`, the path Hermes
records in `state.json`.

`check` recomputes every file digest under `run/` and every entry of Hermes's
`artifact_hashes`: the three text artefacts from the record, the corpus copy
from the repository corpus, and the rest from the committed files. It
recomputes each canonical layout from its raw inspector output through
Hermes's own `canonical_storage_layout`. It checks the commit, the protected
set, the exclusion, the seed, the compiler, the argv, the environment, the
status and the Gate 1 commands against the inventory and study. The pass
count and the submodule list are recorded only.

## Gate 5 rejections

Each attempt ran on its own fresh clone. On that clone, Hermes sealed its own
Gate 1 with the tree's protected set, then the candidate patch was applied and
`verify` was run. Afterwards `git apply -R` and removal of Hermes's
`.gas-snapshot` left `git status` clean at the pinned commit. Each attempt
record keeps the patch and its digest and Hermes's `candidate.solidity.diff`.
It also keeps the rule, class, both argv lists, the environment, both exit
codes, the gate reached and its reason, the last lines of output with the
stdout digest, the status before and after restoration, and the committed
`state.json` and `result.json`. A candidate that stopped before Gate 5 keeps
its directory and was never retried there.

For every attempt, `check` recomputes the committed file digests and the
patch digest. It checks that the patch and Hermes's diff change the same lines
and touch no test file or path outside `src/`. It checks that each hunk
changes a line naming the rule's fields (a token check; the single-class
judgement stays Hermes's attestation). It checks the gates, exit and reason
against Hermes's own result, and a clean restoration at the pinned commit. For
an attempt on a sealed anchor, the copy's Gate 1 maps, toolchain and source
manifest must equal that anchor's, and a selected attempt must be on one. For a Gate 5 rejection, it recomputes Hermes's map diff
from the committed before and after maps. The restoration status and stdout
digest are recorded only; the disposable copies are gone.

**Selector.** `selector-mem16` applies rule `MEM-16` (class
`calldata-memory`). It removes the unbounded `getMarketsForHooksInstance(address)`
overload from `HooksFactory` and `IHooksFactory`. It passed Gates 2, 3 and 4
and exited 50: `public method identifiers changed:
src/HooksFactory.sol:HooksFactory`, removing selector `4bd1acf3`. The
`selector-rejection` report is written by:

```sh
python3 scripts/kickoff_hermes_1355.py conformance --criterion selector-rejection \
  --candidate anchor-and-inspect \
  --report .hexaemeron/design-reports/anchor-and-inspect-selector-rejection.json
```

**Layout.** Candidates were tried in the study's order:

1. `STO-18` on `Wildcat4626Wrapper`'s constructor-only `_name` and `_symbol`
   with a retained fallback.
   - `layout-a1-sto18` uses OpenZeppelin `ShortStrings` with storage fallback.
     It exited 30 at Gate 3: the two wrapper factory tests rose by 4,111 gas
     and the two constructor-revert tests by 241.
   - `layout-a2-sto18` uses `ShortString` immutables and rebuilds a long
     label from the market's immutable symbol. It exited 30 at Gate 3: the
     factory tests rose by 143,486 gas and the constructor-revert tests by 231.

   Both forms grow the wrapper's initcode. Those four tests deploy the wrapper
   inside the measured test body, so any growth regresses them.
2. A co-accessed field pair in a protected type.
   - `layout-a3-sto01` applies `STO-01` to `SimpleMarketCollateralMultiParty`
     at collateral-contract `46dba596fa111f868200358f551796e8f73b5fd7`,
     moving `fullLiquidationIndex` into the slot of `totalShares`. It exited
     30 at Gate 3: five invariant snapshot rows changed.
   - `layout-b1-sto04` applies `STO-04` (class `storage-packing`) to
     `WildcatSanctionsSentinel` at the `v1-488b` anchor. It packs the
     three-slot `TmpEscrowParams`, which `createEscrow` writes and the escrow
     constructor reads together, into two words with named offsets and masks,
     with bits 224 to 255 reserved. The `tmpEscrowParams()` getter keeps its
     signature. It passed Gates 2, 3 and 4 and exited 50: `protected storage
     layout changed: src/WildcatSanctionsSentinel.sol:WildcatSanctionsSentinel`.
     Gate 3 found 11 deterministic measurements lower and none higher; each of
     its two targets fell by 3,123 gas.

No split co-accessed pair was found in a v2 protected type. The structs there
already share one slot or fill every slot they use, and `MarketState` is
packed by hand in assembly. The runbook amendment of 2026-09-23 moved the
`v1-488b` Gate 1 into this step so that Gate 5 compares against a sealed
anchor.

Hermes stops at the first Gate 5 difference, the Sentinel's layout, before it
inspects the Sentinel's method identifiers. The attempt's
`method_identifier_check` records a separate `forge inspect ... methodIdentifiers`
on the same copy with the candidate applied, then reverted. `check` recomputes
that the committed after map equals the map the attempt's Gate 1 sealed, and
that the recorded digests match.

The three attempts that stopped at Gate 3 keep their original run directories
under the session scratchpad, which their `state.json` files name. The two
selected attempts and both baselines were re-run from
`/private/tmp/fiat1355-hermes/`.

The `layout-rejection` report is written by:

```sh
python3 scripts/kickoff_hermes_1355.py conformance --criterion layout-rejection \
  --candidate anchor-and-inspect \
  --report .hexaemeron/design-reports/anchor-and-inspect-layout-rejection.json
```
