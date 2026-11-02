# wildcat-v2 constructed fee specimen

Adapter `1.1.0`, canonical schema 3. This synthetic specimen contains 4
rows: fee collection, an independent repayment and an independent withdrawal plus a V2 protocol-fee Bips update.

Run `python3 rebuild.py` from this directory. It builds through the Alexandria
and Tabularium owners, compares every file with the committed release, moves
the release and verifies it offline. Original inputs are disposable.

Fees retain one underlying `assets` amount and the pool as sole party. The
recipient remains unknown. Equal fee, repayment and withdrawal amounts do not
join the actions. A Bips update has no amount; its integer string stays in the
decoded native record. No historical observation, independent chain proof,
identity, repayment completion or publisher authenticity is established.

`release/` is a closed immutable release. `expected.json` records its complete
file inventory. This README and `data-dictionary.md` sit outside that root.
