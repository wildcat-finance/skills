# Preserved Aave V3 Ethereum segments, v0

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Ordinary builds now emit `alexandria-interval-receipt/v2`, which attributes each preserved proxy log to an implementation epoch by block, transaction index and log index, and `check` re-derives every owner offline; reconciliation still compares a log without its transaction index, so a second provider that reports a different index for the same log records `agreed`.
<!-- marketplace-context:end -->

The Aave V3 Ethereum main-market interval, blocks 16,291,071 to 26,022,093, is
captured as twelve contiguous segment releases, one per plan in
`segments.json`. Each segment was collected from the local archive node,
reconciled against the hosted transport, built and checked on the collecting
host. All twelve are preserved here. The twelve staging trees are too large to
check in, so they are held outside this repository as one archive and bound by
digest.

```bash
export ALEXANDRIA_AAVE_V3_STAGING=/path/to/unpacked/segments
python3 plugins/alexandria/examples/aave-v3-interval-v0/demo.py build --output <directory>
python3 plugins/alexandria/examples/aave-v3-interval-v0/demo.py verify <directory>
python3 plugins/alexandria/examples/aave-v3-interval-v0/demo.py verify-preserved
```

`ALEXANDRIA_AAVE_V3_STAGING` names a directory holding one unpacked tree per
segment, at `segment-<index>`. Unpacking the archive into an empty directory
makes exactly that layout, because every member is named
`segment-<index>/<path>`:

```bash
mkdir /path/to/unpacked/segments
zstd -dc aave-v3-ethereum-capture-staging.tar.zst | tar -x -C /path/to/unpacked/segments
```

A full unpacking is 94,973,293,482 bytes in 61,577 files, and
`build` writes twelve releases of 1.2 GB to 12.6 GB each, 102,842,768,826 bytes in
all, so give the two together about 200 GB of free space. A directory that
lacks a committed segment's tree refuses by name for that segment. Without the
variable, `build` refuses by name. Before any rebuild it compares every file in each
tree with that segment's section of `staging-manifest.json`, and refuses by
path on a file the manifest does not list, a listed file the tree lacks, a
changed byte count or digest, or a symlink. It then rebuilds each release with
Python socket construction denied and checks it. `verify` re-derives each
release identifier, epoch count, implementation code digest, interval,
reconciliation status and journal binding, shard status, evidence-class count
and component total, and compares them with that segment's `expected.json`.

`verify-preserved` needs neither the staging trees nor the network. It checks
the staging manifest, and for every committed segment its rebuild record and
expected values, against each other, against the segment table and against the
plan digests `SEGMENT_PLAN_SHA256` pins in the Aave venue module. It prints
`rebuild_performed: false` and the number of segments with a rebuild record,
which is twelve.

## The archive

One tar+zstd archive holds all twelve staging trees: 4,288,061,802 bytes,
SHA-256 `45dc114a35ed9483fc5347827b048348308708766f299f857512a0ccc004e55a`. Members are every regular file of
`staging/segment-0` to `staging/segment-11`, named `segment-<index>/<path>`,
sorted by that path, in PAX format with mtime 0, uid and gid 0, empty owner
names and mode 0644, compressed with zstd level 6 on one thread. It was built
twice with identical bytes. `staging-manifest.json` binds that byte count and
digest and, in one section per segment, every staged file by path, byte count
and SHA-256.

Before the archive was made, every staging file was searched for the endpoints
and bearers in the collecting host's three credential files, their host names,
the primary's loopback address and any URL scheme, and none matched. Each
segment's rebuild record keeps its own count of files and bytes searched.

## Segments

| Segment | Blocks | Shards | Staged files | Staged bytes | Release identifier | Epochs | Components | Release bytes |
| ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| 0 | 16,291,071 to 17,519,870 | 4,096 | 4,102 | 1,109,588,761 | `sha256:6ffed3c87f01a62cf511b6cfe93527055116f0e53f9953f88074a1817cadaae5` | 93 | 5,471 | 1,197,031,879 |
| 1 | 17,519,871 to 18,748,670 | 4,096 | 4,102 | 2,516,524,513 | `sha256:37b5b3ceda4cab52eac86d02ff6ba36f3b1305a322ae97f185506ef5203b7b78` | 145 | 5,471 | 2,711,059,453 |
| 2 | 18,748,671 to 19,977,470 | 4,096 | 4,102 | 4,496,566,689 | `sha256:0a9e289c6c82d138098212a1bd98abf6ddd57b12386314c4cf284914982bb7b0` | 189 | 5,471 | 4,844,943,720 |
| 3 | 19,977,471 to 21,206,270 | 4,096 | 6,149 | 7,443,858,509 | `sha256:0f6fad63f7f172a58d88cd0b9d8bf7ed5eec4d1a0ec9fb6e08880239f18e7f4e` | 246 | 8,199 | 8,035,993,652 |
| 4 | 21,206,271 to 21,969,470 | 2,544 | 2,550 | 8,521,551,062 | `sha256:5d298fe06928bd319b490a7848469917ada7fe36ac106b9569187a68dc16daa4` | 257 | 3,399 | 9,304,917,238 |
| 5 | 21,969,471 to 22,508,570 | 1,797 | 5,400 | 7,563,175,541 | `sha256:ad025388c33045dcb845c8e93c65f0754e25e91943575bcaaef7e3cc78690e81` | 265 | 7,195 | 8,216,902,040 |
| 6 | 22,508,571 to 23,160,470 | 2,173 | 6,527 | 11,069,641,278 | `sha256:c813f14d88eb1e31cec1437bf6d446a204c56e9a8a2afa2291f1ec63014a410a` | 505 | 8,699 | 11,986,935,698 |
| 7 | 23,160,471 to 23,653,670 | 1,644 | 4,940 | 10,237,485,010 | `sha256:801d0ac1893b7dfe9f56c258b2c1078fd5fe9132485923164de6cc2c81ae5588` | 314 | 6,583 | 11,086,871,406 |
| 8 | 23,653,671 to 24,268,970 | 2,051 | 6,158 | 11,484,242,063 | `sha256:788d17bb4d3125ec0a88c8b040c69692a8db86799d10fffcc8a096400a3e8c1d` | 457 | 8,211 | 12,459,902,146 |
| 9 | 24,268,971 to 24,750,170 | 1,604 | 4,817 | 11,681,346,488 | `sha256:b0162b1300f36ba9cfa685ad8a87b9259ad89820ed89d95ae4ff4f1104f68f6d` | 341 | 6,423 | 12,622,531,842 |
| 10 | 24,750,171 to 25,243,370 | 1,644 | 4,937 | 8,111,546,643 | `sha256:6eefbd09416aeb025e561f168a91053c9e53e36f1a99adba46ea1fc639e42ad8` | 356 | 6,583 | 8,782,528,636 |
| 11 | 25,243,371 to 26,022,093 | 2,596 | 7,793 | 10,737,766,925 | `sha256:7e6adeaf1f1ff2ab7abf938f5e50ef03a0f3eb5770c8480f08dda05a346ab6e0` | 356 | 10,391 | 11,593,151,116 |

Every release declares 356 registry subjects and carries no constructed-staging
gap, because `aave-v3-ethereum-main` is admitted for the pinned plan digests.
For each segment a fresh extraction from the archive rebuilt the identifier
above with Python socket construction denied, and `check` and `verify` passed
on it. Each rebuilt manifest is byte-identical to the collected release's.
Every reconciliation is `agreed` with none disputed, between the primary, a
local archive node, trace-enabled, over loopback, and the second provider, a
hosted HTTPS RPC provider, archive- and trace-enabled, bearer-authenticated.
Every plan binds the same finality boundary: `finalized` at block 26,022,093,
hash `0x1cfd09b6dfaa2af921e367d94f24e2b1e6b7f910a7a6f4276576f09aeb3f5cb9`.

Segment 4 was reconciled before the journal binding of skills#1912 existed, so
its release carries the gap "the reconciliation record has no journal digest
binding" and its `reconciliation_binding` status is `absent`. The other eleven
report `verified`.

Segments 5, 6 and 7 were repaired. Their first reconciliations ended disputed
on one, eleven and six trace shards. The primary node's traces for those shards
were collected again with `recollect`; segments 5 and 6 were then reconciled
again in full and segment 7 with the carry-forward mode, and each ended agreed.
The disputed rows stay in the archived staging trees, and each rebuild record
lists the recollected shards. Segment 5 keeps the created-at timestamp of its
first build.

## Time and size against the plan

The rebuild record keeps each figure beside the segment table's plan. Peak
memory is the larger of the collecting host's `build` and `check` peaks.
Collect and reconcile seconds are the processes' own elapsed times, summed over
their invocations; the table plans no per-segment time, so elapsed time has no
plan to overrun.

| Segment | Planned release bytes | Built | Planned peak memory | Recorded | Collect s | Collect runs | Reconcile s | Reconcile runs | Compared |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 1,702,267,283 | 1,197,031,879 | 10,616,674,913 | 4,036,935,680 | 8,265 | 4 | 1,203 | 1 | 1,211,634 |
| 1 | 4,140,556,026 | 2,711,059,453 | 25,823,757,364 | 8,568,979,456 | 13,282 | 8 | 1,283 | 1 | 2,928,558 |
| 2 | 5,169,421,734 | 4,844,943,720 | 32,240,571,491 | 14,950,481,920 | 19,115 | 14 | 1,957 | 1 | 5,310,980 |
| 3 | 8,788,093,921 | 8,035,993,652 | 54,809,451,600 | 24,932,139,008 | 25,493 | 36 | 2,958 | 1 | 8,883,698 |
| 4 | 14,565,484,003 | 9,304,917,238 | 90,841,790,912 | 29,785,587,712 | 19,097 | 34 | 32,019 | 11 | 10,388,802 |
| 5 | 14,565,037,584 | 8,216,902,040 | 90,839,006,693 | 25,866,797,056 | 27,700 | 38 | 24,235 | 22 | 9,151,969 |
| 6 | 14,565,538,177 | 11,986,935,698 | 90,842,128,784 | 37,497,012,224 | 32,064 | 45 | 28,389 | 21 | 13,289,271 |
| 7 | 14,566,830,496 | 11,086,871,406 | 90,850,188,700 | 34,314,928,128 | 40,128 | 44 | 19,581 | 3 | 12,157,849 |
| 8 | 14,563,773,835 | 12,459,902,146 | 90,831,124,962 | 38,401,081,344 | 52,314 | 49 | 5,365 | 1 | 13,581,626 |
| 9 | 14,565,771,218 | 12,622,531,842 | 90,843,582,210 | 38,397,132,800 | 36,376 | 58 | 5,730 | 1 | 13,937,369 |
| 10 | 14,568,868,988 | 8,782,528,636 | 90,862,902,336 | 27,251,933,184 | 25,788 | 36 | 4,072 | 1 | 9,802,505 |
| 11 | 14,568,385,284 | 11,593,151,116 | 90,859,885,578 | 35,366,928,384 | 38,518 | 46 | 5,276 | 1 | 12,864,604 |

No recorded figure exceeds its plan.
Most collect invocations stopped at the collector's per-invocation byte
ceiling and resumed; the others stopped on a primary transport failure or a
JSON-RPC error and are named in the record. The collecting host's execution
logs hold the wall-clock detail, including host sleeps and node waits, and
each record binds its log by digest.

## How this differs from the Wildcat V2 example

Twelve releases force four changes. Metadata lives under `segments/<index>/`
rather than beside `demo.py`. One `staging-manifest.json` binds the single
archive and holds one file section per segment, because the archive is one object. The staging variable names a directory of per-segment
trees rather than one tree. `verify-preserved` prints a per-segment summary
rather than the whole manifest and record, because the manifest alone lists
61,577 files.

## What it does not establish

Agreement between two providers is agreement, not proof. This establishes no
publisher identity, no provider completeness, no consensus finality and no
canonical-chain membership. Reconciliation compares each log without its
`transactionIndex`, and the release says so. Targeted traces cover only
transactions a subject log names. No credit event is derived.

The socket denial is an observed Python boundary, not operating-system
isolation. The collection and reconciliation ran outside this offline
demonstration; the rebuild records keep their timings from the collecting
host's execution logs, which are bound by digest and not committed. The
demonstration's own `build` and `verify` were not run over all twelve trees at
once for the committed records: each segment was rebuilt from its own fresh
extraction with the collector's `build`, `check` and `verify` commands, and
its expected values were derived with this file's `derive` function.

## Files

- `segments.json` is the pinned segment table: each segment's interval, plan
  digest, shard count, component ranges and planned bytes.
- `plans/segment-<index>.json` is each segment's plan, pinned by digest.
- `registry.json` is the pinned 356-subject registry every release carries.
- `staging-manifest.json` binds the one capture archive by byte count and
  SHA-256 and, per segment, every staged file the same way.
- `segments/<index>/rebuild-record.json` records the credential search before
  archiving, the fresh extraction of that segment, the socket-denied build,
  `check` and `verify`, the reconciliation, and the collect and reconcile
  timings beside the planned bytes.
- `segments/<index>/expected.json` pins what a correct rebuild produces.
- `demo.py` holds `build`, `verify` and `verify-preserved`.
