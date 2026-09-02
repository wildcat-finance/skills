# Data dictionary: Aave v4 mainnet credit window v0

Every field in `events.jsonl`, and what each one is derived from. The venue
row it came from is retained verbatim in `native_record`, so nothing here
replaces the source.

## Canonical event, schema v2

Every row carries exactly these twelve top-level fields: `action`, `amounts`, `chain`, `event_family`, `id`, `instrument`, `native_record`, `parties`, `provenance`, `schema_version`, `transaction`, `venue`. Any other field, or a missing one, is refused.

| Field | Value in this release | Derived from |
| --- | --- | --- |
| `schema_version` | `2` | fixed |
| `id` | `tabularium:ethereum-mainnet:aave-v4:<txHash>:<logIndex>:<rule>` | `txHash`, `logIndex`, mapping rule |
| `event_family` | `borrowing` or `repayment` | activity `type` |
| `action` | `aave-v4.borrow` or `aave-v4.repay` | activity `type` |
| `venue` | `aave-v4` | adapter |
| `chain` | `ethereum-mainnet` | adapter |
| `transaction.hash` | transaction hash | `txHash` |
| `transaction.block_number` | integer block height | `block` |
| `transaction.block_hash` | `null` | not reported by the source |
| `transaction.transaction_index` | `null` | not reported by the source |
| `transaction.log_index` | integer log index | `logIndex` |
| `transaction.timestamp` | unix seconds, as a decimal string | `timestamp` |
| `parties[].role` | `borrower`, and `caller` when it differs | `user.id`, `caller` |
| `instrument.type` | `aave-v4-spoke` | fixed |
| `instrument.id` | spoke address | `spoke.id` |
| `amounts` | see below | `amount`, `totalAmountRepaid`, `shares` |
| `provenance.*` | see below | capture manifest and adapter |
| `native_record` | the venue row, unchanged | `useractivities` row |

## Amount legs

Aave v4 reports a share balance alongside the asset movement, and the two
activity types populate different asset fields.

| `type` | `kind` | `base_units` | `asset` |
| --- | --- | --- | --- |
| `BORROW` | `assets_drawn` | `amount` | `null` |
| `BORROW` | `shares` | `shares` | `null` |
| `REPAY` | `assets_repaid` | `totalAmountRepaid` | `null` |
| `REPAY` | `shares` | `shares` | `null` |

`asset` is `null` throughout. The rows name a `reserve` — the spoke address
with the asset id appended — but never the underlying token, and resolving it
across hubs by asset id could misattribute, so the adapter states nothing.
The reserve identifier is preserved in `native_record`.

A `BORROW` carrying a repaid total, or a `REPAY` carrying a drawn amount, is
refused rather than mapped.

## Provenance

| Field | Value |
| --- | --- |
| `source_kind` | `the-graph-entity` |
| `source_contract` | spoke address |
| `source_entity` | `useractivities` |
| `source_id` | the venue row `id` |
| `source_selector` | `useractivities[id=<id>]` |
| `supporting_selectors` | `[]` — no second collection was read |
| `mapping_rule` | `aave-v4.borrow.v1` or `aave-v4.repay.v1` |
| `adapter` / `adapter_version` | `aave-v4` / `1.0.0` |
| `protocol_generation` | `aave-v4` |
| `source_api` | `the-graph` |

## Preserved but unmapped

Counted in `coverage.json` under `unsupported_events` and never mapped,
because they move liquidity or a collateral flag rather than debt:
`SUPPLY` (376), `WITHDRAW` (264), `SET_COLLATERAL` (111).

An activity `type` outside the five this release declares is refused, so a
later capture cannot silently widen the mapped set.
