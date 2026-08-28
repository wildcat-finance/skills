## Supported finding

**High — Fee accrual can consume funds already promised to queued withdrawals**  
Location: `plugins/pandects/specimens/FeeFromQueued.sol:L30-L38`

`accrueFee` caps `value` by `claims - reserved` (`available`) rather than by the amount owed by open withdrawal batches. Because `reserved` is limited by assets actually held, it can be lower than queued obligations during illiquidity. The function then transfers the difference from `claims` to `fees`, reducing the pool backing those recorded claims without changing each batch’s owed or paid amount.

Counterexample:

1. Open batches are owed `100`.
2. The system holds and therefore reserves only `60` for them; `claims = 100`, `reserved = 60`.
3. `accrueFee(40)` computes `available = 40`, accepts `value = 40`, then sets `claims = 60` and `fees += 40`.
4. The batches still record `100` owed, but only `60` remains in `claims`; the `40` shortfall was diverted to fees.

Impact: when undercollateralized, fee collection can worsen the withdrawal shortfall by extracting value already promised to lenders. Accounting conservation may still hold because value moves from `claims` to `fees`, but queued claims are no longer fully backed by the claims pool.

Smallest fix: cap `value` against the amount of `claims` not promised to open batches—i.e., subtract open-batch obligations from `claims`—rather than subtracting `reserved`. The excerpt does not establish the inherited storage/function name that exposes total open-batch obligations, so the exact replacement expression cannot be determined from these bytes alone.