# Lazarus evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `lazarus-v1.2.0`
- Frontier status: `open`
- Frontier revision: `receipt-inclusion-proofs`
- Current frontier: Receipts and logs are recorded RPC evidence only; nothing proves them against the captured header's receiptsRoot.
- Next Fiat job: Prove the fixture's recorded transaction receipt and its logs against the captured header's receiptsRoot, so receipt evidence stops resting on the provider's word, and carry the resulting evidence class through the manifest, the verifier, the release and the Ariadne state-fixture predicate without moving any other recorded RPC response into a proved class. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `lazarus-v0.1.0` | baseline | `ariadne-state-fixture-binding` | `94c0f87fc8dd14562e948fb5b523c9248ffa6fd21849cc433d4a5bc47966daf5` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `lazarus-v1.1.0` | evolution | `receipt-inclusion-proofs` | `ebbefc52fa3dff6c3d5be57ea0d9da7afc0489e34e95cf9dedd5747e401ad1ff` | [preservation release](../../docs/preservation-release.md), [shipped release](../../examples/goldfinch-v0-release/release.json), [audit](../../../../audit/AUDIT.md) | The held job is done. A fixture now binds to an Ariadne state-fixture statement through `release`, which holds the statement to what verification recomputed rather than to what the manifest claims, and `verify-release` reads the whole thing back years later. The Goldfinch release ships. The new frontier is the evidence class this run deliberately did not touch: receipts and logs are still the provider's word. |
| `lazarus-v1.2.0` | generation | `receipt-inclusion-proofs` | `ebbefc52fa3dff6c3d5be57ea0d9da7afc0489e34e95cf9dedd5747e401ad1ff` | [structured multi-provider chain-anchor study](../../../../docs/lazarus-multi-provider-chain-anchor/study.md), [issue #386](https://github.com/wildcat-finance/skills/issues/386) | Lazarus uses plan v2 with sorted, opaque source identifiers and keeps provider observations in a separate anchor-record format. Anchors have their own count and make no claim of canonical-chain membership or provider independence. Changing plan v1 was rejected because it breaks released-fixture compatibility. Storing provider URLs was rejected because it retains secrets. Folding anchors into recorded-RPC or proof counts was rejected because it overstates their evidence. |
