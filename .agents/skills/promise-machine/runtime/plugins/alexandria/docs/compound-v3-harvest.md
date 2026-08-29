# Compound v3 harvest specification

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now pins the Comet registry and preserves one verified Ethereum execution witness; a resumable, reconciled Ethereum USDC interval harvester remains unimplemented.
<!-- marketplace-context:end -->

This is the production collection plan for Compound v3. Phase 0 now ships a
bounded network capture and checked-in method-proof release; it is not the
resumable interval harvester specified below and it does not register a
Compound mapping. A production harvester should preserve the RPC responses and
scope receipts described here as an Alexandria raw release. A separate,
reviewed mapping would turn that release into credit events and position
observations.

## Registry pin

The registry source is the official
[`compound-finance/comet`](https://github.com/compound-finance/comet) repository,
pinned to commit
[`f766f51583c23acc33b2a7824654ef2029a96804`](https://github.com/compound-finance/comet/commit/f766f51583c23acc33b2a7824654ef2029a96804).
The pin contains 28 production Comets across 10 chains. The canonical market
root is each production deployment's `roots.json`; the address named `comet`
is the stable proxy. The pinned
[`hardhat.config.ts`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/hardhat.config.ts#L125-L179)
supplies the network and chain identifiers. Compound's
[`deployments/`](https://github.com/compound-finance/comet/tree/f766f51583c23acc33b2a7824654ef2029a96804/deployments)
tree is the registry; the generated tables on
[`docs.compound.finance`](https://docs.compound.finance/) are a useful dated
view, not a replacement for the pinned files.

| Chain | Chain ID | Deployment names |
| --- | ---: | --- |
| Ethereum | `eip155:1` | `usdc`, `usds`, `usdt`, `wbtc`, `weth`, `wsteth` |
| Optimism | `eip155:10` | `usdc`, `usdt`, `weth` |
| Polygon | `eip155:137` | `usdc`, `usdt` |
| Unichain | `eip155:130` | `usdc`, `weth` |
| Ronin | `eip155:2020` | `weth`, `wron` |
| Mantle | `eip155:5000` | `usde` |
| Base | `eip155:8453` | `aero`, `usdbc`, `usdc`, `usds`, `weth` |
| Arbitrum | `eip155:42161` | `usdc.e`, `usdc`, `usdt`, `weth` |
| Linea | `eip155:59144` | `usdc`, `weth` |
| Scroll | `eip155:534352` | `usdc` |

Testnet entries shown on an older documentation snapshot are outside this
registry pin. A later production registry change requires a new pin and a new
capture plan; it must not silently change an existing release.

## Market and implementation epochs

For every market, preserve the pinned `roots.json`, `configuration.json`,
`deploy.ts` and `relations.ts` bytes. Those files establish declared roots and
build context. They do not establish the active configuration or implementation
at an arbitrary historical block.

Start-block discovery uses chain evidence. Find the proxy's first relevant
transaction or `Upgraded(address)` log, record its block number and hash, and
refuse the market when a start boundary cannot be established. Enumerate every
proxy `Upgraded(address)` log, then read the EIP-1967 implementation slot at
each boundary. Compound's pinned
[`ERC1967Upgrade.sol`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/vendor/proxy/ERC1967/ERC1967Upgrade.sol)
defines that event and slot, while
[`CometProxyAdmin.sol`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/CometProxyAdmin.sol)
shows the deploy-and-upgrade path. The pinned
[`relations.ts`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/deployments/relations.ts)
uses the same implementation slot. Each epoch records:

- chain, deployment name and proxy address;
- inclusive start and end block numbers and hashes;
- upgrade transaction and log coordinates;
- implementation address and runtime bytecode hash;
- ABI and storage-layout source commit;
- Configurator address, factory and configuration reads at the observation
  block; and
- any unsupported or unreconciled boundary as a coverage gap.

[`CometExt.version()`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/CometExt.sol#L9-L10)
is not an implementation identity: the pinned source returns the constant
string `0`. Historic epochs may predate
[`CometWithExtendedAssetList`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/CometWithExtendedAssetList.sol),
so current source cannot be assigned to old runtime bytecode without a matching
code hash. Unknown epochs remain raw and unsupported.

## Raw components

One capture may contain several components, all preserved byte-for-byte:

1. the pinned registry files and a registry enumeration receipt;
2. `eth_getBlockByNumber` responses for every range boundary and every block
   containing a relevant transaction, including its ordered transaction list;
3. proxy upgrade logs and EIP-1967 implementation reads;
4. Comet event log responses, retaining the complete JSON-RPC envelope;
5. transaction envelopes and receipts for every direct or internal proxy call;
6. ordered execution traces and the pre-transaction storage needed to replay
   every successful base action under the active implementation;
7. state-call responses at declared observation blocks;
8. implementation runtime bytecode and its digest;
9. provider reconciliation and finality receipts; and
10. error receipts for every failed, truncated or disputed request.

The capture plan names the provider class but contains no endpoint credential.
Raw files retain provider ordering and formatting. Derived code may parse them;
ingestion must not rewrite them.

## Events and observations

Request every log emitted by the proxy address without a topic filter. Retain
unknown topics as raw records and mark them unsupported until a code-hash-bound
ABI and mapping revision explains them. The known interpretation set comes
from the pinned
[`CometInterface.sol`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/CometInterface.sol)
and
[`CometMainInterface.sol`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/CometMainInterface.sol).
It includes these families:

- base activity: `Supply`, `Withdraw` and ERC-20-style `Transfer`;
- collateral activity: `SupplyCollateral`, `WithdrawCollateral` and
  `TransferCollateral`;
- liquidation: `AbsorbDebt` and every associated `AbsorbCollateral`;
- protocol inventory: `BuyCollateral` and `WithdrawReserves`; and
- configuration context: `PauseAction` and implementation upgrades.

Rewards claims may be retained as context but are not credit events.

At each periodic or release-end observation block, call `baseToken`,
`baseScale`, `numAssets`, `getAssetInfo`, `totalsBasic`, `userBasic`,
`balanceOf`, `borrowBalanceOf`, `collateralBalanceOf`, `isLiquidatable` and
`getReserves` where the epoch supports them. Preserve the block tag, returned
bytes, ABI selector and call target. The
[`Configurator`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/Configurator.sol)
supplies configuration context, not proof of the configuration at another
block.

Compound represents base supply and borrowing as one signed principal. A
`Supply` may repay debt, add supplied balance, or cross zero and do both. A
`Withdraw` may remove supplied balance, create debt, or cross zero. An internal
base transfer may borrow from the sender and repay or supply for the receiver.
The pinned
[`CometWithExtendedAssetList`](https://github.com/compound-finance/comet/blob/f766f51583c23acc33b2a7824654ef2029a96804/contracts/CometWithExtendedAssetList.sol#L866-L902)
emits only the supply-token mint or burn portions of that transfer; a debt-only
transfer has no corresponding `Transfer(src,dst,amount)` log. Log scanning
alone therefore cannot enumerate the credit record.

The harvester must inspect every transaction in each block for direct or
internal calls to the proxy. For each relevant transaction it preserves the
transaction and receipt, an ordered call trace with input, caller, target,
success and nested call order, and enough pre-transaction storage or opcode
trace to recover `userBasic.principal`, the active supply and borrow indexes
and their successive writes. The mapping replays successful base actions in
call order under the code-hash-bound implementation before emitting borrow or
repayment legs. A provider trace that omits an internal call, hides the
necessary storage transition or cannot be reconciled leaves the affected
transaction unsupported. The mapping must not infer the whole event amount
from its topic name or treat missing logs as no activity.

`AbsorbDebt` records protocol reserves settling absorbed debt, not a
borrower-funded repayment. Keep its borrower and the same absorption's
collateral legs together. `BuyCollateral` is a later sale of protocol inventory
and does not identify the absorbed borrower.

## Ranges, checkpoints and reorgs

No Compound source defines finality depths or RPC chunk sizes for these chains.
Those are Alexandria operator policy, recorded rather than attributed to the
protocol.

For each chain and market:

1. resolve the proposed end tag under a named chain policy (`finalized`, `safe`
   or a stated confirmation rule), then bind its block number and hash;
2. obtain the start and end block from two independent providers;
3. reject a hash mismatch or record the range as failed;
4. request logs and scan ordered block transactions in bounded ranges,
   reducing the range after provider errors and never accepting a response
   marked truncated;
5. trace every discovered direct or internal proxy call and bind it to its
   transaction, receipt and containing block;
6. checkpoint only after raw response bytes have been fsynced and digested; and
7. on resume, re-read the last accepted boundary hash and rewind to the last
   matching checkpoint after a reorg.

A checkpoint records chain, proxy, epoch, next block, previous accepted block
and hash, request parameters, response byte count, record count and SHA-256.
It is working state, not release truth. The release manifest records the final
contiguous ranges and all gaps. Adjacent chunks must have neither a missing nor
overlapping block, unless an overlap is deliberately deduplicated by
transaction hash and log index and recorded in the receipt.

## Provider reconciliation and errors

Run the completed range against a second provider. Compare boundary hashes,
ordered block transaction hashes, receipts, the identity tuple `(blockHash,
transactionHash, logIndex, address, topics, data)` for every log and the
normalized call and storage transitions used by the mapper. A disagreement is
not decided by majority or by which endpoint answered first. Preserve both
responses, emit an error receipt and mark the disputed interval partial or
failed.

An error receipt includes the sanitized request, provider class, attempt time,
HTTP or JSON-RPC status, response digest, retry decisions and unresolved block
range. Timeouts, result-size limits, malformed envelopes, duplicate identities,
removed logs, block-hash changes, unknown implementations and failed state
calls each have distinct codes. Retrying does not erase the earlier receipt.

## Release shape

Use one capture per chain, proxy and implementation epoch. Coverage names the
deployment, exact block interval, finality class, captured event collections,
state-call collection, unsupported families and every gap. Components name the
registry, logs, boundary blocks, implementation evidence, observations,
reconciliation and errors separately so a consumer can accept one evidence
class without accepting another.

A future mapping revision must put the proxy, implementation code hash, epoch,
transaction/log coordinates, source component digest and JSON selector on
every derived row. Position observations also name their block hash and call
selector. The mapping remains venue-qualified as `compound-v3`; Alexandria
does not convert it into a claim of default, complete repayment or current
balance.

## Acceptance

A production release is accepted only when:

- all 28 registry entries at the pin are captured or named as gaps;
- every accepted market has hash-bound start and end blocks;
- implementation epochs are contiguous and code-hash-bound;
- every requested RPC object has a digest or an error receipt;
- primary and reconciliation providers agree on boundary hashes and ordered
  log identities;
- log identities are unique and every log falls inside the declared proxy,
  epoch and block interval;
- unknown proxy topics remain in the raw release and in unsupported coverage;
- observation calls name their block hash, target, selector and raw result;
- every successful direct or internal proxy call is represented by an ordered
  transaction trace, or its transaction is an explicit mapping gap;
- release ingestion and offline verification pass twice with identical truth
  bytes; and
- derivation refuses unknown epochs and supplies exact selector provenance for
  every supported row.

These checks establish a reproducible, source-bound capture. They do not prove
publisher identity, independent chain finality or the completeness of either
provider.
