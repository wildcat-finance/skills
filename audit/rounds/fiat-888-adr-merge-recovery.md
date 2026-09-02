## Step 1, round 1 -- 2026-09-02T08:31:24Z

Audit schema: fiat-audit-round/v2

Covered: git-object-input=reviewed; candidate-bytes=reviewed; stale-base=reviewed; workflow-input=reviewed; partial-state=reviewed; provenance=reviewed; hostile-config=reviewed; publication-state=reviewed

Not checked: none

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | .horos/boundary.json | The committed Horos boundary recorded files_walked as 2465 after Step 1 added three durable ADR artefacts. The current-tree root suite reproduced this as two failures in tests.test_agent_instruction.AgentInstructionScaffoldTests.test_horos_boundary_is_current_for_the_scaffold and tests.test_boundary_currency.BoundaryCurrencyTests.test_the_committed_boundary_matches_a_fresh_scan. A fresh scan reported files_walked 2468, entries 128, candidates 85, bytes_binary 43942223, bytes_content_addressed 7844971, bytes_generated 67070, bytes_lockfile 254 and bytes_vendored 94; the focused boundary tests, the root suite (1116 tests), the complete Hexaemeron suite (2204 tests) and the three required lints then passed. | fixed in this commit |

Leads not pursued: none

## Step 1, round 2 -- 2026-09-02T08:34:37Z

Audit schema: fiat-audit-round/v2

Covered: git-object-input=reviewed; candidate-bytes=reviewed; stale-base=reviewed; workflow-input=reviewed; partial-state=reviewed; provenance=reviewed; hostile-config=reviewed; publication-state=reviewed

Not checked: none

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | low | .horos/boundary.json | The round-1 audit commit added audit/rounds/fiat-888-adr-merge-recovery.md and its synopsis after the boundary census was generated, leaving files_walked at 2468 while a fresh scan reported 2470. The root suite again failed tests.test_agent_instruction.AgentInstructionScaffoldTests.test_horos_boundary_is_current_for_the_scaffold and tests.test_boundary_currency.BoundaryCurrencyTests.test_the_committed_boundary_matches_a_fresh_scan; the classified entry set and all other scan counts were unchanged. | fixed in this commit |

Leads not pursued: none
