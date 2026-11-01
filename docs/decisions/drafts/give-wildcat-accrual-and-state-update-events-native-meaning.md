# Decision: Give Wildcat accrual and state-update events native meaning under adapter 1.0.0

## Status

Accepted, 2026-11-01, as the only candidate that passed all five selection gates behind the #2088 design lock; the two selection metrics, `field-reads` and `new-row-bytes`, did not decide it. Numberless until the integration composer assigns it. It adds rules to the set ADR-111 and ADR-125 govern and supersedes nothing.

## Context

Tabularium's Wildcat V1/V2 adapter decodes `InterestAndFeesAccrued(uint256,uint256,uint256,uint256,uint256,uint256)` and `StateUpdated(uint256,bool)` and gives both the disposition `unsupported-canonical-meaning`. The accrual fields and the `isDelinquent` flag never reach `canonical-event-v3`, so a consumer that may not read native logs has to quarantine both events. Issue #2088 asked for native meaning in both generations, with the market as party, each numeric field under its ABI name in its native unit, and the two timestamps and `isDelinquent` as native state.

The deployed source fixes each field. `_getUpdatedState` emits `InterestAndFeesAccrued` for an interval from the stored `lastInterestAccruedTimestamp` to an expired pending batch's expiry or to `block.timestamp`, both in seconds. `scaleFactor` is `MarketState.scaleFactor` after the update, a ray value. `FeeMath.updateScaleFactorAndFees` documents `baseInterestRay` and `delinquencyFeeRay` as ray values and `protocolFee` as a normalized token amount: underlying-asset base units accrued over the interval. Collection is the separate `FeesCollected` path. `_writeState` sets `isDelinquent = liquidityRequired() > totalAssets()` and emits `StateUpdated(state.scaleFactor, isDelinquent)`. `MarketClosed` already keeps its timestamp as decoded native state on a `pool` row. ADR-111 binds Wildcat canonical events to native roles and units, and `verify` requires the current `ADAPTER_VERSION` on every release it rebuilds.

Laurence's #2087 rulings carry over: the adapter maps native meaning only and never infers an event's cause from another event in its transaction.

## Decision

Map both events for both generations as `primary` rows from the market emitter role, with party `pool` only:

- `interest-and-fees-accrued`, family `interest-accrual`, with amounts in the declared field order `scale-factor`, `base-interest-ray`, `delinquency-fee-ray`, `protocol-fees`. The three ray amounts are assetless. `protocol-fees` carries the underlying asset, or null with the gap `attribution:interest-and-fees-accrued:asset` when the context does not establish it. Every row carries `attribution:interest-and-fees-accrued:actor`.
- `state-updated`, family `pool-state`, with one assetless `scale-factor` amount and the gap `attribution:state-updated:actor`.

Each amount `kind` is the ABI field name in the adapter's kebab-case vocabulary, and `base_units` is the exact decoded decimal string with no unit conversion. `fromTimestamp`, `toTimestamp` and `isDelinquent` stay in the decoded mapping record and in `native_record`, never in an amount, a party or a row field. Each rule declares its field order, so a pinned definition whose field names or order differ refuses. A `StateUpdated` boolean word other than zero or one refuses, as does a truncated accrual log, and a log from an unpinned source commit stays `unsupported-decode`. The rules `wildcat-v1.interest-and-fees-accrued.v1`, `wildcat-v1.state-updated.v1`, `wildcat-v2.interest-and-fees-accrued.v1` and `wildcat-v2.state-updated.v1` join the set under adapter `1.0.0`, which grows from twenty-five rules to twenty-nine.

## Alternatives

- **`unit-named-amounts`**, kinds that name only the unit: `ray` for the three ray fields and `assets` for `protocolFees`. Rejected because one row then carries three `ray` kinds that only their order tells apart, and `assets` makes an accrued fee read like the asset movements `deposit` and `borrow` carry. It failed `numeric-fields-carried` and `kinds-distinct`.
- **`native-state-only`**, both events with empty `amounts` and every field decoded. Rejected because the numeric fields never reach the canonical row, which is what the issue asked to end. It failed `numeric-fields-carried`.
- **`envelope-native-state`**, ABI-named amounts plus a `native_state` row field under `schema_version` 4. Rejected because every existing row changes, `verify` needs a fourth read path and every published release needs a superseding directory. It failed `schema-envelope-unchanged` and `existing-rows-unchanged`.
- **A bump of `ADAPTER_VERSION`.** Rejected because `verify` requires the current adapter version on every release it rebuilds, so a bump strands every published Wildcat specimen; the released twenty-five rules keep their bytes under `1.0.0`.
- **The timestamps or `isDelinquent` as amounts or a party.** Rejected because they are native state, not quantities or addresses, as `MarketClosed` keeps its timestamp.

## Consequences

Consumers of a `canonical-event-v3` Wildcat release read both events as `primary` rows. Three of the accrual row's amounts are ray ratios rather than asset quantities, so a consumer that sums every amount must filter by kind. `protocol-fees` is accrued, not collected or paid. `isDelinquent` does not establish when delinquency began, a penalty or current standing, and the archive view still refuses to read delinquency entry from the flag alone. No row asserts that the two events' `scale-factor` amounts in one transaction are equal, and no row joins the two.

Accrual and interest replay stay with #1386 and function reconciliation with #1387. The schema 3 envelope does not change: each new action gets its own branch, and the mapping-rule enums in both schemas grow from thirty-six values to forty. The two published Wildcat specimens, #2087's batch specimens, the six Aave and Euler releases and schema 2 rebuild byte-identical.
