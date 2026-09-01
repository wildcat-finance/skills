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

An oracle carrying no status field at all refuses, and so does one whose status
is blank. Comparing only against the unreviewed value would let every oracle
through in a workbook that has no status column, which is this control failing
open in exactly the direction that widens coverage.

`covered` applies to the inventory side only. An oracle is a workbook case,
and `covered` asserts that something is held to one; a case cannot be held to a
case, because the case is the oracle. A workbook row takes `manual` or
`excluded`, which answer the question actually being asked about it: has this
row been dealt with, and by whom. Left open, a row could name itself as its own
oracle and close the ratio on its own evidence.

A `manual` or `excluded` entry naming an oracle refuses. Such a row would read
as decided by a person and held to a case at once, which are two different
claims about the same item.

No code path proposes a disposition. The reconciler reads the set, checks it,
and reports. An agent may draft a disposition set for a person to review, and
it cannot mark anything covered by running this tool.

## Confirmation

Every entry carries a `confirmed` boolean, and only a confirmed entry is
admitted as a disposition. A generator writes it false and has no path that
writes it true, so drafting cannot move a coverage figure. See
[ADR-002](decisions/ADR-002-confirmation-is-not-a-disposition.md).

An entry is checked in full whatever its confirmation says, so a draft that
could never be valid refuses now rather than when somebody confirms it. Only
then is it admitted or set aside. An unconfirmed entry is refused as a
disposition, named in the record's `unconfirmed` list with its drafted state
and reason intact, and leaves its item in `undisposed` exactly as an item with
no entry at all would.

The entry is refused, not the set. A set holding unconfirmed entries still
reconciles and reports a ratio drawn from whatever was confirmed, because a
reviewer working through a few hundred items needs to see the number move
before the last one is decided.

An entry carrying no `confirmed` field refuses by name. Defaulting it false
would silently discard a set written before the field existed; defaulting it
true would admit every draft. The counts state confirmed dispositions,
unconfirmed entries and undisposed items as three separate figures, so how much
was drafted is never mistaken for how much was decided.

## Staleness

A disposition set declares the inventory digest and the workbook digest it was
written against. Either one disagreeing with the record in front of it refuses
as stale.

This is the failure that looks most like success. A stale set can account for
every item perfectly and be an account of a tree nobody is looking at any more,
and a ratio of one computed from it reads exactly like a ratio of one computed
from the current records.

## Both directions of the join

The record names the inventory items no covered disposition holds to an oracle,
and the workbook cases no covered disposition cites. The first is the uncovered
application surface, which is the question the whole tool exists to answer. The
second is effort spent on something the inventory does not know about.

Both are recorded rather than one being inferred from the other, because a
reader who has to derive a list by subtraction will eventually derive it wrong.

## The ratio

The closure ratio is scoped items carrying one valid confirmed disposition,
over scoped items. Its numerator and denominator are emitted as separate fields
beside the value, so neither can move without the other being visible.

A freshly drafted set therefore closes at zero, which is the figure a reviewer
would have seen with no set at all. Running a generator changes what the work
looks like, never what the number says.

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

## Closed is enforced, not only declared

Each record this plugin emits declares a schema, and each committed schema says
an unknown key is a refusal. Until the release that shipped this section,
nothing checked any of it: the schemas were documentation and the `--check`
verbs asserted behaviour rather than shape.

Every `--check` now validates a real emitted record against the committed
schema it declares. The checker covers exactly the keywords these four schemas
use and refuses an unsupported one rather than skipping it, because a schema
quietly half-checked is worse than one nobody claimed to check.
