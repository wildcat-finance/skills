## High — Fees consume value owed to underfunded open batches

**Location:** `plugins/pandects/specimens/FeeFromQueued.sol:L35-L41`

`accrueFee` caps the fee at `claims - reserved`, but `reserved` represents only the amount earmarked for payment, not the total amount owed by open batches. When open-batch obligations exceed their earmark, the allegedly “available” value remains promised to claimants. Moving it from `claims` to `fees` therefore increases the claims shortfall without reducing any claimant’s recorded entitlement.

Ordered counterexample:

1. `claims = 60`, `reserved = 40`, and open batches are owed `100`.
2. Call `accrueFee(20)` and assume `bounded(20) = 20`.
3. Line 35 computes `available = 20`.
4. Lines 40–41 produce `claims = 40` and increase `fees` by `20`.
5. Open batches remain owed `100`, so their aggregate shortfall grows from `40` to `60`.

Accounting conservation and `reserved <= claims` can remain satisfied: value is merely reclassified from claimant backing to fees. Individual owed and paid records also need not change. Consequently, ordinary balance, reserve, queue-ordering, and per-claim invariants may not detect the loss. The impact is systematic extraction from already undercollateralized claimants, widening precisely with the portion of queued obligations that could not be earmarked.

**Smallest fix:** compute fee availability against the full amount owed by all open batches, as the excerpt says the reference implementation does, rather than against `reserved`. In equivalent terms, fees must be capped at:

```solidity
claims > openBatchesOwed ? claims - openBatchesOwed : 0
```

using the actual inherited accounting expression for `openBatchesOwed`.

The excerpt does not provide `Sound.sol`, so the exact field or helper representing aggregate open-batch obligations cannot be identified. It also does not establish the behavior of `bounded`, caller authorization, or whether inherited code imposes additional restrictions; no separate finding about those matters is supportable from the supplied bytes.