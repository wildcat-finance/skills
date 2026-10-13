# Decision: Give Wildcat withdrawal-batch events native meaning under adapter 1.0.0

## Status

Accepted, 2026-10-13. Numberless until the integration composer assigns it. It widens one sentence of ADR-111 and supersedes nothing.

## Context

Tabularium's Wildcat V1/V2 adapter decodes the four withdrawal-batch events, `WithdrawalBatchCreated(uint256)`, `WithdrawalBatchPayment(uint256,uint256,uint256)`, `WithdrawalBatchExpired(uint256,uint256,uint256,uint256)` and `WithdrawalBatchClosed(uint256)`, and gives each the disposition `unsupported-canonical-meaning`. The scaled-token burn the market emits beside every batch payment comes out as a `transfer` row nothing joins, so a consumer that may not read native logs has to quarantine every such transaction. Issue #2087 asked for native meaning for the four events and a same-transaction join between a payment and its burn.

The deployed source fixes the emission order. In both generations `_applyWithdrawalBatchPayment` is the only function that emits `Transfer(market, 0x0, normalizedAmountPaid)`, and it emits `WithdrawalBatchPayment(expiry, scaledAmountBurned, normalizedAmountPaid)` as the very next log. Created, expired and closed have no burn of their own. One transaction can carry several payments, including two for the same expiry, and two of them can carry equal amounts. ADR-111 binds Wildcat canonical events to native roles and units and says only `market-closed` admits an empty amount list. `verify` requires the current `ADAPTER_VERSION` on every release it rebuilds.

Laurence ruled on 2026-10-13 that a plain `repay` only returns funds to the market, that `normalizedAmountPaid` is an amount reserved for the batch and not lender receipt, spendable cash or execution, and that the adapter never infers a batch event's cause from the action sharing its transaction. Laurence confirmed the choices below the same day.

## Decision

Map the four batch events for both generations as `primary` rows with family `exit-queue`, party `pool` only, units `burned-scaled-claims` for `scaledAmountBurned`, `reserved-assets` for `normalizedAmountPaid` and `scaled-claims` for `scaledTotalAmount`, keep the `uint32` expiry as a decoded native field rather than a party, an amount or a row field, join each payment to the market-to-zero `Transfer` at the log index before it under the six-condition `adjacent-market-burn` rule, and extend the rule set under adapter `1.0.0` with four new `.v1` rules per generation.

The six conditions are the emission order of `_applyWithdrawalBatchPayment`: the log at `log_index - 1` is `Transfer(address,address,uint256)`, its emitter is the same market, `from` is the market, `to` is the zero address, the transaction hash is the same and `value` equals `normalizedAmountPaid`. Any failed condition leaves `attribution:withdrawal-batch-payment:burn` on the payment and `attribution:transfer:unclaimed-burn` on a market-to-zero transfer nothing claims; no join is guessed. Created, expired and closed carry no join. Created and closed carry no amounts, which widens ADR-111's empty-amount sentence from `market-closed` alone to those three actions.

## Alternatives

- **`unique-value-burn`**, the escrow companion key copied to the burn: same market and transaction, equal value, unique in both directions. Rejected because two payments in one transaction can carry equal amounts, which the source permits, and then neither joins; a reordered burn still joins. It failed `source-pairing-determinism` and `missing-or-ambiguous-stays-gap`.
- **`all-batch-events`**, the issue read literally: every batch event joins the nearest earlier burn. Rejected because one burn is claimed by its payment and again by the expired or closed event after it. It failed `source-pairing-determinism`, `single-claim` and `missing-or-ambiguous-stays-gap`.
- **`envelope-batch-field`**, the adjacent join plus a `batch` row field under `schema_version` 4. Rejected because every existing row changes, `verify` needs a fourth read path and every published release needs a superseding directory. It failed `schema-envelope-unchanged` and `existing-rows-unchanged`.
- **A bump of `ADAPTER_VERSION`.** Rejected because `verify` requires the current adapter version on every release it rebuilds, so a bump strands the two published Wildcat specimens; the released seventeen rules keep their bytes under `1.0.0`.
- **The expiry as a party or an amount.** Rejected because it is a `uint32` timestamp, not an address or a quantity; it stays in the decoded mapping record and in `native_record`.

## Consequences

Consumers of a `canonical-event-v3` Wildcat release, Probitas under #1926 first, read the four events as `primary` rows and follow a payment to its burn through the `join-inference` record on both rows. The join is one dictionary lookup per payment. A burn without an adjacent payment, a payment without an adjacent burn, a value mismatch or a reordered pair stays a named gap, so a consumer sees what could not be joined rather than a guessed pairing.

`reserved-assets` never reads as lender receipt, spendable cash or execution, and no row or document names a `repay`, `queue`, `execute` or `close` as a batch event's cause. Queue replay and unpaid-status projection stay with #1926, accounting replay with #1386 and function reconciliation with #1387. The schema 3 envelope does not change; the two published Wildcat specimens, the six Aave and Euler releases and schema 2 rebuild byte-identical; and the new rules carry their own `.v1` identifiers.
