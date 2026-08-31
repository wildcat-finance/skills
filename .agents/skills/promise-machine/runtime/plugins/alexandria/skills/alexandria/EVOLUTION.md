# Alexandria evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `alexandria-v1.4.0`
- Frontier status: `open`
- Frontier revision: `usdc-interval-live-boundaries`
- Current frontier: A resumable Ethereum USDC interval collector now shards, reconciles and verifies offline; it has never run against a live provider, reads no start block and preserves no implementation code.
- Next Fiat job: Run the Ethereum USDC collector against two live providers, read the interval's first block so a finalized scope binds both boundary hashes, and preserve the implementation code each epoch names so its code hash can be rechecked offline.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `alexandria-v0.2.0` | baseline | `usdc-interval-collector` | `d5afa30db4e5769dccded9f28be061dc623e119b328dbbcd87b729567b7eaeff` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `alexandria-v0.3.0` | generation | `usdc-interval-collector` | `d5afa30db4e5769dccded9f28be061dc623e119b328dbbcd87b729567b7eaeff` | [release statement](../../docs/release-statements.md) | Adds the deterministic unsigned release-statement emitter and schema without changing the held frontier or claiming signing, publisher identity, provider completeness, consensus finality or canonical-chain status. |
| `alexandria-v0.4.0` | generation | `usdc-interval-collector` | `d5afa30db4e5769dccded9f28be061dc623e119b328dbbcd87b729567b7eaeff` | [skills#391](https://github.com/wildcat-finance/skills/issues/391) | The Probitas bridge now returns each coverage row's release identities as a `releases` field beside the note that already named them in prose, so a Probitas gate can require an archive row to name what it stands on without parsing another plugin's sentences. A row with no records has no record to derive them from, which is exactly the empty archive row that most needs them. The demonstration's pinned Probitas digests are regenerated for the new evidence schema and its coverage status counts are unchanged. Frontier unchanged: the held USDC interval-collector job is untouched. |
| `alexandria-v1.4.0` | evolution | `usdc-interval-live-boundaries` | `5e225140ccbe4328e07e733ec28f972ff42760f88685109d05a1acd626837372` | [skills#395](https://github.com/wildcat-finance/skills/issues/395), [study](../../docs/usdc-interval-study.md) | The held collector job is delivered. `usdc_interval.py` collects a declared Ethereum USDC Comet interval in bounded shards from an injected transport, is resumable through a checkpointed journal per evidence class with a bounded reorg rewind, discovers code-hash-bound implementation epochs from preserved chain evidence, reconciles the finished interval against a second provider without settling a disagreement, binds its end boundary under a named finality policy, and builds a release the existing `ingest` accepts and a new offline check verifies. The frontier stays open: nothing has run against a live provider, the interval's first block is never read so a scope's finality class is `provider-reported` rather than the policy it names, and no implementation code is preserved, so an epoch's code hash cannot be rechecked from the release. |
