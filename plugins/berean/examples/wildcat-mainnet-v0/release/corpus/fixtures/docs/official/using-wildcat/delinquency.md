---
description: What delinquency means and how it separately affects interest, liquidity, withdrawal payment and claim timing.
---

# Delinquency

## Definition

Any given Wildcat market contains a _reserve ratio_ that dictates what percentage of the assets that are currently being loaned must be available to be withdrawn at any given moment by lenders.

This ratio applies to the current _supply_ of assets to the market. If a market exists that has a capacity of 10,000,000 USDC and a reserve ratio of 20%, the reserve ratio does not apply to that capacity figure unless the market is fully subscribed.

Rather, if the market has a supply of 4,000,000 USDC from lenders, then 800,000 USDC must be in reserve. The amount that a market requires in reserves inflates as interest accrues on a stable supply, since the market token and underlying asset are redeemable 1:1.

A market which has a zero percent reserve ratio need only worry about this to the extent that they need to monitor for withdrawal requests and keep sufficient assets available to cover the protocol fee, if the latter is active.

A market that goes below the reserve ratio - however it does so - is _delinquent_.

## What Delinquency Changes For A Queued Withdrawal

Delinquency does not cancel a withdrawal request, change its place in the queue
or reset its configured cycle expiry. It does show that the market currently
holds less than its collateral obligation, which includes pending and processed
withdrawals as well as ordinary reserve requirements and accrued protocol fees.

The effects must be read separately:

* **Interest:** an amount placed into a withdrawal batch stops earning interest
  from the start of that batch's cycle. Market tokens which remain outside the
  request continue to rebase. If delinquency persists beyond the grace period,
  penalty APR applies to the outstanding lender supply, not to underlying assets
  already allocated to the unclaimed withdrawals pool.
* **Payment and liquidity:** the request remains valid, but a liquidity shortfall
  may leave its batch partly or wholly unfunded. Returned liquidity is applied to
  older expired withdrawal batches before newer ones. Delinquency itself neither
  funds a batch nor moves one lender ahead of another.
* **Claim timing:** cycle expiry makes the batch eligible for settlement; it does
  not guarantee full payment. The lender can claim the funded portion after
  expiry. Any remainder stays queued until additional liquidity is supplied and
  processed.

The live delinquency status therefore cannot, by itself, establish a lender's
claimable amount. That requires the market's withdrawal-batch state and the
lender's position within those batches.

## Related Market Parameters

As well as the reserve ratio, another two parameters are provided when creating a Wildcat market:

* **The grace period**: the time (measured in seconds) that a market is permitted to be delinquent for without adverse effects, and
* **The penalty APR**: the interest rate that applies over and above the base market APR and protocol fee (if present) in the event that a market stays delinquent for longer than the grace period.

## How Delinquency Triggers

Associated with each market is an internal number called the '_grace tracker_' - this is a number that starts counting up from zero after the block in which a market becomes delinquent, and back down towards zero after the block in which a market is cured of its delinquency.

The penalty APR associated with a market activates once the grace tracker exceeds the grace   period, and remains active until it drops below the same. To illustrate:

* A market with a 5 day grace period becomes delinquent for the first time, and the grace tracker begins counting up from zero.
* The borrower takes 7 days to cure the market of its delinquency.
* Once the delinquency is cured, the market calculates that 2 days of penalty APR must be applied and adjusts the scaling factor of market tokens accordingly.
* The grace tracker counts back down to zero from this point - subsequent market state updates will detect when the tracker drops below the market grace period and adjust scaling factors appropriately.
* A total of **4** days of penalty APR will be applied in total: the failure of a market to update its state in a timely fashion as the tracker drops below the grace period does _not_ adversely impact the borrower.

## Unclaimed/Pending Withdrawals & Delinquency

Tthe reserve ratio of a market can be temporarily raised depending on the amount of assets that are either earmarked for withdrawal by a lender, or are part of a pending withdrawal request.

When a lender burns market tokens in order to request a withdrawal of assets they have deposited in a market, any reserves that exist within the market are removed from the market supply. Consider the following:

* A market with a supply of 1,000,000 USDC has a reserve ratio of 20%, and currently holds 250,000 USDC in reserves (current reserve ratio 25%).
* A lender makes a request to withdraw 200,000 USDC, burning 200,000 market tokens to move 200,000 USDC of the reserves into the unclaimed withdrawals pool, and reducing the supply by the same amount.
* The market now has 50,000 USDC in reserves against a supply of 800,000 USDC. This means that the new reserve ratio is 6.25%, and the market is immediately delinquent.
* The borrower needs to return 110,000 USDC to the market reserves in order to cure the delinquency.

More particularly, any withdrawal request that exceeds the reserves currently in a market temporarily forces the reserve ratio upwards. To illustrate:

* A market with a supply of 1,000,000 USDC has a reserve ratio of 20%, and currently holds 250,000 USDC in reserves (current reserve ratio 25%).
* A lender makes a request to withdraw 400,000 USDC, burning 250,000 market tokens to move 250,000 USDC of the reserves into the unclaimed withdrawals pool and generating a pending withdrawal of the remaining 150,000 USDC. The reserve ratio of the market is immediately 0%.
* The supply of the market is reduced by the 250,000 that was moved into unclaimed withdrawals, rather than the full 400,000 requested.
* Pending withdrawals must be 100% collateralised by a market, with the standard reserve ratio of the market applying to the _remainder_ of the supply. In this case, then, the amount of reserves that the market must hold is (150,000 \* 1) + (600,000 \* 0.2) = 270,000 USDC.
* Against a supply of 750,000 USDC, this means that the temporary reserve ratio is 36% rather than the 20% we would 'expect' to see against the remaining supply: the market will remain delinquent until this 36% has been met.
* Pending withdrawals - and their impact on the reserve ratio of a market - remain in place until the lender is capable of burning market tokens in order to reclaim their loaned assets.

\[_The above includes one mild simplification: as stated in_ [_Protocol Usage Fees_](protocol-usage-fees.md)_, lenders are only capable of withdrawing reserves net of any protocol fees that have been accrued and not withdrawn. However, the overall point remains._]

The astute borrower of a market will actively monitor withdrawal requests and current reserve ratios in order to minimise the time for which the grace tracker is active to avoid paying penalties.


