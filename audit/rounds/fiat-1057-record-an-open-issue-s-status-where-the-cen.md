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

## Step 2, round 1 -- 2026-09-01T11:44:02Z

Audit schema: fiat-audit-round/v2

Covered: fenced-decoy=reviewed; unclosed-block=reviewed; duplicate-block=reviewed; control-characters=reviewed; body-size=reviewed; digest-drift=reviewed; extractor-collision=reviewed

Not checked: whether the Atlas dependency extractor skips the delimited block, which needs the Atlas source and is delivered in that repository. The reader was exercised against handwritten bodies and the committed test fixtures, not against a body fetched from GitHub over REST, so the transport path around `read_task_issue_contract` is covered by its existing tests rather than by anything this round added. No measurement was taken of the reader's cost, so the single-read change carries no performance claim.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | `status_block_span` refused a closer with no opener only before the first block. After one closed, a further `<!-- status:end -->` was ignored: the reader returned span `(1, 3)` with no faults and `issue-check` reported a body carrying an unmatched delimiter as clean. The decision record's rule that a closer with no opener refuses was therefore enforced on one side of the block only. | fixed in 956c9e2ef28f5e0bb36192f0b956e1f718b204d3 |

Leads not pursued: the controller digest reconciliation ran twice inside this one step, eleven bindings each time, because the implement commit and this audit fix both changed `hexctl.py`. Issue #892 owns the mechanism; what this round adds is that the cost is per-commit rather than per-step, so an audit loop multiplies it by the number of rounds touching the controller. Recorded rather than built, because collapsing it needs a derived digest at check time, which is a change to the Promise Machine rather than to this step. The committed-copy comparison lead from step 1 also stands, untouched here.

## Step 2, round 2 -- 2026-09-01T11:49:03Z

Audit schema: fiat-audit-round/v2

Covered: fenced-decoy=reviewed; unclosed-block=reviewed; duplicate-block=reviewed; control-characters=reviewed; body-size=reviewed; digest-drift=reviewed; extractor-collision=reviewed

Not checked: whether the Atlas dependency extractor skips the block, unchanged from round 1 and delivered in the Atlas repository. No body was fetched from GitHub over REST in this round. No measurement was taken of the reader, so neither the single-read change nor the added position scan carries a performance claim. Whether "top of the body" should also permit an HTML comment or a title line above the block was not explored; the rule implemented is the strict reading of the record.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R2-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | The record states at `docs/decisions/draft-fix-the-issue-status-block-markers.md:51` that the block sits at the top of the body, before the filing prose. The reader did not check position, so a block opened below the prose parsed to a valid span and `issue-check` reported the body clean. A reader coming top to bottom would meet the stale requirement and never reach the correction, which is the failure #837 records inside documents and the half-enforced-contract shape #427 records. | fixed in 0170a68e057e0d553980a7b16a98599a184d1333 |

Leads not pursued: this step's implement phase wrote eight parser cases where the runbook's Tests field named four, one per reachable risk-register concern. The extra four cover the well-formed span, absence, a closer with no opener, and the block reaching the contract record. More coverage than specified is not a defect, and it is recorded here rather than amended into the runbook because the count in that field is an estimate and the concerns it enumerates are all covered. The digest reconciliation ran three times across this step, eleven bindings each time, once for the implement commit and once for each audit fix; #892 owns the mechanism and the per-commit multiplier is recorded in round 1. The committed-copy comparison lead from step 1 stands.

## Step 2, round 3 -- 2026-09-01T11:54:52Z

Audit schema: fiat-audit-round/v2

Covered: fenced-decoy=reviewed; unclosed-block=reviewed; duplicate-block=reviewed; control-characters=reviewed; body-size=reviewed; digest-drift=reviewed; extractor-collision=reviewed

Not checked: whether the Atlas dependency extractor applies the same comment exemption, which is the obligation this round added to the record and is delivered in the Atlas repository. No body was fetched from GitHub over REST by the reader itself; the real issue 1057 body was fetched with `gh` and checked from a file. No measurement was taken, so the added comment scan carries no performance claim. Whether a title line should also be exempt was considered and refused: a heading is visible, which is the property the rule turns on.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R3-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py | Round 2's position rule refused the arrangement 92 of the 137 open issues would produce, because those bodies begin with the invisible `wildcat-origin` HTML comment. The diagnostic asserted that a reader meets the original requirement before the correction, which an HTML comment cannot cause, so the rule was wrong about its own justification. The record was silent on whether a comment counts as filing prose, so a second consumer matching these bytes could have read it either way. | fixed in 7287f7fb886b32881e19a0ee199f8dd58bc40355, in the code and the record together |

Leads not pursued: the fourth digest reconciliation across this step, eleven bindings each time. Recorded in rounds 1 and 2; nothing new is claimed here beyond the count. The committed-copy comparison lead from step 1 stands. The eight-versus-four test count recorded in round 2 stands, now eleven cases in total, and the three added by audit fixes are the loop's own guards rather than a further deviation from the Tests field.
