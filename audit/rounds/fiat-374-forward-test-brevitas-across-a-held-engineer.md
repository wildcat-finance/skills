## Step 1, round 1 -- 2026-08-27T23:40:46Z

Audit schema: fiat-audit-round/v2

Covered: model-provenance=not-applicable; source-authority=not-applicable; corpus-coverage=reviewed; manifest-drift=not-applicable; schema-ambiguity=not-applicable; path-escape=reviewed; classification-bias=not-applicable; diagnostic-bypass=not-applicable; false-positive-repair=not-applicable; evidence-token-gap=not-applicable; ordered-evidence-loss=not-applicable; exception-abuse=not-applicable; host-contract-conflict=reviewed; regression-overfit=reviewed; sensitive-output=reviewed; external-capture=not-applicable; partial-capture=reviewed; marketplace-drift=not-applicable; frontier-arithmetic=reviewed

Not checked: Solidity-only Pashov X-Ray, Solidity Auditor, and Fizz under the recorded non-Solidity waiver; held-corpus ingestion, manifest validation, model provenance, classification, rule repair, marketplace cold-read, frontier advancement, and release work assigned to Steps 2 through 5; live providers and external model calls

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | `plugins/brevitas/tests/run_tests.py:226` | The target freshness check and `os.rename` were separate operations. A racing writer could create the target between them; rename replaced its bytes and the runner returned success. The pinned reproduction recorded `write_returned_success=True` and `racing_bytes_survived=False`. | fixed and regression-tested in this round; publication now uses an exclusive hard link and rechecks the published inode, bytes, size, and mode without replacing a racing target |
| S1-R1-02 | low | `plugins/brevitas/tests/run_tests.py:173` | Temporary creation requested mode `0600` but did not normalise the result after the process umask. With an existing parent and umask `0777`, the runner returned success with report mode `000`, contradicting the declared `0600` report contract and leaving the result unreadable to its consumer. | fixed and regression-tested in this round; the runner applies `fchmod(0600)` and verifies the mode before and after exclusive publication |

Leads not pursued: no further defect was confirmed across the 13-file Step 1 diff after checking the durable study and runbook digests, unchanged frontier fields and history rows, generated portable parity, report schema and counters, worktree and parent confinement, symlink and existing-target refusal, interrupted-write cleanup, bounded output, result exits, and the three legacy evaluations. Elenchus reports `passed` because its parent overlay includes both changed files below `plugins/brevitas/tests`; the two exact manual parent probes reproduced the defects, but this round does not relabel that classifier result `guarded`. Brevitas report-mode lint returned B010 and B011 because the required Fiat record has one exact heading and a two-finding table; the owning `fiat-audit-round/v2` host structure was retained rather than padded. The full corpus, provider, model, classification, evidence-span, rule-repair, marketplace, and frontier-completion surfaces remain assigned to Steps 2 through 5.

## Step 1, round 2 -- 2026-08-27T23:47:14Z

Audit schema: fiat-audit-round/v2

Covered: model-provenance=not-applicable; source-authority=not-applicable; corpus-coverage=reviewed; manifest-drift=not-applicable; schema-ambiguity=not-applicable; path-escape=reviewed; classification-bias=not-applicable; diagnostic-bypass=not-applicable; false-positive-repair=not-applicable; evidence-token-gap=not-applicable; ordered-evidence-loss=not-applicable; exception-abuse=not-applicable; host-contract-conflict=reviewed; regression-overfit=reviewed; sensitive-output=reviewed; external-capture=not-applicable; partial-capture=reviewed; marketplace-drift=not-applicable; frontier-arithmetic=reviewed

Not checked: Solidity-only Pashov X-Ray, Solidity Auditor, and Fizz under the recorded non-Solidity waiver; held-corpus ingestion, manifest validation, model provenance, classification, rule repair, marketplace cold-read, frontier advancement, and release work assigned to Steps 2 through 5; live providers and external model calls

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: S1-R1-01 and S1-R1-02 remain closed. The focused collision and restrictive-umask guards pass, and a four-case adverse publication matrix refused link failure, parent-directory fsync failure, post-link mode mutation, and post-link byte mutation without retaining a report or temporary. No new defect was confirmed across the cumulative Step 1 tree; the exact runner passed 29/29, all three legacy evaluations passed, and portable, Promise Machine, Horos, Phylax, Ephoros, and Hypomnema checks exited 0. This clean round has no fixes commit and therefore records a null Elenchus verdict. The exact `fiat-audit-round/v2` heading and zero-finding table remain host-required rather than padded for Brevitas. The full corpus, provider, model, classification, evidence-span, rule-repair, marketplace, and frontier-completion surfaces remain assigned to Steps 2 through 5.
