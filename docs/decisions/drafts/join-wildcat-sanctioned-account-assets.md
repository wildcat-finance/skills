# Decision: Join Wildcat sanctioned-account asset companions by unique native identity

## Status

Proposed, 2026-11-01. Issue #2091; numberless until integration. Selected design: `unique-key`.

## Context

The canonical adapter maps queues and market-token transfers but leaves two sanctioned-account asset companions unsupported. The existing execution escrow join uses unique native matching. Batch-payment burns use a separate adjacency rule. Pinned V1 source uses the same normalized value for its account-to-escrow transfer and asset companion. V2 queues claims before emitting its queued companion, with possible intervening batch logs. V2 declares the asset escrow signature, although its reviewed `_blockAccount` path queues instead. A constructed V2 escrow specimen exercises its declared ABI without claiming historical emission.

Both retained generation releases were verified and rebuilt during the study. Neither contains either target signature. Positive branch observations must come from labelled constructed specimens.

## Decision

Use complete-key groups with exactly one primary and one companion. The V2 queue key is generation, market, transaction, account, expiry, scaled amount and normalized amount. The asset escrow key for both declared generations is generation, market, transaction, account/from, escrow/to and amount/value. Require the accepted market role and concrete ABI. Neither input order nor adjacency chooses a match.

Keep primary parties, actions and financial units unchanged. Every companion is `supporting-routing` and creates no canonical action. Missing and ambiguous groups preserve native records and carry a named gap and limitation. Primaries without companions acquire no speculative sanction gap.

Adapter `1.3.0` adds mapping-only `routing_joins`, a deterministic list whose entries contain exactly `evidence_class`, `rule`, `primary_selector`, `companion_selector` and `conditions`. Conditions carry all matched fields. The primary and companion mapping records carry the same inference record and reciprocal supporting selectors; event provenance names the companion. Each companion is claimed once. Empty lists are explicit under this interpretation. Preserve the existing singular `join` for execution escrow and batch burns, including a hostile transfer matching both a batch-burn relation and new sanctions routing. Neither relation overwrites the other. The schema 3 canonical envelope stays unchanged.

Build fresh versioned outputs. Verify each release using its exact supported declared adapter version, with feature gates preserving historical bytes and refusing unknown versions or semantic downgrade attempts. Compose reserved `1.1.0` and `1.2.0` deliveries only after their signed changes land. This starting ref establishes only the existing `1.0.0` interpretation.

## Alternatives

`first-match` does not prove uniqueness in both directions and fails duplicate-group controls. `adjacent-only` loses valid queues with intervening batch logs and fails ambiguity controls. Both failed the executed finite design model. A new canonical action would double count the request or transfer; mapping evidence needs no envelope change.

## Consequences

Consumers can follow qualified routing while preserving primary denominators and claim units. Extra indexes remain bounded by the existing record cap. Constructed positives cover V2 queues and V1/V2 asset escrow. Negative controls change every key field, duplicate both sides, reorder records and exercise wrong roles and simultaneous existing relations. Verification rejects changed joins, selectors and dispositions even after superficial digests are rebound.

Retained reports classify verified targets as exercised or absent. Absence never counts as a historical positive. Missing custody refuses rather than substituting fixtures. Public retained records contain identifiers, digests and bounded booleans only. #2090 retains account-status meaning. Identity, sanctions-law interpretation, underlying cash movement, settlement and independent chain proof remain unestablished.
