# ADR-003: Use checked diagnostic rules

## Status

Accepted, 2026-08-27.

## Context

Findings must recompute from their inputs, refuse causal and quality
language, and never execute observed content. A rule engine that accepts
expressions, imported code or free-form templates cannot hold those
properties: the rule author would hold them, one catalogue at a time.

## Decision

A rule is data. The catalogue in `references/rules-v1.json` is schema-checked
and digest-bound into every findings document; each rule names one shipped
deterministic kind and that kind's closed integer parameters. Relation
templates may use only the kind's plain placeholders, with attribute access,
indexing, conversions and format specifications refused. Rule prose is held
against a fixed list of causal and model-quality word sequences. Thresholds
are integer fractions so no floating-point comparison enters a verdict.

## Alternatives

- Python rule plugins. Rejected: imported code is an execution path from
  input data, and its behaviour cannot be bounded by a schema.
- Regular expressions or a query language in rules. Rejected: both are
  expression evaluators over observation content, with the same problem in a
  smaller costume.
- Model-authored findings. Rejected for the prototype, as recorded in
  ADR-001.

## Consequences

New diagnostic behaviour requires a new shipped kind, which means code, tests
and a study amendment rather than a data edit; the catalogue grows slowly and
deliberately. In exchange, `verify` can recompute every finding byte for
byte, and the negative suite can prove that causal language, strengthened
evidence classes and template escapes refuse.
