# Wildcat withdrawal-batch amount definitions

This record gives [#1926](https://github.com/wildcat-finance/skills/issues/1926)
its amount and status definitions before the Fiat run that restores unpaid
Wildcat withdrawal batches. It reads the deployed V1 and V2 source and states
what each quantity means, which native reads and events supply it, how scale
and rounding apply, and which checks a reconstruction must pass. It captures
nothing, reconstructs no batch and classifies no mainnet batch. #1926 stays
open, because its acceptance needs restored data. The issue's proposed output,
`docs/kickoff/1896/withdrawals.md`, is left for that run, which can link here.

## Sources and roles

- V1: `wildcat-finance/wildcat-protocol` at
  `da74452aa7d1a0f024d99efd22cc6d950a8116b7`.
- V2: `wildcat-finance/v2-protocol` at
  `a70f297fbd1b1ab597e0e9a3458a2d13a34b4657`.
- These are the pins the [value map](../1384/values.md) uses.
  [evidence/sources.json](evidence/sources.json) binds the 16 cited files by
  revision, SHA-256, byte count and permanent URL. Line references are to
  those bytes, under `src/`. A source pin does not prove the code at a block;
  #1384 rechecks code at each boundary.
- Producer: Claude, in the Claude Code session
  `https://claude.ai/code/session_01GCCywtCU4WjqBzE2k1moE9`, on 2026-09-27, at
  laurenceday's request.
- Reviewer: **not yet assigned**. #1926 names Pandects for the amount and
  rounding rules. That review has not happened, and this record claims none.
- Ownership stays as #1926 assigns it. Probitas owns the emitted family and
  Tabularium the native meanings. #1384 owns the final-boundary reads, #1378
  the native events, and #1386 the opening state and queue projection.

## What the deployed code does

V1 and V2 agree except where a reference names one generation.

**Storage.** A batch is keyed by its `uint32` expiry. It holds
`scaledTotalAmount` and `scaledAmountBurned` in scaled units and
`normalizedAmountPaid` in raw underlying units. An account's entry in a batch
holds `scaledAmount` and `normalizedAmountWithdrawn`. The market also keeps a
FIFO of unpaid expiries (V1 `libraries/Withdrawal.sol:17-35`, V2 `:15-33`).
Its state carries the totals `scaledPendingWithdrawals` and
`normalizedUnclaimedWithdrawals`, and one `pendingWithdrawalExpiry`.

**Queueing.** A queue joins the pending batch, or opens one expiring
`withdrawalBatchDuration` later and emits `WithdrawalBatchCreated` (V1
`market/WildcatMarketWithdrawals.sol:102-109`, V2 `:89-98`). On a closed V2
market the duration is zero (V2 `:94`). The same scaled amount is added to the
account entry, the batch and `scaledPendingWithdrawals`, and
`WithdrawalQueued(expiry, account, scaledAmount, normalizedAmount)` is emitted
(V1 `:114-118`, V2 `:112-116`). No other code writes those two scaled fields.

The scaled amount is `rayDiv(amount, scaleFactor)`, rounded half up (V1 `:85`,
V2 `:139`; `libraries/MarketState.sol:76-78`). The event's `normalizedAmount`
is the caller's `amount` for `queueWithdrawal` (V1 `:118`, V2 `:146`). For V2
`queueFullWithdrawal` and V2 sanctions quarantine it is
`rayMul(scaledAmount, scaleFactor)` (V2 `:163-166`;
`market/WildcatMarket.sol:298-321`). The two amounts are rounded separately.
Queued shares stay in `scaledTotalSupply` and keep accruing interest until
they are burned.

**Funding.** `_applyWithdrawalBatchPayment` burns
`min(rayDiv(liquidity, scaleFactor), unburned)` shares. It adds their
underlying value to the batch's `normalizedAmountPaid` and to
`normalizedUnclaimedWithdrawals`. V1 converts with `rayMul`, rounding half up
(V1 `market/WildcatMarketBase.sol:616-618`). V2 floors with
`mulDiv(burned, scaleFactor, RAY)` (V2 `:661-665`). Each payment emits a burn
`Transfer` and `WithdrawalBatchPayment(expiry, scaledAmountBurned,
normalizedAmountPaid)` for that payment alone (V1 `:631-632`, V2 `:678-679`).
The scale factor is the state's value at the payment: the expiry time for an
expiring batch, and the block time otherwise. A batch funded in stages sums
conversions made at different scale factors.

Payments happen in three places:

1. Every state update pays the pending batch from free liquidity (V1
   `:461-474`, V2 `:443-456`), and so does each queue (V1
   `market/WildcatMarketWithdrawals.sol:120-124`, V2 `:118-122`). Free
   liquidity excludes the unburned shares of every earlier batch, valued at
   the current scale factor (V1 `libraries/Withdrawal.sol:47-59`, V2
   `:45-57`).
2. The first state update after `block.timestamp > expiry`
   (`libraries/MarketState.sol:130-136`) accrues to the expiry and pays the
   batch. It emits `WithdrawalBatchExpired(expiry, scaledTotalAmount,
   scaledAmountBurned, normalizedAmountPaid)` with cumulative totals. It then
   pushes the expiry onto the unpaid FIFO if shares remain unburned, or emits
   `WithdrawalBatchClosed` (V1 `market/WildcatMarketBase.sol:414-440`,
   `:570-598`; V2 `:406-427`, `:616-644`). That update can come in any later
   transaction, so the event's block is the processing block, not the expiry.
3. Only `repayAndProcessUnpaidWithdrawalBatches` pays FIFO batches, oldest
   first, and any caller may run it. A fully burned batch leaves the FIFO with
   `WithdrawalBatchClosed` (V1 `market/WildcatMarketWithdrawals.sol:227-285`,
   V2 `:279-341`). V2 `closeMarket` also pays them
   (V2 `market/WildcatMarket.sol:279-285`). Ordinary state updates never do.

**Execution.** Any caller may execute for any account and expiry. Execution
sets the account's `normalizedAmountWithdrawn` to
`floor(normalizedAmountPaid * scaledAmount / scaledTotalAmount)`, pays the
increase, and reverts if the increase is zero (V1
`market/WildcatMarketWithdrawals.sol:177-225`, V2 `:230-277`). An account can
execute again after later funding. V1 refuses an expiry not yet past (V1
`:182-184`). V2 refuses the pending expiry (V2 `:237`) and runs the execution
hook (V2 `:251`), which the deployed templates leave off
([exit policy](../1401/exitpolicy.md)).

If the sentinel flags the account, the amount goes to the escrow that
`sentinel.createEscrow(borrower, account, asset)` returns.
`SanctionedAccountWithdrawalSentToEscrow(account, escrow, expiry, amount)`
then precedes `WithdrawalExecuted` (V1 `:204-222`, V2 `:256-274`; V2
`market/WildcatMarketBase.sol:754-777`). V1 also blocks the account and moves
its remaining market tokens to a second escrow, with
`SanctionedAccountAssetsSentToEscrow` (V1 `market/WildcatMarketBase.sol:157-181`).
That event moves market tokens; it is not a withdrawal execution.

**Dust.** Account shares floor. What the floors leave in a batch stays in
`normalizedUnclaimedWithdrawals`. Only execution reduces that total (V1
`market/WildcatMarketWithdrawals.sol:202`, V2 `:254`).

**Closure.** V2 `closeMarket` pays the pending batch and every FIFO batch. It
emits `WithdrawalBatchExpired` then `WithdrawalBatchClosed` for the pending
batch before its expiry, and reverts if any share is left unburned (V2
`market/WildcatMarket.sol:212-293`). V1 `closeMarket` refuses a non-empty FIFO
before its own state update (V1 `market/WildcatMarket.sol:217-222`). V1
`repayAndProcessUnpaidWithdrawalBatches` refuses a closed market (V1
`market/WildcatMarketWithdrawals.sol:236-239`). A V1 pending batch that
expires underfunded during the closing transaction's state update therefore
enters the FIFO, and no other V1 call pays it after closure. Whether any V1
market reached that state is not established here.

**Reads.** `getUnpaidBatchExpiries()` returns the stored FIFO (V1
`market/WildcatMarketWithdrawals.sol:21-23`, V2 `:22-24`).
`getAccountWithdrawalStatus(address,uint32)` returns storage (V1 `:39-48`, V2
`:40-49`). `getWithdrawalBatch(uint32)` returns storage for every expiry
except the pending one (V1 `:25-37`, V2 `:26-38`). For the pending expiry it
returns the batch as `_calculateCurrentState` simulates it, with expiry
processing and payment applied (V1 `market/WildcatMarketBase.sol:486-546`, V2
`:468-522`). `getAvailableWithdrawalAmount(address,uint32)` applies the
execution formula to the same stored or simulated batch. It reverts for an
expiry not yet past (V1 `market/WildcatMarketWithdrawals.sol:50-73`, V2
`:51-74`).

## Coordinates and units

Every row names chain 1, the market, the expiry and one observation block B by
number and hash, with its timestamp `t_B`. Amounts are raw underlying units
unless their name says scaled. Scaled amounts never go to Pandects. Arithmetic
follows the value map's integer rules (V1 `libraries/MathUtils.sol:138-184`, V2
`:149-195`):

- `rayMul(a, b) = (a * b + 10**27 // 2) // 10**27`
- `rayDiv(a, b) = (a * 10**27 + b // 2) // b`
- `mulDiv(a, b, d) = (a * b) // d`

`sf(x)` is the market scale factor at epoch x.

## Amount definitions

For market m, expiry e and account a:

| Quantity | Definition | Supplied by | Epoch |
| --- | --- | --- | --- |
| `scaled_requested` | `scaledTotalAmount` | `getWithdrawalBatch(e)`; the sum of `WithdrawalQueued.scaledAmount` for e | fixed from expiry |
| `requested` | sum of `WithdrawalQueued.normalizedAmount` for e | #1378 events | each queue's own scale factor |
| `requested_at_expiry` (optional) | `rayMul(scaled_requested, sf(e))` | `sf(e)` from `InterestAndFeesAccrued` with `toTimestamp == e`, or the stored scale factor if the market last accrued at e | e |
| `scaled_funded` | `scaledAmountBurned` | `getWithdrawalBatch(e)`; the sum of `WithdrawalBatchPayment.scaledAmountBurned` | B |
| `funded` | `normalizedAmountPaid` | `getWithdrawalBatch(e)`; the sum of `WithdrawalBatchPayment.normalizedAmountPaid` | cumulative to B, each part at its payment's scale factor |
| `scaled_unfunded` | `scaled_requested - scaled_funded` | derived | B |
| `unfunded` | `rayMul(scaled_unfunded, sf(t_B))` | `currentState().scaleFactor` at B | `t_B` |
| `account_scaled` | `scaledAmount` | `getAccountWithdrawalStatus(a, e)`; the sum of the account's `WithdrawalQueued.scaledAmount` | fixed from expiry |
| `account_entitled` | `floor(funded * account_scaled / scaled_requested)` | derived | B |
| `executed` | `normalizedAmountWithdrawn` | `getAccountWithdrawalStatus(a, e)`; the sum of `WithdrawalExecuted.normalizedAmount` | B |
| `claimable` | `account_entitled - executed` | `getAvailableWithdrawalAmount(a, e)`, for e before `t_B` | B |
| `escrowed` | sum of `SanctionedAccountWithdrawalSentToEscrow.amount` for (a, e), with each escrow address | #1378 events | B |
| `dust` | `funded` minus the sum of `account_entitled` over the batch's accounts | derived | B |

- `unfunded` uses `rayMul` because the market values unburned withdrawal
  shares that way in `liquidityRequired` and `totalDebts`
  (`libraries/MarketState.sol:87-98`, `:138-143`). The funding that clears it
  can differ by a unit, since V1 rounds each payment half up and V2 floors it.
  Pandects decides whether the row carries the V2 floor instead.
- `unfunded` keeps growing after B while the shares stay unburned. The value
  at B needs `sf(t_B)`. The stored `previousState().scaleFactor` is at
  `lastInterestAccruedTimestamp` instead. The row records which it used.
- Never compute `funded` as `rayMul(scaled_funded, sf(t_B))`. Each part
  converts at its own payment's scale factor.
- `funded + unfunded` exceeds `requested` by the interest the queued shares
  earned, and differs from it by rounding. `requested - funded` is not the
  unfunded obligation.
- `funded` is underlying reserved in the market against burned shares.
  `executed` is underlying that left the market for the account or its escrow,
  and `escrowed` is part of `executed`. None of them establishes that the
  lender can spend the proceeds. #1495 and #1497 own those conclusions.

## Status at the observation block

With `P = previousState()` and `F = getUnpaidBatchExpiries()` at B, a batch has
exactly one status:

| Status | Condition at B | Row |
| --- | --- | --- |
| `open` | `e == P.pendingWithdrawalExpiry` and `t_B <= e` | none; the batch still accepts queues |
| `expired-unprocessed` | `e == P.pendingWithdrawalExpiry` and `t_B > e` | proposed: emitted, with its simulated amounts marked |
| `expired-unfunded` | e in F and `scaled_funded == 0` | `withdrawal_batch_expired_unpaid` |
| `expired-partly-funded` | e in F and `0 < scaled_funded < scaled_requested` | `withdrawal_batch_expired_unpaid` |
| `funded` | e neither pending nor in F, and `scaled_funded == scaled_requested > 0` | none |
| `never-queued` | `scaled_requested == 0` in a stored read | none |

An `expired-unprocessed` batch has no `WithdrawalBatchExpired` yet and is not
in F. `getWithdrawalBatch(e)` simulates the processing that a state update at
`t_B` would perform. Its amounts are derived by call and are never stored
values. The batch's final status depends on the liquidity when a transaction
processes it.

`never-queued` holds only for an expiry someone asked about. Because
`scaledTotalAmount` only grows, a stored zero shows that e never received a
queue. No read enumerates the expiries, so the population comes from events.

In this family, **unpaid** means `scaled_unfunded > 0` for an expired batch:
the market has not reserved funds for every share. A funded batch with
unexecuted accounts is not unpaid; its accounts show `claimable`. The rendered
claim "A lender asked for money and did not get it"
([venues.md](../../../plugins/probitas/skills/probitas/references/venues.md))
reads as receipt, which neither stage proves. Probitas owns that wording.

**Transitions.** A batch keeps its history when its status at B changes:

- Unfunded or partly funded at processing: `WithdrawalBatchExpired` with
  `scaledAmountBurned < scaledTotalAmount`. Its block is the processing block.
- Funded later: `WithdrawalBatchClosed` for e after such an event.
- Funded at processing: `WithdrawalBatchExpired` with
  `scaledAmountBurned == scaledTotalAmount`, and `WithdrawalBatchClosed` in
  the same transaction.
- Closed by market closure (V2): both events from `closeMarket`, in a block
  before e. This is not an expiry.

**Account status**, for e before `t_B`:

- `nothing-entitled`: `account_entitled == 0`.
- `claimable`: `claimable > 0`.
- `executed-to-date`: `claimable == 0` and `executed > 0`, in a batch not yet
  `funded`.
- `executed`: `claimable == 0` and `executed > 0`, in a `funded` batch.

Each execution records its destination: the account, or an escrow address.

## Resolving the old fields

The old adapter emitted a row when the subgraph reported `isExpired` and not
`isClosed`. It set `requested` to `totalNormalizedRequests` and `paid` to
`normalizedAmountPaid`. It cited the row to the expiration record's
transaction, or to the market's deployment when the subgraph had none
([wildcat.py](../../../plugins/probitas/scripts/probitas_lib/adapters/wildcat.py),
`_BATCH_FIELDS` and the `withdrawalBatches` loop).

- `requested`: the replacement takes the sum of native
  `WithdrawalQueued.normalizedAmount`. The old field name suggests the
  subgraph summed the same values. Its mapping was not inspected and is not an
  input.
- `paid`: this is `funded`, underlying reserved in the market. It is not
  `executed` and not lender receipt, and the replacement renders it as funded.
- Epochs: the old status and amounts came from the subgraph's unpinned head,
  while the row's block and time came from the expiration transaction. The
  replacement takes status and amounts from one pinned B, and keeps the
  processing block as a separate history field.
- The old row had no unfunded obligation, and `requested - paid` does not
  supply one.
- Account `normalizedAmountWithdrawn` becomes `executed`. It is reported apart
  from batch funding, with escrow destinations kept.

## Proposed row

`withdrawal_batch_expired_unpaid` has one row per (m, e) whose status at B is
`expired-unfunded` or `expired-partly-funded`, and is proposed for
`expired-unprocessed`. Its fields:

- `market`, `expiry`, `status`, `market_closed` from `P.isClosed`
- `observation_block`, `observation_block_hash`, `observation_time`
- `requested`, `scaled_requested`, `funded`, `scaled_funded`, `unfunded`
- `scale_factor` and `scale_factor_epoch` for `unfunded`
- `processed_block`, absent while the batch is unprocessed
- a mark on every simulated value

Account execution stays out of this row. The dossier carries it per (m, e, a)
as `account_scaled`, `executed`, `claimable`, and each execution's block and
destination. Probitas decides the family names and fields.

## Joins

Per market, the reconstruction joins these native events from #1378 to the
opening state from #1386 and the boundary reads from #1384. Declarations are in
`interfaces/IMarketEventsAndErrors.sol`.

| Event | V1 | V2 | Joins as |
| --- | --- | --- | --- |
| `WithdrawalBatchCreated(expiry)` | `:122` | `:141` | opens e |
| `WithdrawalQueued(expiry, account, scaledAmount, normalizedAmount)` | `:135-140` | `:152-157` | adds to `scaled_requested`, `account_scaled` and `requested` |
| `SanctionedAccountAssetsQueuedForWithdrawal(account, expiry, scaledAmount, normalizedAmount)` | none | `:99-104` | marks a quarantine queue; the paired `WithdrawalQueued` carries the amounts |
| `WithdrawalBatchPayment(expiry, scaledAmountBurned, normalizedAmountPaid)` | `:129-133` | `:146-150` | adds to `scaled_funded` and `funded` |
| `WithdrawalBatchExpired(expiry, scaledTotalAmount, scaledAmountBurned, normalizedAmountPaid)` | `:112-117` | `:133-138` | records processing; checks the running totals |
| `WithdrawalBatchClosed(expiry)` | `:127` | `:144` | batch fully funded |
| `WithdrawalExecuted(expiry, account, normalizedAmount)` | `:142-146` | `:159-163` | adds to `executed` |
| `SanctionedAccountWithdrawalSentToEscrow(account, escrow, expiry, amount)` | `:148-153` | `:165-170` | escrow destination of the execution that follows it |
| `InterestAndFeesAccrued(fromTimestamp, toTimestamp, scaleFactor, ...)` | `:97-104` | `:118-125` | payment scale factor |
| `StateUpdated(scaleFactor, isDelinquent)` | `:95` | `:116` | payment scale factor |

The market's queue and burn `Transfer` logs repeat these amounts and are not
an independent source. Events are ordered by block, transaction index and log
index. #1386's queue projection owns the replay. This record states what that
replay must reproduce and does not specify a second one.

## Checks

A reconstruction must pass each check, or the conclusions it covers are
refused:

1. **Event consistency.** Each `WithdrawalBatchExpired` equals the running
   totals at its log. Each `WithdrawalBatchClosed` follows
   `scaled_funded == scaled_requested`. Each escrow log is followed in the
   same transaction by a `WithdrawalExecuted` for the same account, expiry and
   amount.
2. **Batch totals.** For each e other than the pending one, the event sums
   equal `getWithdrawalBatch(e)` at B. For the pending batch, the view's
   `scaledTotalAmount` equals the event sum, and its burned and paid amounts
   are at least the event sums. Any excess is a simulated payment: the run
   recomputes it with the view's formulas or reports it as simulated.
3. **Account totals.** For every (e, a), the event sums equal
   `getAccountWithdrawalStatus(a, e)` at B.
4. **Lender set.** For each e, the accounts' `account_scaled` sum to
   `scaled_requested`. A shortfall means a missing lender.
5. **Open shares.** Over F and the pending batch, `scaled_unfunded` from the
   event sums totals `P.scaledPendingWithdrawals`.
6. **Unexecuted funds.** Over every batch, `funded - executed` from the event
   sums totals `P.normalizedUnclaimedWithdrawals`. A remainder means a batch
   holding funds or dust is missing from the population.
7. **FIFO.** F lists, in the order of their `WithdrawalBatchExpired` logs,
   the expiries whose expiry log left shares unburned and that have no later
   `WithdrawalBatchClosed`.
8. **Payment scale.** Each `WithdrawalBatchPayment` satisfies
   `normalizedAmountPaid == convert(scaledAmountBurned, s)`, where `convert` is
   `rayMul(x, s)` in V1 and `mulDiv(x, s, 10**27)` in V2. `s` is the
   `scaleFactor` of the latest `InterestAndFeesAccrued` or `StateUpdated` from
   the same market before the payment log.
9. **Execution order.** After each `WithdrawalExecuted`, the account's running
   `executed` equals `floor(funded * account_scaled / scaled_requested)` with
   `funded` as of that log. A reordered payment or execution fails here.
10. **Claimable.** For e before `t_B`, `getAvailableWithdrawalAmount(a, e)` at B
    equals the derived `claimable`.
11. **One block.** Every read names B by hash under EIP-1898, and every
    compared value comes from that B. Every input keeps its Alexandria digest,
    and changed bytes refuse.

Checks 4 to 7 close the population only for batches that still carry unburned
shares, unexecuted funds or dust. A batch before the capture start that was
fully funded, fully executed and left no dust leaves no trace in state at B.
Its history needs logs from the market's deployment or #1386's opening state.
Without them that history is unsupported, not zero. #1386 can rule out carried
value: at the block before the capture start, each market either has no code,
or has zero `scaledPendingWithdrawals` and `normalizedUnclaimedWithdrawals`, no
pending expiry and an empty FIFO. Then no earlier batch carries value into the
interval.

## Acceptance cases

How each case #1926 names is classified, and which checks exercise it:

| Case | Classified by | Checks |
| --- | --- | --- |
| Pending, V1 and V2 | `open` or `expired-unprocessed` | 2, 5 |
| Expired unfunded | `expired-unfunded` | 5, 7 |
| Partly funded, partial burns | `expired-partly-funded` | 2, 8 |
| Later funding | the funded-later transition | 7, 8, 9 |
| Funded, unexecuted | `funded` with `claimable > 0` | 6, 10 |
| Fully executed | `funded`, every account `executed` | 6, 9 |
| Multiple lenders, dust | `account_entitled`, `dust` | 4, 6 |
| Escrow execution | the execution's destination | 1, 9 |
| Before the interval | #1386 opening state | 6, and the paragraph above |
| Missing population | refused | 4, 6, 7 |
| Wrong scale | refused | 2, 8 |
| Reordered funding or execution | refused | 9 |
| Changed bytes, mismatched blocks | refused | 11 |

This record does not say which cases occur on mainnet. Where the estate has no
instance, the run says so.

## What this record does not establish

- It captured nothing and ran no check. It classifies no batch at either
  boundary: V1 block 22074622, V2 block 26022093.
- It does not prove code at a block, and it does not establish storage slots.
  The value map leaves slots open.
- It did not inspect the Wildcat subgraph's mapping.
- It does not say whether the V1 closure case occurred.
- An escrow execution is not lender receipt or spendability.
- Pandects has not reviewed the amount and rounding rules.
- #1926 stays open. Its acceptance needs the restored data, the offline
  dossier and the Probitas gates.
