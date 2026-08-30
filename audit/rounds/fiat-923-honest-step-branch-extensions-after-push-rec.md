## Step 1, round 1 -- 2026-08-30T03:43:55Z

Audit schema: fiat-audit-round/v2

Covered: descendant-is-not-verification=reviewed; nonancestor-accepted=not-applicable; ancestry-unanswered=not-applicable; replacement-ref-substitution=not-applicable; legacy-short-head=not-applicable; post-merge-verification-window=reviewed; remote-tip-race=not-applicable; state-mutation-on-refusal=not-applicable; diagnostic-overclaim=reviewed; genuine-rewrite-recovery-regression=reviewed; effective-range-staleness=not-applicable; current-step-scope-drift=not-applicable; run-branch-topology-regression=not-applicable; publisher-separation-regression=reviewed; prior-run-cause-drift=reviewed; performance-amplification=reviewed; historical-overclaim=reviewed

Not checked: Step 2 controller behaviour and its tests; live branch, pull-request, GitHub, signature, attribution, merge, integration, and publication operations.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: none

## Step 2, round 1 -- 2026-08-30T07:01:10Z

Audit schema: fiat-audit-round/v2

Covered: descendant-is-not-verification=reviewed; nonancestor-accepted=reviewed; ancestry-unanswered=reviewed; replacement-ref-substitution=reviewed; legacy-short-head=reviewed; post-merge-verification-window=reviewed; remote-tip-race=reviewed; state-mutation-on-refusal=reviewed; diagnostic-overclaim=reviewed; genuine-rewrite-recovery-regression=reviewed; effective-range-staleness=reviewed; current-step-scope-drift=reviewed; run-branch-topology-regression=reviewed; publisher-separation-regression=reviewed; prior-run-cause-drift=reviewed; performance-amplification=reviewed; historical-overclaim=reviewed

Not checked: Live GitHub branch, pull-request, merge, signature-API, publication, and integration operations; the recorded non-Solidity waiver excludes the Pashov Solidity suite.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/hexaemeron/tests/test_step_branch_extensions.py | The receipted audit command passed the focused test filename as a second report path to `run_tests.py`; both reproductions exited 2 before discovery and wrote no report. The scoped direct mode now runs this module's 10 tests and delegates secure target binding, exact payload construction, and exclusive creation to the existing reporter. | fixed in this round |

Leads not pursued: Four amended-entry census events remain outside issue #923 and were neither repaired nor suppressed: `test_hexctl_checkpoint.HexctlCheckpointTests.test_resource_limits_refuse_before_publish` (macOS `Errno 63`); `test_issue_429_recovery.Issue429RecoveryTests.test_root_audit_is_the_exact_pinned_base_blob` (observed `d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d`, stale pin `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa`); `test_hexctl_checkpoint.HexctlCheckpointTests.test_duplicate_state_and_ledger_keys_refuse` (Python 3.14.6 deep-nesting assertion); and `test_check_runner.CheckMapContractTests.test_every_tracked_path_has_exactly_one_owner` (14 Homologia paths, list SHA-256 `24546ae5296e36960544549c6f43c570dfb09782e30bb9dc9388181b6e139c1b`).

## Step 2, round 2 -- 2026-08-30T07:40:57Z

Audit schema: fiat-audit-round/v2

Covered: descendant-is-not-verification=reviewed; nonancestor-accepted=reviewed; ancestry-unanswered=reviewed; replacement-ref-substitution=reviewed; legacy-short-head=reviewed; post-merge-verification-window=reviewed; remote-tip-race=reviewed; state-mutation-on-refusal=reviewed; diagnostic-overclaim=reviewed; genuine-rewrite-recovery-regression=reviewed; effective-range-staleness=reviewed; current-step-scope-drift=reviewed; run-branch-topology-regression=reviewed; publisher-separation-regression=reviewed; prior-run-cause-drift=reviewed; performance-amplification=reviewed; historical-overclaim=reviewed

Not checked: Live GitHub branch, pull-request, merge, signature-API, publication, and integration operations; the recorded non-Solidity waiver excludes the Pashov Solidity suite.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: Four amended-entry census events remain outside issue #923 and were neither repaired nor suppressed: `test_hexctl_checkpoint.HexctlCheckpointTests.test_resource_limits_refuse_before_publish` (macOS `Errno 63`); `test_issue_429_recovery.Issue429RecoveryTests.test_root_audit_is_the_exact_pinned_base_blob` (observed `d0be89aa23e8db7979ac29ff1613e31d59a1ee78d07131147d50eb6268e01d9d`, stale pin `c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa`); `test_hexctl_checkpoint.HexctlCheckpointTests.test_duplicate_state_and_ledger_keys_refuse` (Python 3.14.6 deep-nesting assertion); and `test_check_runner.CheckMapContractTests.test_every_tracked_path_has_exactly_one_owner` (14 Homologia paths, list SHA-256 `24546ae5296e36960544549c6f43c570dfb09782e30bb9dc9388181b6e139c1b`).
