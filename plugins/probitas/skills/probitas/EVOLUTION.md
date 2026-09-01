# Probitas evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `probitas-v1.3.0`
- Frontier status: `open`
- Frontier revision: `midnight-secondary-close-attribution`
- Current frontier: Morpho Midnight fixed-maturity coverage now ships API-scoped on Base; secondary-market borrow exits stay refused as unattributable and Morpho curation remains uncollected.
- Next Fiat job: Establish account-attributed debt units for a Morpho Midnight `exit_borrow_secondary` event so a secondary-market close reconciles into the debt ledger instead of refusing the collection.
- Venues: [../../../../VENUES.json](../../../../VENUES.json)

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `probitas-v0.1.0` | baseline | `morpho-midnight-coverage` | `5f66077a0c39a9ee647bd34233504b3891493f864fe4a16a9eb0c0337b3ee688` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `probitas-v0.2.0` | generation | `morpho-midnight-coverage` | `5f66077a0c39a9ee647bd34233504b3891493f864fe4a16a9eb0c0337b3ee688` | [skills#391](https://github.com/wildcat-finance/skills/issues/391), with the chosen design and the three options that lost in [the study](../../../../docs/probitas-unified-collection-study.md) | One `collect` run now gathers the adapter route and the archive route together, so archive-backed Goldfinch and Clearpool history can share an evidence file with live or fixture-backed Wildcat, Morpho Blue and Euler findings. Every coverage row names the route that produced it from a closed vocabulary, an archive row names the Alexandria releases behind it, and gate 2 counts rows on the venue and the source together rather than collapsing the ones that share a venue. The evidence schema becomes 2 and a schema 1 file is refused by name. An index passed on its own still suppresses the adapter route and reaches no network, so no existing invocation widens what it reaches; `--live` is how a run asks for the network beside one. Frontier unchanged: the held Morpho Midnight job is untouched. |
| `probitas-v1.2.0` | evolution | `midnight-secondary-close-attribution` | `f947d2653e33240e5f2d368cc6c952af5939c0187741fba04896a6d32aa9cbe2` | [example dossier](../../docs/example-dossier.md) | Fail-closed Morpho Midnight fixed-maturity coverage ships: a strict Base v0 adapter, registry and dossier integration, and a guarded maturity renderer. The held frontier advances to secondary-close attribution. |
| `probitas-v1.3.0` | generation | `midnight-secondary-close-attribution` | `f947d2653e33240e5f2d368cc6c952af5939c0187741fba04896a6d32aa9cbe2` | [skills#410](https://github.com/wildcat-finance/skills/issues/410), [statement tests](../../tests/test_statement.py) | A successful verify run can emit one canonical unsigned statement whose statement-level subject array binds the exact checked dossier and evidence bytes. Five claims record the passed gates against the dossier digest, and Ariadne keeps its unregistered-predicate boundary visible. The held frontier and next Fiat job are unchanged. |
