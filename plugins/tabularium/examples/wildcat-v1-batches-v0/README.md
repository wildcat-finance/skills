# Constructed Wildcat V1 batch specimen

This unsigned fixture exercises the four withdrawal-batch events of the deployed
V1 market ABI and the `adjacent-market-burn` join. Every log is synthetic and
follows the emission order of the pinned V1 market source. The specimen
establishes no historical activity, runtime equivalence, independent finality,
lender receipt or borrower identity.

## Fixture scope

`release/` holds 33 canonical rows from 33 native logs in nine transactions of
one block. Four source-order transactions cover the queue path, in which the
queue transfer precedes `WithdrawalBatchCreated`; two payments to one expiry in
one transaction; expiry processing followed by closure; and a repayment that
pays two unpaid batches equal amounts. Seven of the ten payments join their
burn. Five hostile transactions leave named gaps. A burn after its payment, a
burn with another value, a burn without a payment and a payment without a burn
leave no join; two burns before one payment join the payment to the adjacent
burn and leave the earlier burn unclaimed. `coverage.json` counts the mapped
batch rows under `included_events` and the three payment burn gaps and four
unclaimed burns under `unsupported_events`.

`reserved-assets` is `normalizedAmountPaid`: underlying units set aside in the
market for the batch. It is not lender receipt, spendable cash or execution.
No batch row names the queue, repayment or closure sharing its transaction as
its cause. V1 `closeMarket` emits no batch event, so the specimen carries none.

## Rebuild

From the repository root:

```bash
python3 plugins/tabularium/examples/wildcat-v1-batches-v0/rebuild.py
python3 plugins/tabularium/scripts/tabularium.py verify plugins/tabularium/examples/wildcat-v1-batches-v0/release/coverage.json
```

The builder ingests the synthetic logs through the native Alexandria raw-release
API in a fresh temporary directory and builds with `wildcat-canonical`. It
compares every release file with this fixture and
[expected.json](expected.json), moves the complete root, removes the disposable
original input and verifies the moved root offline. It changes no public file.

## Consumer boundary

Keep the complete root together, including `source/raw-release/`. The
[Wildcat V1 data dictionary](../wildcat-v1-v0/DATA-DICTIONARY.md) describes the
shared release files; the [mapping guide](../../docs/wildcat-canonical.md) gives
the four batch meanings, the join rule and the refusal rules. On a mismatch,
preserve the published fixture and rebuild in a fresh directory.

The release has declared constructed context and the `constructed-fixture`
scope. It supplies no queue replay, unpaid-batch status, accounting replay,
settlement, canonical-chain proof or address-to-person link.
