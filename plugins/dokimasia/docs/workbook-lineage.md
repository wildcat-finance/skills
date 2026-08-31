# Workbook lineage, version 1

What survives an import, what a split owes its source, and what this importer
refuses to decide. The lineage identifier is `dokimasia-workbook-lineage/v1`
and every import records it, so a record made under different rules cannot be
mistaken for one made under these.

## What survives

Every case keeps four things a reader can use to go back to the spreadsheet:
the sheet it came from, the row it sat on, the identifier it was filed under,
and every column the header named, as text.

Nothing is normalised away. A status nobody recognises is kept as written,
because an importer that mapped an unexpected status onto a known one would
hide the disagreement it should surface. A blank cell is a blank string rather
than an absent key, so a reader can tell a field that was empty from a field
that did not exist.

A header row is the first row whose leftmost cell is exactly `ID`. Labels are
read left to right and the first occurrence of a label wins, so a merged or
repeated header cannot let a blank spanning cell take a named field's place.
A row is a case when its leftmost cell matches an identifier such as `ADM-01`
or `M2-03`. Section headings and blank rows are not cases and are not counted.

## Splitting is declared, never inferred

One workbook row sometimes describes two things. Deciding that is a judgement
about product intent, and this importer does not make judgements about product
intent. A split is supplied as a declaration mapping one source identifier to
the atomic identifiers a reviewer decided it holds.

Each atomic case carries the whole source row and the identifier it came from,
so nothing about the split is lossy and the round trip still rebuilds the row.
An identifier that appears twice refuses, because a disposition could not then
be attached to one row.

## The round trip

`source_rows` rebuilds the sheet and row map from the cases alone. Every atomic
case of one source row must agree about the fields of that row, or the split
lost something and the import refuses. That check is what makes the record a
view of the workbook rather than a replacement for it.

## Reading, not evaluating

A spreadsheet is an untrusted zip archive of XML. Member names are checked
before extraction, member and total sizes are bounded, and the expansion ratio
is bounded so an archive cannot spend the reader's memory. A member name that
is absolute or holds a parent-directory segment refuses. A file that is not a
zip archive refuses.

No formula is evaluated. Where a cell holds one, the value read is the one the
producing application cached, and the formula text is never consulted. A fixture
carries a formula whose cached value differs from what evaluating it would give,
and a test requires the cached value.

## What this does not establish

An import establishes what the workbook said. It does not establish that a
recorded status is correct, that a passing row was right to pass, or that the
cases cover anything. Whether a case has a reviewed oracle, and whether the
application has behaviour no case names, are the reconciliation's questions.

## Changing these rules

A change to what counts as a case, or to which fields survive, changes every
recorded workbook digest and every disposition attached to one. Bump the lineage
identifier, state what moved, and say what happens to records made under the
previous version.
