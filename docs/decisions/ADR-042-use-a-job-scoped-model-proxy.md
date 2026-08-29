# ADR-042: Use a job-scoped model proxy

## Status

Accepted, 2026-08-28.

## Context

A disposable worker needs model inference without receiving a provider
credential or gaining a general network path. The accepted job must determine
the destination family, operation, model, data class, features, limits, and
lifetime. Those choices have to remain reviewable after the worker exits.

The accepted JobSpec is an external authority boundary. Its exact bytes and
SHA-256 digest must stay joined to the policy that the proxy enforces. A
parser default, provider SDK default, or guest-selected request field would
make the enforced policy broader than the accepted bytes describe.

The design and constraints are developed in the
[model proxy study](../phylax-model-proxy/study.md). The wire and policy rules
are fixed by the
[Phylax model proxy reference](../../plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md).

## Decision

Run one trusted model proxy per accepted job. The trusted supervisor supplies
digest-bound accepted-job evidence. The proxy recomputes the digest, projects
one closed `model-proxy-policy/v1`, and resolves a provider profile from
reviewed code. Guest traffic later uses a small provider-independent protocol;
it cannot select a provider URL, method, model, header, credential, feature,
or lifecycle action.

Version 1 begins with a synthetic loopback profile. It proves policy
compilation without selecting a live provider, credential source, transport,
or retention tier. Later provider adapters must preserve the same normalised
guest protocol and earn their own provider-specific decision and evidence.

## Alternatives

- An allowlisted HTTP forward proxy would let existing provider clients run in
  the guest. It was rejected because provider paths, headers, request fields,
  redirects, storage flags, and API growth would remain guest-controlled.
- A short-lived provider token in the guest would remove the request mapper.
  It was rejected because the token is still a provider credential and direct
  provider egress would contradict the worker's network boundary.
- A shared multi-tenant gateway could centralise operations. It was rejected
  for this component because its administrative API, cross-job counters,
  caches, logs, credential store, and upgrade cadence enlarge the first proof.

## Consequences

The guest protocol stays small and every authority-bearing field is visible in
one canonical policy. A profile or schema change requires a new version rather
than a permissive fallback. One process per job gives counters and lifecycle a
single job identity, at the cost of an adapter for each provider and model
family.

The policy digest joins the exact accepted JobSpec digest to the compiled
profile and limits. This join proves which channel the proxy allowed. It does
not prove that a provider will avoid retention, inspection, transformation, or
exfiltration after content reaches that allowed channel. Operator disclosure,
tests, and later audit records must retain that limit.

The synthetic profile is component evidence only. It does not establish a
live provider, a signed JobSpec acceptance, a virtual-machine transport, or an
end-to-end Fiat integration.
