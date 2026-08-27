# ADR-001: Keep cross-run diagnosis separate

## Status

Accepted, 2026-08-27.

## Context

Issues 434 to 436 gave the suite validated, redacted, receipt-bound run
observations, and nothing interprets a repeated pattern across runs. Three
existing owners were candidates for that work. Ephoros designs and reviews
telemetry for a named step. The Promise Machine governs evidence and
transitions. Fiat controls receipted delivery. Issue 449's study weighed
extending each of them against a standalone plugin.

## Decision

Cross-run diagnosis lives in its own plugin, `plugins/synkrisis/`, with its
own promises: cohort construction, bounded diagnosis and report verification.
It consumes the issue-434 to issue-436 artefacts as declared inputs and owns
comparison and bounded inference only.

## Alternatives

- Extend Ephoros. Rejected: the telemetry producer would judge what its own
  output means across runs, crossing its named-step boundary into comparison
  and improvement selection.
- Add analysis to the Promise Machine. Rejected: the law governs evidence and
  transitions without owning domain conclusions, and a diagnosis is a domain
  conclusion.
- Add analysis to Fiat. Rejected: issue 436 deliberately keeps observation
  separate from the delivery control path; optional interpretation must not
  join that path.
- A model-authored reviewer. Rejected for the prototype: its output is not
  deterministic, a stable negative corpus cannot pin its refusals, and it can
  turn association into cause. A model-assisted lane needs a later study and
  its own promise.

## Consequences

The marketplace carries one more package and result schema, and in exchange no
existing skill's promise widens. Synkrisis can refuse causal and quality
language mechanically because its rules are data over closed deterministic
kinds. The cost is a boundary to maintain: capture, redaction, binding, causal
triage and dispatch stay with their current owners, and requests that cross
into them hand off rather than grow this plugin.
