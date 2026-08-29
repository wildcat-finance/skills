<!-- brevitas: evidence-exception reason="ordered counterexample, trace, independence limit, and closure evidence are irreducible" -->
FINDING
title: Fund-safety claim trusts an unaudited bypass pointer
stage: T0
severity: high
disposition: SPEC_DEFECT
claim: DB-055 permits a FUND_SAFETY event to pass an earlier event only after the hard deadline, only when the named predecessor is QUARANTINED, and only when the same transaction inserts an immutable validated work.outbox_order_bypasses row.
claim_source: source-bundle.md:31902
invariants: [DB-055]
gate_axes: [Objective validation]
owner: inferrex_worker / work
counterexample: In the executable reference schema, create predecessor P at aggregate sequence n with delivery_state PENDING or LEASED, create later candidate S at n+1 with ordering_class FUND_SAFETY and bypass_predecessor_event_id=P, insert no work.outbox_order_bypasses row, and call work.claim_next_outbox_v1 after S becomes available. The NOT EXISTS predicate exempts P solely because S names P, so S is leased even though P is not quarantined, no deadline fact was checked, no exact reason was checked, and no audit row exists.
trace: work.claim_next_outbox_v1 at source-bundle.md:30556 excludes a predecessor when candidate.ordering_class='FUND_SAFETY' and candidate.bypass_predecessor_event_id equals the predecessor ID. It neither joins nor requires work.outbox_order_bypasses. The validator at source-bundle.md:30612 checks the required predicates only if an audit row is inserted; there is no reverse constraint making that row mandatory before claim. The reference checker case NEG-DB-055-INVALID-FUND-SAFETY-BYPASS attempts a malformed audit-row insert, not a claim with no audit row. The T0.9 checker evaluates an independent auditRecord boolean vector, while its SQL check at source-bundle.md:33352 only searches for the table name.
evidence_present: PGlite executes the reference DDL and rejects a malformed bypass audit row; deterministic T0.9 vectors include all seven intended predicates.
evidence_independence: The PGlite case, model mapping, SQL substring checks, and deterministic vectors are all source-tier evidence from the same packet. None executes the missing-audit-row claim schedule, and no pinned real-PostgreSQL result is present at T0.
smallest_correction: Make work.claim_next_outbox_v1 exempt a predecessor only under an EXISTS subquery for work.outbox_order_bypasses matching candidate event, predecessor event, reservation, exact reason, and validated deadline facts; lock the matched rows consistently. Add a database constraint or constrained append procedure that prevents a non-null bypass pointer from existing without its validated audit row.
closure_evidence: Add a PGlite negative case that inserts the pointer without an audit row and proves claim returns no row, plus cases for a non-quarantined predecessor and mismatched audit pair. At T1, provide the migration, worker-role privilege-negative test, and a pinned real-PostgreSQL T1-CONC-SAFETY-006 interleaving proving only the validated audited path can publish.
confidence: 99
group_key: T0|DB-055 audited fund-safety bypass|claim predicate requires validated audit row
END
