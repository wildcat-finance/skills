# Reproduce Wildcat sanctioned-account routing

## Source commands

Run from the repository root with Python `3.14.6`. Each destination must be absent. The two `-step-3` destinations are the study amendment's fresh reruns; original Step 2 proof files remain unchanged design-transition inputs.

```bash
python3 plugins/tabularium/tests/prove_wildcat_sanctions.py --candidate unique-key --criterion semantic-conformance --report .hexaemeron/reports/unique-key-semantic-conformance-step-3.json
python3 plugins/tabularium/tests/prove_wildcat_sanctions.py --candidate unique-key --criterion release-compatibility --report .hexaemeron/reports/unique-key-release-compatibility-step-3.json
python3 plugins/tabularium/tests/prove_wildcat_sanctions.py --candidate unique-key --criterion retained-coverage --report .hexaemeron/reports/unique-key-retained-coverage.json
python3 plugins/tabularium/tests/emit_wildcat_sanctions_report.py --step 3 --report .hexaemeron/step-3-check.json
python3 plugins/tabularium/examples/wildcat-v1-sanctions-v0/rebuild.py
python3 plugins/tabularium/examples/wildcat-v2-sanctions-v0/rebuild.py
python3 scripts/run_checks.py --base 8b4e137917d754a7b7c3d5e74d141c0bedf70aa2 --scope root --scope tabularium --scope repo-lints --jobs 8 --format json
```

The retained command requires the separately held staging trees named by `ALEXANDRIA_WILDCAT_V1_STAGING` and `ALEXANDRIA_WILDCAT_V2_STAGING`. Missing custody refuses with exit 2 and no proof report. Do not substitute constructed fixtures for those inputs. No network or new historical capture is involved.

## Recorded evidence

[Study](study.md) preserves the original specification and both append-only corrections. [Design evidence](design-evidence.json) and its original 15 selection reports retain their historical bytes. The [execution record](reports/step-3-execution.json) binds the actual proof and focused-profile results. Constructed V1/V2 specimens independently exercise escrow transfer routing, V2 queue routing, simultaneous batch-burn/routing relations, and missing or ambiguous complete-key matches. All old native and batch examples rebuild with explicit original adapter `1.0.0`; new specimens use `1.3.0`.

The retained resolver validates both complete staging inventories before building, rebuilds each raw release through its Alexandria owner, verifies raw identity, builds explicit `1.3.0` outputs and invokes full canonical verification. It rechecks both staging inventories after the builds. A present companion with no unique eligible primary, any unexplained routing gap or a nonreciprocal relation refuses. Public observations retain release identifiers, digests and bounded outcomes only.

## Limits and cleanup

`checked-absence` covers only the verified finite inputs. It supplies no positive historical join, global no-event conclusion, provider completeness, sanction status, identity, policy or settlement claim. The two supporting routing joins remain separate from #2090's `AccountSanctioned` meaning. Composition with #2089/#2090 waits for their actual landed deliveries; this isolated product supports only `1.0.0` and `1.3.0`.

The 16 Step 3 tests pass in normal, safe-path, owned isolated-Python and native Darwin deny-process-fork profiles. A separate actual fork probe fails with permission denied. The Popen sentinel is process instrumentation; the native sandbox and failed probe supply the narrower operating-system observation. Reports distinguish assertion failures, infrastructure errors and skips. These observations do not establish whole-system isolation.

Owned temporary outputs are removed on success, refusal and Python interruption, with controls exercising each route. An uncatchable forceful process kill can leave scratch; it must be inspected before removal. Retained inputs and historical evidence are preserved. Fiat uses ordinary phase receipts; no optional controller success-criteria receipt is claimed. Formal parent-guard classifications remain the actual recorded results and never inherit these passing owned-environment controls. Publication and integration are separate pending operations.
