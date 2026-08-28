# ADR-038: Pin the Python suite to one interpreter

## Status

Accepted, 2026-08-27.

## Context

The repository had no central Python contract. Four workflows each tested two
minor versions, one workflow named only its newest minor, plugin prose claimed
several different minimums, and local commands silently used whichever
`python3` appeared first on `PATH`. Parser compatibility made older versions
look supported even when imports, evaluated annotations, runtime calls, or the
shipped Lazarus dependency lock could not run there.

At the deciding commit, unchanged first-party code required at least the 3.10
runtime feature set and the exact Lazarus lock required at least 3.11. Every
Python workflow already tested 3.13, while 3.14 had no repository CI evidence.
The evidence establishes 3.11 as the implementation floor; it does not make
that floor a supported suite target.

## Decision

Declare the supported minor once as `==3.13.*` in
[`pyproject.toml`](../../pyproject.toml), and keep the exact execution patch in
[`.python-version`](../../.python-version). Every repository-owned Python
workflow reads that exact pin. Current README, agent, skill, and operating
prose point to the pin instead of carrying another runtime version claim.

Full checkouts use `scripts/python` as the repository-owned entrypoint. It
validates the pin, accepts an exact CPython already on `PATH`, or asks `uv` for
an already-installed exact interpreter. It never downloads a runtime and never
falls back to a different version. CI may continue to call `python3` after
`actions/setup-python` has bound that command to the exact pin.

The exact patch may advance within the declared minor after the full suite
passes. Moving to another minor changes this decision and requires fresh CI
evidence. Historical studies, runbooks, proofs, audit records, and evidence
files keep the interpreter versions they actually observed.

## Alternatives

- Keep the two-version matrices. This retained evidence for older minors, but
  repeated every test without changing behavioural coverage and left no one
  version common to prose, local execution, and every workflow.
- Make 3.11 the supported target. It met the proven implementation floor, but
  3.13 was already the highest tested target and the only minor common to all
  Python workflows.
- Keep or restore 3.8. Every tracked source file parsed with its grammar, but
  parsing did not execute imports, annotations, runtime calls, or the shipped
  lock. It was not whole-repository compatibility.
- Move directly to 3.14. It was newer, but the repository had no 3.14 CI
  evidence at the decision point.
- Put exact versions in every plugin document. That made each document locally
  explicit, but every patch release would create a repository-wide prose edit
  and another chance for the requirements to disagree.

## Consequences

The four duplicated interpreter matrices collapse to one lane each without
removing a test case, assertion, fixture, platform test, or non-Python job. A
single patch edit is consumed by the checkout launcher, local version managers
and every Python workflow; the repository gate rejects an ambient interpreter,
workflow, dependency pin, or current runtime document that drifts from the
contract.

The supported contract is deliberately narrower than the code's proven
minimum. Consumers that choose another interpreter are outside the supported
suite even when a subset happens to run. Patch updates require the same exact
lock and full verification, and a later minor needs its own evidence and a
superseding decision record.
