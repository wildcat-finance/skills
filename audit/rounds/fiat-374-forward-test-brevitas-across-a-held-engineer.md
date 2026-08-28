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

## Step 2, round 1 -- 2026-08-28T00:44:31Z

Audit schema: fiat-audit-round/v2

Covered: model-provenance=reviewed; source-authority=reviewed; corpus-coverage=reviewed; manifest-drift=reviewed; schema-ambiguity=reviewed; path-escape=reviewed; classification-bias=reviewed; diagnostic-bypass=not-applicable; false-positive-repair=not-applicable; evidence-token-gap=reviewed; ordered-evidence-loss=reviewed; exception-abuse=not-applicable; host-contract-conflict=reviewed; regression-overfit=reviewed; sensitive-output=reviewed; external-capture=reviewed; partial-capture=reviewed; marketplace-drift=not-applicable; frontier-arithmetic=not-applicable

Not checked: Solidity-only Pashov X-Ray, Solidity Auditor, and Fizz under the recorded non-Solidity waiver; a provider-returned model field because `codex-cli 0.150.1` did not retain one; any off-record human classification; Step 3 diagnostic comparison and rule repair; Step 4 marketplace reconciliation and frontier arithmetic

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | `plugins/brevitas/skills/brevitas/evals/corpus.json:8` | All 10 cases label a requested Codex alias as `returned_model_id`. The capture command passed `-m <alias>` and accepted `grep -Fx "model: <alias>"` from the client banner; it retained no provider response field. The backend model therefore remains unestablished, so the reported two-model coverage is unsupported. | open; requires a recapture client or response receipt that preserves the provider-returned full model id rather than another alias/banner check |
| S2-R1-02 | high | `plugins/brevitas/skills/brevitas/evals/corpus.json:42` | All 10 cases assert `reviewer: human-review`, but the only available pre-lint timeline shows the Mason agent reading the outputs and current linter source and then authoring the classifications. No human classification record is present. An off-record human review cannot be excluded, but it cannot qualify the cases under the declared contract. | open; requires a human to record the rule-cited classifications before any new current-diagnostic comparison |
| S2-R1-03 | medium | `plugins/brevitas/skills/brevitas/evals/cases/fixtures/held-diff-review/source.md:1` | The 2,680-byte diff fixture with SHA-256 `4c4cb2d17c7cc841091a18eff6fb34f2adbec37d79508732265abe98b8dce7af` does not reproduce from declared commit `2afa9438e7b7c2d61c627c1d4b0cb515fb8a8461`, path `plugins/pandects/specimens/Sound.sol`, and range `unified diff hunks L222-L273`; the actual commit diff is 3,139 bytes and `cmp` exits 1. The validator also accepted an all-zero origin commit for every case. Apache-2.0 authority exists for Pandects, but these source bytes are not bound to the claimed origin. | open; preserve the captured request, but replace unsupported provenance with a truthful digest-bound derivation record or recapture against exact reproducible source bytes |
| S2-R1-04 | medium | `plugins/brevitas/skills/brevitas/scripts/held_corpus.py:175` | Duplicate-output accounting compared raw path strings after `PurePosixPath` had normalised them. A second model case could use `cases//...` to read the first model's output, copy its digest, classification, and spans, and still validate as 10 qualifying cases. | fixed and regression-tested in this round; every manifest path must now equal its canonical POSIX spelling before any read or coverage accounting |

Leads not pursued: The exact captured Markdown hard-break in `held-solidity-auditor/output-gpt-5.6-terra.md:3` remains byte-identical and digest-bound; base-to-head whitespace inspection warns, while the source-bound clean-tree `git diff --check` exits 0. The other four source excerpts reproduce exactly from their declared ranges, Pandects carries Apache-2.0 at both named source commits, duplicate JSON fields and hostile regular-file, size, UTF-8, symlink, secret-metadata, exact-span, and span-order cases refuse with bounded codes, and diagnostics do not print fixture bytes. Direct report-mode probes exposed six expectation mismatches; Step 3 owns those comparisons and any confirmed bypass or false-positive repair, so no Brevitas rule or captured output changed here. The canonical-path guard reproduced the parent acceptance with `alias_accept cases=10`, passes on the fixed tree, and changes no capture bytes.
