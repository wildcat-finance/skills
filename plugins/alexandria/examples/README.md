# Alexandria examples

<!-- marketplace-context:start -->
> **Marketplace context: Alexandria.** Alexandria preserves heterogeneous lending data as digest-bound releases, then derives only the credit views a reviewed mapping can defend. Use Tabularium when the job is semantic event mapping, Probitas when the deliverable is a counterparty dossier, and Lazarus when a test needs finite historical state or exact RPC replay. **Current frontier:** A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.
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

[`compound-v3-phase0-v0`](compound-v3-phase0-v0/README.md) preserves the
pinned Comet registry and exact RPC corpus for one old and one recent Ethereum
USDC transaction. It rebuilds and checks the raw release offline; it is a
method proof, not an interval history.
