# ADR-003: attribution names a person, and a rule is a table row

## Status

Accepted, 2026-09-06. Raised by
[the attributed-confirmation study](../dokimasia-attribution-study.md) and the
frontier job [ADR-002](ADR-002-confirmation-is-not-a-disposition.md) left open
when it made `confirmed` a boolean anything with write access can set. The
selected design and the two that lost are recorded in
[the design record](../attribution-design-evidence.json); this file records
the decisions the design leaves to prose.

## Context

ADR-002 made a confirmed entry the only thing the closure ratio counts, and
made confirmation one boolean on the entry. The committed scrutiny of
`wildcat-app-v2` says 202 of 261 were confirmed and cannot say by whom or under
what rule. It cannot tell a reviewer who worked through 261 items from a script
that flipped a field, and producing those 202 required halting a run to ask a
person by name, because there was nowhere to write the answer down.

The task issue refuses any citation of the figure until it states whose
judgement it is. The reviewer, on the other side, wants confirming an entry to
cost one edit and wants a rule applied to 202 rows written once.

The topic said the reconciler refuses an entry "carrying no person and no
stated rule". That sentence has two readings, and one of them had to be chosen.

## Decision

A confirmed entry names a person in `confirmed_by`, always, and may name a
`rule`, an id into a set-level `rules` table whose row holds the rule's `text`
and `stated_by`, the person who stated it.

Four things follow, each of them a refusal in the reconciler:

1. **A person is required.** A confirmed entry with no `confirmed_by`, or a
   blank or non-string one, refuses by name and is never counted. Of the two
   readings of the topic, this is the stricter: a rule alone does not suffice,
   because a rule with no person would attribute a judgement to a sentence.
   The held job's own words are that a coverage figure must state whose
   judgement it is, and ADR-001's are that a person owns every disposition.
2. **A rule is a table row, not free text on the entry.** A `rule` id the
   table does not hold refuses, a row with blank `text` or blank `stated_by`
   refuses, and a `rules` value that is not an object refuses. A row nobody
   applies does not refuse; the record reports it as applied zero times,
   because a stated rule nobody used is information about the review, not a
   defect in the file. That is the second reading, resolved here rather than
   silently.
3. **A draft carries neither field.** An unconfirmed entry with `confirmed_by`
   or `rule` refuses, so a draft cannot pre-name its confirmer, and no
   generator writes either field.
4. **The identifiers stay at `/v1`.** `dokimasia-dispositions/v1` gains two
   optional entry fields and one optional set-level table;
   `dokimasia-coverage/v1` gains a `confirmations` block and four caps. A set
   confirmed under `dokimasia-v2.1.0` is still a `/v1` set that this version
   reads; what changes is that it now refuses on its first confirmed entry,
   naming the item and the missing field. ADR-002 kept the identifier when it
   added `confirmed` for the same reason.

The coverage record's `confirmations` block states how many people decided,
how many entries each confirmed, which rules were applied with their text and
author and how many times, and how many entries were confirmed individually.
It reconciles with `disposed` three ways and the canonical coverage digest
covers it, so a changed attribution is a changed record.

**Migration: no defaulting.** A set written before this version is not given a
person by code. Defaulting a person is the exact forgery this decision exists
to make impossible, in the same way ADR-002 refused to default `confirmed`. The
pinned set is attributed as one reviewed edit of the reviewer's file: its 202
confirmed entries name `Laurence Day` under the one rule
`row-author-owns-walking-it`, stated by the same person, which is what the run
that confirmed them recorded.

## Alternatives

**Either a person or a rule suffices.** The other reading of the topic. It
lost because it allows a confirmation that names no human at all, and the
figure would then attribute a judgement to a sentence. The rule row carries
`stated_by` precisely so that a rule-based confirmation still names a person.

**The rule's text written on every entry.** The design record scores this as
`inline-attribution`. No join to refuse and every entry self-contained, at the
cost of writing the same sentence 202 times on the pinned set, of two entries
meant to share a rule drifting by a character and counting as two rules, and
of "how many rules were applied" becoming a question about string equality.
It ties `rule-table` on reviewer actions and artefacts and loses on the one
measured metric, rule statements on the pinned set, 202 against 1.

**A separate attestations file.** Scored as `attestation-ledger`. The rule is
stated once and the disposition file is untouched, at the cost of a second
file, a second digest binding, two edits to confirm one item, and a dropped
item leaving a dangling attestation, which is a second staleness to refuse.
ADR-002 rejected the same shape for confirmation, and it loses here on
actions and artefacts, two against one of each.

**Verifying the named person.** A signature, a key, an identity lookup. None
of it is built. `confirmed_by` and `stated_by` are claims the file makes under
a person's name, the same class of claim as `generated_by`, and making them a
proof needs a key this skill deliberately does not hold. What changes is that
the claim now exists to be read and checked by a person, where before there
was nothing to check.

## Consequences

The closure ratio keeps meaning what ADR-001 and ADR-002 say it means, and now
says whose judgement it reports. A confirmation with no person lowers nothing
and raises nothing; it refuses.

A person's name and a rule's text are the first reviewer-typed prose to reach
the committed coverage record. Each is bounded where it enters, by caps that
are parameters of the reconciler with defaults the record reports:
`confirmed_by` and `stated_by` at 128 bytes, a rule id at 64 bytes in one safe
segment, a rule's text at the 512-byte reason cap, and the table at 256 rows.
The existing test that refuses the five workbook column names anywhere in the
record now covers the rule text too.

Regeneration must carry an attributed entry and the `rules` table forward byte
for byte, which the proposal surface owes in the step after this one; an
attributed entry is always a touched entry, because `confirmed` is read first.

A crawler that fills confirmations later would write `confirmed_by` from a
reviewed cell and `rule` naming a row whose `stated_by` is the person who
stated the crawler's rule, so its confirmations would be attributed to that
person and never to the crawler. Nothing here builds toward that, and nothing
forecloses it.
