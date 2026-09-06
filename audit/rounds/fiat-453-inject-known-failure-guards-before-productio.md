## Step 1, round 1 -- 2026-09-05T21:45:20Z

Audit schema: fiat-audit-round/v2

Covered: inventory-omission=reviewed; source-view-drift=reviewed; parent-substitution=reviewed; guard-path-escape=reviewed; report-substitution=reviewed; verdict-confusion=reviewed; partial-inoculation=reviewed; preedit-bypass=reviewed; resume-loss=reviewed; empty-success=reviewed; red-step-handoff=reviewed; self-hosting-overclaim=reviewed

Not checked: The implementations and receipts assigned to Steps 2 through 5; this round reviewed only their Step 1 interfaces. Live GitHub publication, non-macOS secure reads, same-UID mutation after the final identity check, and Solidity were not checked. Solidity is waived by the packet because issue 453 changes no Solidity source or behaviour.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | `docs/known-failure-inoculation-study.md:1`; `plugins/hexaemeron/docs/known-failure-inoculation/runbook.md:1447` | The shipped study has no closed `hypomnema-design-bridge/v1` block. The exact study-mode Hypomnema command exits 1 with `H008 study has no design bridge block`. A minimal bridge to `docs/decisions/drafts/require-inoculation-before-implementation.md` also exits 1 because study mode admits a numbered ADR or governed-skill ledger, not that draft. The effective Step 1 Exit runs only the ordinary Hypomnema walk and says Hypomnema checks all five shipped documents, so it does not establish the selected design's join to its record before the study ships. | open; repair requires controller-receipted study and runbook amendments plus a literal Hypomnema generation before another audit round |
| S1-R1-02 | high | `plugins/hexaemeron/docs/known-failure-inoculation/runbook.md:1449`; `plugins/brevitas/skills/brevitas/scripts/brevitas.py:286` | The effective Exit sends the required audit record through Brevitas report mode. This `fiat-audit-round/v2` record has the one required Step heading and one row per real finding, so the exact command exits 1 with B010, `draft has 1 section headings; minimum is 3`, and B011, `table has 2 data rows and 5 real-data columns; minimum is 3x3`. Adding headings or dummy rows would corrupt the audit grammar and finding count. Brevitas's evidence exception does not waive either structural rule. The Exit therefore requires an unattainable shape for this round and every zero-finding round. | open; repair requires a controller-receipted runbook amendment and an audit-record-aware Brevitas contract before another audit round |

Leads not pursued: No repair was applied in this round. Early ADR numbering conflicts with ADR-077's integration-time assignment and can collide before integration. A governed-skill ledger is the wrong home for this cross-cutting decision. The first repair lead is an exact `adr/<slug>` bridge resolved to one canonical draft or final record after the controller receipts append-only study and runbook amendments. The second is a literal Brevitas generation that recognises the fixed Fiat audit-record structure without weakening its evidence budgets. Before this record was written, the inventory suite passed 37 of 37 tests; the added mutation campaign returned all five expected outcomes; the exact Hexaemeron audit runner passed 2,376 of 2,376 tests with no failures, errors, skips, expected failures, or unexpected successes; the clean detached root suite passed 1,330 of 1,330 tests and its 1,258-case inoculation census had zero crashes and zero unexpected-clean cases; Phylax, Ephoros, and the ordinary Hypomnema walk exited 0; and the exact mapped command selected nine checks, passed all nine, and reported `outcome green`. Specialised study-mode Hypomnema and audit-record Brevitas remain at exit 1 as S1-R1-01 and S1-R1-02.

## Step 1, round 2 -- 2026-09-05T23:11:44Z

Audit schema: fiat-audit-round/v2

Covered: inventory-omission=reviewed; source-view-drift=reviewed; parent-substitution=reviewed; guard-path-escape=reviewed; report-substitution=reviewed; verdict-confusion=reviewed; partial-inoculation=reviewed; preedit-bypass=reviewed; resume-loss=reviewed; empty-success=reviewed; red-step-handoff=reviewed; self-hosting-overclaim=reviewed

Not checked: The implementations and receipts assigned to Steps 2 through 5; this round reviewed only their Step 1 interfaces. Live GitHub publication, non-macOS secure reads, same-UID mutation after the final identity check, and Solidity were not checked. Solidity is waived exactly as `waived: no Solidity source or Solidity behaviour is in the issue 453 scope`.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: The two round-1 findings are fixed by signed product commit `1019fd36326b7e1c51765f3f0d5a0ef57805304a`, whose sole parent is `3253af2a873028d87111237bd3638905626956d4`, and signed no-fast-forward merge `9b5c4418e1a9ec51ba54fb22b46e7d64f51b04b2`, whose parents are the round-1 record `0d58501d6fb3b3e073f3bd9c900b3424928f8ff5` and the product fix in that order. The source-bound H008 guard returned `guarded` with 2,389 executed tests, 13 assertion failures, zero errors, and zero skips; the Brevitas guard returned `guarded` with 91 executed tests, four assertion failures, zero errors, and zero skips. Both parent runners exited 1 on the recorded assertion failures. On the fixed tree, the Hexaemeron report at `.elenchus/fiat-453-step-1-audit.json` passed 2,389 of 2,389 tests and has SHA-256 `c578a814100b50ca1be72d648eec5d21282b8cf7a57907bbae174c79183cff13`; the Brevitas report passed 91 of 91 tests and has SHA-256 `4537e936d4864a2a6b1c142645a7c01dcfc3a9de578afe32983f39501720d160`. Focused inventory, design-bridge, allocator, and contract suites passed 37, 39, 41, and 85 tests. The clean detached root suite passed 1,332 tests, its 1,258-case inoculation census had zero crashes and zero unexpected-clean cases, and the mapped command selected and passed all ten checks with `outcome green`. The committed study and runbook equal their receipted bytes at SHA-256 `b761db434c406dcce1f24bee00a374403c16aa57ea4b462bd4372f1828a966cb` and `0827c534ddffc70c8b6df96f0b80be1042a4410793ebe4296bb30a78c29145fd`. The inventory remains exactly `kf-453-01` through `kf-453-07`; the stable bridge accepts one canonical bounded draft or three-digit final and refuses missing, duplicate, malformed, aliased, special, oversized, or unstable candidates; explicit `fiat-audit-record` mode suppresses only B010 and B011 after the synopsis check, while auto, answer, and report modes remain unchanged. Full diff review and the named refusal tests found no route through any of the twelve covered risks. A scan on the audit branch sees the two inherited Warden files and would move only `.horos/boundary.json#counts` from 2,576 to 2,578 files; the amended contract assigns Horos and root-tree currency to exact product F, where both are clean, and assigns the synopsis, audit Imprimatur input, and `fiat-audit-record` lint to this audit branch. The generated boundary change was not retained in A2. Next action: receipt this zero-finding round with the product fix and exact `guarded` verdict; `done audit` remains a later controller gate and has not run.

## Step 2, round 1 -- 2026-09-06T03:06:17Z

Audit schema: fiat-audit-round/v2

Covered: inventory-omission=reviewed; source-view-drift=reviewed; parent-substitution=reviewed; guard-path-escape=reviewed; report-substitution=reviewed; verdict-confusion=reviewed; partial-inoculation=reviewed; preedit-bypass=reviewed; resume-loss=reviewed; empty-success=reviewed; red-step-handoff=reviewed; self-hosting-overclaim=reviewed

Not checked: the Pashov Solidity suite under its non-Solidity waiver; external repositories, network services, credentials, native Windows, CI, controller receipt, push, pull request, merge, publication and issue closure; Step 3 report retention, manifest admission and guard-manifest proof; model, measurement, parity, tokenizer, Ollama and recorded-adapter processes, which the amended Step 2 contract explicitly disables; and an Elenchus fix replay, because Warden made no product repair and this round's verdict is null

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | `tests/test_promise_machine_contract.py` | The candidate changes this repository-level contract test to require the new `fiat-known-failure-inoculation` promise and raise the closed runtime-binding count from 47 to 48, but the effective Step 2 Complete replacement Files clause omits the path. The signed product range therefore exceeds its source-bound runbook authority even though the change is mechanically necessary. | open; amend the Step 2 Files clause to include this path and refresh the tracked runbook mirror |

Leads not pursued: none
