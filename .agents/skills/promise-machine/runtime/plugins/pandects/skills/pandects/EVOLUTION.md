# Pandects evolution ledger

Policy: [../../../hexaemeron/skills/VERSIONING.md](../../../hexaemeron/skills/VERSIONING.md)

- Current version: `pandects-v1.1.0`
- Frontier status: `open`
- Frontier revision: `search-record-engine-coverage`
- Current frontier: The search-record runner records only the Foundry campaign, so Echidna and Medusa results survive as audit prose rather than as records.
- Next Fiat job: Widen the search-record runner to the Echidna and Medusa campaigns, so every engine result ships as a record carrying its engine, configuration, sequence length and corpus digest, with a seed where the engine exposes one and a stated absence where it does not. Before the run finishes, cold-read and reconcile all mutable first-party marketplace prose.

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
| `pandects-v0.1.0` | baseline | `withdrawal-batch-fee-law` | `c5156fb0e08112cd003f4baceb58c66856a5fee23f49e38d27ed73a458dda369` | [README marketplace-context](../../README.md) | Versioning starts here. The held frontier is adopted from the plugin's marketplace-context block unchanged. |
| `pandects-v1.1.0` | evolution | `search-record-engine-coverage` | `f8c17a1b872e93439fa85122d703565d880f3d70321305edae04abc51274a3de` | [the law](../../src/laws/PooledClaimsCoverOpenBatches.sol), [its specimen](../../specimens/FeeFromQueued.sol), [the study and runbook](../../docs/withdrawal-batch-fee-law/), [the audit record](../../../../audit/AUDIT.md) | The held frontier completed. `claims/pooled-claims-cover-open-batches/v1` ships with all six parts, and both models were corrected because both carried the defect it names: the fee was capped against assets set aside rather than against what the open batches are owed, and an earmark cannot exceed what a system holds, so the two part company exactly when the system is illiquid. On the Wildcat model a market holding 200 against a batch owed 1000 permitted a fee of 800 and now permits nothing. Both engines catch the specimen and neither catches another, across every campaign in the harness. The new frontier is evidenced by this run's own audit log, which had to record Echidna and Medusa results as prose because `pandects run` knows one engine. |
