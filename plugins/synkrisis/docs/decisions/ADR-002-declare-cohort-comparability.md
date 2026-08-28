# ADR-002: Declare cohort comparability

## Status

Accepted, 2026-08-27.

## Context

Two runs are comparable only under a judgement about task, role, skill, host
and accounting. The tool can read those fields from run-context; it cannot
know which of them may legitimately differ for the question being asked.
Inferring comparability from the data would make the tool decide the study
design, and a wrong inference would present unlike runs as one population.

## Decision

A person declares one comparison policy per cohort. The policy classifies
every run-context dimension explicitly, either `match` with the expected value
or `differ`, and declares a token accounting mode. Synkrisis checks the
declaration: a run whose matched dimension differs is excluded with the exact
policy field named, an incompletely classified policy refuses, and a
require-equal accounting policy refuses a cohort whose included runs carry
unlike accounting identities.

## Alternatives

- Infer comparability from majority values. Rejected: which runs form the
  majority is an artefact of the declared universe, and the tool would be
  choosing the in-group.
- Compare everything and annotate differences. Rejected: token counts from
  unlike accounting identities are not one quantity, and a table that mixes
  them reads as if they were.
- Require byte-equal context across all five fields. Rejected: it forbids the
  useful cohorts, such as one skill across different issues and steps.

## Consequences

Cohort membership is reproducible from the manifest and policy alone, and an
exclusion always names its reason. The cost falls on the operator, who must
state the study design up front; the worked example under
`examples/cross-run-v0/` shows one complete declaration.
