# Receipt inclusion proofs

Lazarus plan v3 binds a full ordered receipt witness to the `receiptsRoot` in
a verified Ethereum header. A scoped witness adds two narrow relations. An
empty witness is accepted only for Ethereum's empty trie root and adds none.
Neither shape upgrades the rest of the recorded JSON-RPC response.

The shipped fixture is
[`examples/aave-v4-spoke-v1`](../examples/aave-v4-spoke-v1). It fixes Ethereum mainnet
block `0x18ac22c`, reconstructs the root from 177 consensus receipts, selects
transaction index `0x3f`, checks that receipt's 4 consensus logs, and checks
the exact two-log projection declared by the fixed-block filter. The fixture
reports exactly two `receipt_trie_proved` relations.

The empty example is
[`tests/fixtures/ethereum-genesis-empty-receipts-v1`](../tests/fixtures/ethereum-genesis-empty-receipts-v1).
It fixes Ethereum block `0x0`, verifies the canonical empty trie root, carries
no target receipt or filtered-log request, and reports exactly zero
`receipt_trie_proved` relations.

## Verify and demonstrate offline

Use the repository's locked Lazarus environment. None of these commands accepts
an RPC URL or opens a network connection:

```bash
python3 plugins/lazarus/scripts/lazarus.py verify \
  plugins/lazarus/examples/aave-v4-spoke-v1
python3 plugins/lazarus/scripts/lazarus.py verify-release \
  plugins/lazarus/examples/aave-v4-spoke-v1-release
python3 plugins/lazarus/examples/aave-v4-spoke-v1/demo.py
python3 plugins/lazarus/tests/fixtures/ethereum-genesis-empty-receipts-v1/demo.py
```

The Aave demonstration verifies the fixture and the state-fixture/v2 release,
captures the Ariadne statement twice, builds the release twice, and compares
both rebuilt trees with the shipped bytes. It then rejects one-byte mutations
to a consensus receipt, receipt index, consensus log, receipts root, evidence
count and release document. Its single JSON event carries the correlation ID,
block identity, bounded counts, evidence classes, versions, digests and mutation
verdicts. It emits no log topics, log data, provider URL or credential.

The genesis demonstration denies network connections while it verifies the
fixture and manifest, captures and checks a state-fixture/v2 statement, writes
and reads a release, and rejects non-empty-root, mixed-shape, count, component
digest and release mutations. Its event reports the empty root, zero receipt
and relation counts, format versions and local digests.

## What is proved

Ethereum's receipts trie commits to ordered consensus receipt payloads. Lazarus
encodes every witness receipt using its transaction type, status or state root,
cumulative gas used, bloom and consensus log tuples, then reconstructs the
Merkle Patricia trie at keys `rlp(transaction_index)`. A matching root proves
that sequence against the captured header. Lazarus then compares:

- the selected consensus receipt payload at the declared transaction index;
- every consensus log in that selected receipt; and
- the stable ordered projection selected by the declared fixed-block log
  filter.

The filter admits only `blockHash` plus optional address and topic selectors.
The relation does not infer data beyond that finite request.

For an empty witness, the plan contains only the block-receipts request and the
witness contains only its version, header and literal empty receipt array.
Verification reconstructs Ethereum's canonical empty trie root, checks it
against the verified header, and derives zero target or log relations. A
non-empty header root, a mixed target shape, or a positive relation count
fails closed.

## What remains recorded evidence

Transaction hashes are RPC decorations, not fields in a consensus receipt
payload. Block transaction ordering, the target receipt lookup, the block-wide
receipt response and the filtered-log response must agree on the recorded hash,
but that agreement does not move the hash into the trie proof. A coherent hash
rewrite leaves `receiptsRoot` and both proved relations unchanged. A rewrite in
only one recorded source fails as a recorded-RPC disagreement.

Calls, traces, unrelated receipts, unrelated log projections, canonical-chain
membership and provider independence also remain outside this proof. Account,
storage and code claims retain their separate EIP-1186 state-proof boundary.

## Failure and compatibility boundary

Verification fails closed before replay or release when the witness is absent,
malformed, incomplete, non-contiguous, out of order, attached to another
header, inconsistent with the recorded sources, or reconstructs another root.
Evidence counts are recomputed from accepted relations rather than trusted from
the manifest. Release verification repeats the receipt-root and count binding
from local bytes.

Plan v1 and v2, manifest v1, state-fixture/v1 and release v1 remain supported
byte for byte. The historical
[`aave-v4-spoke-v0`](../examples/aave-v4-spoke-v0) fixture and its release stay at writer
0.1.0; new output uses writer 0.2.0. Receipt-witness/v1 now has two exclusive
shapes: the existing non-empty scoped sequence and the empty-root sequence with
no target fields and zero relations.
