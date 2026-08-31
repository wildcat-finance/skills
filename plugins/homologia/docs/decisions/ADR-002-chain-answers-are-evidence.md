# ADR-002: take chain answers as evidence rather than execute an EVM

## Status

Accepted, 2026-08-31. Raised by [skills#458](https://github.com/wildcat-finance/skills/issues/458)
and the checked-input implementation study.

## Context

Homologia compares a pinned on-chain computation with a pinned off-chain
mirror. Its first operational boundary must admit the chain-side expected
integer before any mirror can run. Fetching or executing that answer inside
Homologia would add an RPC, EVM and historical-state boundary to a tool whose
result must remain offline and recomputable. Lazarus already owns preservation
and proof of historical Ethereum state.

Expected answers also arrive with different strengths. Some have a Lazarus
artefact, some are tied to a recorded chain and block identity, and some are
committed assertions with a named author. Treating those forms as equivalent
would strengthen evidence silently.

## Decision

Homologia accepts the expected integer as input with exactly one closed
provenance class: `proved`, `recorded` or `asserted`. A proved answer must carry
a repository-relative Lazarus artefact reference. Homologia checks that
reference's form but does not open it or repeat the producer's proof.

The manifest and vector shapes are documented in
[schema compatibility](../schema-compatibility.md). No operation in this step
contacts a chain, executes a contract or decides whether an expected answer is
true. Later verdicts must retain the weakest class they consume.

## Alternatives

- **Execute the contract through a live RPC.** Rejected because the result
  would depend on a network and provider response, would not be offline
  recomputable, and would give the live response no preserved evidence class.
- **Embed an EVM in Homologia.** Rejected because it duplicates the historical
  state and proof boundary Lazarus owns and adds a substantial runtime
  dependency to the comparison tool.
- **Accept expected integers with no class.** Rejected because an asserted
  value could then be read as proved, and a later verdict could not report the
  strength of the chain-side evidence it used.
- **Require every answer to be proved.** Rejected because recorded and asserted
  vectors are useful when labelled honestly; excluding them would hide the
  distinction instead of preserving it.

## Consequences

Manifest checking remains standard-library-only, bounded and offline. A
checked-inputs record can say which evidence class and reference accompanied an
answer without claiming that Homologia produced or verified that evidence.

Operators must preserve and verify a referenced Lazarus artefact separately.
Recorded and asserted inputs remain visibly weaker. Mirror execution,
comparison and any agreement verdict remain later governed steps.
