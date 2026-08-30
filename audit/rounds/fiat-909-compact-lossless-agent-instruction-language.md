## Step 1, round 1 -- 2026-08-30T01:19:18Z

Audit schema: fiat-audit-round/v2

Covered: semantic-domain-gap=reviewed; source-model-mismatch=reviewed; precedence-collapse=reviewed; negation-drop=reviewed; exception-scope-drift=reviewed; evidence-authority-drift=reviewed; exact-literal-change=reviewed; unknown-opcode-acceptance=reviewed; duplicate-key-shadowing=reviewed; resource-exhaustion=reviewed; path-or-shell-escape=reviewed; bootstrap-understatement=not-applicable; tokenizer-mismatch=not-applicable; evaluation-contamination=not-applicable; closed-answer-omission=not-applicable; agent-transfer-overclaim=not-applicable; derived-view-drift=reviewed; ownership-expansion=reviewed

Not checked: the waived Pashov Solidity suite, because this step changes no Solidity; decoder, formatter, manifest, tokenizer, model-family, mutation, or measurement behaviour reserved for steps 2 through 5; external repositories, network services, credentials, native Windows, and CI; plugin suites outside the checked runner's selected root, documentation, schema, and repository-lint scopes; and a structured Elenchus report adapter, because the source-bound runner declares UTF-8 unittest text and no other runner or report format may be substituted

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | schemas/agent-instruction-v1.schema.json | The version-1 Promise object required its id, evidence, evidence classes, boundary, authorisations, consequence, refusals, recovery, and exceptions but omitted the governed Promise claim itself; compact opcode `M` likewise carried only the id. A model could therefore retain every authority field while losing the claim those fields qualify, so the required Promise Machine fixture could not round-trip a complete promise. The added schema guard reproduced this as one assertion failure on the unfixed step tree. | fixed in this commit; `claim` is now a required exact literal, `M` carries it, and the parent-tree guard records the omission |

Leads not pursued: the physical-line and decoded-literal caps overlap, so step 2 must exercise each limit with every other limit still satisfied and refuse an encoded record over 65,536 bytes; this is not a second step-1 finding because the limits are conjunctive and the contract already requires all other rules to pass. The exact source-bound parent report is plain UTF-8 unittest text rather than one of the current Elenchus script's structured adapters, so the declared report bytes were inspected directly and no nearby runner, output, or format was substituted. No further lead was found in the full diff or the eighteen-item risk review.
