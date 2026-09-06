## Step 1, round 1 -- 2026-09-06T22:39:03Z

Audit schema: fiat-audit-round/v2

Covered: signature-loss=reviewed; residual-host-ban=reviewed; residual-trailer-mandate=reviewed; identity-job-wedge=reviewed; ruleset-overwrite=reviewed; connector-evidence-gap=reviewed; contributor-policy-leak=reviewed; shoggoth-lookalike-residue=reviewed; historical-record-rewrite=reviewed; generated-copy-drift=reviewed; signature-fixture-masking=reviewed; authority-confusion=reviewed

Not checked: live ruleset mutation, the external Interceptor repository, and future Step 2 policy behaviour; outside Step 1 static-record scope

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | docs/shoggoth-signature-only-retirement-study.md:1 | Hypomnema study mode exits 1 with H008 because the shipped study has no `design-bridge` block binding `signature-only-retirement` to `docs/decisions/drafts/accept-any-validly-signed-authorship.md`. The receipted study digest is already fixed, so Warden cannot add the block without invalidating source-bound evidence. | open: controller amendment required |

Leads not pursued: The decision draft remains Proposed until integration assignment; no change because its dated status passes the current Hypomnema draft contract.
