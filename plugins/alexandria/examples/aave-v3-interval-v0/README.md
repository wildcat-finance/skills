# Preserved Aave V3 Ethereum segments, v0

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Ordinary builds now emit `alexandria-interval-receipt/v2`, which attributes each preserved proxy log to an implementation epoch by block, transaction index and log index, and `check` re-derives every owner offline; reconciliation still compares a log without its transaction index, so a second provider that reports a different index for the same log records `agreed`.
<!-- marketplace-context:end -->

The Aave V3 Ethereum main-market interval, blocks 16,291,071 to 26,022,093, is
captured as twelve contiguous segment releases, one per plan in
`segments.json`. Each segment is collected from the local archive node,
reconciled against the hosted transport, built and checked on the collecting
host. Its staging tree is too large to check in, so it is
held outside this repository and bound by digest.

Segment 4 is preserved. The other eleven are not yet committed here, and
`verify-preserved` lists them by index as segments without a rebuild record.

```bash
export ALEXANDRIA_AAVE_V3_STAGING=/path/to/unpacked/segments
python3 plugins/alexandria/examples/aave-v3-interval-v0/demo.py build --output <directory>
python3 plugins/alexandria/examples/aave-v3-interval-v0/demo.py verify <directory>
python3 plugins/alexandria/examples/aave-v3-interval-v0/demo.py verify-preserved
```

`ALEXANDRIA_AAVE_V3_STAGING` names a directory holding one unpacked tree per
committed segment, at `segment-<index>`. Without the variable, `build` refuses
by name. Before any rebuild it compares every file in each tree with that
segment's staging manifest, and refuses by path on a file the manifest does not
list, a listed file the tree lacks, a changed byte count or digest, or a
symlink. It then rebuilds each release with Python socket construction denied
and checks it. `verify` re-derives each release identifier, epoch count,
implementation code digest, interval, reconciliation status, shard status,
evidence-class count and component total, and compares them with that
segment's `expected.json`.

`verify-preserved` needs neither the staging trees nor the network. For every
committed segment it checks the staging manifest, rebuild record and expected
values against each other, against the segment table and against the plan
digests `SEGMENT_PLAN_SHA256` pins in the Aave venue module. It prints
`rebuild_performed: false` and the number of segments with a rebuild record.

## Segment 4

Blocks 21,206,271 to 21,969,470 in 2,544 shards of 300 blocks, split into 848
component ranges per shard class, across all 356 registry subjects. The plan's
finality is `finalized` at block 26,022,093, hash
`0x1cfd09b6dfaa2af921e367d94f24e2b1e6b7f910a7a6f4276576f09aeb3f5cb9`.

The staging tree holds 2,550 files and 8,521,551,062 bytes: 2,545 journals,
the checkpoint, two primary-provider error receipts and the reconciliation
record with its checkpoint and ten retained second-provider transport errors.
The largest journal is 60,380,258 bytes. Every file was searched for the
second transport's endpoint, its host name and bearer, the primary's loopback
address and any URL scheme before the archive was made, and none matched. The
archive is 371,578,630 bytes, SHA-256
`aef14bc38a329f871ce9463922af31e191e55f2fcf6f48f6b6a26b19f47e5f20`, built
twice with identical bytes.

The release identifier is
`sha256:5d298fe06928bd319b490a7848469917ada7fe36ac106b9569187a68dc16daa4`,
with 257 epochs and 3,399 components totalling 9,304,917,238 bytes; the
largest is 60,380,380 bytes. A fresh extraction of the archive rebuilt that
identifier with Python socket construction denied, and `check` and `verify`
passed on it. The rebuilt manifest is byte-identical to the collected
release's. The release carries no constructed-staging gap, because
`aave-v3-ethereum-main` is admitted for the pinned plan digests.

The reconciliation is `agreed`: 10,388,802 comparisons, all matched, none
disputed, between the primary, a local archive node, trace-enabled, over
loopback, and the second provider, a hosted HTTPS RPC provider, archive- and
trace-enabled, bearer-authenticated. It took eleven invocations. Each of the
first ten ended `unreconciled` after one second-provider transport error, and
the eleventh resumed to `agreed`.

## Time and size against the plan

The rebuild record keeps each figure beside the segment table's plan.

| Figure | Planned | Recorded |
| --- | ---: | ---: |
| Release bytes | 14,565,484,003 | 9,304,917,238 |
| Components | 3,399 | 3,399 |
| Peak memory, bytes | 90,841,790,912 | 29,785,587,712 at `check` |
| Collect, seconds in process | none planned | 19,097 over 34 invocations |
| Reconcile, seconds in process | none planned | 32,019 over 11 invocations |

Collection ran from 19:13:12Z on 2026-09-24 to 01:13:06Z on 2026-09-25.
Thirty-one invocations stopped at the collector's per-invocation byte ceiling
and resumed, one stopped on a primary transport failure at shard 406 and one
on a primary JSON-RPC error at shard 1201. Reconciliation ran from 01:13:06Z to
10:17:37Z; the operator reports the host hibernated from 01:58Z to 05:25Z
inside one of those passes. No recorded figure exceeds its plan. The table
plans no per-segment time, so elapsed time has no plan to overrun.

## How this differs from the Wildcat V2 example

Twelve releases force three changes. Metadata lives under
`segments/<index>/` rather than beside `demo.py`. The staging variable names
a directory of per-segment trees rather than one tree. `verify-preserved`
prints a per-segment summary rather than the whole manifest and record,
because one segment's manifest alone lists 2,550 files. Segments not yet
committed are counted and named, and never pass.

## What it does not establish

Agreement between two providers is agreement, not proof. This establishes no
publisher identity, no provider completeness, no consensus finality and no
canonical-chain membership. Reconciliation compares each log without its
`transactionIndex`, and the release says so. Targeted traces cover only
transactions a subject log names. No credit event is derived.

The socket denial is an observed Python boundary, not operating-system
isolation. The collection and reconciliation ran outside this offline
demonstration; the rebuild record keeps their timings from the collecting
host's execution log, which is bound by digest and not committed.

## Files

- `segments.json` is the pinned segment table: each segment's interval, plan
  digest, shard count, component ranges and planned bytes.
- `plans/segment-<index>.json` is each segment's plan, pinned by digest.
- `registry.json` is the pinned 356-subject registry every release carries.
- `segments/<index>/staging-manifest.json` binds one segment's archive, and
  every file in it, by byte count and SHA-256.
- `segments/<index>/rebuild-record.json` records the credential search before
  archiving, the fresh extraction, the socket-denied build, `check` and
  `verify`, the reconciliation, and the collect and reconcile timings beside the
  planned bytes.
- `segments/<index>/expected.json` pins what a correct rebuild produces.
- `demo.py` holds `build`, `verify` and `verify-preserved`.
