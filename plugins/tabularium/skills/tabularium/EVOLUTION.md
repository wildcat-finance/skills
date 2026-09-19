# Tabularium evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `tabularium-v0.4.0`
- Frontier status: `open`
- Frontier revision: `compound-v3-phase-1`
- Current frontier: Compound v3 Phase 0 now rebuilds ordered calls and signed-principal transitions from one verified Alexandria witness; the Phase 1 canonical adapter and Ethereum USDC specimen remain unimplemented.
- Next Fiat job: Ship Compound v3 Phase 1 from Alexandria raw evidence with a new canonical and coverage schema version, supply, withdraw, base-transfer and absorb mappings, a mined borrower-to-borrower transfer witness, hostile fixtures and a byte-identical offline Ethereum USDC specimen. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.
- Sources: [../../../../SOURCES.md](../../../../SOURCES.md)

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `tabularium-v0.3.0` | baseline | `compound-v3-phase-1` | `c3aac484a13f97742a45f07a4d3ca42cec29e4e4a9666cfd2701d825e4752d6e` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `tabularium-v0.4.0` | generation | `compound-v3-phase-1` | `c3aac484a13f97742a45f07a4d3ca42cec29e4e4a9666cfd2701d825e4752d6e` | [skills#1362](https://github.com/wildcat-finance/skills/issues/1362), [canonical event v3 schema](../../schemas/canonical-event-v3.json), [release policy](../../docs/release-policy.md) | Canonical event and coverage schema v3 close the admitted vocabulary against the registered adapter tuple table, `build` writes 3 and `verify` reads 2 and 3, and the design bridge from v2 is superseding releases rather than in-place migration: `aave-v4-v1`, `euler-v1-v1` and `euler-v2-v1` restate the three v0 releases under v3 from the same `source.json` bytes, each v0 release keeps its published bytes and gains a note naming its successor, and the corrected v2 schema documents stay readable. The trade is 1,710,643 added bytes of example data. Frontier unchanged: the held Compound v3 Phase 1 job is untouched. |
