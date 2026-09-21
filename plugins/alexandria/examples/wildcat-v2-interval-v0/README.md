# Preserved Wildcat V2 mainnet interval, v0

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Ordinary builds now emit `alexandria-interval-receipt/v2`, which attributes each preserved proxy log to an implementation epoch by block, transaction index and log index, and `check` re-derives every owner offline; reconciliation still compares a log without its transaction index, so a second provider that reports a different index for the same log records `agreed`.
<!-- marketplace-context:end -->

The interval this example preserves was collected once, from two live
providers, by the runbook step that created it. The staging tree it was built
from -- 3,463 shards' worth of `logs` and targeted `trace_transaction`
journals, plus the opening-read journal, checkpoint and reconciliation record
-- is too large to check into this repository, so it
**is preserved outside this repository** and verified by digest:
`staging-manifest.json` binds the preserved archive's own byte count and
SHA-256 to the byte count and SHA-256 of every one of its 124 files, and
`rebuild-record.json` is what this collecting host got when it actually
rebuilt the release from that tree, recorded beside the manifest.

```bash
export ALEXANDRIA_WILDCAT_V2_STAGING=/path/to/unpacked/staging
python3 plugins/alexandria/examples/wildcat-v2-interval-v0/demo.py build --output <directory>
python3 plugins/alexandria/examples/wildcat-v2-interval-v0/demo.py verify <directory>
```

`build` needs the staging tree unpacked locally at the path
`ALEXANDRIA_WILDCAT_V2_STAGING` names; without that variable set, it refuses
by name rather than silently skipping. Once set, it rebuilds the Alexandria
release from those preserved bytes and checks it, reaching no network of its
own -- the two live reads already happened, once, when the tree was
collected. `verify` re-derives the release identifier, the epoch count, every
subject's implementation code digest and the reconciliation status from the
rebuilt release, and compares them, and the recorded summary, with
`expected.json`.

A second, separate check needs no staging tree at all: it reads
`staging-manifest.json` and `rebuild-record.json` and confirms they are
present, well-formed, and agree with each other and with `expected.json` --
so a reviewer with no access to the preserved archive can still confirm what
this example claims was actually rebuilt once, on the collecting host, from
exactly the bytes the manifest's digests describe.

## What was collected

Ethereum mainnet blocks 21,866,550 to 26,022,093 (finality `finalized`,
re-read at block hash
`0x1cfd09b6dfaa2af921e367d94f24e2b1e6b7f910a7a6f4276576f09aeb3f5cb9`), the
Wildcat V2 deployment `wildcat-v2-hooksfactory`, in 3,463 shards of 1,200
blocks. Every subject the pinned registry names is collected -- 137 in all,
including the `WildcatArchController`, the `HooksFactory`, every
`HooksTemplate` and `HooksInstance`, every registered market and its own
market-init-code storage, the sanctions sentinel, the role providers, the fee
recipient, the wrapper factory and the lens -- not a curated subset of them.

Three of those 137 are the collateral trio: `WildcatMarketCollateralFactory`
(`WildcatCollateralFactoryV1`) at
`0xbdf64bd7ea91a534445d06736a0f0e2a33ffa47c`, the
`SimpleMarketCollateralMultiParty` init-code storage at
`0xbbb998043a20a26828617769f37dc3980be25ebc`, and `CollateralLens` at
`0x422489ba6bddd5954c379c41b6c97ab0e4494f90`. Laurence stated on 2026-09-20
that these three are deployed on mainnet but not in production -- unused, not
reachable from the front end. They are collected and preserved like every
other subject because they are part of the pinned registry's 137, but nothing
here describes them as live V2, and nothing here drops them from the 137.

Each shard preserves `boundary-blocks` and `logs` the way earlier Alexandria
interval releases do. `traces` are collected differently: rather than one
blanket `trace_filter` call per shard, the collector derives the distinct
transaction hashes named by that shard's own `logs` result and makes one
`trace_transaction` call per hash, then filters the results to the same
`toAddress`-shaped subject membership a `trace_filter` call would have
applied -- call actions by `to`, create actions by the created address,
suicide actions by the refund address, reward actions by the block's miner --
and stages the combined result as exactly one `traces` record per shard. 404
of the 3,463 shards carry neither a log nor a targeted trace. Transactions
without a matching subject log were not traced, so an empty shard does not
establish that its subjects had no calls or state changes.

The two providers agreed on all 124,200 comparisons the reconciliation made,
nothing disputed: every shard's boundary-block hash, every preserved log, and
every preserved targeted-trace identity. That recorded comparison did not
compare trace action, result, error or location content. A new reconciliation
with the repaired comparator is needed to establish agreement on those fields.
The primary transport answered as a local archive node, trace-
enabled, reached over loopback; the second, reconciling transport answered as
a hosted HTTPS RPC provider, archive- and trace-enabled, bearer-authenticated.
Neither endpoint nor credential is recorded here or anywhere else in the
repository. The optional bearer is read from the environment and sent only in
the second transport's request-scoped Authorization header.

The release identifier is
`sha256:d76cce047564818a5ff3ccf1b730ba16fca20a05037f96f870b3e076f9e4ad35`,
built across 137 epoch-table entries (one per subject). It is fixed by the
preserved bytes and the demonstration's pinned created-at timestamp; one
changed byte in one journal changes it, and `verify` catches that.

## What it does not establish

Agreement between two providers is agreement, not proof. This establishes no
publisher identity, no provider completeness, no consensus finality and no
canonical-chain membership: `finalized` here is the operator policy the plan
pinned and the boundary block the collector re-read, nothing more. It derives
no credit event; that mapping belongs to a component this example does not
build.

The collateral trio's deployment does not mean production use -- see the
dated statement above. Their presence in the 137 records that they exist on
mainnet at the stated addresses, not that they carry traffic.

`build` and `verify` reach no network; a test asserts neither opens a socket.
The two live reads that produced the preserved bytes happened once, outside
this repository, by the runbook step that collected them.

## Files

- `plan.json` is the interval plan the live collection ran, with its evidence
  classes, its 3,463 shards, its finality boundary and the primary provider's
  class.
- `registry.json` is the pinned Wildcat V2 deployment registry the release
  carries -- all 137 entries, the collateral trio among them.
- `expected.json` pins what a correct rebuild produces: the release
  identifier, the epoch count, every subject's implementation code digest,
  the collected interval, the reconciliation status, the shard statuses and
  the receipt semantics.
- `staging-manifest.json` binds the preserved staging archive's own byte
  count and SHA-256 to the byte count and SHA-256 of every file it contains,
  so a corrupted or partial unpack is caught before a rebuild is even
  attempted.
- `rebuild-record.json` is the result this collecting host got when it
  actually rebuilt the release from the preserved staging tree, checked
  beside the manifest.
- `demo.py` is the offline-once-staged path: `build` and `verify` need the
  preserved staging tree unpacked locally; `verify-preserved` needs neither
  the staging tree nor the network, checking the manifest and rebuild record
  against `expected.json` alone.
