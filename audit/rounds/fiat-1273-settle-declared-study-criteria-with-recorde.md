## Step 1, round 1 -- 2026-09-16T13:12:53Z

Audit schema: fiat-audit-round/v2

Covered: declaration-shape=not-applicable; exit-identity=not-applicable; execution-authority=reviewed; source-binding=reviewed; subprocess-input=reviewed; partial-result=reviewed; amendment-history=reviewed; completion-gap=not-applicable; legacy-replay=reviewed; checkpoint-context=reviewed; resource-growth=reviewed; self-hosting=reviewed; release-copies=reviewed; claim-boundary=reviewed

Not checked: The complete Step 1 range from eaab110104d186bdd0b1d362dd583a2e72ecc21a through 4a02969baefe45d02a8a931f0c630be0480e8ff6 was reviewed against controller-capture and the admitted study/runbook amendments. Declaration and Exit parsing, production execution and attempt recovery, terminal, legacy and checkpoint enforcement and the successor demonstration remain due in Steps 2–5. The selection measurements remain synthetic observations. No Solidity changed; the packet's security-suite waiver applies. This outer run does not demonstrate the new success-criteria feature.

Elenchus verdict: inconclusive

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/hexaemeron/tests/test_imprimatur_family_evidence.py:237 | An occupied escaped-schemas sibling made the old fixture rename fail before testing symlink refusal. Two isolated reproductions failed. The published repair gives the fixture an owned parent, retains symlink refusal and checks that an occupied sibling survives. | fixed in 4a02969baefe45d02a8a931f0c630be0480e8ff6; ordinary and adopted restricted-environment replays pass |

Leads not pursued: No additional actionable lead. Working evidence is under .hexaemeron/evidence/warden-step-1-round-1/: focused-repair.json records 113 passing tests; hex-summary.json records 3,354 tests, zero failures/errors, five skips and one expected failure; greenlight.json records the normal gate running the exact python3 -m unittest discover -s tests command, with 2,046 tests passing; checked-runner.json and .hexaemeron/reports/step-1-checked.json record all 13 checks passing on clean commit 4a02969baefe45d02a8a931f0c630be0480e8ff6. Phylax, Ephoros, Hypomnema, the explicit design bridge, portable sync/check and the prose checks passed. source-copy-check.json verifies 256 copied artifacts; the opening study remains the preserved prefix. evaluation-unchanged.json and the owning emit/tally/verify retain the exact record, 11 prompts and 55 outcomes; no new model observation occurred. elenchus-verdict.json retains the actual incomplete report and runner exit 3: its process boundary refused all 12 child launches, so no guarded result was established. The source adoption and historical d230b3ac07158bd5786a5c58539e6999ed3dda54 implementation admission remain separately preserved in docs/protasis-success-criteria/evidence/. --audit-filter sapheneia:sapheneia was applied with all protected content retained.
