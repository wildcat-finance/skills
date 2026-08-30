# ADR-051: Keep dead-code discovery report-only

## Status

Accepted, 2026-08-29.

## Context

Issue #437 needs one repository-wide inventory of possible dead code. The
repository already has two narrower authorities that must not drift: Horos
classifies generated, vendored, binary, lockfile and content-addressed reading
exclusions, while tests/check-map-v1.json and scripts/run_checks.py select and
execute checks.

A reachability signal is incomplete around dynamic imports, registrations,
entry points, fixtures and computed paths. Candidate counts therefore cannot
establish semantic uselessness or authorise deletion.

## Decision

Provide one root report-only command whose universe is the clean tracked Git
tree. It consumes hard Horos classifications without changing Horos and
consumes the checked runner without becoming another scheduler. Findings remain
candidates with explicit evidence and false-positive boundaries. Candidate
count never fails the command, blocks a merge or authorises source deletion.

The dead-code scope owns this command, schema, focused tests, workflow and
documentation. Horos continues to own classification evidence. The checked
runner continues to own scope selection, snapshots, process budgets and result
accounting.

## Alternatives

Put one analyser in every plugin. Rejected because plugin-local views cannot
resolve cross-plugin imports, root manifests, generated-copy topology or
orphaned repository objects.

Widen Horos into reachability analysis. Rejected because reading exclusion and
semantic reachability make different promises. Combining them would strengthen
Horos evidence beyond its contract and blur which component owns a refusal.

Use candidate count as a workflow gate. Rejected because a static or execution
signal does not prove that a candidate is unused. A future diff gate requires
a separate decision after the baseline is reviewed.

## Consequences

Contributors get one deterministic text and JSON report bound to commit, Git
tree and universe identity. CI fails on command, schema, discovery or analyser
failure, not on findings. The root command must preserve unavailable and
degraded analyser states and must not edit analysed source.

The command depends on Horos and the checked runner, so their changes select
the dead-code suite through the repository check graph. Later analysers extend
the versioned schema; they do not acquire deletion authority.
