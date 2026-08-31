## Step 1, round 1 -- 2026-08-31T20:57:59Z

Audit schema: fiat-audit-round/v2

Covered: frontier-drift=reviewed; projection-drift=reviewed; stale-prose=reviewed; decision-overreach=not-applicable; reader-unnamed=not-applicable; ledger-arithmetic=not-applicable

Not checked: the security suite is waived for this run and the waiver is on the ledger. This step adds Markdown, JSON and Python tests and changes no Solidity, so x-ray, solidity-auditor and fizz have no target. The three not-applicable register items name artefacts that do not exist at this commit: the decision record and the named reader are owed by step 2, and the ledger row by step 3. Also unchecked: hosted CI, the controller receipt, push and publication, and whether the study's argument about the cohort boundary is correct, which this step commits rather than establishes.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/anamnesis/docs/synkrisis-admission-study.md | The five discipline citations were written as `../<skill>/SKILL.md`, which resolve from the Protasis skill directory the citation style was copied out of and from neither location the study actually occupies. Hypomnema exited 1 with five H001 findings on the committed copy. The receipted study is immutable and `amend study` only appends, so the body could not be corrected in place; the committed copy now carries commit-pinned absolute URLs at 9783e2631de1614716eda5043cd843768d3baa06, matching the convention the prior Anamnesis study already uses, and the runbook's step 1 exit was amended through `hexctl amend runbook` to state the one difference between the committed and receipted study bytes | fixed in this round |

Leads not pursued: two observations carry forward rather than changing code. First, the design record's eighteen reports each name `python3 .hexaemeron/reports/resolve.py <criterion>` as the command that produced them, and `.hexaemeron/` is controller state that is never committed, so a reader of the committed reports cannot rerun them from the repository alone; the study's design-options section states how every value was derived, which is weaker than a runnable script and is what exists. Second, the committed study and the receipted study now differ in five byte ranges by design, so the committed copy is a corrected rendering of the receipted record rather than a byte copy of it; the amendment names the difference, and nothing recomputes one from the other.
