# Data dictionary: Aave v4 mainnet credit window v0

Every field in `events.jsonl`, and what each one is derived from. The
consensus log it came from is retained verbatim in `native_record`, so nothing
here replaces the source.

## Canonical event, schema v2

Every row carries exactly these twelve top-level fields: `action`, `amounts`, `chain`, `event_family`, `id`, `instrument`, `native_record`, `parties`, `provenance`, `schema_version`, `transaction`, `venue`. Any other field, or a missing one, is refused.

| Field | Value in this release | Derived from |
| --- | --- | --- |
| `schema_version` | `2` | fixed |
| `id` | `tabularium:ethereum-mainnet:aave-v4:<txHash>:<logIndex>:<rule>` | `transactionHash`, `logIndex`, mapping rule |
| `event_family` | `borrowing` or `repayment` | `topics[0]` |
| `action` | `aave-v4.borrow` or `aave-v4.repay` | `topics[0]` |
| `venue` | `aave-v4` | adapter |
| `chain` | `ethereum-mainnet` | adapter |
| `transaction.hash` | transaction hash | `transactionHash` |
| `transaction.block_number` | integer block height | `blockNumber` |
| `transaction.block_hash` | block hash | `blockHash` |
| `transaction.transaction_index` | integer index in the block | `transactionIndex` |
| `transaction.log_index` | integer log index | `logIndex` |
| `transaction.timestamp` | unix seconds, as a decimal string | `blockTimestamp` |
| `parties[].role` | `borrower`, and `caller` when it differs | `topics[2]`, `topics[3]` |
| `instrument.type` | `aave-v4-spoke` | fixed |
| `instrument.id` | spoke address | the log's `address` |
| `amounts` | see below | data words plus the supporting reads |
| `provenance.*` | see below | capture manifest, adapter and supporting reads |
| `native_record` | the consensus log, unchanged | `eth_getLogs` entry |

## Log layout

Both topics carry four topics. The indexed parameters are the asset id, the
user and the caller.

| Position | BORROW | REPAY |
| --- | --- | --- |
| `topics[0]` | `0xef181747…` | `0xd765a026…` |
| `topics[1]` | asset id | asset id |
| `topics[2]` | user | user |
| `topics[3]` | caller | caller |
| data word 0 | shares | shares |
| data word 1 | assets drawn | total assets repaid |
| data words 2 to 4 | not present | present, not established |

A borrow states two data words and a repay five. The final three repay words
were zero in every preserved log, so this release does not name them and the
adapter never reads them. A log whose word count disagrees with its topic is
refused.

## Amount legs

| `topics[0]` | `kind` | `base_units` | `asset` |
| --- | --- | --- | --- |
| BORROW | `assets_drawn` | data word 1 | underlying token address |
| BORROW | `shares` | data word 0 | `null` |
| REPAY | `assets_repaid` | data word 1 | underlying token address |
| REPAY | `shares` | data word 0 | `null` |

The asset leg names the token that `getReserve(assetId)` reported for that
spoke. The share leg names no asset, because shares are the spoke's own
accounting unit rather than a token.

## Resolving the asset

A log names a spoke and an asset id, never a token. `source.json` preserves
the reads that close that gap, and the adapter refuses any log whose reserve
was not read:

| Read | Purpose | Count |
| --- | --- | --- |
| `getReserve(uint256)` on the spoke | word 0 is the underlying, word 1 the owning hub | 35 |
| `symbol()` on the underlying | token symbol | 10 |
| `decimals()` on the underlying | token decimals | 10 |

Each record keeps the exact call parameters and the returned bytes. The
adapter checks its convenience fields against those bytes and refuses a
disagreement, so the recorded result stays the authority.

## Provenance

| Field | Value |
| --- | --- |
| `source_kind` | `consensus-log` |
| `source_contract` | spoke address |
| `source_entity` | `logs` |
| `source_id` | `<txHash>:<logIndex>` |
| `source_selector` | `eth_getLogs[transactionHash=…,logIndex=…]` |
| `supporting_selectors` | the `getReserve`, `symbol` and `decimals` calls this event depended on |
| `mapping_rule` | `aave-v4.borrow.v2` or `aave-v4.repay.v2` |
| `adapter` / `adapter_version` | `aave-v4` / `2.0.0` |
| `protocol_generation` | `aave-v4` |
| `source_api` | `ethereum-json-rpc` |

## Scope

The capture is a topic pair over a block range, so there is no unmapped
remainder inside it: `unsupported_events` is empty. Supply, withdraw and
collateral-flag activity is outside the captured topics and is neither
preserved nor counted.

One block reporting two different hashes, a duplicate log selector, or a log
outside the declared window is refused rather than mapped.
