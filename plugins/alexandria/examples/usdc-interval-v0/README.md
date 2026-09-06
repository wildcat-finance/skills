# Ethereum USDC interval collector, v0

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.
<!-- marketplace-context:end -->

The whole collector, end to end, with no network:

```bash
python3 plugins/alexandria/examples/usdc-interval-v0/demo.py build --output <directory>
python3 plugins/alexandria/examples/usdc-interval-v0/demo.py verify <directory>
```

`build` collects the fixture interval in bounded shards and then its opening
reads, is killed once mid-shard and resumed, reconciles the finished interval
against the second fixture provider, builds the Alexandria release from the
journals alone and verifies it. `verify` re-derives the release identifier
from the built release, re-hashes the implementation code, and compares both,
and the recorded summary, with `expected.json`.

## What it produces

Five shards of twenty blocks over the Ethereum USDC Comet's declared interval,
one implementation epoch covering all of it, an agreement between the two
providers over 25 shard comparisons and 3 opening-read comparisons, and release
`sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa`. The
release carries ten components: the three evidence journals, the
`epoch-evidence` journal of opening reads, the `implementation-code` component
the epoch table names by digest, the epoch table, the error receipts, the
plan, the reconciliation record and the registry. Every evidence scope carries
finality `finalized` with the first block's hash and the last shard's. Two
builds of the same fixtures agree byte for byte.

## What it does not establish

The fixtures are synthetic. Block hashes, transaction hashes, log payloads and
the implementation code read are derived from fixed strings and were
not observed on any chain. Only the proxy address, the EIP-1967 implementation
slot and the `Upgraded(address)` topic are the real ones. Both paths run with
no network: neither opens a socket, and a test asserts it.

So this demonstrates the collector's behaviour, not a preserved Compound v3
record. It establishes no publisher identity, no provider completeness, no
consensus finality and no canonical-chain membership, and it derives no credit
event: the release's own coverage says all of that in its gaps.

## Files

- `demo.py` is the whole path, `build` and `verify`.
- `fixtures/primary.json` holds the first provider's synthetic chain state,
  the interval plan it answers for, and its answers to the opening reads: the
  first block's hash, one implementation slot word and one runtime code body.
- `fixtures/secondary.json` names the second provider's class and carries its
  own copies of the opening-read answers; it agrees with the first everywhere,
  and the tests cover what a disagreement does.
- `expected.json` pins what the path produces, including the implementation
  digest `check` re-hashes from the release.
