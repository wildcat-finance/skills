# Preserved Ethereum USDC interval, live v0

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector has now run against two live providers over an Ethereum mainnet interval, binding both boundary hashes under a finalized scope and preserving each epoch's implementation code so its code hash is rechecked offline; the epoch table still attributes a log by block rather than by transaction position.
<!-- marketplace-context:end -->

The interval this example preserves was collected once, from two live
providers, by the runbook step that created it. Everything below runs offline
over those preserved bytes:

```bash
python3 plugins/alexandria/examples/usdc-interval-live-v0/demo.py build --output <directory>
python3 plugins/alexandria/examples/usdc-interval-live-v0/demo.py verify <directory>
```

`build` rebuilds the Alexandria release from the checked-in staging tree and
checks it. `verify` re-derives the release identifier, the epoch count, the
reconciliation status, both implementation code digests and the interval's two
boundary hashes from the rebuilt release, and compares them, and the recorded
summary, with `expected.json`.

## What was collected

Ethereum mainnet blocks 25,903,935 to 25,905,934, the Compound v3 USDC Comet
proxy `0xc3d688b66703497daa19211eedff47f25384cdc3`, in four shards of 500
blocks. The shards carry 47, 25, 6 and 15 logs, 93 in all, and each is bound by
its boundary block's hash. The interval opens at
`0xa4e35dad60b77815249c12cf22ad83056f2ad041ef9b6340dee03e83502d70f0` and closes
at `0xc0ac604f5eaf0b78ee147ed3cec4f5c5ab1f7d66d1607266cbf343d7bdc959bd`, and
every evidence scope in the release carries finality `finalized` with both.

The interval straddles an `Upgraded(address)` at block 25,904,935, log index
524 of transaction
`0xd6cfe9b49e659649961f350721ea52b42107293e4b0eed2671259d7b328d33f3`, so it
holds two epochs:

| Epoch | Blocks | Implementation | Runtime code SHA-256 |
| --- | --- | --- | --- |
| 1 | 25,903,935 to 25,904,934 | `0x83d491269720ce925f92c6bf9f66b7a0779a293a` | `93ac04f8ffb0962157af92ee7cf7c1583937d013bde1b6d592ec2a726d624b79` |
| 2 | 25,904,935 to 25,905,934 | `0x63e749153baf1838f63ca22c275370bd2b1ceb15` | `b942614560ef7218a52173cc501ce9198f74a558348edf957cda62a218aa20fe` |

Both digests are re-hashed by `check` out of the `implementation-code`
component the release ships, so neither is a number an operator declared.

The second transport agreed on all 106 comparisons with nothing disputed: the
four shard boundary hashes and their log sets, the interval's first block, each
implementation slot word and each code digest.

The release identifier is
`sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32`. It
is fixed by the preserved bytes and the demonstration's pinned created-at
timestamp; one changed byte in one journal changes it, and a test proves that.

## What it does not establish

The two providers are named by class, not by operator: the primary answered as
an archive gateway, public tier, no trace methods, and the second transport as
a public relay endpoint, archive logs and state, no trace methods. No endpoint
or credential is recorded here or anywhere else in the repository, and no
header this collector sends comes from the environment.

No traces were collected. Neither provider serves `trace_filter` without a
credential, so the plan declares `boundary-blocks` and `logs` only and every
evidence component's coverage names `traces` as an uncollected class with its
reason.

Agreement between two providers is agreement, not proof. This establishes no
publisher identity, no provider completeness, no consensus finality and no
canonical-chain membership: `finalized` here is the operator policy the plan
pinned and the boundary block the collector re-read, nothing more. It derives
no credit event; that mapping is Tabularium's.

Both commands here run with no network. Neither opens a socket, and a test
asserts it.

## Files

- `plan.json` is the interval plan the live collection ran, with its evidence
  classes, its shards, its finality boundary and its provider class.
- `registry.json` is the pinned Comet deployment registry the release carries.
- `staging/` is the capture: the shard journals, the `epoch-evidence` journal
  of the opening reads, the checkpoint and the reconciliation record, committed
  exactly as the providers answered them.
- `demo.py` is the offline path, `build` and `verify`.
- `expected.json` pins what that path produces.
