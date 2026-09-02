# ADR-002: Keep submissions, findings, occurrences, remedies and verifications separate

## Status

Accepted, 2026-08-31.

## Context

The obvious record for this corpus is a pair: a finding, and the patch that
fixed it. It is the wrong unit, and the published work says so.

Contest platforms adjudicate. A submission may be judged a duplicate, invalid,
out of scope, or acknowledged without a fix, and the adjudicated finding is not
the same object as any one submission that reported it. Vul4J examined 1,803
fix commits for 912 vulnerabilities and retained 79 reproducible cases, which
is what happens when a fix commit is assumed to be a clean repair. Croft, Babar
and Kholoosi show that label error and duplication in vulnerability datasets
distort whatever is built on top of them.

The relationship is not one to one in either direction. One refactor can answer
several findings. One finding can need several changes across releases, and can
be reverted after that.

## Decision

The graph keeps these as separate entities: engagement, submission, duplicate
cluster, canonical finding, occurrence, remediation attempt, verification,
residual or regression, and derived pattern.

Findings and remediation attempts are joined by many-to-many relations. The
remediation lifecycle states -- proposed, applied, released, deployed, reverted,
verified -- are independent, and none implies another. A normalised assertion
carries its source locator, method, mapper version and state, and never
replaces the native record it came from.

Unknown, none, and not applicable are three distinct values. A field the source
never established stays unknown.

## Alternatives

**A finding-and-patch pair.** One row per fixed finding. It cannot express a
duplicate cluster, a rejected finding, a zero-finding round, a partial fix, or a
regression, and it silently converts "merged" into "fixed".

**A flat list of adjudicated findings with a fix status enum.** Cheaper to query
and enough for counting. It loses the submissions behind an adjudication and
collapses the many-to-many edge, so a single refactor answering four findings
becomes four unrelated rows.

## Consequences

The schema is larger and the queries need joins. Aggregates must name their
denominator, because "how many findings were fixed" has several defensible
answers and the corpus refuses to pick one silently.

The corpus can represent a round that found nothing, a finding nobody fixed, a
fix that broke something else, and a verdict that stayed inconclusive. Those are
the cases a smaller schema would have dropped, and they carry most of the
lesson.
