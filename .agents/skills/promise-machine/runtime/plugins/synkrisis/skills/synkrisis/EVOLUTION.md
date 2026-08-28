# Synkrisis evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `synkrisis-v1.1.0`
- Frontier status: `open`
- Frontier revision: `diagnostic-rule-catalogue`
- Current frontier: Synkrisis builds one checked cohort from declared run observations, and its diagnostic rule catalogue, renderer and verifier have not yet landed.
- Next Fiat job: Complete Step 3 of the committed runbook: ship the digest-bound deterministic rule catalogue behind synkrisis.py diagnose, emitting findings with exact event references, counterevidence, unknown runs, the nearest forbidden claim and one named handoff. Accepted when the example cohort yields the late-boundary-consultation/v1 and unchanged-retry-before-handoff/v1 findings, fingerprints survive harmless manifest reordering, and every named negative fixture refuses.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `synkrisis-v0.1.0` | baseline | `cohort-construction` | `f5ecc2bea318637223d5115b76fcbe354957783ddb56fc2256c257710af80e51` | [the anchor study](../../../../docs/synkrisis/study.md) and [issue 449](https://github.com/wildcat-finance/skills/issues/449) | Versioning starts here. Synkrisis ships as the runbook's Step 1 scaffold: both host manifests, the marketplace and router surfaces, this ledger, the committed study, runbook and first decision record, and a command stub that declares the four specified operations and refuses each with a stable code naming the runbook step that implements it. The held frontier is Step 2, observation admission and cohort construction. |
| `synkrisis-v1.1.0` | evolution | `diagnostic-rule-catalogue` | `b79fc7ed23a252ee977b8ebf0353f0fbef3897de7de222f41b1a75fd216c6404` | [the committed runbook](../../../../docs/synkrisis/runbook.md) Step 2 and [issue 449](https://github.com/wildcat-finance/skills/issues/449) | Step 2 delivered. `synkrisis.py cohort` admits declared run-observation records under the producer contract, recomputing digests and bound prefixes, holding caps and path form, and classifying every declared run as included, excluded or unknown with the responsible policy field, written atomically with no partial output behind a refusal. The policy and cohort schemas, the schema-compatibility record, the comparability decision record and the worked example with its committed expected cohort land beside the suite's positive and hostile fixtures. Diagnose, render and verify still refuse with the step that lands each. The held frontier is Step 3, the diagnostic rule catalogue. |
