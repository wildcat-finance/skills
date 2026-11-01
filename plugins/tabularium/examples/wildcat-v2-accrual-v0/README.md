# Constructed Wildcat V2 accrual specimen

This unsigned fixture exercises `InterestAndFeesAccrued` and `StateUpdated` of
the deployed V2 market ABI. Every log and value is synthetic, and the logs
follow the emission order of the pinned V2 market source. The specimen
establishes no historical activity, runtime equivalence, independent finality,
interest or accounting replay, delinquency history or borrower identity.

## Fixture scope

`release/` holds 10 canonical rows from 10 native logs in three transactions of
one block. Each transaction is an `updateState` call: `_getUpdatedState` emits
any accrual before `_writeState` emits `StateUpdated`.

1. The first market processes a batch that expired at 1500. It accrues from
   1000 to 1500, emits the batch burn, payment, expiry and closure, accrues
   from 1500 to 2000, then writes its state.
2. That market writes its state again at 2000. No time has elapsed, so
   `StateUpdated` appears with no accrual.
3. A second market accrues from 1000 to 2000, then writes its state.

Three rows are accruals and three are state writes. The batch burn, payment,
expiry and closure make the other four; the payment joins its burn under
`adjacent-market-burn`. `isDelinquent` is false in the first market's two
state writes and true in the second market's.

The first market's context declares its asset, so its two `protocol-fees`
amounts name it. The second market's context declares no asset, so its
`protocol-fees` amount stays null and its row carries
`attribution:interest-and-fees-accrued:asset`. `coverage.json` counts the
mapped rows under `included_events` and the actor and asset gaps under
`unsupported_events`.

`scale-factor`, `base-interest-ray` and `delinquency-fee-ray` are decoded ray
values with no asset and no conversion. `protocol-fees` is the decoded fee in
underlying base units, accrued and not collected or paid. The two timestamps
and `isDelinquent` stay in the decoded record and `native_record`. No accrual or
state row joins another event or names one as its cause, and no row equates
the scale factor in the two events. The values are round constructed numbers,
not results of the market's interest formula.

## Rebuild

From the repository root:

```bash
python3 plugins/tabularium/examples/wildcat-v2-accrual-v0/rebuild.py
python3 plugins/tabularium/scripts/tabularium.py verify plugins/tabularium/examples/wildcat-v2-accrual-v0/release/coverage.json
```

The builder ingests the synthetic logs through the native Alexandria raw-release
API in a fresh temporary directory and builds with `wildcat-canonical`. It
compares every release file with this fixture and
[expected.json](expected.json), moves the complete root, removes the disposable
original input and verifies the moved root offline. It changes no public file.

## Consumer boundary

Keep the complete root together, including `source/raw-release/`. The
[Wildcat V2 data dictionary](../wildcat-v2-v0/DATA-DICTIONARY.md) describes the
shared release files; the [mapping guide](../../docs/wildcat-canonical.md) gives
the two meanings, their units and the refusal rules. On a mismatch, preserve
the published fixture and rebuild in a fresh directory.

The release has declared constructed context and the `constructed-fixture`
scope. Its declared wrapper context emits no log here. It supplies no
delinquency projection, settlement, canonical-chain proof or address-to-person
link. `isDelinquent` does not establish when delinquency began, a penalty or
current standing.
