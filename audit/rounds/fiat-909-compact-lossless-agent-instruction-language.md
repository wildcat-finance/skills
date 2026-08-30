## Step 1, round 1 -- 2026-08-30T01:19:18Z

Audit schema: fiat-audit-round/v2

Covered: semantic-domain-gap=reviewed; source-model-mismatch=reviewed; precedence-collapse=reviewed; negation-drop=reviewed; exception-scope-drift=reviewed; evidence-authority-drift=reviewed; exact-literal-change=reviewed; unknown-opcode-acceptance=reviewed; duplicate-key-shadowing=reviewed; resource-exhaustion=reviewed; path-or-shell-escape=reviewed; bootstrap-understatement=not-applicable; tokenizer-mismatch=not-applicable; evaluation-contamination=not-applicable; closed-answer-omission=not-applicable; agent-transfer-overclaim=not-applicable; derived-view-drift=reviewed; ownership-expansion=reviewed

Not checked: the waived Pashov Solidity suite, because this step changes no Solidity; decoder, formatter, manifest, tokenizer, model-family, mutation, or measurement behaviour reserved for steps 2 through 5; external repositories, network services, credentials, native Windows, and CI; plugin suites outside the checked runner's selected root, documentation, schema, and repository-lint scopes; and a structured Elenchus report adapter, because the source-bound runner declares UTF-8 unittest text and no other runner or report format may be substituted

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | schemas/agent-instruction-v1.schema.json | The version-1 Promise object required its id, evidence, evidence classes, boundary, authorisations, consequence, refusals, recovery, and exceptions but omitted the governed Promise claim itself; compact opcode `M` likewise carried only the id. A model could therefore retain every authority field while losing the claim those fields qualify, so the required Promise Machine fixture could not round-trip a complete promise. The added schema guard reproduced this as one assertion failure on the unfixed step tree. | fixed in this commit; `claim` is now a required exact literal, `M` carries it, and the parent-tree guard records the omission |

Leads not pursued: the physical-line and decoded-literal caps overlap, so step 2 must exercise each limit with every other limit still satisfied and refuse an encoded record over 65,536 bytes; this is not a second step-1 finding because the limits are conjunctive and the contract already requires all other rules to pass. The exact source-bound parent report is plain UTF-8 unittest text rather than one of the current Elenchus script's structured adapters, so the declared report bytes were inspected directly and no nearby runner, output, or format was substituted. No further lead was found in the full diff or the eighteen-item risk review.

## Step 1, round 2 -- 2026-08-30T01:24:40Z

Audit schema: fiat-audit-round/v2

Covered: semantic-domain-gap=reviewed; source-model-mismatch=reviewed; precedence-collapse=reviewed; negation-drop=reviewed; exception-scope-drift=reviewed; evidence-authority-drift=reviewed; exact-literal-change=reviewed; unknown-opcode-acceptance=reviewed; duplicate-key-shadowing=reviewed; resource-exhaustion=reviewed; path-or-shell-escape=reviewed; bootstrap-understatement=not-applicable; tokenizer-mismatch=not-applicable; evaluation-contamination=not-applicable; closed-answer-omission=not-applicable; agent-transfer-overclaim=not-applicable; derived-view-drift=reviewed; ownership-expansion=reviewed

Not checked: the waived Pashov Solidity suite, because the fixed Step 1 tree changes no Solidity; decoder, formatter, manifest, tokenizer, model-family, mutation, or measurement behaviour reserved for steps 2 through 5; external repositories, network services, credentials, native Windows, and CI; plugin suites outside the checked runner's selected root, documentation, schema, and repository-lint scopes; and a structured Elenchus report adapter, because the source-bound runner declares UTF-8 unittest text and no other runner or report format may be substituted

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | .horos/boundary.json | Committing round 1 added the audit record and its generated synopsis as two tracked files after the Step 1 boundary count had been fixed at 2,073. A fresh scan walked 2,075 files, and `BoundaryCurrencyTests.test_the_committed_boundary_matches_a_fresh_scan` failed with `.horos/boundary.json#counts`; the signed fixed tree therefore did not retain the root-suite result observed before those paths became committed history. | fixed in this commit; a complete Horos write records 2,075 and the focused Step 1 runner now carries the same fresh-scan guard |

Leads not pursued: round 1's Promise-claim fix still holds in the schema, compact contract, and focused guard. The physical-line and decoded-literal caps remain a step-2 test-design constraint rather than a second step-1 finding for the reason round 1 records. The parent and fixed source-bound reports remain plain UTF-8 unittest text and were inspected directly without substituting a structured adapter. No further lead was found in the complete fixed diff or the eighteen-item risk review.

## Step 1, round 3 -- 2026-08-30T01:33:26Z

Audit schema: fiat-audit-round/v2

Covered: semantic-domain-gap=reviewed; source-model-mismatch=reviewed; precedence-collapse=reviewed; negation-drop=reviewed; exception-scope-drift=reviewed; evidence-authority-drift=reviewed; exact-literal-change=reviewed; unknown-opcode-acceptance=reviewed; duplicate-key-shadowing=reviewed; resource-exhaustion=reviewed; path-or-shell-escape=reviewed; bootstrap-understatement=not-applicable; tokenizer-mismatch=not-applicable; evaluation-contamination=not-applicable; closed-answer-omission=not-applicable; agent-transfer-overclaim=not-applicable; derived-view-drift=reviewed; ownership-expansion=reviewed

Not checked: the waived Pashov Solidity suite, because the fixed Step 1 tree changes no Solidity; decoder, formatter, manifest, tokenizer, model-family, mutation, or measurement behaviour reserved for steps 2 through 5; external repositories, network services, credentials, native Windows, and CI; plugin suites outside the checked runner's selected root, documentation, schema, and repository-lint scopes; and an Elenchus replay, because this zero-finding round makes no product fix

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: round 1's Promise-claim fix and round 2's Horos currency fix remain present and covered by the focused runner. The physical-line and decoded-literal cap overlap remains a step-2 test-design constraint, and the source-bound runner remains plain UTF-8 unittest text without a structured Elenchus adapter. The complete fixed diff contains only runbook-authorised product paths plus the append-only audit record and synopsis; no further lead emerged from the eighteen-item review.

## Step 2, round 1 -- 2026-08-30T02:59:12Z

Audit schema: fiat-audit-round/v2

Covered: semantic-domain-gap=reviewed; source-model-mismatch=reviewed; precedence-collapse=reviewed; negation-drop=reviewed; exception-scope-drift=reviewed; evidence-authority-drift=reviewed; exact-literal-change=reviewed; unknown-opcode-acceptance=reviewed; duplicate-key-shadowing=reviewed; resource-exhaustion=reviewed; path-or-shell-escape=reviewed; bootstrap-understatement=not-applicable; tokenizer-mismatch=not-applicable; evaluation-contamination=not-applicable; closed-answer-omission=not-applicable; agent-transfer-overclaim=not-applicable; derived-view-drift=reviewed; ownership-expansion=reviewed

Not checked: the Pashov suite under `waived: this run produces no Solidity, so hexaemeron:x-ray, hexaemeron:solidity-auditor, and hexaemeron:fizz do not apply`; source-to-model question fixtures and mutation scoring reserved for Step 3; manifest, compression, tokenizer, bootstrap-cost and cross-family evaluation work reserved for Steps 4 and 5; external repositories, networks, credentials, native Windows and CI; controller receipt, push, pull request, merge, publication and issue closure; and a structured Elenchus adapter, because the exact source-bound runner declares plain UTF-8 unittest text and no runner or format may be substituted

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | `scripts/agent_instruction.py:157`; `scripts/agent_instruction.py:453`; `scripts/agent_instruction.py:579`; `tests/test_agent_instruction.py:410`; `tests/test_agent_instruction.py:634`; `tests/test_agent_instruction.py:880`; `tests/test_agent_instruction.py:951` | Canonical decimals have no digit cap, but binding order, span comparison and compact literal length used Python `int()`. Under Python 3.14, 4,301 decimal digits escaped as `ValueError` instead of one `WAI-*` refusal; a valid model and the required valid 65,536-byte physical-line boundary could not round-trip, while the original at-limit tests parsed invalid records without completing model validation. | fixed and regression-tested in this commit; canonical decimal strings now compare by length and lexical value, literal lengths refuse above 65,000 before safe conversion, and complete models cover exact 65,536-byte line, 16,384-line and 1,048,576-byte file limits plus valid line limit-plus-one refusal |
| S2-R1-02 | medium | `scripts/agent_instruction.py:1050`; `tests/test_agent_instruction.py:1127` | Atomic output derived the sibling temporary name as `.{leaf}.wai-<token>`. An existing filesystem-valid 255-byte target component therefore required a 293-byte temporary component and refused `WAI-E-IO.WRITE`; the old target remained intact, but a valid selected output could not be replaced. | fixed and regression-tested in this commit; the exclusive sibling name is a target-independent 37-byte `.wai-<token>`, and the maximum filesystem component now replaces atomically without leaving a temporary file |

Leads not pursued: The complete Step 2 diff from signed base `ddc5334dc8204e685a7612216d766ad770eda3d4` through signed implementation `b4807a8785ec6e773c3635dcee7ee110f79e1045` and this repaired tree was reviewed for all 18 risks. Duplicate keys and unknown versions, opcodes, keys, enums and escapes refuse; reference coverage, relation cycles, scope ancestry, exception targets and binding overlap remain closed; decode exposes no partial model; symlink, FIFO, directory, traversal and failed-replace paths remain confined; and result records remain one bounded JSON line. `CompactParser` materialises at most the already bounded 1,048,576-byte, 16,384-line input before semantic count validation; this was not promoted because the outer caps precede allocation and no model returns before every semantic cap passes. The exact fixed-tree runner passed 134 of 134 tests; `.hexaemeron/audit-fix-step-2.txt` has SHA-256 `ccd1cc2a474aa25231b86801ca878a8405e3c7f75988c11d8d621461f6cf5050`. The exact parent overlay records assertion failures for both mechanisms and no infrastructure error, so the source-bound plain-text Elenchus verdict is `guarded`; no structured adapter was substituted. The root suite passed 641 tests with 1,258 inoculation cases, zero crashes and zero unexpected-clean cases; `self-test`, `git diff --check`, and the changed-tree Phylax, Ephoros and Hypomnema commands exited zero. Imprimatur scored this record 100.0 with zero defects. Brevitas reported B010 and B011 because Fiat's required one-record host has one heading and the exact two-finding table has two rows; adding headings or an invented row would change protected structure or evidence, so no Brevitas-clean claim is made. An additional repository-wide Hypomnema invocation including the pre-existing generated `.agents/skills/promise-machine/runtime` mirror exited 1 on 71 unresolved mirror links; Step 2 changes none of those paths, and the required changed-document review is clean. No third product defect survived review.
