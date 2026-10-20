# Wildcat withdrawal-batch retained reproduction

## What the check establishes

The Step 4 retained-conformance check rebuilt both retained Wildcat raw releases held in custody through the public Alexandria example builders, built a canonical release from each with the current `wildcat-canonical` mapping in a private temporary directory outside the repository, verified it offline and asked one question per generation: do the four batch signatures map, does every `withdrawal-batch-payment` row join one adjacent market burn, is every market burn claimed exactly once, and does `verify` pass. Both generations answered yes, so the report value is `true`.

Under Laurence's ruling of 2026-10-13 this record carries raw release identifiers, canonical and coverage digests and pass or refuse results only. No count of logs, rows, burns, joins or unsupported events from the retained releases appears here or in any committed file; those stay in private local reports.

## Commands

From the repository root with Python `3.14.6`, after restoring the two staging trees from custody into private directories:

```sh
export ALEXANDRIA_WILDCAT_V1_STAGING=<restored V1 staging tree>
export ALEXANDRIA_WILDCAT_V2_STAGING=<restored V2 staging tree>
python3 plugins/tabularium/tests/emit_wildcat_batch_report.py --step 4 --report .hexaemeron/steps/4/focused.json
python3 plugins/tabularium/tests/prove_wildcat_batches.py --candidate adjacent-burn --criterion retained-conformance --report .hexaemeron/design-reports/adjacent-burn-retained-conformance.json
python3 scripts/run_checks.py --base 50d71a2e8c1777f8eb26db32dd8adeadb34063bd --scope root --scope tabularium --scope repo-lints --format json
```

The first command runs the 13 Step 4 focused tests in process. They build constructed controls and refuse absent custody by variable name, so they pass on a clone without the staging trees. The second needs both trees: it checks each against `plugins/alexandria/examples/wildcat-v1-interval-v0/staging-manifest.json` or `plugins/alexandria/examples/wildcat-v2-interval-v0/staging-manifest.json`, rebuilds the raw release, maps it, verifies the result, removes the temporary directory and writes the boolean report with its sidecar. An unset or unreadable variable exits 2 with no report. The third is the checked runner over the root, Tabularium and repository-lint scopes.

## Result

Wildcat V1 rebuilt to raw release `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`; its canonical release has `events.jsonl` SHA-256 `215171799f649d9800e51c2ef054152d118a34d1fcf1926f796fdac66821c525` and `coverage.json` SHA-256 `596cb7206bc9c25200ac87d88c53f203386a5e14d4994701503afe842c2b2029`, and it passed. Wildcat V2 rebuilt to raw release `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`; its canonical release has `events.jsonl` SHA-256 `9ee23127623b34c11825761ed4c8f73d3274f41d8e3f1d82d6d232bde7a6b37c` and `coverage.json` SHA-256 `04771ba30d022088b2f2585dca500f29074f662bcc93acc45b1170e18bf2f34b`, and it passed.

The report at `.hexaemeron/design-reports/adjacent-burn-retained-conformance.json` holds `value: true`, `unit: boolean`, `exit: 0` and the exact resolver command from the design record. Its `.observations.json` sidecar holds the two identifiers, the four digests and `passed_generations: ["wildcat-v1", "wildcat-v2"]`. Each raw release identifier equals the `release_id` its public example pins in `expected.json`; the example's own `verify` compared the rebuilt release with that pin before the mapping ran. The canonical and coverage digests are of the canonical release this tree's adapter builds from those raw releases. They differ from the design-phase `retained-join-closure` digests under `design-reports/`, which were taken before Step 2 mapped the four events.

## Duration

One run of the second command took 107.21 seconds of wall clock on the delivering host, measured with `/usr/bin/time -p`. This is one observation of one run and carries no performance claim.

## Constructed controls

The Step 4 focused tests ran 13 tests with failures, errors and skips all 0. They hold the resolver to refusal by variable name with exit 2 and no report when a staging variable is unset, relative, missing, a regular file, a symlink or an unreadable directory; refusal when a staging tree fails its manifest; a boolean report and a sidecar of identifiers and digests only; `false` rather than a passing report on a constructed control with an unclaimed market burn or a payment without its burn, and on each of the five hostile shapes; and removal of the temporary directory after success, after a false result and after refusal. Every control is built from the constructed transactions in `plugins/tabularium/tests/wildcat_batch_fixtures.py`, so no retained byte is read.

## What stays unestablished

A passing check establishes that the current mapping gives the four batch events native meaning in both retained releases and joins every payment in them to one adjacent market burn. It does not establish historical completeness of either capture, provider independence, finality, a chain proof, lender receipt of any amount, unpaid-batch status, account-level withdrawal status, identity, settlement or current standing. `reserved-assets` stays an amount set aside in the market. A plain `repay` only returns funds to the market, and only `repayAndProcessUnpaidWithdrawalBatches` allocates them to batches. The adapter infers no batch event's cause from the action sharing its transaction. Queue replay and unpaid-status projection stay with issue 1926, accounting replay with issue 1386 and function reconciliation with issue 1387.
