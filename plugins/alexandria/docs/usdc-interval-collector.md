# The resumable Ethereum USDC interval collector

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector has now run against two live providers over an Ethereum mainnet interval, binding both boundary hashes under a finalized scope and preserving each epoch's implementation code so its code hash is rechecked offline; the epoch table still attributes a log by block rather than by transaction position.
<!-- marketplace-context:end -->

`docs/compound-v3-harvest.md` specifies the production harvester. This document
covers the part of it that now exists: one collector over one market, the
Ethereum mainnet Compound v3 USDC Comet at proxy
`0xc3d688b66703497daa19211eedff47f25384cdc3`, which has now been run against two
live providers and whose preserved interval is checked in.

## The four commands

```bash
python3 plugins/alexandria/scripts/usdc_interval.py collect --plan <plan> --staging <directory>
python3 plugins/alexandria/scripts/usdc_interval.py reconcile --plan <plan> --staging <directory> --provider-class <class>
python3 plugins/alexandria/scripts/usdc_interval.py build --plan <plan> --staging <directory> \
  --registry <registry> --created-at <timestamp> --output <release>
python3 plugins/alexandria/scripts/usdc_interval.py check <release>
```

`build` no longer takes `--epochs`. The epoch table used to be an operator's
file handed in at build time; it is now derived from bytes the collector read
and journaled itself, so there is nothing left for an operator to supply and
the argument is retired rather than deprecated.

`collect` and `reconcile` are the two network paths, and each reads its endpoint
from `ALEXANDRIA_COMPOUND_RPC_URL` alone. The endpoint reaches no file, no
receipt and no message. `build` and `check` are offline.

Two historical demonstrations run the whole path with no network at all:
`examples/usdc-interval-v0/demo.py` over synthetic fixtures, and
`examples/usdc-interval-live-v0/demo.py` over the preserved bytes of a real
Ethereum mainnet interval. Their confined reconstruction paths preserve the
original v1 release identifiers. Ordinary `build` emits
`alexandria-interval-receipt/v2`; it has no public legacy-build option.

## What a request carries

Every request carries exactly two headers: `Content-Type: application/json` and
a constant `User-Agent` of the form `alexandria-usdc-interval/<package
version>`, built at import from the plugin manifest. Two of the five providers
the study probed answer HTTP 403 to Python's default `User-Agent`, so a
constant one is the difference between a run and a refusal.

No header value comes from the environment, and there is no argument, variable
or plan field that adds one. A provider that requires a credential header is
therefore out of scope rather than awkward: the collector cannot send one. The
only thing the environment supplies is the endpoint, and that is never written
down.

A release names the provider by class, not by operator. The plan carries a
non-secret `provider.class` string, such as `archive gateway, public tier, no
trace methods`, and that string is what reaches every error receipt, every
reconciliation record and every evidence scope's source reference. A hostname
would be a credential-shaped value in a durable file. A class carries what a
reader needs: which methods the provider served and which it refused.

## The shard plan

An `alexandria-interval-plan/v1` document names the chain, the deployment, the
proxy, the inclusive block interval, the shard width, the evidence classes and
the finality policy. The planner tiles the interval with ordered,
non-overlapping shards, at most 4,096 of them and at most 50,000 blocks each,
and refuses a reversed, empty, zero-width or unbounded interval by name.

The plan also declares its evidence classes: a non-empty subset of
`boundary-blocks`, `logs` and `traces`, in the order the collector requests
them. A shard asks one question per declared class -- the block at its end, the
proxy's logs across its range, the traces of calls into the proxy across the
same range -- and the collector issues no request and opens no journal for a
class the plan omits. An omitted class is not silence: the release names it as a
coverage gap on every evidence scope, with the reason it was not preserved. A
plan that omits `boundary-blocks` is refused outright, because every shard is
checkpointed by its boundary block's hash.

Declaring the classes in the plan is what makes a `traces` omission a stated
scope rather than a provider's limitation quietly inherited. Every request
identifier is derived from the shard index and the evidence class, so an
interrupted run and a clean run ask for the same bytes.

## The opening reads

After the last shard commits, `collect` makes one more pass, journaled and
checkpointed exactly like a shard: it reads the interval's first block, the
EIP-1967 implementation slot at that block and at each upgrade block, the header
at each upgrade block and the block before it, and each named implementation's
runtime code.

These reads are staged as a fourth journal class, `epoch-evidence`, under the
virtual shard index one past the plan's last. A checkpoint whose next shard is
one past the plan therefore says the shards are done, and its `epoch-evidence`
offset says how many opening reads are committed, so a run killed inside the
opening pass resumes into it rather than restarting the interval.

Two things follow. The interval's start hash is now a value the collector read,
so a scope can bind both boundary hashes. And the implementation code is now
bytes in the tree, so an epoch's code hash can be re-derived rather than
trusted.

## What a finality class now says

No Compound source defines a finality depth. The plan names one of `finalized`,
`safe` or a stated confirmation depth, pins the boundary block's number and the
hash it carried, and the collector reads that block by number before it asks for
a shard. A different hash for the same number is a boundary that left the chain,
and the run refuses by name. Under `finalized` or `safe` it then reads the tag
and requires the tag's number to be at or above the pinned boundary, so a plan
survives the tag advancing and fails only when its own boundary block goes.

This is the rebind. Every evidence capture used to carry finality class
`provider-reported` whatever the plan named, because Alexandria requires a
`safe` or `finalized` block-range scope to bind both boundary hashes and the
collector read only each shard's end block. The opening reads supply the missing
one. A plan naming `finalized` or `safe` now earns that class on each evidence
capture's scope, with the interval's start hash and its end hash both bound; a
`confirmations` plan keeps `provider-reported`, because a depth this collector
chose is not a class the chain reports, and it still carries both hashes. The
derived captures -- the epoch table, the code, the plan, the receipts, the
reconciliation record and the registry -- stay `provider-reported`, because they
are built offline from the journals rather than read from a chain.

What a `finalized` scope establishes is still bounded: that a provider answered
the finalized tag, and that both boundary hashes are the ones this collector was
given. It is not consensus finality and not canonical-chain membership.

## Implementation epochs are bound by code hash

`CometExt.version()` returns the constant string `0` in the pinned source, so it
cannot tell two implementations apart. An epoch is bound instead by the SHA-256
of its implementation's runtime bytecode.

`discover_epochs` takes all preserved proxy logs, including `Upgraded(address)`, the
EIP-1967 implementation slot read at each boundary and the runtime code read at
each implementation. V2 epochs tile transaction positions across the declared
interval with no gap or overlap. `build` reads the logs from committed shard
journals and the slot and code evidence from `epoch-evidence`, so the table is
derived from preserved bytes. A boundary with no slot read of its own
does not inherit the implementation beside it: it refuses. So do a zero-address slot, an empty code
read, a slot that is not a left-padded address, a log from another contract,
malformed upgrade topics, unordered logs, a log outside the interval and a
missing block hash. Where the log's announced implementation and the slot read
disagree, or the log's own block hash and the preserved block disagree, the
epoch table refuses rather than choosing.

The implementation slot and the `Upgraded(address)` topic are pinned constants
rather than computed values, because the standard library carries no keccak.
Both are attested by the Phase 0 capture preserved in this repository, and a
test binds them to it.

## Transaction-position ownership

Each v2 epoch adds `start_position` and exclusive `end_position`. A position
contains exactly `block_number`, `transaction_index` and `log_index`: a decimal
block string and non-negative integer indexes. Both indexes are null together
only for a block-edge sentinel, meaning before every log in that block. The
first epoch starts at the interval's first block; the last ends at the block
after the interval's inclusive end. Interior boundaries use the preserved
upgrade's transaction and log indexes, and adjacent epoch positions match.

The existing `start_block`, `end_block`, `start_hash` and `end_hash` describe
each epoch's block envelope. Adjacent envelopes share the upgrade block;
exclusive positions determine ownership inside it. A non-null `upgrade` also
carries `transaction_index`, and its coordinates match the epoch's start.

The receipt's `log_attributions` array records every preserved proxy log in
validated order. Each row contains `block_number`, `block_hash`,
`transaction_hash`, `transaction_index`, `log_index`, zero-based `epoch_index`
and `kind`. An ordinary log has kind `proxy-log`; the upgrade announcement has
kind `upgrade-boundary`. A log in an earlier transaction belongs to the preceding
implementation, and one in a later transaction belongs to the replacement.
The announcement records a boundary without claiming which implementation
executed it.

Missing, boolean, negative, malformed, duplicate, contradictory, unordered or
out-of-range coordinates refuse. Within a block, transaction indexes cannot
decrease and block-wide log indexes must increase; transaction indexes and
hashes must agree, as must block hashes. Three unsupported histories also
refuse: an upgrade in the interval's first block without prior implementation
evidence, more than one upgrade in a block, and an ordinary proxy log in the
upgrade transaction, whether before or after the announcement. End-of-block
slot reads and log order cannot establish intermediate execution state.

A plan omitting logs keeps its omission gap and an empty attribution array.
It claims neither unpreserved log coverage nor the absence of unseen upgrades.
`check` re-derives the positions and ownership from preserved journals and
compares the complete attribution array. Rebinding a changed receipt to new
component digests does not make invented ownership pass.

The check result names `receipt_semantics` as `v1-block-only` or
`v2-positional`. V1 verification retains its block-only meaning and immutable
schema; a valid v1 release gains no positional guarantee. The reasons for the v2 format and
these refusals live in the [standing design decision](../skills/alexandria/EVOLUTION.md#transaction-position-design-decision).

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

Both log streams undergo coordinate validation, but the preserved comparison
tuple does not include `transactionIndex`. V2 ownership is derived from the
primary journal; an `agreed` reconciliation does not establish second-provider
agreement on transaction indexes.

A disagreement is recorded, not resolved. Neither provider wins by answering
first or by being in a majority of two. A shard whose boundary hash disagrees is
`failed`; one whose logs or transaction order disagree is `partial`; the second
provider's bytes for that shard are kept beside the first's. A second provider
that cannot answer leaves the interval `unreconciled`, keeps the counts it
reached, and says so.

## The release, and what it claims

`build` emits an ordinary `alexandria-capture-plan/v1` document and calls the
existing `ingest`. Its components are one JSON journal per declared evidence
class, each carrying the interval and one record per preserved exchange; the
`epoch-evidence` journal of opening reads; and six more -- the interval receipt,
the implementation code, the reconciliation record, the error receipts, the plan
and the pinned registry.

Two of those are new with the opening reads. `epoch-evidence` preserves the
exchanges the epoch table was derived from, so a reader can rebuild the table
rather than take it. `implementation-code` carries each implementation's runtime
bytecode as its own component, so `check` re-hashes those bytes and compares the
digest with the one the epoch table declares, offline, from the release alone.

Every coverage count is a JSON pointer into the component it describes, so
`ingest` refuses a count the payload does not carry. `check` then re-derives
every shard's record counts from the journals, because a release rebuilt with an
inflated receipt would otherwise be self-consistent.

`check` runs Alexandria's own verification first, then the things only an
interval release can be wrong about: shards contiguous and non-overlapping
across the declared interval, epochs tiling it under their declared receipt
version and naming this market's proxy,
each epoch's declared code hash re-derived from the `implementation-code`
component's bytes, the opening reads replayed against the plan so the journal
holds exactly the reads the plan names and no others, a finality boundary with
its hash above the interval's end, a reconciliation record for the same plan
agreeing with the receipt about every shard, and every shard that is not
complete named in the coverage of every evidence component.
For v2, it also compares freshly derived log ownership with every attribution
row. A v1 result remains block-only; it does not inherit that stronger check.

## The interval it has actually collected

The collector has run against two live providers, of classes `archive gateway,
public tier, no trace methods` and `public relay endpoint, archive logs and
state, no trace methods`, over Ethereum mainnet blocks 25,903,935 to
25,905,934. Four shards of 500 blocks all came back `complete`, carrying 93
proxy logs. The opening reads bound the start hash
`0xa4e35dad60b77815249c12cf22ad83056f2ad041ef9b6340dee03e83502d70f0` and the end
hash `0xc0ac604f5eaf0b78ee147ed3cec4f5c5ab1f7d66d1607266cbf343d7bdc959bd` into
every evidence scope under a `finalized` boundary, and produced two
implementation epochs split by an `Upgraded(address)` at block 25,904,935, both
implementations' runtime code preserved and re-hashed by `check`. Reconciliation
came back `agreed` over 106 comparisons with none disputed. `collect` and
`reconcile` together took 5,370 ms against the study's 120,000 ms budget.

The whole capture is committed at `examples/usdc-interval-live-v0/`, and its
demonstration rebuilds it offline to release identifier
`sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32`.
Neither provider's endpoint or hostname appears anywhere in it.

The historical v1 epoch table tiles by block, so a
proxy log emitted earlier in an upgrade block than the upgrade itself would be
attributed to the implementation that replaced the one which produced it. Block
25,904,935 here carries only the upgrade, at transaction index 193 and log index
524, so nothing in this capture is misattributed. These preserved bytes do not
demonstrate the before-upgrade defect, and their original identifier retains
the v1 scope. A v2 reconstruction has its own identifier.

## What this does not establish

- No publisher identity and no provider completeness. Two providers agreeing
  says they agree, not that either preserved everything there was.
- No consensus finality and no canonical-chain membership. A `finalized` scope
  records that a provider answered the finalized tag and that both boundary
  hashes are bound; a digest check establishes neither claim.
- No traces, unless a plan declares the class and a provider serves it. Neither
  provider of the live capture serves `trace_filter`, so that capture declares
  the omission as a gap rather than covering it.
- No credit event, position observation, repayment or default, and no mapping.
  Turning this evidence into venue-qualified events is Tabularium's Compound v3
  Phase 1.
- No market other than the Ethereum mainnet USDC Comet. The other 27 markets at
  the registry pin are each a declared gap.
