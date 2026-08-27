# The catalogue

Pandects supplies executable laws for credit contracts, each paired with a
deliberately broken specimen and a reduced counterexample. Use Fizz to generate
a protocol-specific harness. The corpus holds ten laws; broader families remain in
the planning specification.

Ten laws in three families, rendered for a reader. The catalogue itself is
`catalogue/pandects.json`, and a test fails if this document and that file stop
naming the same laws, so this is a rendering rather than a second source.

Regenerate it with `python3 scripts/pandects.py render`. Editing it by hand is
how a rendering becomes a second source.

Every law here has six parts. It executes, it catches a contract written to
break it, that failure has been reduced to a replay with no fuzzer in it, it
says where it applies, its bounds are justified, and it judges rather than
reverting. `python3 scripts/pandects.py check` refuses anything with fewer.

## Conservation

What the system holds, owes and has promised, held against each other.
Every one of these is a fact about a single state: the sums agree or they do
not, and no history is needed to say which.

### `conservation/value-conserved/v1`

> Assets held plus debt owed equals lender claims plus accrued fees.

| | |
| --- | --- |
| Component | `src/laws/ValueConserved.sol` |
| Specimen | `specimens/MintedClaims.sol` |
| Counterexample | `test/counterexamples/Conservation.t.sol` |
| Bounds | exact |
| Reads | `totalAssets`, `totalDebt`, `totalLenderClaims`, `accruedFees` |

Applies to a pooled lender claim denominated in one asset, where borrowers owe that same asset and fees accrue out of lender yield. Assuming:

- every quantity is denominated in the asset the system reports
- a written-down debt is written down against claims in the same state transition
- collateral posted by borrowers, if any, is not counted in assets held

### `conservation/reserves-backed-by-claims/v1`

> Assets reserved never exceed the lender claims recorded.

| | |
| --- | --- |
| Component | `src/laws/ReservesBackedByClaims.sol` |
| Specimen | `specimens/OverReserved.sol` |
| Counterexample | `test/counterexamples/Conservation.t.sol` |
| Bounds | exact |
| Reads | `reservedAssets`, `totalLenderClaims` |

Applies to a system that earmarks held assets against recorded withdrawal claims. Assuming:

- a reservation is made against a claim that has been recorded
- a system with no withdrawal queue reports zero reserved

### `conservation/held-assets-partitioned/v1`

> Reserved assets plus borrowable assets never exceed assets held.

| | |
| --- | --- |
| Component | `src/laws/HeldAssetsPartitioned.sol` |
| Specimen | `specimens/OverPromised.sol` |
| Counterexample | `test/counterexamples/Conservation.t.sol` |
| Bounds | exact |
| Reads | `reservedAssets`, `borrowableAssets`, `totalAssets` |

Applies to a system where borrower liquidity and withdrawal reservations are drawn from the same held assets. Assuming:

- borrowable assets are what a borrower may take right now, not a credit limit
- reserved assets are unavailable to the borrower

## Accrual

How debt and claims move with time. None of these can be violated by any
single state, however wrong that state is, because the violation is in the
transition.

### `accrual/debt-falls-only-against-payment/v1`

> Debt falls only against held assets rising by at least the fall.

| | |
| --- | --- |
| Component | `src/laws/DebtFallsOnlyAgainstPayment.sol` |
| Specimen | `specimens/DebtForgiven.sol` |
| Counterexample | `test/counterexamples/Accrual.t.sol` |
| Bounds | exact |
| Reads | `totalDebt`, `totalAssets` |

Applies to a pooled lender claim denominated in one asset, where borrowers owe that same asset and fees accrue out of lender yield. Assuming:

- the two observations are one system and its own past, in that order
- assets a borrower repays are held by the system rather than forwarded
- no third party settles debt outside the system's own accounting
- the two observations bracket a single operation; an offsetting movement inside one batched transition would hide a violation from a law that compares totals

### `accrual/no-accrual-at-rest/v1`

> At equal observation times, debt rises only against held assets leaving.

| | |
| --- | --- |
| Component | `src/laws/NoAccrualAtRest.sol` |
| Specimen | `specimens/AccruesAtRest.sol` |
| Counterexample | `test/counterexamples/Accrual.t.sol` |
| Bounds | exact |
| Reads | `totalDebt`, `totalAssets`, `observedAt` |

Applies to a pooled lender claim denominated in one asset, where borrowers owe that same asset and fees accrue out of lender yield. Assuming:

- the two observations are one system and its own past, in that order
- observedAt advances only with real elapsed time, never per call
- a borrowing removes from held assets what it adds to debt
- the two observations bracket a single operation; an offsetting movement inside one batched transition would hide a violation from a law that compares totals

### `accrual/path-independent/v1`

> One long step and the same span in equal small steps agree on debt, within one unit per step less one.

| | |
| --- | --- |
| Component | `src/laws/AccrualPathIndependent.sol` |
| Specimen | `specimens/CompoundsPerStep.sol` |
| Counterexample | `test/counterexamples/Accrual.t.sol` |
| Bounds | one unit of the asset per subdivision, less one (linear accrual on principal truncates once per step: the subdivided run accrues n*floor(x) where the single run accrues floor(n*x), and those differ by at most n-1) |
| Reads | `totalDebt`, `observedAt` |

Applies to a pooled lender claim denominated in one asset, where borrowers owe that same asset and fees accrue out of lender yield, accruing linearly on principal rather than compounding. Assuming:

- the two observations are two systems, not one system and its past
- both began from the same state and were advanced over the same span
- the span divides evenly into the number of subdivisions
- the rate did not change during the span
- the law is deployed with the subdivision count the run actually used; nothing in either observation reveals a mismatch, and a mismatch silently changes the bound

## Claims

What a recorded withdrawal claim is owed, and in what order. These need the
withdrawal-queue extension, and a target without one reverts on the read
rather than being reported as orderly.

### `claims/recorded-claim-never-shrinks/v1`

> A recorded claim keeps its owed amount and never loses payment already made.

| | |
| --- | --- |
| Component | `src/laws/RecordedClaimNeverShrinks.sol` |
| Specimen | `specimens/ClaimHaircut.sol` |
| Counterexample | `test/counterexamples/Claims.t.sol` |
| Bounds | exact |
| Reads | `withdrawalQueue.claimCount`, `withdrawalQueue.claimAt` |

Applies to a pooled lender claim denominated in one asset, with withdrawals recorded as an ordered queue of individual claims that keep their position once made. Assuming:

- the two observations are one system and its own past, in that order
- a claim keeps its index once recorded, including after it is paid in full
- both observations read the queue rather than the core observables alone
- the two observations bracket a single operation; an offsetting movement inside one batched transition would hide a violation from a law that compares totals
- the queue is short enough to read in one call; a law that runs out of gas traversing it reverts, and a revert is no verdict

### `claims/queue-order-preserved/v1`

> No withdrawal claim is paid while an older claim is still owed something.

| | |
| --- | --- |
| Component | `src/laws/QueueOrderPreserved.sol` |
| Specimen | `specimens/QueueJumped.sol` |
| Counterexample | `test/counterexamples/Claims.t.sol` |
| Bounds | exact |
| Reads | `withdrawalQueue.claimCount`, `withdrawalQueue.claimAt` |

Applies to a pooled lender claim denominated in one asset, with withdrawals recorded as an ordered queue of individual claims that keep their position once made. Assuming:

- the queue is ordered oldest first
- partial payment is recorded against the claim rather than held elsewhere
- the system promises order, rather than paying pro rata
- the queue is short enough to read in one call; a law that runs out of gas traversing it reverts, and a revert is no verdict

### `claims/reserves-cover-payable/v1`

> Reserved assets cover everything still owed on the claims declared payable.

| | |
| --- | --- |
| Component | `src/laws/ReservesCoverPayableClaims.sol` |
| Specimen | `specimens/PayableBeyondReserves.sol` |
| Counterexample | `test/counterexamples/Claims.t.sol` |
| Bounds | exact |
| Reads | `reservedAssets`, `withdrawalQueue.claimCount`, `withdrawalQueue.claimAt`, `withdrawalQueue.payableThrough` |

Applies to a pooled lender claim denominated in one asset, with withdrawals recorded as an ordered queue of individual claims that keep their position once made. Assuming:

- payableThrough is what the system declares, not something derived from the reserves
- reserved assets are held against the queue and against nothing else
- a claim is never paid more than it is owed; no law in the corpus covers that yet
- the queue is short enough to read in one call; a law that runs out of gas traversing it reverts, and a revert is no verdict

### `claims/pooled-claims-cover-open-batches/v1`

> Pooled lender claims cover everything still owed on open withdrawal batches.

| | |
| --- | --- |
| Component | `src/laws/PooledClaimsCoverOpenBatches.sol` |
| Specimen | `specimens/FeeFromQueued.sol` |
| Counterexample | `test/counterexamples/Claims.t.sol` |
| Bounds | exact |
| Reads | `totalLenderClaims`, `withdrawalQueue.claimCount`, `withdrawalQueue.claimAt` |

Applies to a pooled lender claim denominated in one asset, with withdrawals recorded as an ordered queue of individual claims that keep their position once made. Assuming:

- an amount recorded against a withdrawal is already owed by the pool, so nothing may reduce the pool beneath it
- a fee is capped against the pooled claim the open batches are not already owed, rather than against what has been set aside; an earmark cannot exceed what is held, so the two part company exactly when the system is illiquid
- a claim is never paid more than it is owed; no law in the corpus covers that yet
- the queue is short enough to read in one call; a law that runs out of gas traversing it reverts, and a revert is no verdict
