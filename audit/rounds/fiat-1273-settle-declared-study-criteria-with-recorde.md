## Step 1, round 1 -- 2026-09-16T13:12:53Z

Audit schema: fiat-audit-round/v2

Covered: declaration-shape=not-applicable; exit-identity=not-applicable; execution-authority=reviewed; source-binding=reviewed; subprocess-input=reviewed; partial-result=reviewed; amendment-history=reviewed; completion-gap=not-applicable; legacy-replay=reviewed; checkpoint-context=reviewed; resource-growth=reviewed; self-hosting=reviewed; release-copies=reviewed; claim-boundary=reviewed

Not checked: The complete Step 1 range from eaab110104d186bdd0b1d362dd583a2e72ecc21a through 4a02969baefe45d02a8a931f0c630be0480e8ff6 was reviewed against controller-capture and the admitted study/runbook amendments. Declaration and Exit parsing, production execution and attempt recovery, terminal, legacy and checkpoint enforcement and the successor demonstration remain due in Steps 2–5. The selection measurements remain synthetic observations. No Solidity changed; the packet's security-suite waiver applies. This outer run does not demonstrate the new success-criteria feature.

Elenchus verdict: inconclusive

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | plugins/hexaemeron/tests/test_imprimatur_family_evidence.py:237 | An occupied escaped-schemas sibling made the old fixture rename fail before testing symlink refusal. Two isolated reproductions failed. The published repair gives the fixture an owned parent, retains symlink refusal and checks that an occupied sibling survives. | fixed in 4a02969baefe45d02a8a931f0c630be0480e8ff6; ordinary and adopted restricted-environment replays pass |

Leads not pursued: No additional actionable lead. Working evidence is under .hexaemeron/evidence/warden-step-1-round-1/: focused-repair.json records 113 passing tests; hex-summary.json records 3,354 tests, zero failures/errors, five skips and one expected failure; greenlight.json records the normal gate running the exact python3 -m unittest discover -s tests command, with 2,046 tests passing; checked-runner.json and .hexaemeron/reports/step-1-checked.json record all 13 checks passing on clean commit 4a02969baefe45d02a8a931f0c630be0480e8ff6. Phylax, Ephoros, Hypomnema, the explicit design bridge, portable sync/check and the prose checks passed. source-copy-check.json verifies 256 copied artifacts; the opening study remains the preserved prefix. evaluation-unchanged.json and the owning emit/tally/verify retain the exact record, 11 prompts and 55 outcomes; no new model observation occurred. elenchus-verdict.json retains the actual incomplete report and runner exit 3: its process boundary refused all 12 child launches, so no guarded result was established. The source adoption and historical d230b3ac07158bd5786a5c58539e6999ed3dda54 implementation admission remain separately preserved in docs/protasis-success-criteria/evidence/. --audit-filter sapheneia:sapheneia was applied with all protected content retained.

## Step 1, round 2 -- 2026-09-16T14:19:02Z

Audit schema: fiat-audit-round/v2

Covered: declaration-shape=not-applicable; exit-identity=not-applicable; execution-authority=reviewed; source-binding=reviewed; subprocess-input=reviewed; partial-result=reviewed; amendment-history=reviewed; completion-gap=not-applicable; legacy-replay=reviewed; checkpoint-context=reviewed; resource-growth=reviewed; self-hosting=reviewed; release-copies=reviewed; claim-boundary=reviewed

Not checked: This follow-up reviewed the fixed S1-R1-01 fixture and the unchanged Step 1 product scope, then investigated the hosted audit PR failure against the exact d230b3ac07158bd5786a5c58539e6999ed3dda54 base and cc71d04984d8a6ca2c197055aff96e6cf5c7a61b audit head. The independent plugin-release check refused because the audit PR changed Hex-owned files while both sides declared package 1.6.44; two local reproductions had the same result and digest. The bounded repair changes only the four package values and two exact version expectations to 1.6.45. Fresh affected tests, three lints, design bridge, evaluation replay, portable checks, normal root suite, full Hex Exit and exact checked runner passed on signed commit 225b1e640136c67471d4f6bf556924ea4692f299 with tree 4ab8a0ba1951d0250bebcd0701e86910ac018937. Elenchus ran against that candidate but remained inconclusive: its process boundary refused all 12 child launches with Operation not permitted and returned runner exit 3; no guarded result was established. Production declaration, execution, recovery, terminal, legacy and checkpoint enforcement and the successor demonstration remain due in Steps 2-5. The accepted non-Solidity waiver applies. All round-1 audit bytes, the failed release checks, and the unadmitted zero-finding draft history remain preserved.

Elenchus verdict: inconclusive

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | low | .claude-plugin/marketplace.json:35; plugins/hexaemeron/.claude-plugin/plugin.json:4 | The audit PR changed Hex package metadata while its base already declared 1.6.44, so plugin-release refused the equal version. Two local reproductions had the same failure digest. | fixed in 225b1e640136c67471d4f6bf556924ea4692f299; all six version values now declare 1.6.45 and the release check passes |

Leads not pursued: No additional actionable lead. The fixed candidate's fresh evidence is under .hexaemeron/evidence/warden-step-1-round-2/package-repair/: release-red-1.json and release-red-2.json preserve the two identical failures; release-commit-green.json and release-staged-green.json preserve the passing release checks; affected-package-tests.json, family-ordinary.json, family-restricted.json, phylax.json, ephoros.json, hypomnema.json, design-bridge.json, evaluation-emit.json, evaluation-tally.json, evaluation-verify.json, portable-sync.json, portable-check.json, greenlight.json, hex-exit.json and checked-runner.json preserve the required green gates. review.json binds the six-path metadata-only repair, 290 current provenance rows and 256 unchanged historical rows; fixed-commit.json binds the clean signed tree. elenchus-verdict.json retains the actual incomplete scheduler report and exit 3. The selected Step 1 scaffold remains the only delivered product; future criteria and controller operations remain due in Steps 2-5. --audit-filter sapheneia:sapheneia was applied with every protected item retained.

## Step 1, round 3 -- 2026-09-16T14:36:19Z

Audit schema: fiat-audit-round/v2

Covered: declaration-shape=not-applicable; exit-identity=not-applicable; execution-authority=reviewed; source-binding=reviewed; subprocess-input=reviewed; partial-result=reviewed; amendment-history=reviewed; completion-gap=not-applicable; legacy-replay=reviewed; checkpoint-context=reviewed; resource-growth=reviewed; self-hosting=reviewed; release-copies=reviewed; claim-boundary=reviewed

Not checked: This follow-up reviewed the signed Hex 1.6.45 repair and ran the required fresh lints and exact root suite on its unchanged tree. The first round-3 root execution found that the committed Horos census did not include the newly appended audit record: its Markdown byte total was stale. The bounded owner repair regenerated only .horos/census.json. A fresh census check, three fresh lints, the exact root suite, the full Hex Exit and the declared Elenchus command then passed on the unchanged signed candidate; the Elenchus report is complete with 3,354 tests, zero failures and zero errors, five skips and one expected failure. Production declaration, execution, recovery, terminal, legacy and checkpoint enforcement and the successor demonstration remain due in Steps 2-5. The accepted non-Solidity waiver applies. Round-1 and round-2 audit bytes, both prior release failures, and all prior inconclusive evidence remain preserved.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | low | .horos/census.json:11,216 | The committed Horos census omitted the bytes added by the round-2 audit record, so the exact root suite refused its fresh-census currency assertion. | fixed in the signed round-3 audit repair commit; owner regeneration now reports 1,175 Markdown files at 25,555,655 bytes and 4,097 total files at 122,702,147 bytes, and the root suite passes |

Leads not pursued: None. The initial failing root run is preserved as .hexaemeron/evidence/warden-step-1-round-2/round-3-root-suite.log; the fixed run is round-3-root-suite-fixed.log, with its exact tree and index identity. round-3-phylax-fixed.json, round-3-ephoros-fixed.json, round-3-hypomnema-fixed.json and round-3-horos-census-fixed.json record fresh zero-exit checks. round-3-elenchus-fixed.log and .hexaemeron/reports/step-1-round-3-elenchus.json record the complete passing Elenchus result. The selected Step 1 scaffold remains the only delivered product; future criteria and controller operations remain due in Steps 2-5. --audit-filter sapheneia:sapheneia was applied with every protected item retained.

## Step 1, round 4 -- 2026-09-16T14:53:31Z

Audit schema: fiat-audit-round/v2

Covered: declaration-shape=not-applicable; exit-identity=not-applicable; execution-authority=reviewed; source-binding=reviewed; subprocess-input=reviewed; partial-result=reviewed; amendment-history=reviewed; completion-gap=not-applicable; legacy-replay=reviewed; checkpoint-context=reviewed; resource-growth=reviewed; self-hosting=reviewed; release-copies=reviewed; claim-boundary=reviewed

Not checked: This clean follow-up reviewed the fixed Step 1 tree at 8285ceaa48eff14d9eb2dd4ed7696a6a9a401014, reran the three required lints and the exact root suite, and found no new issue. The release metadata and Horos census repairs remain present and source-bound. Production declaration, execution, recovery, terminal, legacy and checkpoint enforcement and the successor demonstration remain due in Steps 2-5. The accepted non-Solidity waiver applies. Earlier audit rounds, their failures, fixes and actual Elenchus classifications remain preserved.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: None. round-4-phylax.json, round-4-ephoros.json, round-4-hypomnema.json and round-4-root-suite.json record the clean follow-up. No additional product change or audit lead was identified; Step 1 is ready for its audit close and prose handoff. --audit-filter sapheneia:sapheneia was applied with every protected item retained.

## Step 2, round 1 -- 2026-09-16T16:44:20Z

Audit schema: fiat-audit-round/v2

Covered: declaration-shape=reviewed; exit-identity=reviewed; execution-authority=reviewed; source-binding=reviewed; subprocess-input=reviewed; partial-result=not-applicable; amendment-history=reviewed; completion-gap=not-applicable; legacy-replay=not-applicable; checkpoint-context=not-applicable; resource-growth=reviewed; self-hosting=reviewed; release-copies=reviewed; claim-boundary=reviewed

Not checked: Step 2 does not launch a target command or claim an execution result. Child execution custody, interrupted attempts, retries, terminal completion, legacy replay, checkpoint restore and the successor demonstration remain due in Steps 3-5. The selection measurements remain synthetic observations. No Solidity changed; the packet's security-suite waiver applies.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: None. The pure bounded parser and inert adapter were reviewed against the exact Step 2 commit f04918a2cd89573914db65cf275c4e146262655f. Focused criteria tests, the full Hex Exit (3,395 tests, zero failures/errors, five skips and one expected failure), the checked runner (13/13 checks green), the staged root gate (2,047 tests), fresh Phylax, Ephoros and Hypomnema lints, and the fresh root suite (2,047 tests) passed. Evidence is under .hexaemeron/evidence/warden-step-2-round-1/: review.json records the bounded review and its exclusions; phylax.json, ephoros.json, hypomnema.json and root-suite.json retain the fresh mechanical checks. No actionable lead was identified. --audit-filter sapheneia:sapheneia was applied with every protected item retained.

## Step 3, round 1 -- 2026-09-16T20:11:39Z

Audit schema: fiat-audit-round/v2

Covered: declaration-shape=reviewed; exit-identity=reviewed; execution-authority=reviewed; source-binding=reviewed; subprocess-input=reviewed; partial-result=reviewed; amendment-history=not-applicable; completion-gap=reviewed; legacy-replay=not-applicable; checkpoint-context=not-applicable; resource-growth=reviewed; self-hosting=not-applicable; release-copies=reviewed; claim-boundary=reviewed

Not checked: This round reviewed the Step 3 execution adapter, its due-step controller bindings, the declared command admission and the source-bound replay path. Amendment custody, legacy compatibility, checkpoint restoration and the separate successor-controller demonstration remain due in Steps 4 and 5. No Solidity changed; the packet's security-suite waiver applies. Elenchus completed the declared Hex guard with 3,380 tests, zero failures and zero errors, five skips and one expected failure; the local execution proof also recorded an actual bounded timeout. Hosted pull-request and merge state remain outside this round.

Elenchus verdict: passed

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | high | plugins/hexaemeron/skills/fiat/scripts/criteria_execution.py:609 | Result replay called an undefined `as_dict`, so a real observed attempt could not be validated or settle its consuming criterion. | fixed in 73978449950ad4b2720cfd155bfdcf7668bc8e5c; focused tests, the full Hex guard, the checked root gate and a real timeout replay pass |
| S3-R1-02 | high | plugins/hexaemeron/skills/fiat/scripts/criteria_execution.py:141 | Source custody rejected this repository's 40-character Git SHA-1 commit and tree identities before launching any registered command. | fixed in 4d206f25fd2074746e43ea56d7459f7fcb1de988; disposable Git identity regression, full Hex guard, root gate and the real source-bound timeout path pass |

Leads not pursued: No additional actionable lead was identified after the two causal repairs. The clean signed source-bound execution record is the direct replay evidence: `observed-execution` admitted and launched the registered Step 3 Hex command, recorded `timeout`, kept `settled=false`, and preserved identical clean signed commit/tree identities before and after. The full Hex guard is `.hexaemeron/reports/step-3-guard.json` with the counts above; the normal root gate recorded 2,048 passing tests; focused criteria/gate/scaffold tests recorded 65 passing tests before the final source-identity regression and 66 after it. Fresh Imprimatur, Phylax, Ephoros and Hypomnema checks were clean, and the required `--audit-filter sapheneia:sapheneia` was applied. Earlier Step 1 and Step 2 audit records and their generated synopses remain unchanged.

## Step 3, round 2 -- 2026-09-16T20:29:06Z

Audit schema: fiat-audit-round/v2

Covered: declaration-shape=reviewed; exit-identity=reviewed; execution-authority=reviewed; source-binding=reviewed; subprocess-input=reviewed; partial-result=reviewed; amendment-history=not-applicable; completion-gap=reviewed; legacy-replay=not-applicable; checkpoint-context=not-applicable; resource-growth=reviewed; self-hosting=not-applicable; release-copies=reviewed; claim-boundary=reviewed

Not checked: This round rechecked the Step 3 execution adapter, its due-step bindings, the declared command admission and the source-bound replay path after both causal repairs. Amendment custody, legacy compatibility, checkpoint restoration and the separate successor-controller demonstration remain due in Steps 4 and 5. No Solidity changed; the packet's security-suite waiver applies. Hosted pull-request and merge state remain outside this round.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: Nothing new was found. S3-R1-01 is fixed in 73978449950ad4b2720cfd155bfdcf7668bc8e5c and S3-R1-02 is fixed in 4d206f25fd2074746e43ea56d7459f7fcb1de988. The current clean signed source-bound execution record still admits and launches the registered Step 3 command, records its bounded timeout, keeps `settled=false`, and preserves identical commit and tree identities before and after. The required lints and root suite were rerun for this round; the audit filter remains `sapheneia:sapheneia`.
