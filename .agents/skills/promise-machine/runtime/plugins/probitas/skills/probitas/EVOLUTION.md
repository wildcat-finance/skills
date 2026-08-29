# Probitas evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `probitas-v0.2.0`
- Frontier status: `open`
- Frontier revision: `morpho-midnight-coverage`
- Current frontier: Euler v1/v2 now ship; Morpho Midnight fixed-maturity coverage and curation remain unimplemented.
- Next Fiat job: Add fail-closed Morpho Midnight fixed-maturity coverage so a dossier can establish whether repayment was timely. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `probitas-v0.1.0` | baseline | `morpho-midnight-coverage` | `5f66077a0c39a9ee647bd34233504b3891493f864fe4a16a9eb0c0337b3ee688` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `probitas-v0.2.0` | generation | `morpho-midnight-coverage` | `5f66077a0c39a9ee647bd34233504b3891493f864fe4a16a9eb0c0337b3ee688` | [skills#391](https://github.com/wildcat-finance/skills/issues/391), with the chosen design and the three options that lost in [the study](../../../../docs/probitas-unified-collection-study.md) | One `collect` run now gathers the adapter route and the archive route together, so archive-backed Goldfinch and Clearpool history can share an evidence file with live or fixture-backed Wildcat, Morpho Blue and Euler findings. Every coverage row names the route that produced it from a closed vocabulary, an archive row names the Alexandria releases behind it, and gate 2 counts rows on the venue and the source together rather than collapsing the ones that share a venue. The evidence schema becomes 2 and a schema 1 file is refused by name. An index passed on its own still suppresses the adapter route and reaches no network, so no existing invocation widens what it reaches; `--live` is how a run asks for the network beside one. Frontier unchanged: the held Morpho Midnight job is untouched. |
