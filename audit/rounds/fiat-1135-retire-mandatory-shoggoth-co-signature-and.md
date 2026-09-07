## Step 1, round 1 -- 2026-09-06T22:39:03Z

Audit schema: fiat-audit-round/v2

Covered: signature-loss=reviewed; residual-host-ban=reviewed; residual-trailer-mandate=reviewed; identity-job-wedge=reviewed; ruleset-overwrite=reviewed; connector-evidence-gap=reviewed; contributor-policy-leak=reviewed; shoggoth-lookalike-residue=reviewed; historical-record-rewrite=reviewed; generated-copy-drift=reviewed; signature-fixture-masking=reviewed; authority-confusion=reviewed

Not checked: live ruleset mutation, the external Interceptor repository, and future Step 2 policy behaviour; outside Step 1 static-record scope

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | docs/shoggoth-signature-only-retirement-study.md:1 | Hypomnema study mode exits 1 with H008 because the shipped study has no `design-bridge` block binding `signature-only-retirement` to `docs/decisions/drafts/accept-any-validly-signed-authorship.md`. The receipted study digest is already fixed, so Warden cannot add the block without invalidating source-bound evidence. | open: controller amendment required |

Leads not pursued: The decision draft remains Proposed until integration assignment; no change because its dated status passes the current Hypomnema draft contract.

## Step 1, round 2 -- 2026-09-06T22:55:50Z

Audit schema: fiat-audit-round/v2

Covered: signature-loss=reviewed; residual-host-ban=reviewed; residual-trailer-mandate=reviewed; identity-job-wedge=reviewed; ruleset-overwrite=reviewed; connector-evidence-gap=reviewed; contributor-policy-leak=reviewed; shoggoth-lookalike-residue=reviewed; historical-record-rewrite=reviewed; generated-copy-drift=reviewed; signature-fixture-masking=reviewed; authority-confusion=reviewed

Not checked: live ruleset mutation, the external Interceptor repository, and future Step 2 policy behaviour; outside Step 1 static-record scope

Elenchus verdict: unguarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: S1-R1-01 was fixed in cfebac48673d14920d9eedb1461ac04051cfc0b1; explicit Hypomnema study mode is clean. Elenchus reports unguarded because the repair changed no test files.

## Step 2, round 1 -- 2026-09-07T10:32:50Z

Audit schema: fiat-audit-round/v2

Covered: signature-loss=reviewed; residual-host-ban=reviewed; residual-trailer-mandate=reviewed; identity-job-wedge=reviewed; ruleset-overwrite=reviewed; connector-evidence-gap=reviewed; contributor-policy-leak=reviewed; shoggoth-lookalike-residue=reviewed; historical-record-rewrite=reviewed; generated-copy-drift=reviewed; signature-fixture-masking=reviewed; authority-confusion=reviewed

Not checked: live ruleset mutation and the external Interceptor repository; outside Step 2 local-policy scope

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | PROMISE_MACHINE.md:263 | The contributor-ranking refusal and recovery still required parity with Fiat's removed host sets, contradicting the new local-only classification boundary and directing an unknown-account repair back into `hexctl.py`. | fixed in this round's signed fixes commit |
| S2-R1-02 | medium | docs/how-to-help-shoggoth.md:15 | Current contributor guidance still required a human identity and a GitHub-matched author address even though valid signature evidence is now the admission rule and unmatched attribution is recorded as unresolved. | fixed in this round's signed fixes commit |

Leads not pursued: The digest-neutral agent-instruction fixtures changed only their bound source digests while preserving reviewed spans and measured projections; their checker and complete repository suite cover the rebind. The hosted identity workflow remains live until Step 3 removes its required status first.
