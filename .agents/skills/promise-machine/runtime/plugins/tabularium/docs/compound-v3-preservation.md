# Compound III mapping and preservation requirements

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

Status: Phase 0 method proof shipped, 2026-08-17. The checked-in witness is
non-canonical and transaction-scoped. This document defines the remaining
canonical release work; it does not claim that a Compound III event release or
interval history exists.

## Decision

Preserve the raw Compound III record under Alexandria, beginning with the
Ethereum mainnet USDC Comet and then widening by market and chain. Alexandria's
[harvest specification](https://github.com/wildcat-finance/skills/blob/main/plugins/alexandria/docs/compound-v3-harvest.md)
owns the registry pin, RPC collection, provider reconciliation and raw-release
boundary.
Use Hinterlight for the first archive, debug and trace pass where its exact
methods have been tested. Tabularium starts from a verified Alexandria release
and owns the reviewed credit mapping, canonical rows and mapping coverage.

Do not build from logs alone. Compound III records base-asset movement, signed
principal and accrued interest through the same account balance. A `Supply`
can be a repayment, a deposit, or both. A `Withdraw` can remove supplied funds,
create debt, or do both. A base `transfer` can create debt for its source and
repay debt for its destination without emitting a credit-specific event.

The first canonical release therefore needs execution evidence for every successful call
to a Comet proxy, not merely the proxy's logs. The canonical rows must be
derived from per-call principal transitions at the indices used by that call.

## Fixed research boundary

The initial registry is the production deployment tree at Compound's Comet
commit [`f766f51583c23acc33b2a7824654ef2029a96804`](https://github.com/compound-finance/comet/tree/f766f51583c23acc33b2a7824654ef2029a96804/deployments).
At that commit it contains 28 production market directories across ten
networks:

| Network | Chain ID | Markets |
| --- | ---: | --- |
| Ethereum | 1 | USDC, USDS, USDT, WBTC, WETH, wstETH |
| Optimism | 10 | USDC, USDT, WETH |
| Polygon | 137 | USDC, USDT |
| Ronin | 2020 | WETH, WRON |
| Mantle | 5000 | USDe |
| Base | 8453 | AERO, USDbC, USDC, USDS, WETH |
| Arbitrum | 42161 | USDC, USDC.e, USDT, WETH |
| Linea | 59144 | USDC, WETH |
| Unichain | 130 | USDC, WETH |
| Scroll | 534352 | USDC |

This list is an input version, not a permanent roster. Later registry commits,
new markets and retired markets receive new registry versions. Testnets are
outside the production backfill.

Compound's [network documentation](https://docs.compound.finance/) points to
the Comet deployment directories for proxy addresses. Each directory's
`roots.json` and `configuration.json` are preserved verbatim. The collector
also discovers and records the proxy's first code block, that block's hash,
the base token, base-token decimals and every implementation interval. A
repository address is not accepted until `eth_getCode` and the Comet getters
agree at the chosen chain boundary.

## What the ledger covers

The long-term capture covers every successful call frame to each registered
Comet proxy over a declared half-open block interval
`[from_block, to_block)`. It also preserves every log emitted by that proxy in
the interval. Coverage distinguishes read-only calls from state-changing calls
and counts both by selector.

The canonical credit ledger covers these debt effects:

- a borrow leg when an account's debt principal increases;
- a repayment leg when an account's debt principal decreases through a base
  supply or incoming base transfer;
- a liquidation debt-resolution leg when `absorb` removes debt; and
- both source and destination debt legs created by a base transfer.

Collateral supply, withdrawal, transfer and absorption remain canonical
position events in the Compound adapter, but they are not called borrowing or
repayment. `BuyCollateral`, reserve withdrawals, pauses, approvals, rewards
and configuration changes remain preserved native records with explicit
coverage counts. They do not become credit rows unless a later schema gives
them a precise family.

Interest accrual is not a new borrow. The adapter measures a credit action at
one accrued borrow index so that elapsed-time interest is not relabelled as
principal advanced by the borrower.

## Why logs are insufficient

The Comet interface declares `Supply`, `Withdraw`, base `Transfer`, collateral
events and absorption events. The implementation then splits each signed
principal transition internally. See
[`supplyBase`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/CometWithExtendedAssetList.sol#L754),
[`transferBase`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/CometWithExtendedAssetList.sol#L866),
and
[`withdrawBase`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/CometWithExtendedAssetList.sol#L976).

Three cases defeat a log-only adapter:

1. `Supply.amount` is the base token received. It does not state how much
   reduced debt and how much became positive supply.
2. `Withdraw.amount` is the base token sent. It does not state how much consumed
   positive supply and how much became new debt.
3. `transferBase` emits only the ERC-20-compatible mint or burn portions of
   positive supply. A transfer from a borrower to another borrower can increase
   one debt and reduce the other while emitting neither portion.

Pairing `Supply` or `Withdraw` with zero-address `Transfer` logs helps with
ordinary calls, but it cannot repair the third case or resolve several actions
for the same account inside one transaction. Logs are an independent
completeness check, not the sole source of credit semantics.

## Collection architecture

Collection and derivation have four stages. Every stage writes immutable,
digest-bound shards.
An interrupted stage resumes from its journal and never edits a completed
shard.

### 1. Registry

Create a versioned registry from the pinned Comet deployment tree. One entry
contains:

- registry commit, network name and chain ID;
- market slug and Comet proxy address;
- base-token address, symbol and decimals;
- first code block and block hash;
- proxy implementation address and code hash for each observed interval; and
- preserved `roots.json` and `configuration.json` digests.

Upgrades and configuration changes are evidence. The collector records them
rather than replacing the original market description with its current state.

### 2. Candidate enumeration

For each bounded block range, take the union of:

- all logs whose address is the Comet proxy; and
- all successful call frames whose destination is the Comet proxy.

The preferred call source is a tested `trace_filter` or per-block trace method
that includes nested calls. If it is unavailable, enumerate block transactions
and use `debug_traceTransaction`. Top-level transaction destination filtering
is insufficient because Bulker and other contracts call Comet internally.

The journal stores requested ranges, returned counts, provider identity,
method, request digest, response digest, attempt number and terminal status.
Ranges may be split to satisfy provider limits, but the union must equal the
declared release interval without gaps or overlap ambiguity.

### 3. Execution witness

For every candidate transaction, preserve:

- the block header, transaction and receipt;
- every Comet log with its original log index;
- the raw call trace, including call path, input, output, status and caller;
- the transaction's credit-relevant storage writes in execution order;
- the pre-transaction values needed to interpret those writes; and
- the implementation code hash and storage-layout version in force.

A transaction-wide pre/post state difference is not enough when the same
account changes more than once. The witness must allow the adapter to recover
the old and new signed principal for each successful Comet call frame. An EVM
struct-log trace plus the initial slot values can meet this requirement. A
client-specific state-difference tracer can be retained as a cross-check, but
it does not replace the ordered witness.

Capture full raw RPC responses before producing normalized witness records.
The normalization is versioned and reproducible from those bytes.

### 4. Offline derivation

The Tabularium adapter consumes only a verified Alexandria raw release. It
makes no RPC request. It validates the witness, replays the relevant Comet
principal transitions and writes deterministic canonical JSONL plus mapping
coverage.

The verifier repeats that work without network access or writes. It rejects a
missing range, duplicate call locator, unbound shard, implementation interval
gap, undecodable successful call, unexplained principal write, log mismatch or
canonical byte drift.

## Release layout

An Alexandria raw release is partitioned by chain, Comet proxy and block
interval. Its captured objects include at least:

```text
registry.json
capture.json
blocks.jsonl
transactions.jsonl
receipts.jsonl
logs.jsonl
traces.jsonl
storage-writes.jsonl
raw-coverage.json
```

The Tabularium derived release adds canonical `events.jsonl` and mapping
coverage without rewriting those raw objects. The first prototype keeps the
files uncompressed. Large releases may use
deterministic gzip shards with fixed headers after the same bytes can be
rebuilt on Linux and macOS. Each shard has a path, SHA-256 digest, byte count,
row count and first/last source locator in `capture.json`.

Git should hold code, schemas, fixtures, small examples and release manifests.
Bulk capture shards belong in a versioned object store. A release manifest
binds their content addresses; a mutable bucket listing is never the release.

Use one market per release. Split long histories into adjacent block epochs so
a failed or superseded interpretation does not require republishing the whole
venue. Epoch boundaries bind both block number and block hash. Do not set a
fixed range size until the Ethereum prototype measures trace volume and
verification memory.

## Canonical mapping

Compound III needs a new canonical event schema version. V1 is fixed to the
Goldfinch hosted-indexer entity, while v2 is already published for Euler and
cannot be widened in place. Phase 1 therefore adds schema v3, or the next
available version if another release lands first.

The Compound schema adds:

- `block.number`, `block.hash` and `transaction.index`;
- a source locator with call path, optional log index and deterministic leg
  index;
- `debt-resolution` and `collateral` families;
- venue-neutral provenance source kinds and mapping-rule strings;
- derived principal, index and rounding fields beside the token amount; and
- schema support for one native call producing several account legs.

For one account leg, let `p0` and `p1` be the signed principal immediately
before and after the action. Negative principal is debt. The versioned mapping
first separates the debt portions:

```text
old_debt_principal = max(0, -p0)
new_debt_principal = max(0, -p1)
borrow_principal   = max(0, new_debt_principal - old_debt_principal)
repay_principal    = max(0, old_debt_principal - new_debt_principal)
```

The adapter converts the old and new debt principal separately at the borrow
index used by that action, then takes the difference between those two
present-value amounts. This follows Comet's integer rounding more closely than
converting the principal delta once. It records the index, principal delta,
both present values, the resulting debt delta, the raw transferred amount when
one exists and any integer rounding remainder. The canonical
`amount.base_units` is the present-value debt delta, not the whole `Supply` or
`Withdraw` amount.

One call can have several accounting legs. A crossing-zero supply has repayment
and positive-supply portions; only the repayment portion enters the credit
ledger. A base transfer can yield a borrow row for `src` and a repayment row for
`dst`. Deterministic IDs use chain ID, Comet proxy, transaction hash, call path,
account role and leg index.

`AbsorbDebt` maps to `compound-v3.absorb-debt.v1` and the
`debt-resolution` family. It is not labelled voluntary repayment. Preserve the
matching `AbsorbCollateral` records, prices and reserve-funded amount beside
the debt leg.

## Compound coverage manifest

Coverage is declared for each release and for the registry as a whole. It
records:

- chain ID, proxy, registry version and block-number/hash boundaries;
- blocks expected and captured;
- call and log ranges requested, split and completed;
- successful, reverted and undecodable Comet call counts by selector;
- raw log counts by topic;
- canonical row counts by family and mapping rule;
- principal writes explained by a call and unexplained writes;
- transactions found by calls, by logs and by both;
- implementation and storage-layout intervals;
- provider, RPC method and normalized-capture versions; and
- every omitted native event family and known semantic gap.

Coverage fails closed. An unsupported successful state-changing selector, a
Comet log outside the candidate transaction set, a changed principal without an
explaining call, or a range with no terminal response prevents release
publication. Known read-only selectors are counted but do not need mapping
rules.

A separate registry report names markets and intervals not yet captured. It is
the only place where “all Compound III” may be assessed. One valid epoch must
not be presented as venue-wide coverage.

## Reorg and finality rules

Backfills stop at a configured finalized or chain-specific safe boundary. The
capture records the boundary tag, resolved number and hash. Before sealing an
epoch, refetch every boundary block and compare all stored block hashes.

If a hash changes before publication, discard the affected unsealed journal
entries and recollect from the last matching ancestor. If a published release
later falls off the canonical chain, do not rewrite it. Publish a superseding
release that names the orphaned block interval and its replacement.

The first prototype uses finalized Ethereum blocks. Each later chain needs its
own documented finality rule and reorg exercise before publication.

## Hinterlight's role

Wildcat's hosted-data work records Hinterlight as its only currently verified
archive, debug and trace source and describes it as roughly twelve low-power
nodes at one operator-hosted site. See the
[hosted-data gateway decision](https://github.com/wildcat-finance/mono/blob/a15d7af0eb34835739d0ba006cec2fd32cda7e00/kb/workstreams/hosted-data-gateway/README.md#L12-L20).

Use it for the Ethereum prototype if these exact calls pass a fixed acceptance
corpus:

- bounded historical `eth_getLogs`;
- old block, transaction and receipt reads;
- the selected call-trace method with nested Comet calls;
- the selected ordered storage-write trace;
- historical `eth_getStorageAt` for initial slot values; and
- repeated reads that return identical finalized results.

Hinterlight supplies RPC evidence. It does not supply Alexandria's registry,
journal, completeness accounting, object storage or raw-release verification,
nor Tabularium's canonical mapping. It is one operator and one physical site,
so it is not an independent confirmation source. Public Wildcat material
currently documents
the Ethereum endpoint and the operator's archive/debug/trace role; it does not
establish those capabilities for all ten Compound networks. Test each chain
separately.

A Compound subgraph on Hinterlight may accelerate queries and give an
independent transformation to compare. It cannot be the primary capture: a
log-driven subgraph inherits the silent-transfer gap, and any indexer remains a
reported boundary unless its source evidence is preserved.

## Infrastructure shape

Do not begin with a distributed service. The first slice needs:

- one resumable collector process;
- SQLite for range leases, attempts and shard state;
- a local content-addressed spool;
- Hinterlight's Ethereum RPC;
- an S3-compatible bucket for sealed raw shards; and
- Alexandria for collector policy, raw schemas, fixtures and small manifests;
  and
- Tabularium for the adapter, derived schemas and mapping fixtures.

Use a database server and multiple workers only after measurements show that
one process cannot keep the selected RPC lane busy or the journal cannot be
operated safely. The job model must already make that change possible: a lease
owns one chain, market and bounded range; sealing is atomic; retries produce new
attempt records; only one content digest becomes the accepted result.

Apply separate concurrency limits to logs, ordinary reads and debug/trace
methods. Trace responses are the cost and memory risk. Bound request ranges,
response bytes, decoded JSON depth, per-transaction trace bytes, retry count and
worker memory. Quarantine oversized or malformed responses instead of silently
dropping their transactions.

## Delivery plan

### Phase 0: method proof

Shipped. The release pins the Comet commit and 28-market registry, then records
one old and one recent Ethereum USDC transaction from Hinterlight. The corpus
passes archive, nested-call, ordered-storage and provider-reported finality
gates. Tabularium rebuilds two ordered Comet calls, eight relevant storage
writes and one signed-principal transition without network access.

The checked-in mined transaction does not exercise a borrower-to-borrower base
transfer. A synthetic hostile fixture proves the log-silent shape and refusal
rules, but it is not mined evidence. Finding and preserving the mined case is a
Phase 1 gate.

### Phase 1: Ethereum USDC specimen

Capture a small finalized interval around hand-picked supply, withdraw,
crossing-zero transfer and absorption cases. Include a mined
borrower-to-borrower transfer. Add a new canonical and coverage schema version,
the Compound adapter and hostile fixtures.

Exit when an offline rebuild is byte-identical and deliberate omissions,
reordering, unknown selectors, extra logs, altered block hashes and unexplained
principal writes all fail.

### Phase 2: full Ethereum USDC history

Discover the proxy's first code block, backfill adjacent epochs to a fixed
finalized boundary and publish the registry coverage report. Measure raw trace
bytes, compressed bytes, RPC time, verifier time and peak memory before choosing
the permanent epoch size.

Exit when every epoch verifies, boundaries join without gaps, totals reconcile
across epochs and a second collection of sampled epochs returns the same raw
facts.

### Phase 3: remaining Ethereum markets

Backfill USDS, USDT, WBTC, WETH and wstETH. Exercise every implementation and
storage-layout interval before sealing its first release.

Exit when all six pinned Ethereum market directories have explicit captured or
failed intervals in the registry report.

### Phase 4: other chains

Add one chain at a time after its RPC, trace semantics, receipt fields,
finality rule and reorg drill pass. A commercial archive provider can replace
or confirm Hinterlight where the chain is absent or an exact trace method
differs.

Exit when each of the 28 pinned production markets has a truthful coverage
state. “Failed” with the exact missing capability is preferable to an
incomplete release labelled complete.

### Phase 5: chain inclusion proof

The earlier phases bind releases to RPC-reported block hashes, receipts, traces
and state. They do not independently prove those facts came from the canonical
chain. A later proof-bearing capture may add block-header ancestry, receipt or
log inclusion proofs and account/storage proofs where the chain and client can
supply them.

This phase gets a new evidence class. It must not retroactively strengthen the
claims made by RPC-bound releases.

## Acceptance conditions

The Compound adapter is ready for a public specimen only when:

1. a pinned registry entry resolves to the expected proxy code and base-token
   configuration;
2. nested and top-level successful Comet calls are both enumerated;
3. every principal-changing call has ordered pre/post principal evidence;
4. supply, withdraw, transfer, crossing-zero and absorb fixtures map to the
   expected legs;
5. interest accrued before an action is not counted as new borrowing;
6. all raw logs and successful selectors appear in coverage;
7. the same frozen input produces byte-identical output twice;
8. verification runs offline and writes nothing;
9. tampered ranges, hashes, traces, storage writes, implementations and output
   bytes are refused; and
10. the release states that it proves internal consistency, not publisher
    identity, provider independence or canonical-chain inclusion.

## Deliberate exclusions

- Do not use Dune, a hosted subgraph or a dashboard export as the preservation
  source.
- Do not infer an address owner's identity.
- Do not turn the ledger into a counterparty score or claim that one repayment
  settled an account's full obligations.
- Do not commit a multi-gigabyte history to the skills repository.
- Do not call a logs-only or single-chain release “Compound III coverage”.
- Do not make the offline verifier depend on Hinterlight or any other network
  service.

## Questions the prototype must answer

The first implementation keeps these choices open until measured:

- Which Hinterlight trace method gives ordered storage writes with acceptable
  response size?
- Can call enumeration use `trace_filter` safely, or must every candidate block
  be debug-traced?
- What block epoch keeps raw shards and verifier memory within their bounds?
- Which second RPC source can reproduce a sample of Ethereum facts?
- Does deterministic gzip save enough storage to justify compressed release
  shards?
- Which non-Ethereum chain should follow Ethereum, based on available archive
  and trace methods rather than market count alone?

Answers become versioned collector policy. They are not assumptions hidden in
the first release.
