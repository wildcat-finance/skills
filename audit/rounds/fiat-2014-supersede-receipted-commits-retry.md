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
