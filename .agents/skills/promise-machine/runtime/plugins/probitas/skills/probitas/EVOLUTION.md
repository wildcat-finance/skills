# Probitas evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `probitas-v1.1.0`
- Frontier status: `open`
- Frontier revision: `midnight-secondary-close-attribution`
- Current frontier: Morpho Midnight fixed-maturity coverage now ships API-scoped on Base; secondary-market borrow exits stay refused as unattributable and Morpho curation remains uncollected.
- Next Fiat job: Establish account-attributed debt units for a Morpho Midnight `exit_borrow_secondary` event so a secondary-market close reconciles into the debt ledger instead of refusing the collection.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `probitas-v0.1.0` | baseline | `morpho-midnight-coverage` | `5f66077a0c39a9ee647bd34233504b3891493f864fe4a16a9eb0c0337b3ee688` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `probitas-v1.1.0` | evolution | `midnight-secondary-close-attribution` | `f947d2653e33240e5f2d368cc6c952af5939c0187741fba04896a6d32aa9cbe2` | [example dossier](../../docs/example-dossier.md) | Fail-closed Morpho Midnight fixed-maturity coverage ships: a strict Base v0 adapter, registry and dossier integration, and a guarded maturity renderer. The held frontier advances to secondary-close attribution. |
