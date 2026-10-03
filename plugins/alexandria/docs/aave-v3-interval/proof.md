# Aave V3 Ethereum interval: offline delivery proof

The [Aave demonstration](../../examples/aave-v3-interval-v0/README.md) holds the
registry, the segment table, twelve plans, one staging manifest and, for each of
the twelve segments, a rebuild record and expected values. Its `verify-preserved`
operation checks that committed metadata and rebuilds nothing. The twelve staging
trees are held outside the repository as one archive,
`sha256:45dc114a35ed9483fc5347827b048348308708766f299f857512a0ccc004e55a`,
4,288,061,802 bytes, holding 61,577 files of 94,973,293,482 bytes. Where the
runbook says every segment's manifest, this record reads the one manifest's
twelve per-segment sections, the layout Step 7 settled on.

## Executed criteria

Every command ran from the repository root on this branch. The fifteen
conformance resolvers each ran as
`python3 .hexaemeron/design/conformance.py <criterion> --candidate segmented-proxy-set-venue`
and exited 0 with zero failures, errors and skips; the `tests run` counts below
equal the counts each resolver required.

| Criterion | Result | Command and observed evidence |
| --- | --- | --- |
| 1: fixture plan builds and checks | Passed | Resolver `aave-fixture-rebuilds-offline-without-sockets`, exit 0, 2 tests run: the fixture build and `check` agree with Python sockets denied, and the fixture release declares constructed staging. |
| 2: registry reproduces the merged row | Passed | Resolvers `registry-reproduces-recorded-subject-set` and `registry-pin-change-refuses`, exit 0, 2 and 2 tests run. The 356 addresses hash to `289bbdf765e2e66f335f46706269dfbcc63600108d0ef5eb22ba814ecbcf8d64`, the role counts equal the row's, and the 22 listed contracts match. |
| 3: per-subject epochs | Passed | Resolver `per-subject-proxy-epochs-derived`, exit 0, 3 tests run: epochs follow upgrade positions, a pre-interval subject opens at the interval start, a proxy created in the interval opens at its creation block. The twelve committed segment records hold 3,524 epochs in all. |
| 4: named refusals | Passed | Resolvers `unsupported-upgrade-shapes-refuse` (4), `wrong-chain-or-market-refuses` (2), `registry-pin-change-refuses` (2), `other-venues-keep-upgrade-transaction-refusal` (2) and `collection-refusal-battery` (8), each exit 0. |
| 5: provider failure, dispute and resume | Passed | Resolver `collection-refusal-battery`, exit 0, 8 tests run: a provider failure leaves a receipt, a disagreement is disputed, an interrupted collection resumes to identical journals. |
| 6: index-only disagreement | Passed | Resolver `transaction-index-only-disagreement-declared`, exit 0, 3 tests run: a difference only in `transactionIndex` still records `agreed`, the release says agreement excludes transaction position, and `check` refuses a release without that sentence. The held reconciliation job still owns that gap. |
| 7: no credential or endpoint | Passed | Resolver `credential-absent-from-artefacts`, exit 0, 2 tests run. |
| 8: segment table | Passed | Resolvers `segment-plans-tile-the-interval` and `segment-budget-within-ceilings`, exit 0, 2 and 2 tests run. Twelve plans tile blocks 16,291,071 to 26,022,093; every digest is pinned. |
| 9: preflight record | Passed | Resolver `preflight-measurement-recorded`, exit 0, 2 tests run. |
| 10: every segment preserved and rebuilt | Passed | `python3 plugins/alexandria/examples/aave-v3-interval-v0/demo.py verify-preserved`, exit 0, `rebuild_performed` false, 12 of 12 segments with a rebuild record, 32,437 shards, every segment `agreed`. Resolver `production-segments-preserved-and-rebuilt`, exit 0, 3 tests run. Each record shows a fresh extraction rebuilding its collected release identifier with sockets denied, then `check` and `verify` exit 0; no segment records an overrun. Largest component 61,863,743 bytes and largest journal 61,863,621 bytes, both below 67,108,864. |
| 11: existing identifiers | Passed | `python3 plugins/alexandria/examples/usdc-interval-live-v0/demo.py build --output <fresh directory>`, exit 0, `release_id` `sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32`. `python3 plugins/alexandria/examples/usdc-interval-epochs-v0/demo.py build --output <fresh directory>`, exit 0, rebuilds `sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a`; `verify` exit 0. `wildcat-v1-interval-v0/demo.py verify-preserved` and `wildcat-v2-interval-v0/demo.py verify-preserved`, each exit 0. Resolver `existing-release-identities-retained`, exit 0, 4 tests run. |
| 12: repository stays green | Passed | `python3 scripts/run_checks.py --base fiat/1872-aave-v3-ethereum-interval-capture --scope root --scope alexandria --format json`, exit 0, outcome `green`: 12 selected checks, each exit 0, among them `alexandria-suite` (161.059 s) and `root-suite` (287.702 s). Run on the tree at the commit before this record. |

The fifteen reports are in [`reports/conformance/`](reports/conformance/).
`python3 plugins/hexaemeron/skills/protasis/scripts/design_evidence.py .hexaemeron/design-evidence.json --transition integration`
printed `clean` and exited 0. The full Alexandria suite: `python3 plugins/alexandria/tests/run_tests.py --elenchus-report .elenchus/aave-step-8.json` exit 0, 1,452 tests run, 0 failures, 0 errors, 10 skipped, 1,442 passed.

## Per-segment measurements against the Step 6 plan

Planned figures come from `segments.json`; built and measured figures come from
each segment's committed rebuild record. Bytes are release bytes built over
planned, and peak resident memory is the collecting host's `check` over the
planned peak. Wall seconds run from the first start to the last finish of that
stage and include gaps between invocations; invocation counts follow in
brackets. The table plans no per-segment time, so the durations have no plan to
overrun.

| Segment | Shards | Release bytes, built / planned | Largest component | Check peak memory, measured / planned | Collect wall s (invocations) | Reconcile wall s (invocations) |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 4,096 | 1,197,031,879 / 1,702,267,283 | 6,420,050 | 4,036,935,680 / 10,616,674,913 | 8,295 (4) | 1,203 (1) |
| 1 | 4,096 | 2,711,059,453 / 4,140,556,026 | 8,277,142 | 8,568,979,456 / 25,823,757,364 | 13,352 (8) | 1,283 (1) |
| 2 | 4,096 | 4,844,943,720 / 5,169,421,734 | 20,434,245 | 14,950,481,920 / 32,240,571,491 | 19,246 (14) | 1,957 (1) |
| 3 | 4,096 | 8,035,993,652 / 8,788,093,921 | 53,651,878 | 24,932,139,008 / 54,809,451,600 | 62,185 (36) | 2,958 (1) |
| 4 | 2,544 | 9,304,917,238 / 14,565,484,003 | 60,380,380 | 29,785,587,712 / 90,841,790,912 | 21,594 (34) | 32,671 (11) |
| 5 | 1,797 | 8,216,902,040 / 14,565,037,584 | 40,263,556 | 25,866,797,056 / 90,839,006,693 | 28,636 (38) | 158,666 (22) |
| 6 | 2,173 | 11,986,935,698 / 14,565,538,177 | 18,978,410 | 37,497,012,224 / 90,842,128,784 | 32,612 (45) | 84,344 (21) |
| 7 | 1,644 | 11,086,871,406 / 14,566,830,496 | 28,366,568 | 34,314,928,128 / 90,850,188,700 | 40,897 (44) | 44,497 (3) |
| 8 | 2,051 | 12,459,902,146 / 14,563,773,835 | 25,523,848 | 38,401,081,344 / 90,831,124,962 | 55,017 (49) | 5,365 (1) |
| 9 | 1,604 | 12,622,531,842 / 14,565,771,218 | 61,863,743 | 38,397,132,800 / 90,843,582,210 | 39,264 (58) | 5,730 (1) |
| 10 | 1,644 | 8,782,528,636 / 14,568,868,988 | 60,525,446 | 27,251,933,184 / 90,862,902,336 | 111,606 (36) | 4,072 (1) |
| 11 | 2,596 | 11,593,151,116 / 14,568,385,284 | 25,456,859 | 35,366,928,384 / 90,859,885,578 | 40,770 (46) | 5,276 (1) |

Totals: 102,842,768,826 release bytes built against 136,330,028,549 planned,
82,096 components, 32,437 shards and 412 collect invocations. Collect wall time
sums to 473,474 seconds and reconcile wall time to 348,022 seconds across 65
invocations; segment 5's 158,666 reconcile seconds and segment 10's 111,606
collect seconds are the longest.

No segment overran its planned bytes, components or peak memory. Two planning
assumptions did overrun and were ruled on by the maintainer, as `segments.json`
records. Segment 5's collect refused component 269's trace journal after two
shards held 44,614,996 bytes under three shards per component, so segments 5 to
11 take one shard per component. Segment 3's collect refused component 535 at
62,682,461 bytes after two shards, so segment 3 takes two shards per component.
Neither changed the shard width or the boundaries.

Collection ran through faults the rebuild records list: invocations that
stopped at the total byte ceiling, single-shard transport failures and trace
shards a second transport disputed. The run carried these fixes and processes:
[#1918] (a trace accepted from a syncing node), [#1928] and [#1929] (request
windows refill), [#1990] (`eth_getLogs` split at a node cap) and the supersede
commits for commits GitHub did not verify ([#2014], [#2042], [#2057], [#2059]).
Segment 4's reconciliation record predates the journal binding, so its release
reports `reconciliation_binding.status` `absent`; the other eleven report
`verified`. An interim reconcile disputed 1 trace shard in segment 5, 11 in
segment 6 and 6 in segment 7; each was collected again and the final
reconciliation of all twelve segments is `agreed` with 0 disputed items.

[#1918]: https://github.com/wildcat-finance/skills/issues/1918
[#1928]: https://github.com/wildcat-finance/skills/issues/1928
[#1929]: https://github.com/wildcat-finance/skills/issues/1929
[#1990]: https://github.com/wildcat-finance/skills/issues/1990
[#2014]: https://github.com/wildcat-finance/skills/issues/2014
[#2042]: https://github.com/wildcat-finance/skills/issues/2042
[#2057]: https://github.com/wildcat-finance/skills/issues/2057
[#2059]: https://github.com/wildcat-finance/skills/issues/2059

## Retained boundaries

The held `transaction-index-reconciliation` job is unchanged: reconciliation
still omits a log's transaction index from its comparison tuple. The second
transport is a hosted one held outside the repository and bound by digest, and
the primary is a local archive node. Provider agreement and digest checks
establish neither publisher identity, completeness nor canonical-chain
finality. Targeted traces cover transactions with matching subject logs only.
