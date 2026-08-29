# ADR-037: Prove receipts with a full ordered witness

## Status

Accepted, 2026-08-26.

## Context

Lazarus already checks a captured block header and therefore binds its
`receiptsRoot` to that header hash. The Goldfinch fixture also preserves one
transaction receipt and one five-log `eth_getLogs` result, but those RPC
records remain the provider's statements. A target receipt proof alone cannot
show that the filtered result is complete: an unseen receipt could contain
another matching log.

The accepted [study](../lazarus-receipt-inclusion-proofs/study.md) fixes the
evidence boundary and the
[runbook](../lazarus-receipt-inclusion-proofs/runbook.md) divides its delivery.
Existing plan-v1, plan-v2, manifest-v1, release-v1, state-fixture/v1, and
Goldfinch v0 bytes must keep their existing meaning.

## Decision

Capture the complete ordered receipt set with one standard
`eth_getBlockReceipts` request whose only parameter is the fixed block hash.
Plan-v3 names that required `recorded-rpc` request, the required named
transaction-receipt request as a recorded lookup label, the target trie index,
and the required block-hash log-filter request. These references make the two
intended derived relations explicit without changing the evidence class of any
source RPC record. The transaction hash remains in that recorded request only.

Receipt-witness-v1 records the verified header number, hash, `receiptsRoot`,
and one canonical consensus receipt payload at every contiguous
trie index. Each receipt contains only its index, type, status or pre-Byzantium
root, cumulative gas used, logs bloom, and ordered `(address, topics, data)`
logs. Transaction hashes, per-receipt block identities, and RPC log positions
do not enter the witness. The format accepts legacy receipts and EIP-2718 types
`0x1` and `0x2`. Status and the pre-Byzantium root are mutually exclusive, and
a typed receipt cannot use the pre-Byzantium root form. A later receipt type
requires an explicit format review instead of being accepted as an unknown
envelope.

The filtered-log relation is the exact ordered projection of all witness logs
under the named `blockHash`, address, and topics filter. Neither the target
relation nor the filtered relation becomes `receipt_trie_proved` until the
offline verifier has reconstructed the trie, matched its root, and compared
the projection. The transaction index and block-global log positions follow
from trie and list order. Header `transactions[]`, receipt/log
`transactionHash`, sender, destination, contract address, gas used, effective
gas price, and other RPC decorations remain `recorded_rpc`.

Changed wire shapes take new versions. Plan-v3 and receipt-witness-v1 are
registered first; manifest-v2, release-v2, and Ariadne state-fixture/v2 follow
in their owning steps. The initial scaffold validates the new formats but
capture and whole-fixture verification refuse plan-v3 by name until the proof
path exists. No old reader silently upgrades an old document.

## Alternatives

- Capture only the target receipt and its trie path. This proves membership at
  one index but cannot establish completeness for a block-wide filtered log
  result, so it does not satisfy the second relation.
- Capture `debug_getRawReceipts`. Raw envelope bytes avoid translation from
  JSON fields, but the debug namespace is optional and still needs ordered
  transaction binding and log decoding. It would make provider support part of
  the preservation boundary.
- Re-execute every transaction in the block. This can derive the receipt root,
  but it also requires an execution client, historical state, and fork-rule
  coverage outside the finite Lazarus fixture.
- Reconstruct the transaction trie as well. That could bind transaction hashes
  to receipt indices, but it requires full typed transaction bodies, canonical
  transaction encoding, another capture boundary, and a claim outside issue
  #383's `receiptsRoot` scope.

## Consequences

The fixture gains one bounded response and an ordered witness large enough to
cover every transaction in the block. In return, one offline root comparison
can support both target receipt membership and complete filtered-log equality.
The format duplicates the selected header identity and `receiptsRoot` so each
mismatch has a named failure boundary; component digests bind those bytes
later.

The proof establishes only the receipt-trie and filter relations for the
captured header. It does not bind a transaction hash to a receipt index,
establish that the header is canonical, show that two source identifiers are
independent providers, turn RPC decorations into consensus fields, or show
that transaction execution was replayed. New receipt types, new query shapes,
and changed evidence classes require another explicit decision and version
transition.
