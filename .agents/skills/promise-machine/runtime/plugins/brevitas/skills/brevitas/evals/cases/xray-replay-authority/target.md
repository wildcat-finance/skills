[High] Signed replay identity can collide or survive revocation at intake.
Location: `inferrex-t0.3-signed-protocol-objects-spec.md:411`; `inferrex-t0.8-database-model-invariants-spec.md:194`
Mechanism: Two grants can share one environment-scoped signer/nonce identity, or acceptance can race revocation without the specified lock order across T0 and T1/T4.
Impact: SYS-005 and SYS-012 can admit replay or revoked authority; T1 real revocation concurrency could not be established from the schemas, vectors, and source checkers.
Fix: Serialize acceptance and revocation under one lock order keyed by environment, signer, nonce, purpose, object, scope, and owner.
