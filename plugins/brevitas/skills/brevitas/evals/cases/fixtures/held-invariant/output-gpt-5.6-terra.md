The code establishes this observable invariant: for every pair of queue indices `i < j`, if `claimAt(i)` reports `paid < owed`, then `claimAt(j)` must report `paid == 0`. Equivalently, once any older observed claim is still owed something, no later observed claim may have a positive recorded payment. This is checked exactly, with no tolerance, over `claimCount()` and `claimAt(i)` results. [plugins/pandects/src/laws/QueueOrderPreserved.sol:L49-L64]

The loop is ordered from index `0` through `count - 1`. It latches `anOlderClaimIsStillOwed` when it sees `paid < owed`; any later `paid > 0` then fails. Thus a partially paid older claim blocks every later payment, while a fully paid older claim does not. A later claim with `paid == 0` is permitted regardless of its `owed` value. [plugins/pandects/src/laws/QueueOrderPreserved.sol:L55-L63]

Concrete failing trace:

1. `claimCount()` returns `2`.
2. `claimAt(0)` returns `(owed=100, paid=40)`.
3. The checker sets `anOlderClaimIsStillOwed = true`.
4. `claimAt(1)` returns `(owed=50, paid=1)`.
5. Since an older claim remains owed (`40 < 100`) and the later claim has positive payment (`1 > 0`), `check` returns `false` with `"a claim was paid while an older one was still owed"`. [plugins/pandects/src/laws/QueueOrderPreserved.sol:L58-L61]

Applicability depends on the target actually implementing `IWithdrawalQueueObservables` at its address and exposing a stable, index-ordered queue where lower indices are older claims. The cast itself does not prove either condition. If `claimCount()` or any `claimAt()` call reverts, including because the target lacks the extension or traversal exhausts gas, this law yields no boolean verdict; whether that is surfaced as a failed harness run depends on the unseen `Law`/harness behavior.

The code does not establish that claims are genuinely ordered by age, that `owed` and `paid` represent trustworthy cumulative amounts, that payments cannot occur between calls, or that every claim is represented exactly once. It also cannot detect a queue implementation that reorders indices, omits older claims, reports `paid == 0` despite an external payout, or supplies inconsistent snapshots across external calls. Those properties require the unseen target and harness.