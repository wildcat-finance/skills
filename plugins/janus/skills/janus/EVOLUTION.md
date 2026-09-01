# Janus evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `janus-v0.2.0`
- Frontier status: `open`
- Frontier revision: `second-host-adapter`
- Current frontier: Janus ships the Wildcat v2.5 host adapter and its seven gates against modeled hooks, and no second host adapter yet shows the manifest format holds for another callback model.
- Next Fiat job: Ship a second host adapter for a different callback model, added only after the Wildcat adapter's suite passes, so the manifest format is shown host-neutral rather than asserted. Accepted when the second adapter's honest hook passes its gates, its hostile hooks are each caught, and the shared harness runs both adapters green.
- Venues: [../../../../VENUES.json](../../../../VENUES.json)

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `janus-v0.1.0` | baseline | `second-host-adapter` | `c244247ec1071dda04c29206e52efe3eab264e8c323eaf15468f03e3a9688764` | [the anchor specification](../../../../docs/janus-suite/study.md) | Versioning starts here. Janus ships as a built conformance suite: a JSON hook-manifest schema and validator, a Solidity host-adapter interface and state-delta recorder, a stateful Foundry harness with a deterministic unit mode, five hostile reference hooks, a faithful model of the Wildcat v2.5 market-to-hook seam with an honest hook that passes all seven gates, and human and SARIF reports. The held frontier is the second host adapter, deferred until the Wildcat boundary survives its own suite, as the anchor specification required. |
| `janus-v0.2.0` | generation | `second-host-adapter` | `c244247ec1071dda04c29206e52efe3eab264e8c323eaf15468f03e3a9688764` | [the manifest-resolution specification](../../../../docs/janus-manifest-resolution/study.md) | The conformance gates read the manifest. Until now every verdict compared a hook's recorded effects against an `address[]` a test author wrote beside the assertion, so the suite enforced the literal and the manifest was documentation; a `ManifestReader` now selects a threshold by action name, resolves each permitted call, storage scope and value movement through the host adapter's own name table, and hands the gates those addresses. Resolution fails closed: an absent or duplicated action, an unresolvable symbol, a blank account symbol, a resolution to the zero address, and a dotted name with more than one reading each revert with a named error rather than yielding a smaller permitted set. Two schema-valid fixtures pin the disagreement class the suite exists to detect -- an omitted entry is refused, the same hook and delta are admitted against the shipped manifest, and an unresolvable symbol aborts the run. The exercise also found a disagreement inside the shipped manifest itself, which is recorded rather than repaired here: its deposit threshold permits a state-changing call to the role provider and permits no write to it, so any provider that records anything when validated produces a storage effect the manifest never enumerated. The held frontier is unchanged, because a second host adapter is still what would show the format host-neutral. |
