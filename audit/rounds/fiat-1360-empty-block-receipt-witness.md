## Step 1, round 1 -- 2026-09-06T22:01:54Z

Audit schema: fiat-audit-round/v2

Covered: empty-root-binding=reviewed; empty-set-completeness=reviewed; branch-shape-parity=reviewed; evidence-count-zero=reviewed; nonempty-regression=reviewed; rpc-surface-minimisation=reviewed; manifest-report-shape=reviewed; fixture-provenance=not-applicable; atomic-fixture-write=not-applicable; marketplace-prose-drift=not-applicable

Not checked: Pashov security suite, waived because step 1 changes no Solidity; live genesis provenance, capture and atomic publication, downstream manifest and release propagation, and public marketplace prose remain assigned to later steps.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | docs/lazarus-empty-block-receipt-witness/study.md | Hypomnema H008: the shipped study did not bind selected design `shape-discriminated` to its standing draft decision through one `hypomnema-design-bridge/v1` block. | fixed in this audit commit; focused guard added |

Leads not pursued: none

## Step 1, round 2 -- 2026-09-06T22:14:44Z

Audit schema: fiat-audit-round/v2

Covered: empty-root-binding=reviewed; empty-set-completeness=reviewed; branch-shape-parity=reviewed; evidence-count-zero=reviewed; nonempty-regression=reviewed; rpc-surface-minimisation=reviewed; manifest-report-shape=reviewed; fixture-provenance=not-applicable; atomic-fixture-write=not-applicable; marketplace-prose-drift=not-applicable

Not checked: Pashov security suite, waived because step 1 changes no Solidity; live genesis provenance, capture and atomic publication, downstream manifest and release propagation, and public marketplace prose remain assigned to later steps.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: none

## Step 2, round 1 -- 2026-09-06T23:26:00Z

Audit schema: fiat-audit-round/v2

Covered: empty-root-binding=reviewed; empty-set-completeness=reviewed; branch-shape-parity=reviewed; evidence-count-zero=reviewed; nonempty-regression=reviewed; rpc-surface-minimisation=reviewed; manifest-report-shape=reviewed; fixture-provenance=reviewed; atomic-fixture-write=reviewed; marketplace-prose-drift=not-applicable

Not checked: Pashov security suite, waived because step 2 changes no Solidity; the external truth of the operator-authored 2026-09-06 live-provider observation was not independently corroborated, and canonical-chain membership and provider independence remain explicitly unclaimed; public marketplace prose remains assigned to step 3.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: live-provider recapture, because no provider input belongs to this offline audit and the fixture claims only a recorded observation.
