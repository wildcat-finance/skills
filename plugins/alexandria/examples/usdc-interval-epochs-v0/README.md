# Positional implementation epochs, v0

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Ordinary builds now emit `alexandria-interval-receipt/v2`, which attributes each preserved proxy log to an implementation epoch by block, transaction index and log index, and `check` re-derives every owner offline; reconciliation still compares a log without its transaction index, so a second provider that reports a different index for the same log records `agreed`.
<!-- marketplace-context:end -->

Both v2 releases and every probe, with no network:

```bash
python3 plugins/alexandria/examples/usdc-interval-epochs-v0/demo.py build --output <directory>
python3 plugins/alexandria/examples/usdc-interval-epochs-v0/demo.py verify <directory>
```

`build` collects a synthetic interval whose upgrade block, 15,331,626, holds an
ordinary proxy log at transaction index 1 and log index 3, the
`Upgraded(address)` announcement at 2 and 4, and an ordinary proxy log at 3
and 5. It reconciles against a second fixture provider, builds an
`alexandria-interval-receipt/v2` release and checks it. It then builds a second
v2 release from the unchanged staging bytes of
[`usdc-interval-live-v0`](../usdc-interval-live-v0/README.md). `verify`
re-checks both releases offline, re-runs every probe, and compares the results
with `expected.json`, `live-v2-expected.json` and the recorded summary.

## What it produces

The synthetic release is
`sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036`, with
`receipt_semantics` `v2-positional`, five complete shards, two implementation
epochs and reconciliation `agreed`. Its 17 preserved logs have these owners:

- the seven logs before the announcement, including the one earlier in the
  upgrade block, belong to `0x42f9505a376761b180e27a01ba0554244ed1de7d`;
- the announcement opens the epoch of
  `0x8b3e1f2a4c5d6e7f8091a2b3c4d5e6f708192a3b` as its `upgrade-boundary` row;
- the nine later proxy logs, including the one later in the upgrade block,
  belong to that replacement.

`expected.json` writes those owners out row by row. They were derived from the
positions alone, without calling the attribution code, and then compared with
the build.

The live v2 release is
`sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a`. The
same staging bytes still rebuild as v1 release
`sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32`
through the historical example, and `live-v2-expected.json` records both
identifiers. Its boundary sits at block 25,904,935, transaction index 193 and
log index 524; 72 proxy logs precede it and 20 follow it. `build` digests the
staging tree before and after the v2 build and refuses if the digest moved.

The probes record these refusals and one open gap:

| Probe | Recorded result |
| --- | --- |
| An ordinary log moved into the upgrade transaction, before or after the announcement | Collection refuses with error receipt code `malformed-upgrade-log` and names the block, transaction index and log index. |
| The synthetic release re-ingested under fresh digests with the earlier log moved to the replacement | `check` refuses: the log attributions do not match the ownership derived from preserved logs. |
| The same with the boundary moved one log later | `check` refuses: the epoch table does not match the epochs the opening reads derive. |
| The synthetic fixture's own first-block answer | The v2 build refuses, because that hash contradicts the block hash its first log carries. V1 never compared the two. |
| A second provider that differs only in the later log's transaction index, 0x3 against 0x7 | Reconciliation records `agreed` with no dispute. This is the gap the next Alexandria job names. |

## What it does not establish

The synthetic chain state is the
[`usdc-interval-v0`](../usdc-interval-v0/README.md) fixture, read under its
pinned digest, plus the literal upgrade constants in `demo.py`. Its hashes,
payloads and code were not observed on any chain, and the specimen answers the
first block with its first log's hash rather than the fixture's own answer.

An owner is an inference from the preserved announcement and log positions. It
does not prove which implementation executed or emitted a log. The live capture
carries no proxy log earlier in its upgrade block, so only the synthetic
release instantiates the before-upgrade case. Neither path opens a socket, and
a test asserts it.

## Files

- `demo.py` is both paths and every probe.
- `expected.json` pins the synthetic release, its literal owners and the probe
  results.
- `live-v2-expected.json` pins the live v2 rebuild, the historical v1
  identifier it must differ from, and the staging digest.
