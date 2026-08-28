## Step 1, round 1 -- 2026-08-28T04:19:30Z

Audit schema: fiat-audit-round/v2

Covered: general-cap-regression=reviewed; undeclared-owner=reviewed; aggregate-overreach=reviewed; manifest-self-gap=reviewed; manifest-tree-drift=reviewed; commit-worktree-confusion=reviewed; path-escape=reviewed; outside-path-omission=reviewed; check-coverage-gap=reviewed; schema-compatibility=reviewed; resource-exhaustion=reviewed; subprocess-framing=reviewed; receipt-mutation-order=reviewed; incident-fixture-drift=reviewed; generated-copy-drift=not-applicable

Not checked: the waived Pashov Solidity suite, because this step ships only two Markdown documents and no Solidity; controller, fixture, package, version, or generated-copy behaviour, which step 2 owns; the unavailable #622 operator artefact and checkpoint bytes; and live GitHub state, which this audit did not refetch. The register dispositions review the published specification only and do not claim the step-2 implementation exists.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | docs/fiat-sync-run-generator-aggregates-runbook.md:45; docs/fiat-sync-run-generator-aggregates-study.md:501 | Step 1 ships the study while its Files field permits only the study and runbook, and runbook lines 89-90 declare those two files to be the durable decision homes. Hypomnema requires a shipped study's expensive decisions and rejected alternatives to reach a standing record or point at one before the shipping step is receipted, and explicitly says the study itself is not that record. Study lines 501-504 defer those decisions to `docs/decisions/ADR-042-bind-sync-run-generator-aggregates.md`, but that ADR is absent and step 2 owns creating it. The mechanical pointer lint is clean because the future path is plain code text, so it does not establish record placement. | open; amend step 1 to permit and add ADR-042, or point to an existing standing record that actually holds the chosen design and rejected alternatives, then rerun the round |

Leads not pursued: no further step-1 defect after the complete two-file diff and all fifteen register concerns were reviewed at the specification boundary. Both tracked files are byte-identical to their receipted sources at SHA-256 24e723155b1dd232a2adb2ef2442cd7bf5e9808a3636e8533c5e523e0d6dee56 and 65fa7298a68930e97f9f11db81393a0e99eeaee54f51a463b7fa1f2cc0d1f482; the implementation commit has a good Shoggoth signature and exact required trailers; Phylax, Ephoros, Hypomnema, Protasis, Imprimatur, Brevitas on the runbook, Horos, and `git diff --check` exit 0; the root suite passes 460 of 460 and Hexaemeron passes 1,377 of 1,377 with one skip. Brevitas was not run on the study because the receipted amendment records its completeness-oriented specification exclusion. The bounded Sapheneia pass preserved the heading, schema fields, all fifteen risk ids and dispositions, waived and deferred scope, finding id, severity, two file locations, missing-ADR fact, status, hashes, counts, verdict, and unpursued leads without changing any claim.

## Step 1, round 2 -- 2026-08-28T04:34:25Z

Audit schema: fiat-audit-round/v2

Covered: general-cap-regression=reviewed; undeclared-owner=reviewed; aggregate-overreach=reviewed; manifest-self-gap=reviewed; manifest-tree-drift=reviewed; commit-worktree-confusion=reviewed; path-escape=reviewed; outside-path-omission=reviewed; check-coverage-gap=reviewed; schema-compatibility=reviewed; resource-exhaustion=reviewed; subprocess-framing=reviewed; receipt-mutation-order=reviewed; incident-fixture-drift=reviewed; generated-copy-drift=not-applicable

Not checked: the waived Pashov Solidity suite, because this step ships only Markdown and no Solidity; controller, fixture, package, version, or generated-copy behaviour, which step 2 owns; and the unavailable #622 operator artefact and checkpoint bytes. The register dispositions review the published specification only and do not claim the step-2 implementation exists.

Elenchus verdict: unguarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: S1-R1-01 is closed by signed commit 63f62b6aae5852ba6c659b1c43ef961547ae7cbc. The tracked runbook is byte-identical to the amended canonical source at SHA-256 33ce8ee90c388fa613feab6a7d4bc155d2524a8215c4891681b58476facfa61b, and ADR-042 at SHA-256 5654a5d5843271e9d28be1d53ee386e849016453369e6eea221d6211aa6e5041 is now the standing record without claiming implementation. Phylax, Ephoros, Hypomnema, Protasis, Imprimatur, both applicable Brevitas runs, Horos, and `git diff --check` exit 0; the root suite passes 460 of 460 and Hexaemeron passes 1,377 of 1,377 with one skip. The fresh fixed-tree report `.elenchus/fiat-710-step-1.json`, SHA-256 dc708142c75170bcda644d91edb05efb6794d9554e7d4540bdbc7885978f74f8, declares `elenchus.unittest.v1`, `complete: true`, 1,377 tests, zero failures, zero errors, and one skip. The exact source-bound Elenchus classifier returns `unguarded` because the documentation repair changes no test file; byte identity and the named structure, prose, placement, boundary, and suite gates establish the fixed-tree checks without strengthening that verdict. No further step-1 defect was found. The bounded Sapheneia pass preserved the heading, schema fields, all fifteen risk ids and dispositions, waived and deferred scope, prior finding id and closure, commit and document hashes, report schema and digest, test counts, exact verdict, zero-finding row, and unpursued leads without changing any claim.
