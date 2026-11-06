# Both Wildcat estates: offline delivery proof

The [combined demonstration](../../examples/wildcat-estates-interval-v0/README.md)
rebuilds both externally preserved mainnet captures and the current Compound
release in one Python process with socket construction denied. Its complete
observations are pinned in `examples/wildcat-estates-interval-v0/expected.json`.
The separate `verify-preserved` operation checks committed metadata only;
it does not rebuild a release or read either archive.

## Executed criteria

| Criterion | Result | Observed evidence |
| --- | --- | --- |
| 1 to 3: both estate builds and offline rebuilds | Passed | V1: 16 subjects, 667 complete shards, 16 epochs; V2: 137 subjects, 3,463 complete shards, 137 epochs. Both release identifiers match their preserved pins. |
| 4 and 5: named refusals | Passed | The actual CLI build handler exits 1 for an unregistered venue and for a wrong format or changed registry pin in each estate. No refused release is installed. |
| 6: coverage parity | Passed | Both releases match every capture and nested coverage, source and scope field of Compound built in the same run. The nine recorded Compound coverage rows retain their field mapping. |
| 7: subjects and attribution | Passed | The declared sets intersect in exactly ArchController and Sentinel. Both reject foreign emitters. Real ArchController attribution counts are 54 for V1 and 215 for V2; Sentinel has zero in both. Constructed positive tests remain separate from these observations. |
| 8: V1 source identity | Passed | All 16 subjects match the registry generated from the pinned source records. Four have sourced deployment blocks, 12 retain explicit deployment-block gaps. Four equivalent commits remain alongside the recorded source commit; the deployer's exact checkout among those five is unknown. |
| 9: resource ceilings | Passed | Largest V1 component/journal: 4,461,512/4,461,382 bytes; V2: 25,079,138/7,617,883 bytes. Every one is below 67,108,864 bytes. |
| 10: Compound compatibility | Passed | The three existing interval demonstrations retain their own identifiers. Current Compound emits receipt v2 and release `sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a`; the historical live demo retains receipt v1 and `sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32`. |

The V1 release is
`sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`.
The V2 release is
`sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`.
Their individual examples bind the plans, registry, archive and each staging file.
The actual V1 production runtime is commit
`296a794d8bca1ad051d3b4d9cae1339f5e433571`; the later saved toolkit pin does
not change that capture provenance.

The eight [conformance reports](reports/conformance/) retain the selected
`venue-module-registry` candidate. Each resolver executed two named tests with
zero failures, errors or skips; the integration design check printed `clean`.
The legacy resolver name `v1-source-gap-declared` retains its original identity
while its assertions prove the corrected all-subject source claim.

## Collection measurements

The study budgets each estate's collection within a working day but gives no
numerical duration for that day. The V1 current-plan collect invocations total
1,346.269 seconds; the superseded wider-plan attempts add 552.012 seconds, for
1,898.281 seconds across all recorded collection attempts. Reconciliation took
85.966 seconds. First collection start to completed reconciliation spans
2,363.742001 seconds, including the two plan widths and resumed attempts.

The three recorded V2 collection invocations total 8,313 seconds and cover the
resume from checkpoint shard 1 to shard 3,463. The first shard's elapsed time
is not established by that log, so an exact whole-collection duration and a
strict whole-run budget verdict remain unestablished. All four recorded
reconciliation attempts total 8,715.343 seconds, including the unreconciled
and interrupted runs. The study sets no budget for reconciliation or rebuilding.
These figures come from the V1 capture-evidence and V2 rebuild-record files;
paired request speedups do not establish a whole-job speedup.

## Retained boundaries

The held `transaction-index-reconciliation` job is unchanged. Reconciliation
still omits the log's transaction index from its comparison tuple. Its agreement
cannot establish complete positional agreement. Targeted traces cover only
transactions with matching subject logs; logless transactions remain outside
the capture. Neither provider agreement nor digest verification establishes
publisher identity, completeness or canonical-chain finality.

Correction recorded 2026-09-22 for W8-R1-01: the earlier specification's claim
that every error string names the provider class was too broad. Structured
receipts carry `provider_class`; transport and CLI error strings may name only
the read or shard. Historical specifications and audit records remain intact.
The separate runbook command-count fix, issue
[#1762](https://github.com/wildcat-finance/skills/issues/1762), merged through
[#1814](https://github.com/wildcat-finance/skills/pull/1814); it does not change
that observed error-string boundary.
