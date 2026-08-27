# Hermes evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `hermes-v0.1.1`
- Frontier status: `open`
- Frontier revision: `class-vocabulary-coverage`
- Current frontier: Hermes's twelve optimisation classes name 62 of the corpus's 120 rules, so 58 documented rules cannot be selected as candidates.
- Next Fiat job: Widen the Hermes optimisation classes against the pinned rule corpus until every rule with a source-level candidate can be selected, starting with the reduction in storage writes that STO-09's neighbour STO-12 needs and no class names. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `hermes-v0.1.0` | baseline | `live-evidence-bundle` | `7d5489a979e01a2ac5f27ad9dbc70811375104a76482f218b72b559bf6298f40` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `hermes-v0.1.1` | epoch | `class-vocabulary-coverage` | `1916665dfd39d78323da197f498707002f4b9626567048e80d7f98ee2a464ea5` | [ADR-007](../../../../docs/decisions/ADR-007-displace-the-hermes-evidence-bundle-frontier.md), [ADR-008](../../../../docs/decisions/ADR-008-adopt-the-source-rule-namespace-and-a-declared-scope.md), [study](../../../../docs/hermes-rule-corpus-study.md) | A maintainer supplied a pinned gas-optimisation reference as a new external requirement, and the corpus built from it absorbs the catalogue's role while `verify` gains a required `--rule` that breaks every earlier invocation. Both make the pre-corpus lineage an unsafe guide. The displaced `live-evidence-bundle` target is reopened rather than recorded complete, and the successor named above is what this run's own evidence supports. |
