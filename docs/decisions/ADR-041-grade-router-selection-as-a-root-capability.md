# ADR-041: Grade router selection as a root capability

## Status

Accepted, 2026-08-27.

## Context

The router at `.agents/skills/promise-machine/SKILL.md` sends a request to one
of 24 rows. Nothing in this repository presents a request to it and checks
which row comes back. The five tests in `tests/test_portable_skills.py` hold
the router to resolution: links reach the file they name, canonical names match
their directories and stay unique, and the frontmatter declares no version.
None of them reads the `Request` column of either table.

Closing that gap means adding a promise, and a promise has to sit somewhere a
checker can find it. Two facts decide where.

`promise_records` in `scripts/promise_machine.py` builds the promise universe
from the canonical skills under `plugins/` and then from the vendored overlay.
The router is in neither set. A `## Promise Machine contract` section written
into the router file would be found by no checker, required by no coverage row
and held by nothing.

The root law also says that routers "select that implementation and establish
no domain result of their own". Giving the router a promise of its own would
argue with the law it exists to point at.

## Decision

The promise lives in [the root law](../../PROMISE_MACHINE.md) as
`promise-machine-router-selection`, beside the licence, run-observation and
contributor-ranking promises. The router gains none.

`tests/promise_machine_coverage.json` binds it through a `router_selection`
capability entry that names the corpus fixture, the checker with its selectors,
and the versioned contract document, each carrying a digest that recomputes.
That is the shape `contributor_ranking`, `run_observation` and
`run_observation_capture` already take, and the shape
`tests/test_unique_identifiers.py` already holds every entry to.

What the promise claims stops at the corpus. A passing check says the corpus
has the shape its schema declares, that every canonical name it expects is a
real skill, and that every sentence it quotes still occurs in the file it
names. It says nothing about how an agent routes.

## Alternatives

- Write the promise into the router's own file. No checker reads it there, and
  the law says a router owns no result of its own.
- Attach it to a canonical skill under `plugins/`. No skill's contract mentions
  the router, so the promise would sit under an owner whose evidence does not
  reach it, and that skill would take an evolution ledger row for work outside
  its subject.
- Add a coverage row rather than a capability entry. A row is keyed by a
  promise some `SKILL.md` declares, so `check_coverage` would report the row as
  one `promise_records` never produced.
- Leave selection ungraded and keep checking resolution alone. That is the
  state this record exists to leave behind.

These four are the options for where the promise lives. The design options that
lost are in section 4 of the committed
[study](../router-selection/study.md): a deterministic matcher scored against
the corpus, Berean's evaluation harness, and Brevitas's `run_evals.py`. The
study gives the reason each one lost.

## Consequences

The corpus, the checker and the contract document are bound to one promise id
whose digests recompute on every suite run. A checker that drifts from its
document, or a fixture edited without its digest, fails instead of passing
quietly.

Moving the promise later is costly. Every digest in the capability entry is
bound to the path named beside it, so a move invalidates the entry, the
contract document's binding, and any recorded run block citing the promise.
That cost is why this is a record rather than a comment.

The router still carries no promise. An agent reading it learns what to select
and learns nothing about whether the suite grades that selection; the grading
evidence sits in the root law and the corpus instead, one directory away from
the file being graded.
