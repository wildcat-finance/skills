# Alexandria evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `alexandria-v0.3.0`
- Frontier status: `open`
- Frontier revision: `usdc-interval-collector`
- Current frontier: Compound v3 Phase 0 now pins the Comet registry and preserves one verified Ethereum execution witness; a resumable, reconciled Ethereum USDC interval harvester remains unimplemented.
- Next Fiat job: Build the first resumable Ethereum USDC interval collector with implementation-epoch discovery, bounded shards, a second-provider reconciliation path, explicit finality and offline raw-release verification. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `alexandria-v0.2.0` | baseline | `usdc-interval-collector` | `d5afa30db4e5769dccded9f28be061dc623e119b328dbbcd87b729567b7eaeff` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `alexandria-v0.3.0` | generation | `usdc-interval-collector` | `d5afa30db4e5769dccded9f28be061dc623e119b328dbbcd87b729567b7eaeff` | [release statement](../../docs/release-statements.md) | Adds the deterministic unsigned release-statement emitter and schema without changing the held frontier or claiming signing, publisher identity, provider completeness, consensus finality or canonical-chain status. |
