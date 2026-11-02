# Wildcat accrual and state-update retained reproduction

## What the check establishes

The Step 4 retained-conformance check rebuilt both retained Wildcat raw releases held in custody through the public Alexandria example builders. It built a canonical release from each with the current `wildcat-canonical` mapping in a private temporary directory outside the repository, verified it offline and asked one question per generation: do `InterestAndFeesAccrued` and `StateUpdated` map with the selected `abi-named-amounts` meaning, and does `verify` pass?

That meaning is checked on every row of either event. The market that emitted the log is the only party, as `pool`, and each decoded field equals its word in the preserved log. An `interest-and-fees-accrued` row carries `scale-factor`, `base-interest-ray`, `delinquency-fee-ray` and `protocol-fees` in that order, and a `state-updated` row carries `scale-factor` alone, each with `base_units` equal to its decoded field. The three ray kinds are assetless. `protocol-fees` names the market's asset, or leaves it null with the gap `attribution:interest-and-fees-accrued:asset`. `fromTimestamp`, `toTimestamp` and `isDelinquent` stay in the mapping record's `decoded` object and in `native_record`. Each row is `primary`, joins no other event and carries only `wildcat-context:` supporting selectors, and neither signature nor its topic stays in unsupported coverage.

A generation whose canonical release maps no row of either event refuses by generation name instead of passing, so a `true` report says both events were exercised in both generations. Both generations passed, so the report value is `true`.

Under the study's public-record rule this record carries raw release identifiers, canonical and coverage digests and pass or refuse results only. No count of logs, rows, events, gaps or amounts from the retained releases appears here or in any committed file; those stay in a private local report.

## Commands

From the repository root with Python `3.14.6`, after restoring the two staging trees from custody into private directories:

```sh
export ALEXANDRIA_WILDCAT_V1_STAGING=<restored V1 staging tree>
export ALEXANDRIA_WILDCAT_V2_STAGING=<restored V2 staging tree>
python3 plugins/tabularium/tests/emit_wildcat_accrual_report.py --step 4 --report .hexaemeron/steps/4/focused.json
python3 plugins/tabularium/tests/prove_wildcat_accrual.py --candidate abi-named-amounts --criterion retained-conformance --report .hexaemeron/design/reports/abi-named-amounts-retained-conformance.json
python3 scripts/run_checks.py --base 1fc995e72cc61267273abd8339a9c1fb2289b068 --scope root --scope tabularium --scope repo-lints --format json
```

The first command runs the 12 Step 4 focused tests in process. They build constructed controls and refuse absent custody by variable name, so they pass on a clone without the staging trees. The second needs both trees. It checks each against `plugins/alexandria/examples/wildcat-v1-interval-v0/staging-manifest.json` or `plugins/alexandria/examples/wildcat-v2-interval-v0/staging-manifest.json`, rebuilds the raw release, maps it, verifies the result, removes the temporary directory and writes the boolean report with its sidecar. An unset or unreadable variable exits 2 with no report. The third is the checked runner over the root, Tabularium and repository-lint scopes.

## Result

Wildcat V1 rebuilt to raw release `sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69`; its canonical release has `events.jsonl` SHA-256 `a1b52ef5a20f5a4e2500b3e842ddd425cd793be172f779f41605d4beda04f772` and `coverage.json` SHA-256 `3ff617715d3ebada247bc15c10e1773ada289c678f6df77329707b1956532619`, and it passed. Wildcat V2 rebuilt to raw release `sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3`; its canonical release has `events.jsonl` SHA-256 `f2522f40c609cb15a636f9bf84ee83ec61e787cfe587abf2e6a26af7d0449141` and `coverage.json` SHA-256 `4849bf841eae4da66987c106674157c388f2332d7aeae28bbd4f55c459c11c0d`, and it passed.

The report at `.hexaemeron/design/reports/abi-named-amounts-retained-conformance.json` holds `value: true`, `unit: boolean`, `exit: 0` and the exact resolver command from the design record. Its `.observations.json` sidecar holds the two identifiers, the four digests and `passed_generations: ["wildcat-v1", "wildcat-v2"]`. Each raw release identifier equals the `release_id` its public example pins in `expected.json`, and the example's own `verify` compared the rebuilt release with that pin before the mapping ran. The same two identifiers appear in `docs/kickoff/2087/reproduction.md`. The canonical and coverage digests are of the canonical releases this tree's adapter builds from those raw releases under the names `wildcat-v1-retained-conformance` and `wildcat-v2-retained-conformance`. Step 4 audit round 1 then made the check compare each decoded field with its word in the preserved log and each party with the log's emitter; run again from a scratch directory with the same arguments, it wrote the same report and sidecar bytes.

## Duration

One run of the second command took 134.98 seconds of wall clock on the delivering host, measured with `/usr/bin/time -p`. This is one observation of one run and carries no performance claim.

## Constructed controls

The Step 4 focused tests ran 12 tests with failures, errors and skips all 0. They hold the resolver to:

- refusal by variable name with exit 2 and no report when a staging variable is unset, and refusal by variable name before any temporary directory exists when it is relative, missing, a regular file, a symlink or an unreadable directory;
- refusal when a staging tree fails its manifest, and when the temporary root lies inside the repository;
- refusal by generation name, with exit 2 and no report, when a constructed generation maps no row of either event, whether it holds no log, batch logs only, state writes only or accruals only;
- a boolean report and a sidecar of identifiers and digests only;
- `false` rather than a passing report when a constructed generation's second emitter has no concrete ABI, so its accrual and state-update logs stay `unsupported-decode` gaps, and `false` when a built release fails `verify`;
- `false` from the release check on each of 29 edits to a built control's rows, mapping records, dispositions or coverage; and
- removal of the temporary directory after success, after a false result and after refusal.

The constructed controls come from the accrual specimen's transactions through `plugins/tabularium/tests/wildcat_accrual_public_fixtures.py`, and the custody cases use temporary trees, so no retained byte is read.

## What stays unestablished

A passing check establishes that the current mapping gives `InterestAndFeesAccrued` and `StateUpdated` the selected native meaning in both retained releases and that `verify` passes on each canonical release. It does not establish historical completeness of either capture, provider independence, finality, a chain proof, identity, settlement, accounting or current standing. The three ray kinds are ratios, not asset quantities, and `protocol-fees` is accrued, not collected or paid. `isDelinquent` does not establish when delinquency began, a penalty or current standing. The adapter infers no event's cause from events sharing its transaction and does not equate the two events' `scale-factor` amounts. Accrual replay and delinquency projection stay outside this run.
