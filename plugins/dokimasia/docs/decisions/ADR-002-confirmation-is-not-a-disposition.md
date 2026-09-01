# ADR-002: confirmation is a field, not a fourth disposition

## Status

Accepted, 2026-09-01. Raised by
[the proposed-disposition study](../dokimasia-proposal-study.md) and the frontier
job [ADR-001](ADR-001-one-disposition-per-scoped-item.md) left open when it wrote
that an agent may propose a disposition.

## Context

ADR-001 fixed three dispositions and one sentence about who owns them: a person
owns every disposition, an agent may propose one, and no code path may mark an
item covered on its own. The first half of that sentence shipped. The second did
not, and the cost showed up immediately: the first scrutiny of a real release
scoped 261 items and found none carrying a disposition, because writing them
meant 261 hand-authored entries against a vocabulary the reviewer had to learn
first.

Building the proposal half raises a question ADR-001 did not have to answer.
Once a tool writes entries into the reviewer's own artefact, the record no longer
says by itself whether a person decided anything. A drafted `excluded` and a
decided `excluded` are the same three fields. Something has to distinguish them,
or the closure ratio stops meaning what ADR-001 says it means: the number would
rise as soon as a generator ran, and the ratio would be measuring how much the
tool drafted rather than how much anybody decided.

## Decision

Confirmation is a boolean field on an entry, not a fourth disposition.

Every entry in a disposition set carries `confirmed`. Only a confirmed entry is
admitted as a disposition and counted in the closure ratio's numerator. A
generator writes `confirmed` false on every entry it drafts and has no path that
writes it true; setting it is a person's act.

An unconfirmed entry is refused as a disposition. It leaves its item in
`undisposed`, appears in the coverage record's `unconfirmed` list with its
drafted state and reason intact, and holds the ratio down exactly as an absent
entry does. **This is a refusal of the entry, not of the set.** A set carrying
unconfirmed entries still reconciles, and reports a ratio drawn from whatever
was confirmed.

That reading is deliberate and the alternative was available: the whole set
could refuse until every entry is confirmed. It was rejected because it makes
partial review impossible. A reviewer working through 261 items would see no
number at all until the last one, which is the interface problem this frontier
exists to remove, reintroduced at the other end. The conservative direction is
preserved either way, because an unconfirmed entry can never raise a figure.

An entry missing the field refuses by name rather than defaulting. Defaulting
false would silently discard a hand-written set produced before this version;
defaulting true would admit every draft. Neither is a decision this record is
willing to make on a reviewer's behalf.

## Alternatives

**A fourth disposition, `proposed`.** Tempting, because it needs no new field
and reads naturally in the vocabulary. ADR-001 already rejected the shape when
it rejected a partial state: a fourth value makes the ratio unreadable, because
two people with the same set report different numbers depending on whether they
count it. It is also the wrong axis. `proposed` is not a claim about the item;
it is a claim about the entry's provenance, and folding the two together means
every future question about provenance has to be answered by widening a
vocabulary ADR-001 made expensive to widen on purpose.

**A separate confirmations file.** The reviewer names the ids they accept in a
second artefact and the reconciler joins the two. It keeps the disposition set
pristine, at the cost of a second file to maintain and a second digest binding
to keep current, so a stale confirmations file becomes a new way to be wrong.
The design record scores this as `two-file-merge` and it loses on the count of
artefacts a reviewer maintains.

**Trusting a generated set and letting the reviewer delete what they disagree
with.** Fastest to a closed ratio and the reason the whole idea is dangerous.
Silence would become agreement, and the number would measure the generator's
output rather than anybody's judgement. It is the failure mode ADR-001's own
context section describes, arrived at from the other direction.

## Consequences

The closure ratio keeps meaning exactly what ADR-001 says it means. A freshly
generated set closes at zero, which is the same figure the reviewer would have
seen with no set at all, and the work of deciding still has to be done by a
person. What changes is that the deciding is now editing rather than authoring.

Generation is safe to repeat. Because confirmation lives on the entry, a
regeneration can carry every confirmed entry forward untouched and replace only
drafts nobody has looked at, so a moved inventory no longer costs a reviewer
their previous decisions.

The disposition set is now a record this plugin emits rather than only reads, so
it acquires a committed schema at `schemas/dispositions-v1.json` and is validated
on the way out, under the rule finding S5-R4-01 established for every emitted
record.

**Nothing needs migrating.** No disposition set exists anywhere: the pinned
scrutiny closed at 0 over 261 with none written. Adding a required field to a
record with no instances is free exactly once, and this is that moment. A set
written by hand after this version and missing the field refuses by name, with
the fix being to add `confirmed` to each entry rather than to guess.
