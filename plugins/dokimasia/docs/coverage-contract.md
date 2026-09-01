# The coverage contract

What a Dokimasia coverage record asserts, and what it refuses to assert. The
closure identifier is `dokimasia-disposition-closure/v1` and the record schema
is `dokimasia-coverage/v1`. The vocabulary and the ratio are fixed by
[ADR-001](decisions/ADR-001-one-disposition-per-scoped-item.md); this document
states how the reconciler enforces them.

## The scoped set

Both sides are scoped. Every inventory item is one scoped entry, identified by
its kind and its source file. Every workbook case is one scoped entry,
identified by its own case identifier.

Scoping both sides is deliberate. An inventory item with no case is the gap the
whole tool exists to find. A case matching no item is effort spent on something
the inventory does not know about, which is either a hole in the rules or work
against a surface nobody scoped. Neither question can be answered by leaving
one side out of the denominator.

## One disposition, from a closed set

Every scoped item carries exactly one disposition: `covered`, `manual` or
`excluded`. Two on one item refuses, because nothing then states what was
decided. Zero does not refuse: an unanswered item is a real state a run can be
in, and it holds the ratio below one, which is the honest report.

`manual` and `excluded` each carry a reason. An unexplained exclusion is how a
denominator shrinks quietly, so an empty or whitespace reason refuses.

## `covered` needs a reviewed oracle

A `covered` disposition names an oracle: a case identifier the workbook holds.
Three things refuse.

A `covered` entry naming no oracle refuses. A `covered` entry naming an oracle
the workbook does not hold refuses. A `covered` entry naming an oracle whose
status is `Not Run` refuses, because nothing is held to a case nobody has run.
A status a person recorded, including `Fail` and `Blocked`, is a reviewed
judgement and is accepted; whether that judgement was correct is not something
this record claims.

No code path proposes a disposition. The reconciler reads the set, checks it,
and reports. An agent may draft a disposition set for a person to review, and
it cannot mark anything covered by running this tool.

## Staleness

A disposition set declares the inventory digest and the workbook digest it was
written against. Either one disagreeing with the record in front of it refuses
as stale.

This is the failure that looks most like success. A stale set can account for
every item perfectly and be an account of a tree nobody is looking at any more,
and a ratio of one computed from it reads exactly like a ratio of one computed
from the current records.

## The ratio

The closure ratio is scoped items carrying one valid disposition, over scoped
items. Its numerator and denominator are emitted as separate fields beside the
value, so neither can move without the other being visible.

One is the only passing value, and it means nothing is unaccounted for. It does
not mean anything passed, and no arrangement of this record can be read as
saying so.

## What the record does not establish

It does not establish that a `covered` item works, that its oracle was a good
oracle, or that a passing status was right to pass. It does not establish that
the inventory rules found everything a framework can express, which is the
inventory's own boundary. It does not establish that an `excluded` item was
correctly excluded; it establishes that somebody said so and wrote down why,
which is what makes the exclusion list reviewable.
