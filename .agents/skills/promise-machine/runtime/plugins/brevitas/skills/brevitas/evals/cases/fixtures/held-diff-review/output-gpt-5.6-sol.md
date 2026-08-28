- **`Sound.reserve`, changed `ceiling` calculation:** The new bound permits an earmark larger than the assets held, contradicting both the function’s “earmark held assets” contract and `accrueFee`’s assertion that an earmark cannot exceed what is held. Reproduction: (1) set `claims = 100`, `held = 10`, and `unpaidTotal() = 0`; (2) call `reserve(100)`; (3) the new ceiling is `100`, so the function accepts `100` despite only `10` being held. If the accepted value updates the earmark/reserved accounting as the excerpt describes, reserved liquidity is overstated by `90`, potentially breaking settlement or any invariant requiring earmarks to be asset-backed. Keep the queue bound, but separately cap the earmarked amount by available held assets; if this function uses one value for both the queued claim and earmark, split those accounting values. Otherwise restore `min(claims - unpaidTotal(), held)`.

Required regression tests:

- With `claims = 100`, `held = 10`, and no unpaid withdrawals, `reserve(100)` may queue at most `100` of claims but must earmark no more than `10`.
- With `claims = 100` and successive requests of `60` and `60`, total unpaid withdrawals must stop at `100`.
- With `claims = 100` and `unpaidTotal() = 80`, `accrueFee(30)` must accrue only `20`.
- With `claims <= unpaidTotal()`, `accrueFee` must accrue `0`.
- With earmarks below unpaid withdrawals because of illiquidity, the fee cap must use total unpaid queue debt, not the smaller earmark.

Whether the implementation already maintains separate queued and earmarked amounts cannot be established because the state updates after the shown bounds are not included. If it does, the apparent `reserve` defect depends on which accounting field receives `value`; the `accrueFee` bound itself is consistent with protecting the entire unpaid withdrawal queue.