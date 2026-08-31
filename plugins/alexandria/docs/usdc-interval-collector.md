# The resumable Ethereum USDC interval collector

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.
<!-- marketplace-context:end -->

`docs/compound-v3-harvest.md` specifies the production harvester. This document
covers the part of it that now exists: one collector over one market, the
Ethereum mainnet Compound v3 USDC Comet at proxy
`0xc3d688b66703497daa19211eedff47f25384cdc3`.

## The four commands

```bash
python3 plugins/alexandria/scripts/usdc_interval.py collect --plan <plan> --staging <directory>
python3 plugins/alexandria/scripts/usdc_interval.py reconcile --plan <plan> --staging <directory> --provider-class <class>
python3 plugins/alexandria/scripts/usdc_interval.py build --plan <plan> --staging <directory> \
  --epochs <table> --registry <registry> --created-at <timestamp> --output <release>
python3 plugins/alexandria/scripts/usdc_interval.py check <release>
```

`collect` is the only one that reaches a network, and it reads its endpoint from
`ALEXANDRIA_COMPOUND_RPC_URL` alone. The endpoint reaches no file, no receipt
and no message. `reconcile`, `build` and `check` are offline.

The complete path, with no network at all, is
`examples/usdc-interval-v0/demo.py`.

## The shard plan

An `alexandria-interval-plan/v1` document names the chain, the deployment, the
proxy, the inclusive block interval, the shard width, the evidence classes and
the finality policy. The planner tiles the interval with ordered,
non-overlapping shards, at most 4,096 of them and at most 50,000 blocks each,
and refuses a reversed, empty, zero-width or unbounded interval by name.

Each shard asks three questions: the block at its end, the proxy's logs across
its range, and the traces of calls into the proxy across the same range. Every
request identifier is derived from the shard index and the evidence class, so an
interrupted run and a clean run ask for the same bytes.

## Finality is operator policy

No Compound source defines a finality depth. The plan names one of `finalized`,
`safe` or a stated confirmation depth, and the collector binds that boundary's
block number and hash before it asks for a shard. If the provider reports a
different boundary than the plan declares, the run refuses.

The release records this honestly and it is worth being clear about why. Every
capture's scope carries finality class `provider-reported`, not the plan's named
policy. Alexandria requires a `safe` or `finalized` block-range scope to bind
both of its boundary hashes, and this collector reads each shard's end block,
never the interval's first one, so the start hash does not exist to give. The
named policy and the boundary block it bound live in the plan and in the
interval receipt. What the release establishes about finality is that a provider
reported it.

## Implementation epochs are bound by code hash

`CometExt.version()` returns the constant string `0` in the pinned source, so it
cannot tell two implementations apart. An epoch is bound instead by the SHA-256
of its implementation's runtime bytecode.

`discover_epochs` takes the ordered `Upgraded(address)` logs for the proxy, the
EIP-1967 implementation slot read at each boundary and the runtime code read at
each implementation, and returns epochs that tile the declared interval with no
gap and no overlap. A boundary with no slot read of its own does not inherit the
implementation beside it: it refuses. So do a zero-address slot, an empty code
read, a slot that is not a left-padded address, a log from another contract, a
log carrying another topic, unordered logs, a log outside the interval and a
missing block hash. Where the log's announced implementation and the slot read
disagree, or the log's own block hash and the preserved block disagree, the
epoch table refuses rather than choosing.

The implementation slot and the `Upgraded(address)` topic are pinned constants
rather than computed values, because the standard library carries no keccak.
Both are attested by the Phase 0 capture preserved in this repository, and a
test binds them to it.

## Resuming, and rewinding

A checkpoint is written only after a shard's bytes are flushed and fsynced. It
records the next shard, the last accepted block and hash, each journal's
committed byte offset, and a bounded trail of the sixteen most recent accepted
boundaries. It is working state; no release names it.

Resume truncates every journal back to its committed offset, so a process
killed between a record and its checkpoint leaves nothing a resumed run keeps.
Before continuing, the collector re-reads the boundary blocks it remembers. When
one has changed under it, it rewinds to the deepest boundary that still matches,
drops the records above it and re-collects. A reorg below every remembered
boundary starts over. One deeper than the trail refuses, because the collector
would otherwise have to guess which of its journals is still on the chain it
started from.

`reconcile`, `build` and `check` read the checkpoint without truncating
anything, so none of them can lose a record it declined to use.

## What a refusal leaves behind

A response is refused when it exceeds the component byte ceiling, fails bounded
JSON parsing, carries a JSON-RPC error, answers a different request, is marked
truncated, or returns a page at the provider's declared limit and may therefore
be short. Each refusal appends a receipt naming the code, the evidence class,
the shard, the unresolved block range and the provider class the plan declared.

A receipt copies nothing a provider or a transport said. The exception text
reaches the operator on stderr instead. That boundary exists because a receipt
is a durable file and a transport's message can carry its own endpoint, and with
it a credential.

Retrying does not erase the earlier receipt.

## Reconciliation settles nothing

`reconcile` runs the finished interval past a second transport and compares each
shard's boundary hash, the ordered transaction hashes in that block, and the
identity tuple `(blockHash, transactionHash, logIndex, address, topics, data)`
for every log.

A disagreement is recorded, not resolved. Neither provider wins by answering
first or by being in a majority of two. A shard whose boundary hash disagrees is
`failed`; one whose logs or transaction order disagree is `partial`; the second
provider's bytes for that shard are kept beside the first's. A second provider
that cannot answer leaves the interval `unreconciled`, keeps the counts it
reached, and says so.

## The release, and what it claims

`build` emits an ordinary `alexandria-capture-plan/v1` document and calls the
existing `ingest`. Eight components: one JSON journal per evidence class, each
carrying the interval and one record per preserved exchange, plus the interval
receipt, the reconciliation record, the error receipts, the plan and the pinned
registry.

Every coverage count is a JSON pointer into the component it describes, so
`ingest` refuses a count the payload does not carry. `check` then re-derives
every shard's record counts from the journals, because a release rebuilt with an
inflated receipt would otherwise be self-consistent.

`check` runs Alexandria's own verification first, then the things only an
interval release can be wrong about: shards contiguous and non-overlapping
across the declared interval, epochs tiling it and naming this market's proxy, a
finality boundary with its hash above the interval's end, a reconciliation
record for the same plan agreeing with the receipt about every shard, and every
shard that is not complete named in the coverage of every evidence component.

## What this does not establish

- No publisher identity, no provider completeness, no consensus finality and no
  canonical-chain membership. A digest check establishes none of them.
- No credit event, position observation, repayment or default. Turning this
  evidence into venue-qualified events is Tabularium's Compound v3 Phase 1.
- No epoch code-hash proof a stranger can recheck. `check` establishes that
  every epoch declares a SHA-256; the release carries no implementation code to
  hash, so the digest cannot be re-derived from it.
- No coverage of the other 27 markets at the registry pin. Each is a declared
  gap.
- No live run. The collector has been exercised against injected transports and
  the checked-in fixtures only. Every claim about its network path is a claim
  about that boundary, not about a provider that answered.
