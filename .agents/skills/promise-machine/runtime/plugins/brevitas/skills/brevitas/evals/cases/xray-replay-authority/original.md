## AS-1: Signed replay identity and authority

- **Stage:** T0; later enforcement T1/T4.
- **Adversary control:** signer address, nonce, cancellation timing, delegated scope.
- **Trust boundary:** seller/buyer signer to intake and database authority.
- **Authoritative clock / identity:** environment-scoped cryptographic identity;
  separately revocable purpose/object/scope/owner authority.
- **Normative claims at risk:** SYS-005, SYS-012.
- **Artifacts / locations:** `inferrex-t0.3-signed-protocol-objects-spec.md:411`,
  `inferrex-t0.8-database-model-invariants-spec.md:194`.
- **Counterexample class:** two grants share a replay identity or revocation
  fails to serialize against intake.
- **Ambiguity / terminal disposition:** acceptance and revocation snapshots must
  resolve under the specified lock order.
- **Existing evidence:** schemas, signing vectors and source checkers; T1 real
  revocation concurrency is later.
- **Priority:** high.
