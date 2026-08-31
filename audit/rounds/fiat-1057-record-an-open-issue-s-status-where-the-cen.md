## Step 1, round 1 -- 2026-08-31T22:03:42Z

Audit schema: fiat-audit-round/v2

Covered: extractor-collision=reviewed; fenced-decoy=not-applicable; unclosed-block=not-applicable; duplicate-block=not-applicable; body-size=not-applicable; control-characters=not-applicable; digest-drift=not-applicable

Not checked: the Atlas dependency extractor itself, which lives in another repository and was neither run nor read, so the record's claim that it must skip the block is stated and unverified. No parser exists yet, so the four parsing concerns were exercised against no code. The 31 controller digest bindings were not touched, because this step changes no controller bytes.

Elenchus verdict: unguarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | docs/decisions/draft-fix-the-issue-status-block-markers.md | The Status section read "A number is assigned when this record merges, per issue #888", and nothing performs that assignment. Issue #888 is open, and ruleset 21830871 requires only `identity` and `invariants`, so no gate assigns a number, checks that one was assigned, or refuses a record left unnumbered. A reader could merge the record and believe numbering had happened. | fixed in 839eb7bfd841aa32d739082755c6220a52d18ce5 |

Leads not pursued: a check comparing a committed copy of a receipted artefact against the ledger's digest. This round found the two copies byte-identical by `diff -q`, but nothing in the step's exits compares them, so a copy taken between two amendments would ship disagreeing with the receipt. Recorded rather than built, because it is a controller change rather than a document fix, and it is a carryover candidate for this run.

## Step 1, round 2 -- 2026-08-31T22:07:05Z

Audit schema: fiat-audit-round/v2

Covered: extractor-collision=reviewed; fenced-decoy=not-applicable; unclosed-block=not-applicable; duplicate-block=not-applicable; body-size=not-applicable; control-characters=not-applicable; digest-drift=not-applicable

Not checked: the Atlas dependency extractor, unchanged from round 1: it lives in another repository and was neither run nor read. The four parsing concerns still have no code to exercise. No controller bytes changed, so the 31 digest bindings were not touched.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the committed-copy comparison carried from round 1, unchanged. Nothing compares a committed copy of a receipted artefact against the ledger's digest; this round confirmed the two copies byte-identical by `diff -q` again, which is evidence about this tree and not a check the repository owns.
