# Alexandria examples

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** Ordinary builds now emit `alexandria-interval-receipt/v2`, which attributes each preserved proxy log to an implementation epoch by block, transaction index and log index, and `check` re-derives every owner offline; reconciliation still compares a log without its transaction index, so a second provider that reports a different index for the same log records `agreed`.
<!-- marketplace-context:end -->

[`credit-history-v0`](credit-history-v0/README.md) runs the checked-in offline
path from existing Aave v4 and Clearpool source bytes through raw release,
derived credit view, address index and Probitas's five dossier gates. Its plan
pins the original repository files rather than duplicating them.

[`usdc-interval-v0`](usdc-interval-v0/README.md) runs the resumable Ethereum
USDC interval collector end to end with no network: it collects five shards, is
killed once mid-shard and resumed, reconciles against a second fixture
provider, builds the release and verifies it. Its fixtures are synthetic and
were not observed on any chain.

[`usdc-interval-live-v0`](usdc-interval-live-v0/README.md) preserves a real
Ethereum USDC interval, blocks 25,903,935 to 25,905,934, collected once from
two live providers and agreed between them. The checked-in staging tree rebuilds
the release offline to the identifier the example pins, across two
implementation epochs whose runtime code the release carries and re-hashes.

[`usdc-interval-epochs-v0`](usdc-interval-epochs-v0/README.md) builds
`alexandria-interval-receipt/v2` releases with no network. Over a synthetic
upgrade block it pins each log's owner, including a proxy log earlier in that
block that stays with the preceding implementation. It rebuilds the live
interval's unchanged staging bytes under a new identifier and records the
refusals for moved owners, moved boundaries and ordinary logs inside the
upgrade transaction.

[`compound-v3-phase0-v0`](compound-v3-phase0-v0/README.md) preserves the
pinned Comet registry and exact RPC corpus for one old and one recent Ethereum
USDC transaction. It rebuilds and checks the raw release offline; it is a
method proof, not an interval history.

[`proof-backed-state-v0`](proof-backed-state-v0/README.md) embeds a small
synthetic Lazarus fixture in an Alexandria release. Verification reconstructs
the fixture by digest, reruns Lazarus and accepts only the proved block and
subjects; the fixture establishes nothing about a real chain.

[`wildcat-v2-interval-v0`](wildcat-v2-interval-v0/README.md) preserves the
real Wildcat V2 mainnet interval, blocks 21,866,550 to 26,022,093, across all
137 registry subjects, collected once from two live transports and agreed
between them on every comparison. Its staging tree is too large to check in
and is preserved outside this repository, verified by a committed manifest
that binds the archive's digest to every file inside it; a separate, offline
check confirms that manifest and the recorded rebuild agree with the pinned
expectation with no staging tree needed, and `demo.py build` rebuilds the
release itself once the preserved tree is unpacked locally.

[`wildcat-v1-interval-v0`](wildcat-v1-interval-v0/README.md) preserves mainnet
blocks 18,743,513 to 22,074,622 for all 16 V1 subjects, in 667 complete shards
with 4,325 agreed comparisons. Its manifest binds 107 externally preserved
staging files. The offline build reproduces the release once those files are
available; a separate metadata check needs no archive. The shared Sentinel has
no recorded logs in either live interval; positive shared-subject attribution
is also tested with constructed captures.
