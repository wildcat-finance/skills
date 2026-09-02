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

Leads not pursued: two intervening root-suite attempts under host contention produced WAI-E-ADAPTER.TIMEOUT results in adapter fixture tests; after fixture warm-up and the competing suites clearing, the complete root suite passed 1116/1116, so those attempts are treated as environmental rather than product findings.

## Step 1, round 3 -- 2026-09-02T09:03:45Z

Audit schema: fiat-audit-round/v2

Covered: git-object-input=reviewed; candidate-bytes=reviewed; stale-base=reviewed; workflow-input=reviewed; partial-state=reviewed; provenance=reviewed; hostile-config=reviewed; publication-state=reviewed

Not checked: none

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: Horos check reported informational candidate drift for the pre-existing fiat-909 audit records, while the boundary matched the tree; candidate entries are report-only and outside this step's boundary owner. The fixed tree was re-reviewed with the root suite (1116 tests) and all three lints at exit 0, with no new finding.

## Step 2, round 1 -- 2026-09-02T09:59:33Z

Audit schema: fiat-audit-round/v2

Covered: git-object-input=reviewed; candidate-bytes=reviewed; stale-base=reviewed; workflow-input=reviewed; partial-state=reviewed; provenance=reviewed; hostile-config=reviewed; publication-state=reviewed

Not checked: none

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py | Repository-local info/grafts could rewrite the ancestry answer used to accept a product commit, so an unrelated object could appear descended from the protected base. | fixed in 7ba217a0 |
| S2-R1-02 | medium | plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py | Assignment application rejected clean/process filters in local config but did not inspect the enabled worktree config scope, leaving a configured filter able to execute while worktree bytes were read. | fixed in 7ba217a0 |
| S2-R1-03 | high | plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py | An interruption or backup-cleanup I/O failure during multi-draft installation could leave sources moved or targets partially installed, so the operation was not fail-closed and verified-atomic. | fixed in 7ba217a0 |

Leads not pursued: none
