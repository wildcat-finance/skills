## Step 1, round 1 -- 2026-08-28T06:01:09Z

Audit schema: fiat-audit-round/v2

Covered: api-schema-drift=not-applicable; cursor-incompleteness=not-applicable; unknown-event=not-applicable; subject-misattribution=not-applicable; maturity-boundary=reviewed; unit-accounting=reviewed; settlement-language=reviewed; derived-citation=reviewed; source-completeness=reviewed; rest-origin=not-applicable; response-bounds=not-applicable; fixture-fidelity=not-applicable; partial-output=reviewed; marketplace-drift=not-applicable

Not checked: the Pashov X-Ray, Solidity Auditor and Fizz pipelines under the recorded non-Solidity waiver; Steps 2 through 4 adapter, API, dossier, demonstration and marketplace behavior; live Morpho responses or archive-chain completeness; power-loss durability; a hostile concurrent writer able to enumerate and replace the unpredictable private stage; hosted CI, controller receipt, push, pull request, merge and issue closure

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `plugins/probitas/tests/run_tests.py:190`; `plugins/probitas/tests/test_run_tests.py:178` | Failed-write cleanup checked the public report name's inode and then unlinked that name. A replacement between those operations could be deleted, violating the promise never to remove a target the runner no longer owned. | fixed and regression-tested in this round; complete bytes are staged under an unpredictable private name and reach the fresh report target only through an exclusive hard link |
| S1-R1-02 | low | `plugins/probitas/tests/run_tests.py:204`; `plugins/probitas/tests/run_tests.py:270`; `plugins/probitas/tests/test_run_tests.py:220`; `plugins/probitas/tests/test_run_tests.py:246` | A post-open `fstat` failure left the fresh file behind, and a `BaseException` during writing bypassed descriptor cleanup. Either path could leave an incomplete target or open descriptor after an interrupted run. | fixed and regression-tested in this round; post-open inspection and interruption paths close the descriptor, remove the private stage and preserve the original exception |

Leads not pursued: No third defect survived the complete diff review from `7e449ba35e1519d28b33f06225c4c4137b548a23` through `db479bbbab3215871a219e5bcb11c52cc7c9e1ee`. The three new guard cases were observed red before their fixes and green afterwards. The exact source-bound Elenchus classifier returned `passed`, not `guarded`, because both the runner implementation and its tests live under `plugins/probitas/tests/` and were overlaid onto the parent. The repaired tree passed 14 focused runner tests, 290 Probitas tests and 460 root tests; portable runtime check, `git diff --check`, Phylax, Ephoros and Hypomnema exited zero. Long-option abbreviation was not promoted because it does not weaken path confinement or the exact controller command. The security waiver remains exactly `waived: Issue #390 changes Probitas off-chain Python, fixtures, tests, and marketplace prose; it produces no Solidity.` The audit-filter declaration is exactly `--audit-filter sapheneia:sapheneia`.
