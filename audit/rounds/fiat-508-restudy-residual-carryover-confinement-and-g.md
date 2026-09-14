## Step 1, round 1 -- 2026-09-13T17:17:29Z

Audit schema: fiat-audit-round/v2

Covered: tool-bypass=reviewed; git-common-dir=reviewed; partial-reconstruction=reviewed; packet-omission=reviewed; origin-drift=reviewed; gate-probe-effects=reviewed; source-substitution=reviewed; false-closure=reviewed; descendant-lifetime=reviewed; controller-metadata=reviewed; inherited-authority=reviewed

Not checked: Runtime launch confinement, metadata and deputy exclusion, descendant lifetime, carryover reconstruction, inoculation and gate replay remain pending at the frozen conformance transitions. This review covers the full Step 1 diff from 45f2a7e3e14395af218c9373eeecaf263bf766da through 2e8eb0220433efbeb04d600a6f0fd17c2395d82c and the README repair. Historical probe outcomes were read and their preserved digests checked; the probes were not rerun. Solidity suite waived because no Solidity changed.

Elenchus verdict: unguarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | low | docs/fiat-508-residual/README.md:5 | The direct draft link becomes dangling when ADR assignment renames the record. Two disposable rename specimens reproduced it. Cite adr/confine-the-worker-before-admitting-its-output. | fixed in de23e1d629f8e1a74ae3889ef5bf207e0b35ead5 |
| S1-R1-02 | low | .hexaemeron/runbook.md:29 | The declared elenchus.unittest.v1 report format is a schema name; the Elenchus CLI rejects it with exit 2. The adapter is unittest-json-v1. | fixed by controlled Step 1 Tests amendment 2f07a2987b4eaff4edf85aefe93a4d7ac9ad018d4f6660cade332e2c0def148a; original source preserved |

Leads not pursued: Fixture schemas deliberately check inert shapes only; unsafe path, digest and command semantics belong to later executors, whose resolver currently refuses all 22 candidate/criterion calls without writing reports. The future Step 7 test filename was corrected by the controller's seventh amendment; no later-step implementation was reviewed. All 14 preserved evidence digests match their inventory. Phylax and Ephoros over plugins, tests and docs/fiat-508-residual exited 0; Hypomnema over the required repository documents and the explicit study/design bridge exited 0. The independent python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-1-warden-round1-tests.json passed 2688 tests, 0 failures, 0 errors and 0 skips. The staged .githooks/greenlight ran python3 -m unittest discover -s tests: 1916 tests, exit 0. Guard check on de23e1d629f8e1a74ae3889ef5bf207e0b35ead5: unguarded -- the commit changed no test files. Elenchus used the amended command python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report {report}, adapter unittest-json-v1 and declared .hexaemeron/reports/step-1-elenchus.json; it ran no parent tests. Current source runbook digest: 3bda1dc90775ac5d7df579e87646201f656b0d268bc586aafeea9c75c0035efb. Audit-filter declaration: sapheneia:sapheneia.

## Step 1, round 2 -- 2026-09-13T17:27:39Z

Audit schema: fiat-audit-round/v2

Covered: tool-bypass=reviewed; git-common-dir=reviewed; partial-reconstruction=reviewed; packet-omission=reviewed; origin-drift=reviewed; gate-probe-effects=reviewed; source-substitution=reviewed; false-closure=reviewed; descendant-lifetime=reviewed; controller-metadata=reviewed; inherited-authority=reviewed

Not checked: Runtime confinement, host deputies, live Git/controller metadata protection, descendant lifetime, carryover reconstruction, inoculation and gate replay remain pending at their named conformance transitions. This fresh review covers the Step 1 tree at 24c83d14f7efbf3d0ddbf53d8c99b952b0f1dce8 against the risk register and amended Tests contract. No Solidity changed; the recorded suite waiver still applies. The unchanged Hexaemeron suite and historical probes were not rerun in round 2.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: S1-R1-01 remains fixed by the stable decision citation; S1-R1-02 remains fixed by the source-bound unittest-json-v1 amendment. All 14 preserved evidence digests still match; no runtime or test source changed. Inert fixture acceptance supplies no runtime authority, and the resolver still contains no report writer or successful criterion result. Fresh Phylax and Ephoros over plugins, tests and docs/fiat-508-residual exited 0; Hypomnema over the required repository documents, audit record and explicit study/design bridge exited 0. Root-suite evidence is /tmp/issue508-warden-round2-greenlight.log from .githooks/greenlight executing python3 -m unittest discover -s tests; this record requires that execution to exit 0 before signing. No new fixes commit or Elenchus classification belongs to this round. Audit-filter declaration: sapheneia:sapheneia.

## Step 2, round 1 -- 2026-09-14T00:48:43Z

Audit schema: fiat-audit-round/v2

Covered: tool-bypass=reviewed; git-common-dir=reviewed; partial-reconstruction=reviewed; packet-omission=reviewed; origin-drift=reviewed; gate-probe-effects=reviewed; source-substitution=reviewed; false-closure=reviewed; descendant-lifetime=reviewed; controller-metadata=reviewed; inherited-authority=reviewed

Not checked: Controller launch admission, cumulative carryover, replacement reconstruction, inoculation and command validation remain due in later steps. This review covers the full Step 2 diff from 04e9d074d39697bf7451e395a71b8d1e6aa98bb1 through 42116a99814f54e7bb738b0dd5d61cf5e4d67d15 and repair 8215c5c360f5b2e8c2ae4497cf5d24f812d6f001 against whole-worker-sandbox. Native results cover this macOS host. Historical model/proof observations were not rerun; current descriptors retain the old observations. Solidity suite waived because no Solidity changed.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S2-R1-01 | high | plugins/hexaemeron/skills/fiat/scripts/worker_exec.py:164 | Numeric sysctl variants 38 and 49 recovered a controlled sibling's environment. The tested host requires both a five-name startup allowance and explicit process-info denial. The regression failed on both variants before repair and passes after it. | fixed in 8215c5c360f5b2e8c2ae4497cf5d24f812d6f001 |

Leads not pursued: Global metadata reads remain allowed; no total scratch disk quota or aggregate descendant resource accounting is claimed. Six extra capture probes passed on the original source. Removing sysctl reads broke uname startup; either single control still exposed the sentinel. Bare by-name calls returned EINVAL and PID-suffixed names ENOENT outside confinement, so they establish no denial. The saved policy matrix and controlled-child guards retain those limits. The original mapped Hex run exited -15 without output; its sender and cause remain unknown, and the policy repair is not claimed to explain or resolve it. The repaired staged run retained eleven passing checks, including 1919 root tests with one snapshot skip; dead-code suppression validation refused the uncommitted tree with exit 2, and Hex exited 3 because the command-local PATH omitted Forge. Fresh clean-commit reruns passed suppression validation and all 2705 Hex tests with zero failures, errors, skips or blocked fixtures. Suppression validation reports 232 candidates and repository=degraded, which is not a clean dead-code analysis. The normal repair commit gate passed 1919 tests without skips. Phylax, Ephoros and Hypomnema each exited 0. The two due resolver observations were refreshed for supervisor SHA-256 78b9e597cd66aee5d5582f232e38bec43105c614264b3736035e626cd3791c29; original reports remain preserved. The separate check evidence is joined only by .hexaemeron/reports/step-2-warden-round-1-validation-inventory.json, SHA-256 9fa96e49dcf58be87424b8fcf71cc914f19abaf396a222b8f6e0c303fa3fec8d; neither red runner report was rewritten. The fresh Elenchus parent report executed 2705 tests with two assertion failures, zero errors and zero skips. The source-owned fixed-and-guarded record is .hexaemeron/reports/step-2-warden-round-1-fixed-and-guarded.json, SHA-256 fa45dc1e87ae4e710bc0a31ea69b85e5b561fcc42bfb4898c24d072d78e2986f. Audit-filter declaration: sapheneia:sapheneia.

## Step 2, round 2 -- 2026-09-14T01:15:44Z

Audit schema: fiat-audit-round/v2

Covered: tool-bypass=reviewed; git-common-dir=reviewed; partial-reconstruction=reviewed; packet-omission=reviewed; origin-drift=reviewed; gate-probe-effects=reviewed; source-substitution=reviewed; false-closure=reviewed; descendant-lifetime=reviewed; controller-metadata=reviewed; inherited-authority=reviewed

Not checked: Controller launch admission, cumulative carryover, reconstruction, inoculation and command validation remain due in later steps. This second review covers the repaired Step 2 source at 9b7e4d01bd262c5769514b6f7f423a84ac419976 against whole-worker-sandbox. Native evidence covers this macOS host. Historical model observations and unchanged Hex tests were not rerun. The Solidity suite waiver still applies.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: S2-R1-01 remains fixed by 8215c5c360f5b2e8c2ae4497cf5d24f812d6f001. Supervisor, native tests and due resolver bytes are unchanged; both refreshed due observations still bind supervisor SHA-256 78b9e597cd66aee5d5582f232e38bec43105c614264b3736035e626cd3791c29. The seven evidence files referenced by the round-one validation inventory retain their digests, including the 2705/2705 Hex pass with zero failures, errors or skips. This round reuses those results and preserves their original source identities. Global metadata reads remain allowed, with no total scratch quota or aggregate descendant accounting. The original Hex exit -15 remains unexplained; suppression validation retains 232 candidates and repository=degraded. Fresh Phylax, Ephoros and Hypomnema each exited 0. The root commit gate writes .hexaemeron/reports/step-2-warden-round-2-audit-greenlight.log; its python3 -m unittest discover -s tests must exit 0 before signing this record. No fixes commit or new Elenchus classification belongs to this round. Audit-filter declaration: sapheneia:sapheneia.

## Step 3, round 1 -- 2026-09-14T04:20:39Z

Audit schema: fiat-audit-round/v2

Covered: tool-bypass=reviewed; git-common-dir=reviewed; partial-reconstruction=not-applicable; packet-omission=not-applicable; origin-drift=reviewed; gate-probe-effects=not-applicable; source-substitution=reviewed; false-closure=reviewed; descendant-lifetime=reviewed; controller-metadata=reviewed; inherited-authority=reviewed

Not checked: Cumulative reconstruction, carryover admission and command validation remain due in later steps. This round reviewed the full Step 3 diff from 0c0b90fe26a3db219955b96737a7838f0ecef377 through 327824807aa84debbd68b0ac71f786aea1aae51a and repair 49846a2b93eb6b641d4a06d5a84938849680dc32 against whole-worker-sandbox. Native execution covers this macOS host. The conversation's tools remain unrestricted. Historical model observations were not rerun. The recorded Solidity suite waiver applies.

Elenchus verdict: guarded

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S3-R1-01 | medium | plugins/hexaemeron/skills/fiat/scripts/worker_exec.py:748 | Admission compared origin before later reads and writes, so an independent edit during those operations still returned admitted. Three interleavings reproduced this. Recheck the declared inventory around promotion and before success, preserving independent edits, partial reports and unknown attribution. | fixed in 49846a2b93eb6b641d4a06d5a84938849680dc32 |
| S3-R1-02 | low | docs/fiat-508-residual/README.md:46 | The current conformance paragraph said only deadline and output-cap criteria execute; whole-launch-dispatch and origin-drift-recovery were already implemented. List all four while preserving historical evidence and refusal limits. | fixed in 49846a2b93eb6b641d4a06d5a84938849680dc32 |

Leads not pursued: Global metadata reads and literal /dev/null data I/O remain allowed. Detached descendant death, total scratch quota and aggregate resource limits are not established. Directory and origin rechecks detect observed changes; an edit after the final check remains outside their observation. Promotion can leave partial reports, and a reports-written marker alone does not establish admitted status. The pre-audit directory repair belongs to implementation commit 327824807aa84debbd68b0ac71f786aea1aae51a, not this round. Step 2's numeric sysctl environment guard and signal-before-reap ordering remain intact. Fresh native tests passed 28 before repair and 30 after repair. The declared 12-worker Hex command passed 2718 tests with zero failures, errors, skips or blocked fixtures; its raw report is .hexaemeron/reports/step-3-warden-round-1-hex-fixed-source.json. The normal repair greenlight ran python3 -m unittest discover -s tests and passed 1919 tests without skips. Fresh canonical Phylax and Ephoros over plugins, tests, scripts and docs exited 0; Hypomnema over the required root documents, plugins and docs exited 0. All four native conformance commands exited 0, and 13 source bindings match supervisor SHA-256 0451e288fd4b655cc716ff129dcc98c621482389d45437a63b0338dbae807ebd. The Hex producer ran against fixed code and tests while the README-only correction was completed; its output is not labelled an immutable committed-source snapshot. The later committed-tree checked runner passed all 11 selected checks with 3579 snapshot entries intact and removed; its root suite passed 1919 tests with one snapshot-only skip. Actual source identity 7f01d345542a107c3fe13f26d3b22198fc5ed70c0041bd89a1bdc0b2fc83433c matched immediately after the run on clean repair commit 49846a2b93eb6b641d4a06d5a84938849680dc32. Prior report and observation bytes were preserved. One occupied-report invocation refused with exit 2 before the producer was rerun. Elenchus against the repair commit executed 2718 parent tests with three assertion failures, zero errors and zero skips; its distinct verdict JSON is .hexaemeron/reports/step-3-warden-round-1-elenchus-verdict.json, SHA-256 a74d45f4b29eee93af6191f5ef6fa8232ab071a62bb2f984b82e333c4c20b89a. Guarded repair evidence does not supply a clean independent audit round. Audit-filter declaration: sapheneia:sapheneia.

## Step 3, round 2 -- 2026-09-14T04:46:22Z

Audit schema: fiat-audit-round/v2

Covered: tool-bypass=reviewed; git-common-dir=reviewed; partial-reconstruction=not-applicable; packet-omission=not-applicable; origin-drift=reviewed; gate-probe-effects=not-applicable; source-substitution=reviewed; false-closure=reviewed; descendant-lifetime=reviewed; controller-metadata=reviewed; inherited-authority=reviewed

Not checked: Cumulative reconstruction, carryover admission and command validation remain due in later steps. Review covers Step 3 through 2d8cfd32c821039a3fa7d0bdd5de19a3379c2301, including repair 49846a2b93eb6b641d4a06d5a84938849680dc32. Native checks cover this macOS host. The recorded Solidity waiver applies. Conversation tools remain unrestricted; historical model observations were not rerun.

Elenchus verdict: null

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| -- | -- | -- | none | -- |

Leads not pursued: No new finding. Fresh native tests passed 30 with no failures, errors or skips, including late origin edits, directory substitution, private capture, one-shot promotion and Step 2's numeric sysctl and signal-before-reap controls. Fresh canonical Phylax, Ephoros and Hypomnema exited 0. The declared root command is python3 -m unittest discover -s tests; the final audit-tree greenlight result belongs in this round's handoff. Global metadata reads and literal /dev/null data I/O remain allowed. Origin and directory checks detect observed changes; a change after the final check is outside their observation. Partial reports may survive refusal, and reports-written alone is not admitted status. Detached descendant death and aggregate scratch/resource quotas remain unproved. Round 1's raw producer, guarded verdict, 11-check committed-source report and clean source join remain unchanged inherited evidence. They were not rerun or relabelled as this round. Parent owns the two omitted roster checks and the full-step selection comparison. No fixes commit or Elenchus invocation belongs to round 2. Audit-filter declaration: sapheneia:sapheneia.
