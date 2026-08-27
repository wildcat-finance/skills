# Janus evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `janus-v0.1.0`
- Frontier status: `open`
- Frontier revision: `second-host-adapter`
- Current frontier: Janus ships the Wildcat v2.5 host adapter and its seven gates against modeled hooks, and no second host adapter yet shows the manifest format holds for another callback model.
- Next Fiat job: Ship a second host adapter for a different callback model, added only after the Wildcat adapter's suite passes, so the manifest format is shown host-neutral rather than asserted. Accepted when the second adapter's honest hook passes its gates, its hostile hooks are each caught, and the shared harness runs both adapters green.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `janus-v0.1.0` | baseline | `second-host-adapter` | `c244247ec1071dda04c29206e52efe3eab264e8c323eaf15468f03e3a9688764` | [the anchor specification](../../../../docs/janus-suite/study.md) | Versioning starts here. Janus ships as a built conformance suite: a JSON hook-manifest schema and validator, a Solidity host-adapter interface and state-delta recorder, a stateful Foundry harness with a deterministic unit mode, five hostile reference hooks, a faithful model of the Wildcat v2.5 market-to-hook seam with an honest hook that passes all seven gates, and human and SARIF reports. The held frontier is the second host adapter, deferred until the Wildcat boundary survives its own suite, as the anchor specification required. |
