# ADR-029: Separate the checkpoint protocol from its authority service

## Status

Retired, 2026-08-27. The proposal below was never accepted and no longer
governs. [ADR-028](ADR-028-use-cumulative-portable-checkpoints-rooted-at-an-immutable-fiat-base.md)
replaces it with same-ledger checkpoint continuation that does not depend on an
authority service. The remaining body is preserved as historical rationale.

PR #569 published this record as ADR-024. That number already held the accepted
run-observation binding decision on `main` when the PR merged. This record moved
to ADR-029. The decision is unchanged.

## Context

Portable checkpointing has three different responsibilities. Contributors and
Fiat need a stable format and offline verifier. A service needs to authenticate,
quarantine, validate, publish, sign, index, and operate accepted archives. A
contributor front door needs a small redacted view that helps somebody resume
without learning or hosting archive contents.

Putting all three in `wildcat-finance/skills` would tie a public skill release
to one deployment and make infrastructure changes look like protocol changes.
Letting the service own the only schemas/verifier would make an accepted
checkpoint depend on the service remaining available. Letting Atlas own the
storage path would mix public routing, private bytes, and policy decisions.

## Decision

`wildcat-finance/skills` owns the portable protocol:

- versioned run-anchor, snapshot, manifest, acceptance, revocation, resolution,
  and redacted-discovery schemas;
- canonical identity rules and golden vectors;
- deterministic export, inspect, and restore reference commands;
- pinned receipt/resolver public keys and typed key-transition rules;
- controller publication-fence behaviour; and
- compatibility/refusal fixtures.

A separately authorised `wildcat-finance/fiat-checkpoints` repository owns the
replaceable service implementation:

- contributor authentication and repository/run authorisation;
- bounded quarantine upload grants;
- isolated validation against a pinned Skills protocol release;
- immutable object publication, replication, and signed statements;
- derived PostgreSQL indexes, lineage/resolution operations, and recovery;
- infrastructure as code, monitoring, and operator runbooks.

The intended service source is reviewable independently from private data. Its
exact repository visibility is an explicit creation-time approval, not inferred
from this Proposed record. No archive, observation, credential, environment
state, or deployment secret belongs in either source repository.

`wildcat-finance/shoggoth-wave-atlas` owns only redacted discovery and handoff.
It reads versioned GitHub/checkpoint summaries, reports each source's freshness,
binds a contributor's resume/redraw/start choice, requests a short-lived
authorised download grant, and passes bytes to the Skills verifier. It does not
validate archives as authority, sign decisions, select a fork, or retain a
durable object URL.

The service pins one exact Skills protocol release or signed commit digest.
Skills clients accept only declared compatible service policy/schema versions.
A protocol or public-key change lands in Skills first with compatibility
fixtures; a service deployment may then adopt it. Service code does not widen a
schema or verifier locally to accept a failing upload.

Checkpoint acceptance is an evidence-statement boundary. The custom acceptance
predicate and KMS signature profile are handed to Ariadne's in-toto/DSSE
contract during CP-2/CP-4 rather than creating an unrelated attestation grammar.
The checkpoint protocol still fixes the predicate fields and authorisation
meaning.

## Alternatives

- **Keep protocol, API, and infrastructure in Skills.** One repository and one
  review queue. Rejected because cloud operations, service dependencies, and
  public skill releases have different cadences and write boundaries.
- **Let the service repository own the schemas and verifier.** Keeps service
  work self-contained. Rejected because offline restore would depend on a live
  service release and the service could silently reinterpret stored objects.
- **Use Atlas as the service and store.** Fewer components. Rejected because a
  public routing surface would hold private archives, credentials, validation,
  and fork authority it does not need.
- **Store only archives and reconstruct all policy in clients.** Removes the
  API database and much service logic. Rejected because authentication,
  quarantine, immutable publication, signed acceptance, revocation, and
  concurrent resolution still need one enforced boundary.

## Consequences

The programme has three repositories and version handshakes rather than one
tree. Each cross-repository change needs a separately authorised run and a
pinned interface. That costs more coordination but prevents one delivery from
silently widening another repository's boundary.

Skills remains enough to inspect and restore downloaded bytes offline. Losing
the service blocks new acceptance and discovery, not interpretation of an
already obtained archive and statement.

The service can replace framework, compute, or database without changing
checkpoint meaning, provided protocol conformance and immutable records remain
the same. Atlas can change its interface without becoming storage authority.

This record does not create the service repository or approve its visibility,
cloud accounts, dependencies, or deployment. Those remain explicit entry gates
in issues #563 and #564.
