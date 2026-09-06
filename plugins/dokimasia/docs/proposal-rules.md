# Proposal rules

The declared rules `dokimasia propose` drafts under, stated here rather than
left in the source, for the same reason
[the inventory rules](inventory-rules.md) and
[the workbook lineage rules](workbook-lineage.md) are stated: what the tool
recognised is a claim a reader has to be able to check without reading Python.

A proposal is a draft. Nothing in this file decides anything, and every entry it
describes is written with `confirmed` false. See
[ADR-002](decisions/ADR-002-confirmation-is-not-a-disposition.md).

## What is drafted, and what is never drafted

Every scoped item gets exactly one entry. The scoped set is the reconciler's
own: every compiled inventory item and every imported workbook case.

Two of ADR-001's three dispositions are drafted. `covered` is never drafted, and
the proposal surface holds no branch that constructs it. That is not a policy
the generator applies at the end; it is the absence of a code path, asserted by
a test against the module's own source and by a test that drives every branch
and requires the emitted vocabulary to be a subset of `{manual, excluded}`.
`covered` asserts that a reviewed oracle exists and something is held to it,
which is a judgement about whether an oracle was any good, and no tool makes it.

## Which state each side is drafted as

**A workbook case is drafted `manual`.** A case is a row a person wrote and
walks. Nothing else can be said about it from the record alone: the importer
preserves the row's own status field, and that status is what somebody typed
into a spreadsheet, not evidence that anything was held to it.

**An inventory item is drafted `excluded`.** This is the conservative direction
and it needs saying plainly, because the opposite reading looks more helpful. A
compiled route with no case citing it is exactly what the tool exists to find,
so drafting it `manual` would assert that a person owns it, which is the claim a
reviewer is supposed to make. Drafting it `excluded` asserts the weaker thing,
that nothing in the reviewed workbook reaches it, and puts it in the exclusion
list, which ADR-001 says is the list a reviewer reads to audit the denominator.
Either draft is wrong for some items and both are corrected the same way, by
editing one field; the difference is which mistake survives an inattentive
review, and an over-broad exclusion list is louder than a quiet claim of
ownership.

## What a reason may say

A reason quotes only fields the record in front of it holds, and asserts nothing
about an outcome. Four templates, one per item kind, each naming its source:

| Item kind | Drafted reason |
| --- | --- |
| `case` | `drafted from workbook row <sheet>:<row>, identifier <id>; a reviewer owns this row` |
| `route` | `drafted from the compiled page route at <source>; no reviewed case cites it` |
| `api` | `drafted from the compiled API handler at <source>; no reviewed case cites it` |
| `action` or `guard` | `drafted from the compiled <kind> at <source>; no reviewed case cites it` |

Each begins with `drafted from`, so a reason nobody has edited is recognisable
as a draft when read in isolation, away from the `confirmed` field.

No template names a status, a result, a pass, a failure or a judgement. The
workbook's status and source vocabularies are not pinned anywhere, which
rounds 1 to 3 of step 3 of the previous run recorded and deferred; a template
that quoted a status would make a renamed status change drafted prose, and a
template that reasoned from one would make it change a decision. Drafted prose
is the only thing this run lets it touch.

A reason is subject to the declared 512-byte reason cap, applied before the
write, and a template that would produce an empty reason refuses.

## Regeneration

Regenerating a proposal against a moved inventory or workbook is the ordinary
case, not the exception: a frontend changes and the denominator changes with it.

- An entry a person **confirmed** is carried forward byte for byte.
- An entry a person **edited** is carried forward byte for byte. An edit is
  detected by comparing the entry against its recorded `proposed_sha256`; an
  entry with no such digest is treated as hand-written and therefore as edited,
  because the conservative reading of an unknown provenance is that a person
  wrote it.
- An entry a person **attributed**, one carrying `confirmed_by` or `rule`
  under [ADR-003](decisions/ADR-003-attribution-names-a-person-and-a-stated-rule.md),
  is carried forward byte for byte. It is always a confirmed entry, so it is
  always touched, whatever its digest says.
- The set-level **`rules` table** is copied forward unchanged, including a row
  no entry applies. A stated rule nobody used is information about the review,
  and the reconciler reports it as applied zero times rather than refusing it.
- An entry nobody has touched is replaced by a fresh draft.
- A scoped item with no entry gains one.
- An entry whose item is no longer scoped is dropped, and the drop is reported,
  unless it is attributed. An attributed entry on an item that no longer exists
  is somebody's recorded judgement about nothing, so the regeneration refuses
  by name and a person removes it.

Every run reports on stderr how many entries it preserved and how many of those
were attributed, how many it replaced, added and dropped, and whether the
`rules` table travelled with it and with how many rows. That line answers the
study's third on-call question, whether the last regeneration kept every
attribution.

A regeneration that cannot carry an attributed entry or the table forward
refuses and writes nothing, leaving the reviewer's file exactly as it was. Four
cases refuse: an attributed entry whose item left the scoped set; an entry
naming a `rule` the table travelling with it does not hold, which is the set a
regeneration once produced by rebuilding without the table; a `rules` value
that is not an object; and an unconfirmed entry carrying either attribution
field, refused at the same pre-write check that refuses a draft carrying one.

The write is staged to a sibling temporary file and renamed into place, so a
killed regeneration leaves either the previous file or the new one and never a
half-written set. The output path takes one safe path segment below a declared
root and is never followed through a symlink.

## What a proposal never does

It does not read the application, execute anything, spawn a subprocess or open a
socket. It does not write to the target checkout. It does not mark an item
covered. It does not confirm an entry. It does not report anything as passed,
and a complete proposal with every entry drafted still reports a closure ratio
of zero, because nobody has decided anything yet.

It does not write `confirmed_by` or `rule` on any entry, and it does not add,
remove or reword a row of the `rules` table. The drafting surface holds neither
field name as a literal, asserted by a test against the module's own source
beside the `covered` assertion, and a test that drives every branch requires
each drafted entry to carry exactly `item`, `disposition`, `reason`, `oracle`,
`confirmed` and `proposed_sha256`. A set in which a draft carries either field
breaches the pre-write check and is never written. Attribution is a person's
mark, made in the reviewer's file, and the generator's only relation to it is
to carry it forward unchanged.
