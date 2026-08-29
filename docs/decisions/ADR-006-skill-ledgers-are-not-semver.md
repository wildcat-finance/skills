# ADR-006: Skill ledgers are not SemVer

## Status

Accepted, 2026-08-20. Records a choice in force since the versioning contract
was adopted; superseded by a later numbered record once it stops being true.

## Context

Every governed skill carries a label of the form
`{skill}-v{evolution}.{generation}.{epoch}` in its `EVOLUTION.md`, defined by
`plugins/hexaemeron/skills/VERSIONING.md`. The label looks like SemVer, and
the contract has to say in passing that it is not, because a reader who
assumes SemVer will misread every row: they will take the first number for a
breaking change, the second for a feature, the third for a patch, and none of
those readings is what the ledger records.

## Decision

The three counters are independent axes of a skill's history, not
compatibility semantics. Evolution increments exactly once per completed
frontier Fiat job; generation increments for meaningful non-frontier change;
epoch increments only when a compatibility or provenance boundary makes the
earlier lineage an unsafe guide. The counters never reset, and a skill adopts
at whatever version it already declared, so no baseline value can be assumed
across the marketplace.

## Alternatives

- SemVer. It is the convention every reader already knows, which is exactly
  the problem: skills are instruction sets, not APIs, so "breaking change"
  has no defined subject, and mapping frontier work onto major-minor-patch
  would either inflate majors on every held-job completion or hide frontier
  advances inside minors. It lost because its promises are about
  compatibility this artefact cannot make.
- The plugin's package version. One number per plugin would be simpler, but a
  plugin bundles skills whose frontiers move independently, and ADR-004
  records a whole release where package versions moved and no skill did. It
  lost because it collapses histories the ledgers exist to keep apart.
- Date-based versions. Dates order history but carry no arithmetic: nothing
  in a date says whether a frontier advanced, and the frontier-hold rule
  (a generation retains the prior revision and digest byte for byte) needs
  counters a checker can verify. It lost because the ledger's guards would
  have nothing to hold.

## Consequences

A ledger row's axis carries meaning a checker enforces: the evolution suite
verifies the arithmetic, the digest hold, and the header-row agreement, and
Fiat's integrate gate refuses a frontier run whose row breaks them. Readers
pay a one-time cost of unlearning SemVer, which this record and the contract
both state plainly. Tools that want compatibility semantics read the package
versions in the plugin manifests instead, which ADR-004 keeps deliberately
separate.

## Issue 556 addendum: relation and resolved label

Accepted, 2026-08-28, for
[skills#556](https://github.com/wildcat-finance/skills/issues/556).

A runbook may declare `next-generation-after-integration-base` for a governed
skill instead of naming a future label. The declaration fixes the arithmetic:
retain evolution and epoch, then select the generation one above the ledger at
the exact integration base. Capturing that declaration and its compatibility
anchor does not reserve a label.

Resolution is a separate transition. Fiat reads one exact integration base
and candidate head and checks that the candidate already carries the selected
generation row and matching skill metadata. Compatible generation drift can
move the answer; evolution, epoch, or held-frontier drift refuses it. The
controller observes this product state and records the evidence, but does not
edit the product.

After the audited step stack closes, a changed projection can travel only in
Fiat's existing signed two-parent sync. Every changed ledger and `SKILL.md`
path must then be covered by the digest-bound
`fiat-integration-revalidation/v1` record before another resolution. This
keeps relation, product correction, and publication evidence separate.

The issue #556 run is self-hosted: its pinned controller predates the receipt
it ships. Its product follows this decision, while the new
`fiat-version-resolution/v1` receipt first governs a later run under the
updated controller. Any correction during this run remains signed sync and
revalidation evidence rather than a receipt constructed after the fact.
