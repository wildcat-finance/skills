# Issue 1355: Wildcat V2 protected inventory

This directory holds the protected-contract inventory for the Wildcat V2
Ethereum estate of [issue 1355](https://github.com/wildcat-finance/skills/issues/1355)
and the evidence behind it: 137 addresses mapped to 17 protected types, five
sealed Hermes Gate 1 anchors, eleven byte-equal equivalence records, and one
selector and one layout candidate that each exit 50 at Gate 5. A reviewer
starts here.

1. Run [Check it](#check-it). It reads committed files only.
2. Read [What this establishes](#what-this-establishes) for the boundary of
   the claim.
3. Follow [Reproduce it](#reproduce-it) to re-run every anchor and both
   rejections from pinned inputs.

The delivery built it in five steps. Step 1 added the inventory, the checker
and the profile-invariance evidence. Step 2 added the fixed-block fixture, the
preserved release and the owner-handoff table. Step 3 sealed Hermes Gate 1 on
the v2-protocol and wildcat-protocol anchors and recorded the selector
rejection and every layout attempt; see [Gate 5 rejections](#gate-5-rejections).
Step 4 sealed the collateral, fee recipient and role provider anchors and
recorded the eleven equivalence types; see [Anchor baselines](#anchor-baselines)
and [Equivalence](#equivalence). Step 5 re-ran all five anchors and both
rejections and added the custody check; see [Reproduction](#reproduction) and
[Evidence custody](#evidence-custody).

## What this establishes

The evidence establishes a baseline and demonstrates its compatibility checks,
within the issue's Boundaries section:

- Each of the 17 types, and so each of the 137 addresses, is covered by one
  of five sealed Gate 1 anchors, natively or through a byte-equal layout and
  method map at its deployed state.
- Hermes's Gate 5 refuses a selector change on `HooksFactory` and a layout
  change on `WildcatSanctionsSentinel`, each after Gates 2 to 4 passed.
- A second run of every anchor and both rejections on fresh clones produced
  the same map digests, exits, gates and reasons.

It does not establish:

- whole-target safety, or the value or correctness of any later gas saving.
  A later candidate needs its own complete Hermes verification, and a
  candidate in a tree that is not an anchor needs a Gate 1 there first;
- that the target maintainer reviewed the inventory. The inventory row of
  `evidence/owner-handoffs.json` has status
  `target-maintainer-review-outstanding`, and that review is carried to the
  run pull request;
- that the fixture's header belongs to the canonical chain; see
  [Evidence classes and custody](#evidence-classes-and-custody);
- that the enumeration of collateral, escrow and wrapper instances is
  complete. Those instances are not enumerated; their types are protected;
- anything the audit's Elenchus runner would have shown. Where a fix changed
  a test, `python3 tests/run_tests.py --elenchus-report` returned
  `inconclusive`, in every step so far, because the runner's containment
  forbids the child processes the root suite starts. Each new guard was
  instead shown to fail on its parent by hand, as the audit rounds in
  `audit/rounds/` record.

The positive and negative observations of the second run are listed in
`evidence/reproduction.json`. They report what was compared and what was
not; they do not claim that the comparison is sufficient.

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
10. The five directories under `baselines/` each hold a Hermes Gate 1 at
    `baseline_ready` over every protected type anchored at that tree, and
    `baselines/exclusions.json` shows that each excluded test file passes zero
    tests, as described in [Anchor baselines](#anchor-baselines).
11. `equivalence/record.json` shows, for each of the eleven equivalence types,
    a layout and method map at the deployed state byte-equal to its sealed
    anchor's, as described in [Equivalence](#equivalence).
12. `rejections/selector/record.json` and `rejections/layout/record.json`
    record every attempt with its patch, gates, exit and restoration, as
    described in [Gate 5 rejections](#gate-5-rejections).
13. `evidence/reproduction.json` shows every anchor and both rejections
    reproduced against those sealed records, as described in
    [Reproduction](#reproduction).

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
otherwise. The other five reports follow the same rule.

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
- `collateral-46db`: collateral-contract
  `46dba596fa111f868200358f551796e8f73b5fd7`, 3 protected contracts, no
  exclusion. `FOUNDRY_SOLC=0.8.28` and cancun. 48 tests passed.
- `fee-ac73`: private fee-recipient-contract
  `ac73bda3642c9a7c8de64e39856b31af53f06068`, 1 protected contract, no
  exclusion. `FOUNDRY_SOLC=0.8.25` and cancun. 19 tests passed.
- `role-provider-5d7f`: private chainalysis-ofac-role-provider
  `5d7f8c889a8d29935838a3906172feb8d9861807`, 1 protected contract, no
  exclusion. `FOUNDRY_SOLC=0.8.25` and cancun. 5 tests passed.

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
tree's compiler pin set, because v2-protocol and collateral-contract set
`ffi=true`. Copies and run
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

**Private anchors.** `fee-ac73` and `role-provider-5d7f` come from private
repositories, and the 2026-09-13 scope approval grants no redistribution. Their
public directories hold only each protected contract's canonical layout, raw
layout and method map. Each `record.json` adds the pass counts, a projection of
Hermes's `state.json` (status, commit, compiler, seed, exclusions, protected
set, Gate 1 commands and map digests) and the digests of `state.json` and
`result.json`. Its `withheld` list names the Hermes files that stay out of Git:
the source copy, logs, source manifest, Foundry config, Forge version, corpus
copy, gas snapshot, git status, state and result. The complete run directories
stay in the run worktree's ignored
`.hexaemeron/restricted/hermes/<sha256 of state.json>/`. `check` refuses a
withheld file, a source copy or an undeclared file in a private anchor's public
directory, beside `run/` as well as inside it.

For a private anchor, `check` recomputes each map digest and each canonical
layout from committed bytes. It checks the projection against the inventory and
study. The projection and the two digests are recorded only until
`sealed-coverage` re-verifies the retained run.

**Zero-loss exclusions.** `baselines/exclusions.json` records, for each anchor
exclusion, `forge test --match-path <file> --fuzz-seed 0x5EED` and the
unexcluded `forge test --fuzz-seed 0x5EED`. Both ran on a fresh clone at the
pinned commit under the tree's Gate 1 environment. At `v2-c7be`,
`test/vault/Wildcat4626WrapperStandard.t.sol` alone passed 0 and failed 2, and
the unexcluded suite passed 795 and failed 2. At `v1-488b`,
`test/market/WildcatMarketToken.t.sol` alone passed 0 and failed 6, and the
unexcluded suite passed 348 and failed 6. Each unexcluded pass count equals
the sealed Gate 1's.

`check` refuses an excluded file with a passing test and an unexcluded pass
count that differs from the sealed Gate 1. It also requires each summary line
to state its counts. The counts and exit codes are recorded only: no committed
or retained byte backs them.

## Equivalence

Eleven types are covered through an anchor rather than a Gate 1 of their own.
For each, one fresh clone of the deployed state ran Hermes's own inspect argv,
`forge inspect <identifier> storageLayout --json --force` and `forge inspect
<identifier> methodIdentifiers --json --force`. The run used `env -i` and the
tree's Gate 1 pins. The raw layout was written in Hermes's JSON form and passed
through Hermes's `canonical_storage_layout`. `equivalence/<type>/` keeps the
raw layout, the canonical layout and the method map.

| Type | Deployed state | Anchor | Layout | Method map |
| --- | --- | --- | --- | --- |
| hooks-factory | v2 `a70f` | `v2-c7be` | byte-equal | byte-equal |
| wildcat-market | v2 `a70f` | `v2-c7be` | byte-equal | byte-equal |
| open-term-hooks | v2 `a70f` | `v2-c7be` | byte-equal | byte-equal |
| fixed-term-hooks-365 | v2 `a70f` | `v2-c7be` | byte-equal | byte-equal |
| fixed-term-hooks-730 | v2 `5838` | `v2-c7be` | byte-equal | byte-equal |
| market-lens-core | v2 `a70f` | `v2-c7be` | byte-equal | byte-equal |
| market-lens-app | v2 `e1f7` | `v2-c7be` | byte-equal | byte-equal |
| open-access-role-provider | v2 `e1f7` | private `role-provider-5d7f` | byte-equal | byte-equal |
| arch-controller | V1 `da74` | `v1-488b` | byte-equal | byte-equal |
| sanctions-sentinel | V1 `6164` | `v1-488b` | byte-equal | byte-equal |
| sanctions-escrow | V1 `6164` | `v1-488b` | byte-equal | byte-equal |

The role provider's deployed state is the public v2-protocol copy at `e1f7`,
per the inventory's source override; its anchor is the private repository's
Gate 1.

`check` recomputes each file digest and each canonical layout from its raw
output through Hermes's canonicaliser. It compares each layout and method map
byte for byte with the anchor's committed Gate 1 file, and checks that file's
digest against the anchor's sealed hashes. It also requires each map to hash
to the profile-invariance record at the same deployed state. It checks the
commit, identifier, anchor and pins against the inventory, and requires the
compiler Forge resolved to equal the anchor's. It refuses a type whose anchor
is not sealed. The Forge version text, config digest, restoration status and
submodule list are recorded only.

The `sealed-coverage` design report is written by:

```sh
python3 scripts/kickoff_hermes_1355.py conformance --criterion sealed-coverage \
  --candidate anchor-and-inspect \
  --report .hexaemeron/design-reports/anchor-and-inspect-sealed-coverage.json
```

It runs `check` and requires all 17 types and 137 addresses to be covered by
one of the five sealed anchors, natively or through a byte-equal equivalence
record. It then re-verifies both retained private runs: the `state.json` and
`result.json` digests, the projection, every `artifact_hashes` entry, each
committed map against the retained file, every source copy against the
manifest, the Forge config and version digests, the resolved compiler and the
Gate 1 pass count. It writes value `true` only when all of them hold, and
refuses by name when a retained run is missing.

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
patch digest, and requires each committed map to hash to the entry the
attempt's own Gate 1 sealed. It refuses any file beside `run/` other than a
declared method check's `supplementary/` map. It checks that the patch and
Hermes's diff change the same lines and touch no test file or path outside
`src/`. It checks that each hunk
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

## Reproduce it

Every run uses Forge 1.7.1, commit `4072e48705af9d93e3c0f6e29e93b5e9a40caed8`,
the CPython that this tree's `.python-version` pins, and this tree's
`plugins/hermes/skills/hermes/scripts/hermes.py`,
SHA-256 `36e80da4405645486e4f34caf6fa59ed795d864c685e04a9b37a959bc43c1805`.
Each anchor's compiler pin is the inventory's `gate1_environment`:

| Anchor | Repository and commit | Pin set in the environment |
| --- | --- | --- |
| `v2-c7be` | v2-protocol `c7be4039f8f383a9dda4e45f63331c17d63f9ed9` | none; `foundry.toml` pins solc 0.8.25 and cancun |
| `v1-488b` | wildcat-protocol `488b30d08c73a93be3e4bf99128c774997411d3a` | `FOUNDRY_SOLC=0.8.22`; `foundry.toml` sets shanghai |
| `col-46db` | collateral-contract `46dba596fa111f868200358f551796e8f73b5fd7` | `FOUNDRY_SOLC=0.8.28`, `FOUNDRY_EVM_VERSION=cancun` |
| `fee-ac73` | private fee-recipient-contract `ac73bda3642c9a7c8de64e39856b31af53f06068` | `FOUNDRY_SOLC=0.8.25`, `FOUNDRY_EVM_VERSION=cancun` |
| `rp-5d7f` | private chainalysis-ofac-role-provider `5d7f8c889a8d29935838a3906172feb8d9861807` | `FOUNDRY_SOLC=0.8.25`, `FOUNDRY_EVM_VERSION=cancun` |

**An anchor.** Clone the repository into a fresh directory and pin it:

```sh
git clone https://github.com/wildcat-finance/<repository>.git <checkout>
git -C <checkout> checkout --detach <commit>
git -C <checkout> submodule update --init --recursive
```

From the root of this Skills tree, with an empty run directory outside the
checkout, run the argv in `invocation.argv` of `baselines/<tree>/record.json`
under `env -i`:

```sh
env -i HOME="$HOME" LANG=en_US.UTF-8 NO_COLOR=1 \
  PATH="$HOME/.foundry/bin:/usr/bin:/bin:/usr/sbin:/sbin" <pins> \
  /path/to/python3.14 plugins/hermes/skills/hermes/scripts/hermes.py baseline \
  --repo <checkout> --evidence-dir <run> --fuzz-seed 0x5EED <the record's remaining operands>
```

The record's `python3` is that pinned interpreter, as its
`invocation.interpreter` states. It is named by absolute path because the
`env -i` `PATH` holds no interpreter of that version. v2-protocol and
collateral-contract set `ffi=true`, so the environment carries no credential.
The run must exit 0 with `state.json` at `baseline_ready`. Each
`storage-layout/<label>.before.json`, `storage-layout/<label>.before.raw.json`
and `method-identifiers/<label>.before.json` under `<run>` must hash to the
digest the record's `run_files` names.

**A rejection.** Clone and pin the attempt's commit the same way and run the
attempt's `invocation.baseline_argv` from `rejections/<kind>/record.json`
under its `invocation.environment`. Write the attempt's `patch` field to a
file, whose SHA-256 must be `patch_sha256`, then:

```sh
git -C <checkout> apply <patch>
env -i <the same environment> /path/to/python3.14 \
  plugins/hermes/skills/hermes/scripts/hermes.py verify --run-dir <run> <the rest of verify_argv>
git -C <checkout> apply -R <patch>
rm -f <checkout>/.gas-snapshot
git -C <checkout> status --porcelain
```

`verify` must exit 50, and its last stderr line must be `Hermes rejected at
Gate 5: ` followed by the record's `reason`. After restoration the status
prints nothing and `HEAD` is the pinned commit.

**Restricted custody.** The two private repositories need read access to
clone. That credential serves `git clone` only and never enters the Hermes
environment. Nothing from a private checkout or run directory is committed.
The complete run goes to the run worktree's ignored
`.hexaemeron/restricted/reproduction/<sha256 of state.json>/`, and
`evidence/reproduction.json` carries only its digests, counts and verdict.
After the run, delete the private checkout and every run directory, build
output and log derived from it outside `.hexaemeron/restricted/`.

## Reproduction

Step 5 ran the commands above for all five anchors and both selected
rejections, each on its own fresh clone under
`/private/tmp/fiat1355-hermes/repro/`, and wrote `evidence/reproduction.json`.

| Run | Result | Compared with the sealed record | Verdict |
| --- | --- | --- | --- |
| `v2-c7be` | exit 0, `baseline_ready`, 795 passed | 21 map digests | reproduced |
| `v1-488b` | exit 0, `baseline_ready`, 348 passed | 9 map digests | reproduced |
| `col-46db` | exit 0, `baseline_ready`, 48 passed | 9 map digests | reproduced |
| `fee-ac73` | exit 0, `baseline_ready`, 19 passed | 3 map digests | reproduced |
| `rp-5d7f` | exit 0, `baseline_ready`, 5 passed | 3 map digests | reproduced |
| `selector-mem16` | Gates 1 to 4 passed, exit 50 at Gate 5: `public method identifiers changed: src/HooksFactory.sol:HooksFactory` | Gate 1 maps, after map, reason, restoration | reproduced |
| `layout-b1-sto04` | Gates 1 to 4 passed, exit 50 at Gate 5: `protected storage layout changed: src/WildcatSanctionsSentinel.sol:WildcatSanctionsSentinel` | Gate 1 maps, after map, reason, restoration | reproduced |

Each reproduced `state.json` differs from the sealed one, because Hermes
records a run id, a creation time and the run directory. The comparison
covers maps, counts, exits, gates and reasons only.

`check` requires each anchor entry to name the digest of its baseline
record's `invocation` and each rejection entry the digest of its attempt's
`invocation` and patch. Every map digest must equal the sealed record's, the
counts, exits, gates and reason must equal the sealed values, and each
verdict must be the one those fields recompute. A digest that differs, or a
rejection that no longer exits 50, is refused by name. The reproduced digests
and counts of the three public anchors and both rejections are recorded only:
their copies and run directories were deleted after the run. The two private
reproductions are retained under `.hexaemeron/restricted/reproduction/`, and
`evidence-custody` recomputes them.

## Evidence custody

The `evidence-custody` design report is written by:

```sh
python3 scripts/kickoff_hermes_1355.py conformance --criterion evidence-custody \
  --candidate anchor-and-inspect \
  --report .hexaemeron/design-reports/anchor-and-inspect-evidence-custody.json
```

It runs `check`, then recomputes from committed and retained bytes:

1. every reproduction verdict is `reproduced`;
2. every retained payload a committed record names by digest is present and
   matches: the fixture's four components and manifest, the capture script,
   the release manifest and plan, both sealed private Hermes runs through the
   `sealed-coverage` re-verification, and both private reproductions with
   their maps and test counts;
3. every `.hexaemeron/restricted` path named anywhere under this directory
   resolves to one of those verified payloads;
4. no file here, and no JSON string in one, has the bytes of a retained
   private file, other than the public maps each private record declares and
   the artefacts every Hermes run shares with the public anchors, such as the
   Forge version text;
5. no file here carries a private test identifier from a retained private gas
   snapshot; and
6. no file here has the digest of a target source file that any sealed source
   manifest names.

It writes value `true` only when all of them hold. The report does not show
that every private byte is absent in some other encoding: the scan compares
whole files, whole JSON strings and test identifiers.
