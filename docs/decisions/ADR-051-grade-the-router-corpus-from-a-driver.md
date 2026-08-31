# ADR-051: Grade the router corpus from a driver that stops at the model boundary

## Status

Accepted, 2026-08-30. This record fixes the rule selected for issue
[#904](https://github.com/wildcat-finance/skills/issues/904).

The number is 051 because ADR-050 was the highest on `origin/main` when this
delivery cut its branch. Numbers here are global and picked before merge, which
is [#798](https://github.com/wildcat-finance/skills/issues/798); if another run
takes 051 first, this record moves and the study naming it does not.

## Context

`test_a_recorded_run_block_matches_the_corpus_digest` binds a recorded grading
run to `corpus_sha256`. Landing a plugin forces a router row, a router row must
be graded by a corpus case, and a new case moves that digest, so the recorded
run stops describing the corpus and the suite goes red.

`docs/promise-machine/router-selection-v1.md` says to regrade rather than edit
the digest. That is the right rule. Nothing performed a regrade, so the next
person to add a plugin inherited a red suite and an unwritten procedure. One
was performed by hand for [#851](https://github.com/wildcat-finance/skills/pull/851),
which is where the cost became legible.

## Decision

Grading runs through `tests/router_selection_driver.py`, which stops at the
model boundary in both directions. `emit` writes one prompt per case and a
manifest. `tally` reads answers back, scores them and writes the run block. The
graded contexts happen in between, one per request, wherever the operator has
them.

The driver holds no credential and opens no socket.

## Alternatives

**A flag on `emit_router_selection_report.py`.** Rejected by inheritance.
[#697](https://github.com/wildcat-finance/skills/pull/697) established that a
reporter echoing request text is a route from the report into a context being
graded, and that the flag "must stay unbuilt". The reporter's own docstring
says the same. This is not a decision reopened here.

**A driver that calls a model.** Rejected. It puts a network client and a
provider credential into a repository holding neither, makes the tests
unrunnable offline, and makes a regrade reproducible only by someone with that
provider. It buys nothing: the contexts already exist wherever the driver runs.

**A pluggable context adapter.** Rejected as premature. One adapter would be
written, it would be this operator's, and the interface would be shaped by that
single case. The answers file is already the interface, and it is a file.

## Consequences

A regrade is still not free: the operator supplies 38 contexts, one per
request. What the driver removes is the error-prone part, not the slow part.

Batching those contexts is forbidden by evidence rather than by preference. The
first grading this surface recorded presented all requests to one context and
was refused and regraded, logged as `S3-R1-03` against
[#697](https://github.com/wildcat-finance/skills/pull/697).

The run block still records nothing about the tree it graded, so a case that
changes answer between runs cannot be attributed to model variance or to a
changed router. That gap is named in
[#904](https://github.com/wildcat-finance/skills/issues/904) and is not closed
here, because the fix invalidates every recorded block at once and belongs with
the migration rather than with the tool.
