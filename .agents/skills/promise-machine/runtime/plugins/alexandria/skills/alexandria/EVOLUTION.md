# Alexandria evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `alexandria-v0.4.0`
- Frontier status: `open`
- Frontier revision: `usdc-interval-collector`
- Current frontier: Compound v3 Phase 0 now pins the Comet registry and preserves one verified Ethereum execution witness; a resumable, reconciled Ethereum USDC interval harvester remains unimplemented.
- Next Fiat job: Build the first resumable Ethereum USDC interval collector with implementation-epoch discovery, bounded shards, a second-provider reconciliation path, explicit finality and offline raw-release verification. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `alexandria-v0.2.0` | baseline | `usdc-interval-collector` | `d5afa30db4e5769dccded9f28be061dc623e119b328dbbcd87b729567b7eaeff` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `alexandria-v0.3.0` | generation | `usdc-interval-collector` | `d5afa30db4e5769dccded9f28be061dc623e119b328dbbcd87b729567b7eaeff` | [release statement](../../docs/release-statements.md) | Adds the deterministic unsigned release-statement emitter and schema without changing the held frontier or claiming signing, publisher identity, provider completeness, consensus finality or canonical-chain status. |
| `alexandria-v0.4.0` | generation | `usdc-interval-collector` | `d5afa30db4e5769dccded9f28be061dc623e119b328dbbcd87b729567b7eaeff` | [skills#391](https://github.com/wildcat-finance/skills/issues/391) | The Probitas bridge now returns each coverage row's release identities as a `releases` field beside the note that already named them in prose, so a Probitas gate can require an archive row to name what it stands on without parsing another plugin's sentences. A row with no records has no record to derive them from, which is exactly the empty archive row that most needs them. The demonstration's pinned Probitas digests are regenerated for the new evidence schema and its coverage status counts are unchanged. Frontier unchanged: the held USDC interval-collector job is untouched. |
