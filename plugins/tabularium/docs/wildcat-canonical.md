# Wildcat canonical events

`wildcat-canonical` writes schema 3 events for deployed Wildcat V1/V2 from a
verified local Alexandria release. It preserves native records, actual parties,
financial units and unsupported coverage. All commands operate offline.

## Build and reproduce

From the repository root:

```bash
python3 plugins/tabularium/scripts/tabularium.py wildcat-canonical \
  --alexandria-release <raw-release-dir> \
  --adapter-version 1.3.0 --release <release-id> --out <new-release-dir>
python3 plugins/tabularium/scripts/tabularium.py verify <new-release-dir>/coverage.json
```

The output directory must be fresh. It contains `source/raw-release/` with
every preserved raw-release file, plus `source.json`, `capture.json`,
`events.jsonl` and `coverage.json`. Moving that directory preserves verification:
`verify` rechecks Alexandria, rederives context and compares every generated
byte. Rebinding descriptor or coverage digests cannot bless changed parties,
selectors, financial units or evidence classes. Links, input/output aliases,
undeclared files, duplicate identities and malformed supported ABI are refused.

## Native meaning

Adapter `1.0.0` has eleven market contexts per generation and three V2 wrapper
contexts: twenty-five primary mappings. Adapter `1.1.0` adds three fee contexts.
Adapter `1.2.0` retains all twenty-eight and adds twenty-nine native
parameter/access contexts across fifty-eight concrete ABI declarations. The action and instrument stay
generation-qualified. The four withdrawal-batch rows are the eight contexts
added under adapter `1.0.0`; the seventeen released rules keep their bytes.

| Native event / scope | Actual parties | Financial units |
| --- | --- | --- |
| Deposit / V1-V2 market | depositor and minted-token account | underlying assets; assetless scaled claims |
| WithdrawalQueued / V1-V2 market | withdrawing account | normalized market claims; assetless scaled claims; no payment |
| WithdrawalExecuted / V1-V2 market | beneficiary account; escrow recipient only after a unique routing join | underlying assets paid |
| Transfer / V1-V2 market | from and to, including zero and queue-custody endpoints | market-token claims; no fresh capital inference |
| Borrow / V1-V2 market | pool only | underlying assets; borrower actor absent |
| DebtRepaid / V1-V2 market | emitted payer and pool | underlying assets; payer need not be debtor |
| FeesCollected / V1-V2 market, adapter 1.1.0 | pool only | `fee-collection`; underlying `assets`; recipient remains unknown |
| ProtocolFeeBipsUpdated / V2 market, adapter 1.1.0 | pool only | `pool-state`; empty `amounts`; `protocolFeeBips` stays decoded native state |
| MarketClosed / V1-V2 market | pool only | empty `amounts`; timestamp stays native state |
| WithdrawalBatchCreated / V1-V2 market | pool only | empty `amounts`; the expiry stays native batch state |
| WithdrawalBatchPayment / V1-V2 market | pool only | burned scaled claims; reserved underlying assets, not received, spendable or executed |
| WithdrawalBatchExpired / V1-V2 market | pool only | cumulative scaled claims, burned scaled claims and reserved assets at expiry |
| WithdrawalBatchClosed / V1-V2 market | pool only | empty `amounts`; the batch is fully burned, which does not establish that any lender was paid |
| Deposit / V2 wrapper | caller and owner | market-token assets; wrapper shares |
| Withdraw / V2 wrapper | caller, receiver and owner | market-token assets; wrapper shares |
| Transfer / V2 wrapper | from and to | wrapper shares |

Withdrawal execution observes the claim account, not its executor. A unique
`SanctionedAccountWithdrawalSentToEscrow(address,address,uint32,uint256)`
companion matches generation, market, transaction, account, expiry and amount.
It preserves beneficiary, escrow recipient and both selectors with
`join-inference`; it adds no second cash withdrawal. Missing or ambiguous
companions leave the recipient gap. Wrapper assets are market tokens, with no
shareholder look-through or underlying pool cash-flow inference.

A `WithdrawalBatchPayment` joins one burn under the `adjacent-market-burn`
rule. The log at `log_index - 1` must be `Transfer(address,address,uint256)`
emitted by the same market, with `from` the market, `to` the zero address, the
same transaction hash and `value` equal to `normalizedAmountPaid`. Those six
conditions are the emission order of `_applyWithdrawalBatchPayment` in both
generations. The payment row and the burn's `transfer` row each carry the
other's selector and the same `join-inference` record. Any failed condition
leaves `attribution:withdrawal-batch-payment:burn` on the payment and
`attribution:transfer:unclaimed-burn` on a market-to-zero transfer nothing
claims; no join is guessed, and a burn is never claimed twice. Created,
expired and closed rows carry no join.

`reserved-assets` is `normalizedAmountPaid`: underlying units set aside in the
market for the batch. It is not lender receipt, spendable cash or execution.
The `uint32` expiry identifies the batch and stays a decoded field in the
mapping record and `native_record`; it is never a party, an amount or a row
field. No batch row names the repay, queue, execute or close sharing its
transaction as its cause. Under `1.0.0`, only `market-closed`, `withdrawal-batch-created` and
`withdrawal-batch-closed` admit an empty `amounts` list. Adapter `1.2.0` also
requires empty `amounts` on every parameter/access row below; the earlier
actions keep their exact amount counts.

## Native parameter and access state

Adapter `1.2.0` maps the following generation, emitter-role and signature
contexts to `pool-state`. Action suffixes use the event name in kebab case;
controller suffixes start `controller-` and hooks-instance suffixes start
`hooks-`. Each rule is `<generation>.<suffix>.v1` and the instrument is
`<generation>-<emitter-role>`, identified by the emitting address.

Every value stays in `mapping_records[].decoded` under its exact ABI name.
These are emitted native state values: no role enum, conversion, new-value or
delta interpretation is established. All financial `amounts` arrays are empty.

| Generation | Emitter role | Native event | Exact decoded fields |
| --- | --- | --- | --- |
| `wildcat-v1` | `controller` | `LenderAuthorized(address)` | `""` |
| `wildcat-v1` | `controller` | `LenderDeauthorized(address)` | `""` |
| `wildcat-v1` | `controller` | `TemporaryExcessReserveRatioActivated(address,uint256,uint256,uint256)` | `market`, `originalReserveRatioBips`, `temporaryReserveRatioBips`, `temporaryReserveRatioExpiry` |
| `wildcat-v1` | `controller` | `TemporaryExcessReserveRatioCanceled(address)` | `market` |
| `wildcat-v1` | `controller` | `TemporaryExcessReserveRatioExpired(address)` | `market` |
| `wildcat-v1` | `controller` | `TemporaryExcessReserveRatioUpdated(address,uint256,uint256,uint256)` | `market`, `originalReserveRatioBips`, `temporaryReserveRatioBips`, `temporaryReserveRatioExpiry` |
| `wildcat-v1` | `market` | `AnnualInterestBipsUpdated(uint256)` | `annualInterestBipsUpdated` |
| `wildcat-v1` | `market` | `AuthorizationStatusUpdated(address,uint8)` | `account`, `role` |
| `wildcat-v1` | `market` | `MaxTotalSupplyUpdated(uint256)` | `assets` |
| `wildcat-v1` | `market` | `ReserveRatioBipsUpdated(uint256)` | `reserveRatioBipsUpdated` |
| `wildcat-v2` | `hooks-instance` | `AccountAccessGranted(address,address,uint32)` | `providerAddress`, `accountAddress`, `credentialTimestamp` |
| `wildcat-v2` | `hooks-instance` | `AccountAccessRevoked(address)` | `accountAddress` |
| `wildcat-v2` | `hooks-instance` | `AccountBlockedFromDeposits(address)` | `accountAddress` |
| `wildcat-v2` | `hooks-instance` | `AccountMadeFirstDeposit(address,address)` | `market`, `accountAddress` |
| `wildcat-v2` | `hooks-instance` | `AccountUnblockedFromDeposits(address)` | `accountAddress` |
| `wildcat-v2` | `hooks-instance` | `FixedTermUpdated(address,uint32)` | `market`, `fixedTermEndTime` |
| `wildcat-v2` | `hooks-instance` | `MinimumDepositUpdated(address,uint128)` | `market`, `newMinimumDeposit` |
| `wildcat-v2` | `hooks-instance` | `NameUpdated(string)` | `name` |
| `wildcat-v2` | `hooks-instance` | `RoleProviderAdded(address,uint32,uint24,uint24)` | `providerAddress`, `timeToLive`, `pullProviderIndex`, `pushProviderIndex` |
| `wildcat-v2` | `hooks-instance` | `RoleProviderRemoved(address,uint24,uint24)` | `providerAddress`, `pullProviderIndex`, `pushProviderIndex` |
| `wildcat-v2` | `hooks-instance` | `RoleProviderUpdated(address,uint32,uint24,uint24)` | `providerAddress`, `timeToLive`, `pullProviderIndex`, `pushProviderIndex` |
| `wildcat-v2` | `hooks-instance` | `TemporaryExcessReserveRatioActivated(address,uint256,uint256,uint256)` | `market`, `originalReserveRatioBips`, `temporaryReserveRatioBips`, `temporaryReserveRatioExpiry` |
| `wildcat-v2` | `hooks-instance` | `TemporaryExcessReserveRatioCanceled(address)` | `market` |
| `wildcat-v2` | `hooks-instance` | `TemporaryExcessReserveRatioExpired(address)` | `market` |
| `wildcat-v2` | `hooks-instance` | `TemporaryExcessReserveRatioUpdated(address,uint256,uint256,uint256)` | `market`, `originalReserveRatioBips`, `temporaryReserveRatioBips`, `temporaryReserveRatioExpiry` |
| `wildcat-v2` | `market` | `AccountSanctioned(address)` | `account` |
| `wildcat-v2` | `market` | `AnnualInterestBipsUpdated(uint256)` | `annualInterestBipsUpdated` |
| `wildcat-v2` | `market` | `MaxTotalSupplyUpdated(uint256)` | `assets` |
| `wildcat-v2` | `market` | `ReserveRatioBipsUpdated(uint256)` | `reserveRatioBipsUpdated` |

A market row carries its own emitter as `pool`. A controller row starts with
`controller`; a hooks-instance row starts with `hooks-instance`. Only an
emitted `market` adds a `pool` to either non-market role. An emitted `account`,
`accountAddress` or the unnamed V1 lender key `""` adds `affected-account`;
`providerAddress` adds `role-provider`. Zero addresses are retained. Known
context never supplies a market or account absent from the event.

A marketless hook or controller row states its scope limitation and contains no
pool party, even when context names associated markets. A hooks template is a
distinct emitter role and gains none of these hooks-instance meanings. The
[locked event inventory and reason table](https://github.com/wildcat-finance/skills/blob/9816d678b137fe3850089dace9d7bc179f6066d7/docs/kickoff/2090/study.md)
names every required concrete context and each last-group signature's own
unsupported reason. Under `1.2.0`, those unsupported records retain
`unsupported-canonical-meaning`, `canonical:<role>:<signature>` and the exact
signature with its reason in `limitations`. Deployment and registry records
supply no inferred funding, access decision or repayment.

## Adapter compatibility

The builder defaults to `1.3.0`. Pass `--adapter-version 1.0.0` only to replay
this run's qualified starting-tree interpretation. Verification selects the
recorded supported version and reconstructs all generated bytes from the raw
copy. Unknown versions and a rule absent from its declared version refuse.
A changed version label cannot admit changed canonical or coverage bytes.

| Adapter version | Meanings | Reproduction |
| --- | --- | --- |
| `1.0.0` | Starting-tree market, wrapper and batch meanings; original generic unsupported limitations | The qualified starting-tree releases retain their exact bytes |
| `1.1.0` | Baseline plus three fee contexts; original generic unsupported limitations | Existing fee releases retain their exact bytes |
| `1.2.0` | Baseline, fee contexts, native parameter/access table and signature-specific unsupported reasons | Fresh parameter releases; sanctions-sentinel extension remains unsupported |
| `1.3.0` | All `1.2.0` meanings plus supporting sanctions asset-routing relations | Earlier selectors retain their original outputs; every mapping carries `routing_joins`, which may be empty |

Package and governed-skill versions are separate from this adapter selector.
These constructed proofs establish mapper behaviour; they establish no
historical occurrence. Retained checks and acceptance of absent historical
positives remain separate.

## Versioned sanctioned-account routing

Adapter `1.3.0` retains the `1.2.0` fee and native-state meanings and adds supporting routing. New builds use `1.3.0`. Pass `--adapter-version 1.0.0` to reproduce
that earlier interpretation; verification dispatches by the exact version in
`coverage.json` and refuses unsupported or mixed versions. The schema 3
envelope and inherited primary rules stay unchanged. Committed release data is immutable.
The old examples select `1.0.0` explicitly when rebuilding; the committed
sanctions control fixes the starting mapper's bytes for the same version.
These controls do not recover every historical recipe that used `1.0.0`.

Under `1.3.0`, every mapping record carries `routing_joins`, empty where no
relation exists. V2 `SanctionedAccountAssetsQueuedForWithdrawal` joins one
`WithdrawalQueued` by generation, market, transaction hash, account, expiry,
scaled amount and normalized amount. V1 has no queued companion. V1/V2
`SanctionedAccountAssetsSentToEscrow` joins one market `Transfer` by generation,
market, transaction hash, account/from, escrow/to and amount/value. The rule ids
are `same-market-transaction-account-expiry-scaled-normalized` and
`same-market-transaction-account-escrow-amount`.

Both groups must contain exactly one record. Each relation has exactly
`evidence_class`, `rule`, `primary_selector`, `companion_selector` and
`conditions`; its evidence class is `join-inference`. Queue condition keys are
`generation`, `market`, `transaction_hash`, `account`, `expiry`, `scaled_amount`
and `normalized_amount`. Escrow condition keys are `generation`, `market`,
`transaction_hash`, `account`, `escrow` and `amount`. Both mappings retain the
relation and counterpart supporting selector; the primary event's provenance
also names the companion. The existing singular `join` survives, including
when one transfer also supplies a batch burn.

Companions remain `supporting-routing` and add no canonical action, even when
unmatched. Each unmatched companion adds one gap with prefix
`routing:sanctioned-assets-queued-for-withdrawal` or
`routing:sanctioned-assets-sent-to-escrow`, followed by `missing-primary` or
`ambiguous-match`. Either group exceeding one record is ambiguous. The count
overlaps preserved source records and is never an extra omitted event.
Ordinary primary rows without a companion acquire no sanctions gap. Queue
amounts remain claims and transfer amounts remain market-token claims; no
sanction status, identity or underlying cash settlement is inferred.

Constructed fixtures exercise all three declared branches and a transfer that
also joins a batch payment. A constructed V2 escrow relation establishes no
historical emission. Retained coverage is conditional: verified absence of a
companion establishes no positive historical join. Retained coverage requires separately verified custody and actual build and
verification results.

## Evidence and coverage

Dispatch uses generation, admitted emitter role and concrete ABI before topic.
Pinned declarations establish ABI layout; the retained normalized inspections
do not establish a new compiler run or runtime-bytecode equivalence. Raw native
references keep their recorded class. Context distinguishes
`checked-registry-context`, `checked-positional-epoch-context`,
`checked-wrapper-subject-context`, `inferred-deployment-asset`,
`recorded-constructor-context`, `registry-inferred-debtor` and
`declared-constructed-context`.

A verified release whose plan declared Wildcat V2 wrapper instances carries
Alexandria's `wrapper-subjects` component. Each wrapper it lists as declared
becomes one `wrapper` context under `checked-wrapper-subject-context`: the
market its `WrapperDeployed` log names is both `market` and `asset`, because
wrapper deposits and withdrawals move market tokens, and the concrete ABI is
the wrapper variant pinned at the wrapper factory's source commit. The wrapper's
native `Deposit`, `Withdraw` and `Transfer` logs then map as the three wrapper
rows above, with market-token assets naming that market. A wrapper the
component lists as undeclared gets no context, because its logs were never
requested; `scope.wrapper_subjects` names both sets and
`scope.wrapper_native_coverage` reads `declared-wrapper-subjects`. A release
without the component maps as before and keeps `not-established`.

Each scoped native log has exactly one disposition: `primary`,
`supporting-routing`, `unsupported-canonical-meaning` or `unsupported-decode`.
The descriptor preserves this closed denominator and all native records.
Coverage counts mapped actions and qualified gaps separately. Keys are
`attribution:<action>:<role>`, `canonical:<role>:<signature>` and
`decode:<role>:<topic>`. Attribution gaps can overlap mapped rows; adding them
to omitted-log counts would overcount. The two burn gaps,
`attribution:withdrawal-batch-payment:burn` and
`attribution:transfer:unclaimed-burn`, are counted per release beside the
mapped batch rows, so an unmatched burn stays visible in `coverage.json`.
Malformed accepted ABI is fatal.

Underlying amounts remain exact base-unit strings. Unknown asset context stays
null with a gap. V1 constructor evidence supplies no decimals; V2 decimals
retain only the recorded constructor context. No display scaling is inferred.

## Capture limits and recovery

Constructed raw releases remain `constructed-fixture` inputs with declared
context and an explicit origin limitation. Each capture must be `subject-scoped`,
with CAIP-10 subjects matching the declared emitter set; this comparison ignores
order. Digest agreement proves those local bytes and declarations; it does not
turn a fixture into historical capture or
prove deployed runtime code. The retained V2 capture has factory wrapper
bindings and market-token counterparties, with no established wrapper-instance
registry, epoch or native-journal coverage.

Components are capped at 64 MiB, aggregate component bytes at 512 MiB, each
journal class at 500,000 records and each generated artefact at 256 MiB.
These finite journals establish neither lifetime activity, canonical-chain
finality, current credit standing, identity nor complete settlement. V1 closure
can leave an expired, unprocessed withdrawal batch unpaid. Releases are unsigned;
offline verification does not authenticate a publisher.

On refusal, preserve the input and inspect the named field or byte mismatch.
Correct the source or interpretation in a new release directory, then rerun
`wildcat-canonical` and `verify`. Schema 2 and all six published Aave/Euler
example releases remain unchanged; Wildcat canonical output requires schema 3.

## Public constructed specimens

[Wildcat V1](../examples/wildcat-v1-v0/README.md) and
[Wildcat V2](../examples/wildcat-v2-v0/README.md) each ship two independent
closed roots. The main root exercises the seven released market mappings,
sanctions routing and decoded/undecoded unsupported records; V2 includes
wrapper mappings. The auxiliary root exercises registry-derived debtor context
through the actual Alexandria collector, reconciler and builder with synthetic
responses and the full authentic registry. Its constructed-staging gap remains
visible.

[Wildcat V1 batches](../examples/wildcat-v1-batches-v0/README.md) and
[Wildcat V2 batches](../examples/wildcat-v2-batches-v0/README.md) each ship one
closed root built from synthetic logs in the pinned source emission order. Each
exercises the four batch events, the `adjacent-market-burn` join, two payments
to one expiry in one transaction and the five hostile shapes that leave a named
gap, four of them with no join and two burns before one payment joining the
adjacent burn alone; the V2 root also carries the `closeMarket` sequence. Their
`coverage.json` counts the mapped batch rows and the two burn gaps separately.

[Wildcat V1 parameters](../examples/wildcat-v1-parameters-v0/README.md) and
[Wildcat V2 parameters](../examples/wildcat-v2-parameters-v0/README.md) contain
only constructed logs and contexts. Together they exercise all fifty-eight
concrete required declarations. Their fixture addresses use repeating bytes;
no retained input is included.

Run each example's `rebuild.py` to compare every file with its public root,
move the complete roots and verify without disposable original inputs.
The README, data dictionary and `expected.json` remain outside every closed
release.

## Saved release reproduction

Ordinary discovery runs public constructed parser controls and custody refusal
controls without retained captures:

```bash
python3 -m unittest discover -s plugins/tabularium/tests \
  -p test_wildcat_v3_reproduction.py -t plugins/tabularium
```

The separate four-input protocol covers the two public main raw roots and the
two admitted retained/R2-recovered V1/V2 releases. It requires 32 successful
owner CLI operations and 20 specific mutation refusals: independent party,
amount-shape, selector, mapping-class and raw-component changes for each input.
Four compatibility/denial diagnostics stay outside those 52 operations.
Auxiliary public registry roots stay outside the four-input count.

The bounded reproduction summary is at repository path
`docs/kickoff/1378/reproduction-summary.json`, in the public Fiat bundle outside
the installable plugin. It binds the privately retained inventory by digest. Saved admission checks every
stream, operation, complete file inventory and mutation against that independent
candidate anchor. It executes no CLI. The original checkout, owned interpreter,
frozen code/resources and separately preserved custody must still match.

Saved positive admission is bound to the original checkout fingerprint. If controller reset removes that worktree, retained custody remains inspectable but cannot transfer positive admission to another checkout. A new checkout or fingerprint requires a new actual four-input matrix, independent verification and public anchor.

```bash
python3 plugins/tabularium/tests/prove_wildcat_v3.py \
  --candidate role-qualified --criterion release-reproduction \
  --report .hexaemeron/reports/wildcat-release-reproduction.json
```

Use a fresh report path. Missing, stale or mismatched custody yields named
`EvidenceUnavailable`, a setup error and status 2; it emits no scalar proof.
A fresh clone can run the ordinary controls. Python socket instrumentation
records the demonstrated path's network attempts; it supplies no OS containment
or hermetic macOS library claim.

The withdrawal-batch join has its own retained check, separate from the
four-input protocol above:

```bash
python3 plugins/tabularium/tests/prove_wildcat_batches.py \
  --candidate adjacent-burn --criterion retained-conformance \
  --report .hexaemeron/design-reports/adjacent-burn-retained-conformance.json
```

It reads the two staging trees named by `ALEXANDRIA_WILDCAT_V1_STAGING` and
`ALEXANDRIA_WILDCAT_V2_STAGING`, checks each against its public example's
staging manifest, rebuilds each raw release through
`plugins/alexandria/examples/wildcat-v1-interval-v0/demo.py` and
`plugins/alexandria/examples/wildcat-v2-interval-v0/demo.py`, then builds and
verifies a canonical release in a private temporary directory outside the
repository and removes that directory. The report is one boolean. It is true
only when, on both generations, the four batch signatures are absent from
unsupported coverage, every `withdrawal-batch-payment` row joins one adjacent
market burn, no market burn stays unclaimed and `verify` passes. A generation
whose canonical release maps no `withdrawal-batch-payment` row refuses by
generation name instead of passing. The sidecar
carries raw release identifiers, canonical and coverage digests and the
generations that passed, with no path or count. An unset or unreadable variable
refuses by name with exit 2 and no report. The public record of the run is
`docs/kickoff/2087/reproduction.md`: digests and pass or refuse results only,
while counts from the retained releases stay in private local reports.

Both retained captures lack sanctions-routing companions. V2 preserves fourteen
factory bindings and 172 market transfers with wrapper counterparties, with zero
wrapper-instance registry entries/epochs and no wrapper-native journal coverage.
Constructed specimens exercise those missing branches without extending capture
coverage. Recorded/inferred context remains qualified. Historical completeness,
provider independence, finality, compiler reruns, runtime-code equivalence,
identity, settlement and accounting conclusions remain unestablished.

## Native parameter retained conformance

The separate `native-fields` retained criterion for #2090 runs:

```bash
python3 plugins/tabularium/tests/prove_wildcat_parameters.py --candidate native-fields --criterion retained-conformance --report .hexaemeron/parameter-retained.json
```

It revalidates both private staging inventories through their Alexandria
builders, builds explicit adapter `1.2.0` releases, and verifies every canonical
byte. Every present required parameter/access event must map; every present
final-group event keeps its declared unsupported disposition. A generation
without an observed required target refuses. Linked staging ancestors, missing
custody and changed inventories refuse before a positive result.

The sidecar contains only release identifiers, digests and pass booleans. Its
inventory digest binds a separately retained private presence/absence inventory;
it establishes no missing historical positive. Private temporary releases are
removed on success, false conformance, refusal and build interruption.
`docs/kickoff/2090/reproduction.md` records execution and the separate user
acceptance required for historical absences before integration.

## Fee meanings and recorded versions

Fee-only builds select adapter `1.1.0`. Pass `--adapter-version 1.0.0` to
reproduce the starting-tree interpretation. Verification selects the version
in `coverage.json`, rebuilds the copied raw release and compares every generated
byte, including source dispositions, capture, row provenance and coverage.
Unknown versions and old-version/new-rule combinations refuse. Package and
skill versions are separate from this mapping version.

`1.1.0` adds exactly `wildcat-v1.fees-collected.v1`,
`wildcat-v2.fees-collected.v1` and `wildcat-v2.protocol-fee-bips-updated.v1`.
Collection retains the native `assets` integer string in underlying base units
and `attribution:fees-collected:recipient`. Missing asset context stays null
with `attribution:fees-collected:asset`. V2 Bips stays an integer string in
`mapping_records[].decoded.protocolFeeBips` and the unchanged native log;
`attribution:protocol-fee-bips-updated:actor` remains. The pool is the sole party
for all three rules. A transfer in the same transaction cannot establish a fee
recipient. Fee collection, repayment and withdrawal remain separate actions,
even when their amounts match. V1 factory fee configuration, native parameter updates under `1.1.0` and sanctions lifecycle meanings remain unsupported.

The compatibility boundary is the exact interpretation at starting commit
`8b4e137917d754a7b7c3d5e74d141c0bedf70aa2`, including its batch and wrapper
support. Earlier releases used `1.0.0` before those additions, so that token
cannot identify every earlier recipe. Universal reconstruction of pre-starting
eras is unestablished. The six committed Wildcat roots reproduce unchanged;
two constructed fee-containing controls retain complete starting-runtime file
inventories in `tests/fixtures/wildcat-fee-legacy.json`.

`examples/wildcat-v1-fees-v0/` and `examples/wildcat-v2-fees-v0/` contain
constructed positives, with three and four rows respectively. Run each
`rebuild.py` to rebuild every file, compare bytes and verify after moving the
release. These examples establish no historical observation. Retained
conformance is a separate gate; absence of a signature never counts as a
positive observation.

## Qualified retained fee check

Run the fee resolver with both private staging variables supplied:

```bash
python3 plugins/tabularium/tests/prove_wildcat_fees.py \
  --candidate versioned-native --criterion retained-conformance \
  --report .hexaemeron/design-reports/versioned-native-retained-conformance.json
```

It checks both Alexandria staging inventories, rebuilds both raw releases,
builds explicit adapter `1.1.0` output and verifies every generated byte.
Every present fee target must map to its exact independent action. Actual V2
fee collection must execute; empty inputs and V1 collection alone refuse.
Missing V1 collection or V2 protocol-fee updates supply no historical positive.
Scratch releases are removed on success, failure, refusal and Python interruption;
the retained staging trees remain unchanged. Missing custody refuses before
scratch creation, and the report contains no scalar success on refusal.

The observations carry release identifiers, canonical and coverage digests and
bounded pass results only. The [executed fee reproduction record](https://github.com/wildcat-finance/skills/blob/a2305294bf11c8f43deb3bc5c67484fb641e5e60/docs/kickoff/2089/reproduction.md)
keeps constructed coverage separate from retained conformance. The maintainer
stated that V1 collected no fees and V2 fee Bips had never been updated, while
future V2 updates remain possible. That statement resolves the issue's
historical qualification; it is separate from the preserved-capture evidence.

## Reproduce supporting asset routing

The constructed [V1 routing specimen](../examples/wildcat-v1-sanctions-v0/README.md) and [V2 routing specimen](../examples/wildcat-v2-sanctions-v0/README.md) use explicit adapter `1.3.0`. They exercise unique escrow transfers, V2 queued claims, simultaneous batch-burn and routing relations, missing primaries and duplicate primaries or companions. Each rebuild compares every generated byte and verifies the moved read-only release. Earlier specimens retain their recorded `1.0.0`, `1.1.0` or `1.2.0` interpretation.

The repository bundle `docs/kickoff/2091/reproduction.md` records source commands, report identities and the conditional retained result. The retained resolver validates both private staging inventories and rebuilds through Alexandria before canonical verification. Verified finite absence supplies no historical positive join or global absence inference. Missing custody, unexplained routing gaps and present companions without a unique primary refuse. Constructed positives remain separate evidence. No sanction status, policy, identity, underlying cash movement, settlement or independent chain proof is established.
