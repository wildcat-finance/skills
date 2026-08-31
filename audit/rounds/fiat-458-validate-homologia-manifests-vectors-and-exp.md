## Step 1, round 1 -- 2026-08-31T11:57:45Z

Audit schema: fiat-audit-round/v2

Covered: path-containment=reviewed; descriptor-race=reviewed; cap-before-decode=reviewed; duplicate-json-key=reviewed; scale-identity=reviewed; proved-provenance=reviewed; provenance-strengthening=reviewed; tolerance-declaration=reviewed; partial-write=reviewed; deterministic-record=reviewed

Not checked: X-Ray, Solidity Auditor, Solidity, EVM execution, network or RPC behaviour, and mirror execution; the recorded security suite waiver applies to this non-Solidity step

Elenchus verdict: inconclusive

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R1-01 | high | plugins/homologia/scripts/homologia.py:622 | On a case-insensitive filesystem, an output spelling that aliases a manifest or vector input bypassed lexical path equality and atomically replaced that input. | fixed in this commit |
| S1-R1-02 | medium | plugins/homologia/scripts/homologia.py:287 | JSON-escaped unpaired surrogates and oversized integer tokens escaped the stable refusal boundary as uncaught `UnicodeEncodeError` or `ValueError`; both failures preserved an existing output. | fixed in this commit |
| S1-R1-03 | low | .agents/skills/promise-machine/runtime/plugins/homologia/skills/homologia/EVOLUTION.md:16 | The installed-runtime ledger linked to an absent `../../tests/test_check.py`, so the first Hypomnema pass exited 1. | fixed in this commit |

Leads not pursued: Concurrent parent-directory symlink substitution between lexical inspection and descriptor open or output replacement was not reproduced; the declared step covers existing symlinks and named-file replacement, not an adversarial directory owner. The aggregate check may read at most one extra per-file-capped input before refusal, but it refuses before JSON decoding and output as declared. Elenchus remained inconclusive because the source-bound runbook supplies the unittest command but no report format or report file; no substitute runner was used.

## Step 1, round 2 -- 2026-08-31T12:17:12Z

Audit schema: fiat-audit-round/v2

Covered: path-containment=reviewed; descriptor-race=reviewed; cap-before-decode=reviewed; duplicate-json-key=reviewed; scale-identity=reviewed; proved-provenance=reviewed; provenance-strengthening=reviewed; tolerance-declaration=reviewed; partial-write=reviewed; deterministic-record=reviewed

Not checked: X-Ray, Solidity Auditor, Solidity, EVM execution, network or RPC behaviour, and mirror execution; the recorded security suite waiver applies to this non-Solidity step

Elenchus verdict: inconclusive

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R2-01 | medium | plugins/homologia/scripts/homologia.py:607 | Uniqueness covered descriptor strings but not file identity, so two declared names for one vector file were admitted as two sets; a case-insensitive alias reproduced a checked record with `vector_set_count` 2. | fixed in this commit |
| S1-R2-02 | medium | plugins/homologia/scripts/homologia.py:369 | A `recorded` expected answer with chain id 43114 was admitted under a pair pinned to chain id 1, misbinding the expected evidence to the declared computation. | fixed in this commit |
| S1-R2-03 | low | plugins/homologia/references/manifest-v1.schema.json:11; plugins/homologia/references/vectors-v1.schema.json:10 | Both published path schemas admitted `./vectors.jsonl`, `nested/./vectors.jsonl` and `nested/`, although the authoritative validator refuses their dot or empty components. | fixed in this commit |

Leads not pursued: The round-1 output-alias, unpaired-surrogate, oversized-integer and installed-ledger regressions remain fixed-green; the focused six-test repair set and 51-test `test_check` suite passed. The concurrent parent-directory substitution and one-extra-bounded-read leads remain outside the declared boundary or fail before decode and output as recorded in round 1. No further candidate crossed the supported-input and observable-consequence threshold during the ten-risk manual review. Elenchus remained inconclusive because the immutable runbook declares the unittest command but no report format or report file; no substitute runner was used. The mandated audit filter is exactly `--audit-filter sapheneia:sapheneia`. The frozen heading, schema, ten risk ids, waiver, verdict, three finding ids, severities, paths, reproductions and fixed statuses match this record item by item; the round-1 bytes were preserved as the prefix with SHA-256 `4868e5bba77d854dce7d690fd9dfa0c380169a2fd6c1fd245053d958f3be8bd0`.

## Step 1, round 3 -- 2026-08-31T12:37:13Z

Audit schema: fiat-audit-round/v2

Covered: path-containment=reviewed; descriptor-race=reviewed; cap-before-decode=reviewed; duplicate-json-key=reviewed; scale-identity=reviewed; proved-provenance=reviewed; provenance-strengthening=reviewed; tolerance-declaration=reviewed; partial-write=reviewed; deterministic-record=reviewed

Not checked: X-Ray, Solidity Auditor, Solidity, EVM execution, network or RPC behaviour, and mirror execution; the recorded security suite waiver applies to this non-Solidity step

Elenchus verdict: inconclusive

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R3-01 | medium | plugins/homologia/scripts/homologia.py:201 | A FIFO supplied as the manifest blocked in `os.open` before the regular-file refusal; the CLI exceeded the 1.0-second reproducer timeout without a stable code or output. | fixed in this commit |
| S1-R3-02 | low | plugins/homologia/references/manifest-v1.schema.json:5; plugins/homologia/references/vectors-v1.schema.json:4; plugins/homologia/docs/schema-compatibility.md:43 | The published schemas admitted whitespace-only function or author fields, newline-suffixed scalar forms and NUL-bearing paths that the authoritative checker refused. Draft 2020-12 also classifies the numeric value `18.0` as an integer although the checker refuses that source token. | fixed in this commit |

Leads not pursued: All six round-1 and round-2 fixes remain fixed-green, as do the two round-3 guards; the 53-test focused suite and 73-test complete Homologia suite passed. Concurrent parent-directory substitution remains outside the declared non-adversarial-directory boundary, and the aggregate cap may read one additional per-file-capped input but still refuses before decoding it or writing output. Cross-set reuse of a vector id has no reproduced collision because records retain their vector-set identity; the focused runbook guard and refusal scope ids within a set. The representable schema mismatches now refuse, while the unavoidable JSON Schema numeric-value equivalence for `18.0` is declared and the original-token checker remains authoritative. Elenchus remained inconclusive because the immutable runbook declares the unittest command but no report format or report file; no substitute runner was used. The mandated audit filter is exactly `--audit-filter sapheneia:sapheneia`. The frozen heading, schema, ten risk ids, waiver, verdict, two finding ids, severities, paths, reproductions, qualifications and fixed statuses match this shaped record item by item; the round-1 and round-2 bytes were preserved as the prefix with SHA-256 `bb31931d0b0164cd2ce46595c5926404173b256ee726ed6d44abbfe6e9f6db8e`.

## Step 1, round 4 -- 2026-08-31T12:56:59Z

Audit schema: fiat-audit-round/v2

Covered: path-containment=reviewed; descriptor-race=reviewed; cap-before-decode=reviewed; duplicate-json-key=reviewed; scale-identity=reviewed; proved-provenance=reviewed; provenance-strengthening=reviewed; tolerance-declaration=reviewed; partial-write=reviewed; deterministic-record=reviewed

Not checked: X-Ray, Solidity Auditor, Solidity, EVM execution, network or RPC behaviour, and mirror execution; the recorded security suite waiver applies to this non-Solidity step

Elenchus verdict: inconclusive

| id | severity | file | finding | status |
| --- | --- | --- | --- | --- |
| S1-R4-01 | low | plugins/homologia/scripts/homologia.py:458 | The JSONL reader used Python's broad `splitlines()` boundary: U+0085, U+2028 and U+2029 inside valid JSON strings refused with `HOM-CHECK-JSON` and no output, while bare CR between two JSON objects was admitted as two records and wrote output. | fixed in this commit |

Leads not pursued: All eight round-1 through round-3 fixes remain fixed-green, as do the three round-4 separator guards; the 56-test focused suite and 76-test complete Homologia suite passed. Concurrent parent-directory substitution remains outside the declared non-adversarial-directory boundary, and the aggregate cap may read one additional per-file-capped input but still refuses before decoding it or writing output. Cross-set reuse of a vector id has no reproduced collision because records retain their vector-set identity; the focused runbook guard and refusal scope ids within a set. The representable schema mismatches remain closed, while the unavoidable JSON Schema numeric-value equivalence for `18.0` is declared and the original-token checker remains authoritative. No further candidate crossed the supported-input and observable-consequence threshold during the ten-risk manual review. Elenchus remained inconclusive because the immutable runbook declares the unittest command but no report format or report file; no substitute runner was used. The mandated audit filter is exactly `--audit-filter sapheneia:sapheneia`. The frozen heading, schema, ten risk ids, waiver, verdict, finding id, severity, path, reproductions, qualifications and fixed status match this shaped record item by item; all three earlier round records were preserved as the prefix with SHA-256 `98200544a488d9cde1be14e1191c3ba753e4c6a472d1d94620087e78cd625c18`.
