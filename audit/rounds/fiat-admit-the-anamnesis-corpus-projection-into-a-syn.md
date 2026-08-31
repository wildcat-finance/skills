## Step 1, round 1 -- 2026-08-31T20:57:59Z

Audit schema: fiat-audit-round/v2

Covered: frontier-drift=reviewed; projection-drift=reviewed; stale-prose=reviewed; decision-overreach=not-applicable; reader-unnamed=not-applicable; ledger-arithmetic=not-applicable

Not checked: the security suite is waived for this run and the waiver is on the ledger. This step adds Markdown, JSON and Python tests and changes no Solidity, so x-ray, solidity-auditor and fizz have no target. The three not-applicable register items name artefacts that do not exist at this commit: the decision record and the named reader are owed by step 2, and the ledger row by step 3. Also unchecked: hosted CI, the controller receipt, push and publication, and whether the study's argument about the cohort boundary is correct, which this step commits rather than establishes.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/anamnesis/docs/synkrisis-admission-study.md | The five discipline citations were written as `../<skill>/SKILL.md`, which resolve from the Protasis skill directory the citation style was copied out of and from neither location the study actually occupies. Hypomnema exited 1 with five H001 findings on the committed copy. The receipted study is immutable and `amend study` only appends, so the body could not be corrected in place; the committed copy now carries commit-pinned absolute URLs at 9783e2631de1614716eda5043cd843768d3baa06, matching the convention the prior Anamnesis study already uses, and the runbook's step 1 exit was amended through `hexctl amend runbook` to state the one difference between the committed and receipted study bytes | fixed in this round |

Leads not pursued: two observations carry forward rather than changing code. First, the design record's eighteen reports each name `python3 .hexaemeron/reports/resolve.py <criterion>` as the command that produced them, and `.hexaemeron/` is controller state that is never committed, so a reader of the committed reports cannot rerun them from the repository alone; the study's design-options section states how every value was derived, which is weaker than a runnable script and is what exists. Second, the committed study and the receipted study now differ in five byte ranges by design, so the committed copy is a corrected rendering of the receipted record rather than a byte copy of it; the amendment names the difference, and nothing recomputes one from the other.

## Step 1, round 2 -- 2026-08-31T21:01:49Z

Audit schema: fiat-audit-round/v2

Covered: frontier-drift=reviewed; projection-drift=reviewed; stale-prose=reviewed; decision-overreach=not-applicable; reader-unnamed=not-applicable; ledger-arithmetic=not-applicable

Not checked: unchanged from round 1. The suite waiver still holds and the three not-applicable register items are still owed by steps 2 and 3. Round 2 re-ran the three lints over round 1's fix, confirmed no file under plugins/synkrisis and no pilot projection is touched by this step, and then reviewed the one path round 1 did not reach: what the step runner does for a step number it now admits but whose test file does not exist yet.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | plugins/anamnesis/tests/elenchus.py | Extending STEPS to admit 4 to 6 made steps 5 and 6 reachable before their test files exist, and unittest's wasSuccessful() is true for an empty suite. The runner therefore exited 0 for step 5 and published a report reading complete true, testsRun 0, failures 0. A consumer reading that report sees a passing step whose guards were never written, and argparse rejected those step numbers before this step changed them, so the step opened the window itself. Discovery of zero tests now prints a named refusal, exits 3 and writes no report at all | fixed in this round |

Leads not pursued: the two observations from round 1 stand unchanged and neither is closed by this round. The committed reports still name a resolver under .hexaemeron/ that is never committed, and the committed study is still a corrected rendering of the receipted study rather than a byte copy of it. One new observation is recorded rather than fixed: the refusal exits 3 where a test failure exits 1 and a report-write failure exits 2, and nothing in the plugin declares that mapping, so a caller distinguishing the three reads the source. The two new guards avoid running the runner at step 4 from inside test_s4_records.py, because that file is itself part of the step 4 pattern and the call would recurse; they use step 5 for the refusal and step 1 for the passing case instead.

## Step 1, round 3 -- 2026-08-31T21:02:51Z

Audit schema: fiat-audit-round/v2

Covered: frontier-drift=reviewed; projection-drift=reviewed; stale-prose=reviewed; decision-overreach=not-applicable; reader-unnamed=not-applicable; ledger-arithmetic=not-applicable

Not checked: unchanged from rounds 1 and 2. This round re-ran the three lints, both suites and the evidence check over round 2's fix, and then looked at what that fix introduced: the two new guards spawn the runner as a subprocess and create scratch directories inside the worktree, so the question was whether a run leaves anything behind that a later commit could pick up. It does not; the tree is clean before and after the suite and no scratch directory survives.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: the three carried observations stand and are the honest residue of this step. The committed reports name a resolver under .hexaemeron/ that is never committed, so they cannot be rerun from the repository alone. The committed study is a corrected rendering of the receipted study rather than a byte copy, and nothing recomputes one from the other. The runner's three non-zero exits, 1 for test failure, 2 for report-write failure and 3 for an empty suite, are not declared anywhere outside the source. None of the three admits a wrong design record or a step that reports success without running its guards. The step's battery is green: 181 Anamnesis tests, 118 Synkrisis tests, phylax, ephoros and hypomnema each exit 0, git diff --check is clean, and design_evidence --transition step:2 exits zero.

## Step 2, round 1 -- 2026-08-31T21:17:17Z

Audit schema: fiat-audit-round/v2

Covered: decision-overreach=reviewed; reader-unnamed=reviewed; frontier-drift=reviewed; projection-drift=reviewed; stale-prose=reviewed; ledger-arithmetic=not-applicable

Not checked: the security suite waiver still holds; this step adds Markdown and Python tests and changes no Solidity. The one not-applicable register item is the ledger row, which step 3 owns. Also unchecked: hosted CI, the controller receipt, push and publication, and whether Synkrisis would in fact decline the admission if asked, which this record does not claim to know.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/anamnesis/docs/decisions/ADR-004-consumer-projections.md | ADR-004 states that the Synkrisis projection emits "the audit-corpus observation schema Synkrisis explicitly admits". Synkrisis has never admitted it, the SKILL.md and pull request 1024 both say so, and ADR-005 now records the opposite decision in the same directory. Two accepted records disagreeing about the same fact leaves a reader no way to tell which is current. No ADR in this repository had ever been superseded, so the correction is a Status annotation naming ADR-005 rather than a rewrite of the reasoning, and a guard holds it there | fixed in this round |
| S2-R1-02 | low | plugins/anamnesis/docs/decisions/ADR-005-corpus-projections-outside-the-cohort-boundary.md | ADR-005 cited "ADR-004" three times meaning the Synkrisis record about reachability evidence, while sitting in a directory whose own ADR-004 is a different document about consumer projections. A reader resolving the reference locally reaches the wrong file. All three now name Synkrisis explicitly and the first carries the full repository path | fixed in this round |

Leads not pursued: two observations carry forward. The register item reader-unnamed is reviewed rather than closed: ADR-005 names the reader as the projection read directly under its own schema, with the emitting command, the shape gate and the self-sufficiency guard behind it, and that is a named surface rather than a named consumer. No other member reads it today and the record says so plainly, so the honest statement is that the projection is legible on its own terms, not that something consumes it. Separately, the ADR-004 correction establishes that the earlier record now carries the right status, and it does not establish that every other first-party document is consistent; the cold read that answers that is step 3's, and the guard added here checks one document rather than the set.
