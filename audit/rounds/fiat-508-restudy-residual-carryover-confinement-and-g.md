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
