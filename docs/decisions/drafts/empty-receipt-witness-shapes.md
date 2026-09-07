# Decision: Keep receipt-aware formats with exclusive empty and scoped shapes

## Status

Accepted, 2026-09-06.

## Context

Lazarus `plan-v3` and `receipt-witness-v1` describe a scoped receipt and its
log projection. They could not represent a block whose verified header commits
to Ethereum's canonical empty receipt trie because both formats required a
target receipt and filter. Existing non-empty fixtures, manifests, statements,
and releases already depend on these versions and their two-relation meaning.

The accepted design and its comparison evidence are recorded in
[`docs/lazarus-empty-block-receipt-witness/study.md`](../../lazarus-empty-block-receipt-witness/study.md).

## Decision

Keep both versions and give each exactly two closed shapes: an empty plan names
only its block-receipts request and an empty witness contains only its header
and `receipts: []`; the existing complete target-and-filter shapes remain the
scoped branch.

## Alternatives

An explicit `mode` field in both formats would make the branch locally
obvious, but it would duplicate information already fixed by the closed shape
and introduce two discriminators that could disagree.

New plan, witness, manifest, and release versions would provide strict version
separation, but would enlarge the conversion, binding, documentation, and
rollback surface for a single additional cardinality.

## Consequences

Existing scoped documents stay valid and retain their two receipt-trie
relations. An empty witness can carry zero relations only when its reconstructed
root and the verified header root are both the canonical empty trie root. Mixed
shapes, an empty witness under a non-empty root, or a non-empty block-receipts
result on the empty path are refused.

Schema and semantic checks must keep the two formats' shapes aligned. Reversing
this choice requires changing both schemas and their validators together. The
capture, manifest, release, and demonstration propagation is deliberately left
to the later runbook steps.
