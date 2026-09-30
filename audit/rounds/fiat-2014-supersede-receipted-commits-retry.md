## Step 1, round 1 -- 2026-09-29T22:23:35Z

Audit schema: fiat-audit-round/v2

Covered: history-rewrite=not-applicable; tree-equivalence=not-applicable; ancestry-leak=not-applicable; mapping-ambiguity=not-applicable; signature-identity=reviewed; platform-identity=not-applicable; consumer-drift=reviewed; partial-write=reviewed; checkpoint-relocation=not-applicable; credential-boundary=reviewed; policy-contradiction=reviewed

Not checked: GitHub account verification, commit supersession, and checkpoint relocation belong to Steps 2 and 3. The recorded security-suite waiver covers this non-Solidity step.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py:3070 | Audit closure can receipt `verified_fixes`, but `last_local_commit` ignored it, so `done prose` checked an earlier SHA instead of the closure-only fixes head. | fixed on audit stack; direct `done_prose` regression failed before the fix and passed after it |
| S1-R1-02 | low | plugins/hexaemeron/tests/test_gate_deferred_registration.py:620 | The new pre-cap runner fixture read the init-base Git object, adding a history dependency to local replay tests. | fixed on audit stack; fixture reconstructs exact bytes from the current runner and asserts the pinned digest |

Leads not pursued: The released-adapter tests still read older Git objects by design; this round did not change that existing fixture contract.

## Step 1, round 2 -- 2026-09-30T00:22:40Z

Audit schema: fiat-audit-round/v2

Covered: history-rewrite=not-applicable; tree-equivalence=not-applicable; ancestry-leak=not-applicable; mapping-ambiguity=not-applicable; signature-identity=reviewed; platform-identity=not-applicable; consumer-drift=reviewed; partial-write=reviewed; checkpoint-relocation=not-applicable; credential-boundary=reviewed; policy-contradiction=reviewed

Not checked: GitHub account verification, commit supersession, and checkpoint relocation belong to Steps 2 and 3. The recorded security-suite waiver covers this non-Solidity step.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: The existing released-adapter historical Git-object dependency remains outside this Step 1 fix; no new lead arose from the fixed tree.

## Step 2, round 1 -- 2026-09-30T03:16:32Z

Audit schema: fiat-audit-round/v2

Covered: history-rewrite=reviewed; tree-equivalence=reviewed; ancestry-leak=reviewed; mapping-ambiguity=reviewed; signature-identity=reviewed; platform-identity=reviewed; consumer-drift=reviewed; partial-write=reviewed; checkpoint-relocation=reviewed; credential-boundary=reviewed; policy-contradiction=reviewed

Not checked: Live GitHub readback was mocked in the signed fixture; complete native checkpoint archive restoration remains for Step 3. The non-Solidity security suite is waived.

Elenchus verdict: inconclusive

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | medium | plugins/hexaemeron/skills/fiat/scripts/hexctl.py:3040 | Append-mode ledger writing could stop inside a JSON line, leaving a pending supersession with no recoverable tail. Publish the checked full ledger through a fsynced stage and atomic replacement. | fixed on the audit stack; the interruption test failed on parent b2add3ff and passed on the fix |

Leads not pursued: The source-bound Elenchus runner launched 12 workers under containment; all received EPERM before any test ran. A diagnostic `--jobs 1` still received EPERM, so the exact verdict is inconclusive, despite the direct parent-red and fixed-tree-green test. No claim of an Elenchus guard is made.

## Step 2, round 2 -- 2026-09-30T06:13:58Z

Audit schema: fiat-audit-round/v2

Covered: history-rewrite=reviewed; tree-equivalence=reviewed; ancestry-leak=reviewed; mapping-ambiguity=reviewed; signature-identity=reviewed; platform-identity=reviewed; consumer-drift=reviewed; partial-write=reviewed; checkpoint-relocation=reviewed; credential-boundary=reviewed; policy-contradiction=reviewed

Not checked: Live GitHub readback remains mocked in the signed fixture. Complete native checkpoint archive restoration belongs to Step 3. The non-Solidity security suite is waived.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: The atomic append, pending replay, original receipt joins, Git ancestry, effective consumers and generated evidence yielded no new finding. Round 1's inconclusive Elenchus verdict remains as recorded.

## Step 3, round 1 -- 2026-09-30T07:54:40Z

Audit schema: fiat-audit-round/v2

Covered: history-rewrite=reviewed; tree-equivalence=reviewed; ancestry-leak=reviewed; mapping-ambiguity=reviewed; signature-identity=reviewed; platform-identity=reviewed; consumer-drift=reviewed; partial-write=reviewed; checkpoint-relocation=reviewed; credential-boundary=reviewed; policy-contradiction=reviewed

Not checked: Live GitHub verification remains pending until the final Step is pushed; the resolver refused before publication and wrote no report. The joined fixture constructs the legacy receipts, mocks pull-request inspection and final-green admission, and tests Git bundle restoration rather than a native outer checkpoint archive. The recorded security-suite waiver covers this non-Solidity step.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: Live `main` carries Hexaemeron package version 1.6.91 while this pinned-base product carries 1.6.89; Fiat's integration sync and version resolution own that comparison. No Step 3 product rewrite was made for it.
