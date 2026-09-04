# Euler preservation study

<!-- marketplace-context:start -->
> **Marketplace context: Tabularium.** Tabularium maps preserved venue-native records into reproducible, venue-qualified credit events without discarding the source or flattening its meaning. Use Alexandria to collect and preserve heterogeneous lending data, Probitas for a counterparty dossier, and Lazarus for proof-checked historical state or exact RPC replay. **Current frontier:** Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
<!-- marketplace-context:end -->

Issue [#57](https://github.com/wildcat-finance/skills/issues/57) ordered
Tabularium preservation and reproducible offline verification after the Euler
adapters landed in Probitas. PR #65 closed the issue after shipping the
Probitas portion, but changed no Tabularium file.

Tabularium's original builder, release manifest and verifier understood only
Aave v4 and canonical schema v1. The existing Probitas adapters supplied
useful source-shape and semantic checks, but their dossier records omit native
detail that a preservation release needs. Their checked-in Euler fixtures are
synthetic and cannot stand in for captured production evidence.

The selected design leaves every Aave v4 release byte and v1 validator
unchanged. Adapter dispatch adds canonical event and coverage schema v2, then
two self-contained release directories bind real, narrow source responses.
The Euler v1 release preserves canonical-proxy logs for one borrower and block.
The Euler V2 release preserves one owner/second activity response from the
hosted Euler V3 API. Each verifier rebuilds canonical bytes from local source
bytes and rejects path, digest, count, selector, order, scope or mapping drift.

Version naming needed a separate decision. Euler's current developer guide
calls the lending protocol Euler V2 and its hosted indexed-data service the
Euler V3 API. Euler Lite likewise uses the Euler V2 SDK through that backend.
An official liquidation bot README uses “Euler V3 lending protocol”, but its
code still targets EVC and EVault. The release therefore records
`protocol_generation: euler-v2` and `source_api: euler-v3` independently. An
API path or repository name cannot create a protocol-generation claim.
This run considered Euler V3 explicitly. The inspected primary sources did
not establish a third architecture or history source separate from EVC,
EVault and the V3 API. A future distinct protocol generation would need its
own adapter and source-bound release.

The source limits remain explicit. The public RPC and hosted indexer report
their boundaries; neither release independently proves a chain boundary.
Euler V2 rows omit block hashes, transaction indexes and some underlying token
addresses. The one-block and one-second samples are not complete borrower,
account or venue histories. Both releases are unsigned.

Rejected designs were relabelling synthetic fixtures as production releases,
widening schema v1 in place, and waiting for a venue-wide archival service.
The first would overstate the evidence, the second would change old release
meaning, and the third was not a dependency of issue #57.

Primary version sources:

- https://docs.euler.finance/developers/
- https://docs.euler.finance/developers/data-querying/euler-v3-api/
- https://github.com/euler-xyz/euler-lite
- https://github.com/euler-xyz/euler-interfaces
- https://github.com/euler-xyz/liquidation-bot-v3

Repository evidence:

- `plugins/probitas/docs/euler-goldsky-discovery.md`
- `plugins/tabularium/docs/release-policy.md`
- `plugins/tabularium/docs/compound-v3-preservation.md`
